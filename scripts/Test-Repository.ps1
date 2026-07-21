[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$skillRoot = Join-Path $repoRoot 'skill\create-auditable-reports'
$exampleRoot = Join-Path $skillRoot 'assets\examples\project-health'
$dslRoot = Join-Path $skillRoot 'assets\examples\report-markdown'
$testLibraryRoot = Join-Path $skillRoot 'assets\examples\test-library'

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

Write-Host 'Testing the Report Markdown compiler...'
py -m unittest discover -s (Join-Path $repoRoot 'tests') -p 'test_*.py'
if ($LASTEXITCODE -ne 0) {
    throw 'Report Markdown compiler tests failed.'
}
py (Join-Path $skillRoot 'scripts\compile_report.py') `
    --input (Join-Path $dslRoot 'report.report.md') `
    --output (Join-Path $dslRoot 'artifact.json') `
    --check
if ($LASTEXITCODE -ne 0) {
    throw 'Report Markdown golden artifact is stale.'
}
Get-ChildItem -LiteralPath $testLibraryRoot -Directory | Sort-Object Name | ForEach-Object {
    $source = Join-Path $_.FullName 'report.report.md'
    $artifact = Join-Path $_.FullName 'artifact.json'
    if (-not (Test-Path -LiteralPath $source) -or -not (Test-Path -LiteralPath $artifact)) {
        throw "Test-library fixture is incomplete: $($_.FullName)"
    }
    py (Join-Path $skillRoot 'scripts\compile_report.py') --input $source --output $artifact --check
    if ($LASTEXITCODE -ne 0) {
        throw "Test-library artifact is stale: $($_.Name)"
    }
}

node --check (Join-Path $skillRoot 'scripts\render_paged_output.mjs')
if ($LASTEXITCODE -ne 0) {
    throw 'Paged.js renderer syntax check failed.'
}
node --check (Join-Path $skillRoot 'scripts\render_chartjs_output.mjs')
if ($LASTEXITCODE -ne 0) {
    throw 'Chart.js renderer syntax check failed.'
}

Write-Host 'Checking the shipped report fixture...'
py (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --html (Join-Path $exampleRoot 'report.html') `
    --print-html (Join-Path $exampleRoot 'report_print.html') `
    --charted-html (Join-Path $exampleRoot 'report_charted.html') `
    --paged-html (Join-Path $exampleRoot 'report_paged.html') `
    --pdf (Join-Path $exampleRoot 'report.pdf')
if ($LASTEXITCODE -ne 0) {
    throw 'Report fixture validation failed.'
}

$pagedJs = Join-Path $repoRoot 'node_modules\pagedjs'
$puppeteerCore = Join-Path $repoRoot 'node_modules\puppeteer-core'
$chartJs = Join-Path $repoRoot 'node_modules\chart.js'
if (-not (Test-Path -LiteralPath $pagedJs) -or -not (Test-Path -LiteralPath $puppeteerCore) -or -not (Test-Path -LiteralPath $chartJs)) {
    throw 'Chart.js/Paged.js dependencies are missing. Run npm install at the repository root.'
}

Write-Host 'Regenerating Chart.js, paginated HTML, and PDF smoke outputs...'
$smokeRoot = Join-Path $repoRoot '.work\paged-smoke'
$smokeCharted = Join-Path $smokeRoot 'report_charted.html'
$smokeHtml = Join-Path $smokeRoot 'report_paged.html'
$smokePdf = Join-Path $smokeRoot 'report.pdf'
py (Join-Path $skillRoot 'scripts\render_chartjs_output.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --input (Join-Path $exampleRoot 'report_print.html') `
    --output $smokeCharted
if ($LASTEXITCODE -ne 0) {
    throw 'Chart.js HTML smoke render failed.'
}
py (Join-Path $skillRoot 'scripts\render_paged_output.py') `
    --input $smokeCharted `
    --output $smokeHtml
if ($LASTEXITCODE -ne 0) {
    throw 'Paged.js HTML smoke render failed.'
}
py (Join-Path $skillRoot 'scripts\render_paged_output.py') `
    --input $smokeCharted `
    --output $smokePdf
if ($LASTEXITCODE -ne 0) {
    throw 'Paged.js PDF smoke render failed.'
}
py (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --html (Join-Path $exampleRoot 'report.html') `
    --print-html (Join-Path $exampleRoot 'report_print.html') `
    --charted-html $smokeCharted `
    --paged-html $smokeHtml `
    --pdf $smokePdf
if ($LASTEXITCODE -ne 0) {
    throw 'Regenerated Paged.js output validation failed.'
}
$fixtureChartedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $exampleRoot 'report_charted.html')).Hash
$smokeChartedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $smokeCharted).Hash
if ($fixtureChartedHash -ne $smokeChartedHash) {
    throw 'Chart.js HTML is not deterministic in the validated browser environment.'
}
$fixturePagedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $exampleRoot 'report_paged.html')).Hash
$smokePagedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $smokeHtml).Hash
if ($fixturePagedHash -ne $smokePagedHash) {
    throw 'Paginated HTML is not deterministic after transient Paged.js identifiers are removed.'
}

Write-Host 'Building the Report Markdown end-to-end fixture...'
$dslSmokeRoot = Join-Path $repoRoot '.work\dsl-smoke'
py (Join-Path $skillRoot 'scripts\build_report_bundle.py') `
    --input (Join-Path $dslRoot 'report.report.md') `
    --output-dir $dslSmokeRoot
if ($LASTEXITCODE -ne 0) {
    throw 'Report Markdown bundle build failed.'
}
py (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $dslSmokeRoot 'artifact.json') `
    --html (Join-Path $dslSmokeRoot 'report.html') `
    --print-html (Join-Path $dslSmokeRoot 'report_print.html') `
    --charted-html (Join-Path $dslSmokeRoot 'report_charted.html') `
    --paged-html (Join-Path $dslSmokeRoot 'report_paged.html') `
    --pdf (Join-Path $dslSmokeRoot 'report.pdf')
if ($LASTEXITCODE -ne 0) {
    throw 'Report Markdown bundle validation failed.'
}
$fixtureDslHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $dslRoot 'artifact.json')).Hash
$smokeDslHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $dslSmokeRoot 'artifact.json')).Hash
if ($fixtureDslHash -ne $smokeDslHash) {
    throw 'Report Markdown compilation is not deterministic.'
}
$dslHtml = Get-Content -Raw -LiteralPath (Join-Path $dslSmokeRoot 'report.html')
if ($dslHtml -notmatch '<pre><code>SELECT' -or $dslHtml -notmatch 'data:image/svg\+xml;base64,') {
    throw 'Report Markdown output lacks the expected code block or embedded figure.'
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
