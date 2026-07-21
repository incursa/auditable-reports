[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$skillRoot = Join-Path $repoRoot 'skill\create-auditable-reports'
$exampleRoot = Join-Path $skillRoot 'assets\examples\project-health'

Write-Host 'Compiling Python utilities...'
$previousPycachePrefix = $env:PYTHONPYCACHEPREFIX
$env:PYTHONPYCACHEPREFIX = Join-Path $repoRoot '.work\pycache'
try {
    Get-ChildItem -LiteralPath (Join-Path $skillRoot 'scripts') -Filter '*.py' | ForEach-Object {
        py -m py_compile $_.FullName
        if ($LASTEXITCODE -ne 0) {
            throw "Python compilation failed: $($_.FullName)"
        }
    }
}
finally {
    $env:PYTHONPYCACHEPREFIX = $previousPycachePrefix
}

node --check (Join-Path $skillRoot 'scripts\render_paged_output.mjs')
if ($LASTEXITCODE -ne 0) {
    throw 'Paged.js renderer syntax check failed.'
}

Write-Host 'Checking the shipped report fixture...'
py (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --html (Join-Path $exampleRoot 'report.html') `
    --print-html (Join-Path $exampleRoot 'report_print.html') `
    --paged-html (Join-Path $exampleRoot 'report_paged.html') `
    --pdf (Join-Path $exampleRoot 'report.pdf')
if ($LASTEXITCODE -ne 0) {
    throw 'Report fixture validation failed.'
}

$pagedJs = Join-Path $repoRoot 'node_modules\pagedjs'
$puppeteerCore = Join-Path $repoRoot 'node_modules\puppeteer-core'
if (-not (Test-Path -LiteralPath $pagedJs) -or -not (Test-Path -LiteralPath $puppeteerCore)) {
    throw 'Paged.js dependencies are missing. Run npm install at the repository root.'
}

Write-Host 'Regenerating paginated HTML and PDF smoke outputs...'
$smokeRoot = Join-Path $repoRoot '.work\paged-smoke'
$smokeHtml = Join-Path $smokeRoot 'report_paged.html'
$smokePdf = Join-Path $smokeRoot 'report.pdf'
py (Join-Path $skillRoot 'scripts\render_paged_output.py') `
    --input (Join-Path $exampleRoot 'report_print.html') `
    --output $smokeHtml
if ($LASTEXITCODE -ne 0) {
    throw 'Paged.js HTML smoke render failed.'
}
py (Join-Path $skillRoot 'scripts\render_paged_output.py') `
    --input (Join-Path $exampleRoot 'report_print.html') `
    --output $smokePdf
if ($LASTEXITCODE -ne 0) {
    throw 'Paged.js PDF smoke render failed.'
}
py (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --html (Join-Path $exampleRoot 'report.html') `
    --print-html (Join-Path $exampleRoot 'report_print.html') `
    --paged-html $smokeHtml `
    --pdf $smokePdf
if ($LASTEXITCODE -ne 0) {
    throw 'Regenerated Paged.js output validation failed.'
}
$fixturePagedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $exampleRoot 'report_paged.html')).Hash
$smokePagedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $smokeHtml).Hash
if ($fixturePagedHash -ne $smokePagedHash) {
    throw 'Paginated HTML is not deterministic after transient Paged.js identifiers are removed.'
}

$skillValidator = Join-Path $env:USERPROFILE '.codex\skills\.system\skill-creator\scripts\quick_validate.py'
if (Test-Path -LiteralPath $skillValidator) {
    Write-Host 'Validating skill metadata and layout...'
    py $skillValidator $skillRoot
    if ($LASTEXITCODE -ne 0) {
        throw 'Skill validation failed.'
    }
}
else {
    Write-Warning "Skill validator not found: $skillValidator"
}

Write-Host 'PASS: repository checks succeeded.'
