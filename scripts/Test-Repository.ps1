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

Write-Host 'Checking the shipped report fixture...'
py (Join-Path $skillRoot 'scripts\check_report.py') `
    --artifact (Join-Path $exampleRoot 'artifact.json') `
    --html (Join-Path $exampleRoot 'report.html') `
    --print-html (Join-Path $exampleRoot 'report_print.html')
if ($LASTEXITCODE -ne 0) {
    throw 'Report fixture validation failed.'
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
