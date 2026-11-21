param(
    [ValidateSet('all', 'frontend', 'backend')]
    [string]$Scope = 'all'
)

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$frontendRoot = Join-Path $repositoryRoot 'frontend'
$backendRoot = Join-Path $repositoryRoot 'backend'
$backendPython = Join-Path $backendRoot '.venv\Scripts\python.exe'

function Invoke-Checked {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Host "Verificando $Label..."
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Falló la verificación: $Label"
    }
}

if ($Scope -in @('all', 'frontend')) {
    Push-Location $frontendRoot
    try {
        Invoke-Checked 'pruebas del frontend' { npm.cmd run test }
        Invoke-Checked 'build del frontend' { npm.cmd run build }
    }
    finally {
        Pop-Location
    }
}

if ($Scope -in @('all', 'backend')) {
    if (-not (Test-Path -LiteralPath $backendPython)) {
        throw 'No existe backend/.venv. Sigue backend/README.md antes de verificar.'
    }

    Push-Location $backendRoot
    try {
        Invoke-Checked 'pruebas del backend' { & $backendPython -m pytest }
        Invoke-Checked 'lint del backend' { & $backendPython -m ruff check . }
    }
    finally {
        Pop-Location
    }
}

Write-Host 'Verificación completada.'

