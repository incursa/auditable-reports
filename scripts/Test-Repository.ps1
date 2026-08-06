[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$skillRoot = Join-Path $repoRoot 'skill\create-auditable-reports'
$exampleRoot = Join-Path $skillRoot 'assets\examples\project-health'
$dslRoot = Join-Path $skillRoot 'assets\examples\report-markdown'
$testLibraryRoot = Join-Path $skillRoot 'assets\examples\test-library'

$pythonCommand = Get-Command py -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $pythonCommand) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $pythonCommand) {
    throw 'Python 3 was not found. Install Python or put py/python3 on PATH.'
}
$python = $pythonCommand.Source

function Get-DeterminismHash {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [switch]$NormalizeRaster
    )

    $content = (Get-Content -Raw -LiteralPath $LiteralPath) -replace "`r`n", "`n"
    if ($NormalizeRaster) {
        # Chart.js embeds a PNG whose bytes can differ across compatible browser
        # builds even when the chart structure and data are identical.
        $content = [regex]::Replace(
            $content,
            'data:image/png;base64,[A-Za-z0-9+/=]+',
            'data:image/png;base64:<normalized-raster>'
        )
    }
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $sha.Dispose()
    }
}

Write-Host 'Compiling Python utilities...'
$previousPycachePrefix = $env:PYTHONPYCACHEPREFIX
$env:PYTHONPYCACHEPREFIX = Join-Path $repoRoot '.work\pycache'
try {
    Get-ChildItem -LiteralPath (Join-Path $skillRoot 'scripts') -Filter '*.py' | ForEach-Object {
        & $python -m py_compile $_.FullName
        if ($LASTEXITCODE -ne 0) {
            throw "Python compilation failed: $($_.FullName)"
        }
    }
}
finally {
    $env:PYTHONPYCACHEPREFIX = $previousPycachePrefix
}

