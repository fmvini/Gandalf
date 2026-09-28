param([switch]$Install)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot 'api/.venv/Scripts/python.exe'
if ($Install) {
    if (-not (Test-Path -LiteralPath $python)) {
        & py -3.12 -m venv (Join-Path $projectRoot 'api/.venv')
        if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o ambiente Python 3.12.' }
    }
    Push-Location (Join-Path $projectRoot 'api')
    try {
        & $python -m pip install -e '.[dev]'
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependências Python.' }
    } finally { Pop-Location }
    Push-Location (Join-Path $projectRoot 'frontend')
    try {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependências da interface.' }
    } finally { Pop-Location }
}
if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/node_modules'))) {
    throw 'Instale as dependências gratuitas com: .\start-local.ps1 -Install'
}
foreach ($port in @(8000, 5173)) {
    $conflicts = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalAddress -in @('127.0.0.1', '0.0.0.0', '::') }
    if ($conflicts) {
        throw "A porta $port já está em uso. Encerre a instância anterior antes de iniciar."
    }
}
$apiProcess = Start-Process -FilePath $python -ArgumentList 'local.py' -WorkingDirectory (Join-Path $projectRoot 'api') -WindowStyle Hidden -PassThru
try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($apiProcess.HasExited) { throw 'A API encerrou durante a inicialização.' }
        try {
            $health = Invoke-RestMethod 'http://127.0.0.1:8000/health/ready' -TimeoutSec 1
            if ($health.status -eq 'ok') { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) { throw 'A API não ficou pronta. Execute api/.venv/Scripts/python.exe api/local.py para ver o erro.' }
    Write-Host 'Gandalf: http://127.0.0.1:5173 — modo local gratuito. Ctrl+C para encerrar.'
    Push-Location (Join-Path $projectRoot 'frontend')
    try {
        $previousApiUrl = $env:VITE_API_BASE_URL
        $env:VITE_API_BASE_URL = 'http://127.0.0.1:8000/api/v1'
        & npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
    } finally {
        $env:VITE_API_BASE_URL = $previousApiUrl
        Pop-Location
    }
} finally {
    if (-not $apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id }
}
