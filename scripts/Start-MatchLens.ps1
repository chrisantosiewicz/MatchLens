param([switch]$Foundry, [int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Choose a port between 1024 and 65535.' }
if ($Foundry) {
    $configuration = Join-Path $projectRoot '.env'
    if (-not (Test-Path -LiteralPath $configuration)) { throw 'Create a local .env from .env.example first.' }
    $allowed = @('AZURE_AI_PROJECT_ENDPOINT', 'AZURE_AI_MODEL_DEPLOYMENT_NAME', 'AZURE_TENANT_ID', 'MATCHLENS_AI_POLICY', 'MATCHLENS_ALLOW_BROWSER_LOGIN')
    foreach ($line in Get-Content -LiteralPath $configuration) {
        if ($line.Trim().StartsWith('#') -or -not $line.Contains('=')) { continue }
        $parts = $line.Split('=', 2)
        $configName = $parts[0].Trim()
        if ($allowed -contains $configName) {
            [Environment]::SetEnvironmentVariable($configName, $parts[1].Trim(), 'Process')
        }
    }
    if (-not $env:AZURE_AI_PROJECT_ENDPOINT -or -not $env:AZURE_AI_MODEL_DEPLOYMENT_NAME) { throw 'Project endpoint and deployment name are required.' }
    $env:MATCHLENS_AI_MODE = 'foundry'
    $env:MATCHLENS_AI_POLICY = 'single'
} else {
    $env:MATCHLENS_AI_MODE = 'template'
    $env:MATCHLENS_AI_POLICY = 'single'
}
$builtFrontend = Join-Path $projectRoot 'frontend/dist'
if (Test-Path -LiteralPath (Join-Path $builtFrontend 'index.html')) {
    $env:MATCHLENS_FRONTEND_DIR = $builtFrontend
}
& (Join-Path $projectRoot 'backend/.venv/Scripts/python.exe') -m uvicorn matchlens.api:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