Write-Host 'Testing the Report Markdown compiler...'
& $python -m unittest discover -s (Join-Path $repoRoot 'tests') -p 'test_*.py'
if ($LASTEXITCODE -ne 0) {
    throw 'Report Markdown compiler tests failed.'
}
& $python (Join-Path $skillRoot 'scripts\compile_report.py') `
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
    & $python (Join-Path $skillRoot 'scripts\compile_report.py') --input $source --output $artifact --check
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
& $python (Join-Path $skillRoot 'scripts\check_report.py') `
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
& $python (Join-Path $skillRoot 'scripts\render_chartjs_output.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --input (Join-Path $exampleRoot 'report_print.html') `
    --output $smokeCharted
if ($LASTEXITCODE -ne 0) {
    throw 'Chart.js HTML smoke render failed.'
}
& $python (Join-Path $skillRoot 'scripts\render_paged_output.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --input $smokeCharted `
    --output $smokeHtml
if ($LASTEXITCODE -ne 0) {
    throw 'Paged.js HTML smoke render failed.'
}
& $python (Join-Path $skillRoot 'scripts\render_paged_output.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --input $smokeCharted `
    --output $smokePdf
if ($LASTEXITCODE -ne 0) {
    throw 'Paged.js PDF smoke render failed.'
}
& $python (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --html (Join-Path $exampleRoot 'report.html') `
    --print-html (Join-Path $exampleRoot 'report_print.html') `
    --charted-html $smokeCharted `
    --paged-html $smokeHtml `
    --pdf $smokePdf
if ($LASTEXITCODE -ne 0) {
    throw 'Regenerated Paged.js output validation failed.'
}
$fixtureChartedHash = Get-DeterminismHash -LiteralPath (Join-Path $exampleRoot 'report_charted.html') -NormalizeRaster
$smokeChartedHash = Get-DeterminismHash -LiteralPath $smokeCharted -NormalizeRaster
if ($fixtureChartedHash -ne $smokeChartedHash) {
    throw 'Chart.js HTML structure is not deterministic in the validated browser environment.'
}
$fixturePagedHash = Get-DeterminismHash -LiteralPath (Join-Path $exampleRoot 'report_paged.html') -NormalizeRaster
$smokePagedHash = Get-DeterminismHash -LiteralPath $smokeHtml -NormalizeRaster
if ($fixturePagedHash -ne $smokePagedHash) {
    throw 'Paginated HTML structure is not deterministic after transient identifiers and raster bytes are removed.'
}

Write-Host 'Building the Report Markdown end-to-end fixture...'
$dslSmokeRoot = Join-Path $repoRoot '.work\dsl-smoke'
& $python (Join-Path $skillRoot 'scripts\build_report_bundle.py') `
    --input (Join-Path $dslRoot 'report.report.md') `
    --output-dir $dslSmokeRoot
if ($LASTEXITCODE -ne 0) {
    throw 'Report Markdown bundle build failed.'
}
& $python (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $dslSmokeRoot 'artifact.json') `
    --html (Join-Path $dslSmokeRoot 'report.html') `
    --print-html (Join-Path $dslSmokeRoot 'report_print.html') `
    --charted-html (Join-Path $dslSmokeRoot 'report_charted.html') `
    --paged-html (Join-Path $dslSmokeRoot 'report_paged.html') `
    --pdf (Join-Path $dslSmokeRoot 'report.pdf')
if ($LASTEXITCODE -ne 0) {
    throw 'Report Markdown bundle validation failed.'
}
$fixtureDslHash = Get-DeterminismHash -LiteralPath (Join-Path $dslRoot 'artifact.json')
$smokeDslHash = Get-DeterminismHash -LiteralPath (Join-Path $dslSmokeRoot 'artifact.json')
if ($fixtureDslHash -ne $smokeDslHash) {
    throw 'Report Markdown compilation is not deterministic.'
}
$dslHtml = Get-Content -Raw -LiteralPath (Join-Path $dslSmokeRoot 'report.html')
if ($dslHtml -notmatch '<pre><code>SELECT' -or $dslHtml -notmatch 'data:image/svg\+xml;base64,') {
    throw 'Report Markdown output lacks the expected code block or embedded figure.'
}

Write-Host 'Building the chartless decision-brief fixture...'
$decisionSourceRoot = Join-Path $testLibraryRoot 'decision-brief'
$decisionSmokeRoot = Join-Path $repoRoot '.work\decision-brief-smoke'
& $python (Join-Path $skillRoot 'scripts\build_report_bundle.py') `
    --input (Join-Path $decisionSourceRoot 'report.report.md') `
    --output-dir $decisionSmokeRoot
if ($LASTEXITCODE -ne 0) {
    throw 'Decision-brief bundle build failed.'
}
& $python (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $decisionSmokeRoot 'artifact.json') `
    --html (Join-Path $decisionSmokeRoot 'stakeholder-report.html') `
    --print-html (Join-Path $decisionSmokeRoot 'stakeholder-report_print.html') `
    --paged-html (Join-Path $decisionSmokeRoot 'stakeholder-report_paged.html') `
    --pdf (Join-Path $decisionSmokeRoot 'stakeholder-report.pdf')
if ($LASTEXITCODE -ne 0) {
    throw 'Decision-brief bundle validation failed.'
}
$decisionArtifact = Get-Content -Raw -LiteralPath (Join-Path $decisionSmokeRoot 'artifact.json')
$decisionPrint = Get-Content -Raw -LiteralPath (Join-Path $decisionSmokeRoot 'stakeholder-report_print.html')
if ($decisionArtifact -notmatch '"evidence"' -or $decisionArtifact -notmatch '"sourceIds"') {
    throw 'Decision-brief artifact does not retain the canonical evidence package.'
}
if ($decisionPrint -match '<section[^>]+portable-sources' -or $decisionPrint -match 'renderer_compat_chart') {
    throw 'Decision-brief stakeholder edition leaked hidden sources or renderer compatibility content.'
}

$userProfile = $env:USERPROFILE
if (-not $userProfile) {
    $userProfile = $HOME
}
$skillValidator = Join-Path $userProfile '.codex' 'skills' '.system' 'skill-creator' 'scripts' 'quick_validate.py'
if (Test-Path -LiteralPath $skillValidator) {
    $yamlCheck = & $python -c 'import yaml' 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'Validating skill metadata and layout...'
        & $python $skillValidator $skillRoot
        if ($LASTEXITCODE -ne 0) {
            throw 'Skill validation failed.'
        }
    }
    else {
        Write-Warning "Skill validator skipped because the selected Python runtime does not have PyYAML installed: $yamlCheck"
    }
}
else {
    Write-Warning "Skill validator not found: $skillValidator"
}

Write-Host 'PASS: repository checks succeeded.'
