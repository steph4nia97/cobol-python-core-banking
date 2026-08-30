param(
    [ValidateSet("seed", "compile", "run", "all", "api", "test")]
    [string]$Command = "all"
)

Set-Location $PSScriptRoot
$env:PYTHONPATH = Join-Path $PSScriptRoot "python"

if ($Command -eq "api") {
    uvicorn banking_pipeline.api:app --app-dir python --reload --port 8000
    exit $LASTEXITCODE
}
if ($Command -eq "test") {
    pytest -v
    exit $LASTEXITCODE
}

python -m banking_pipeline $Command
