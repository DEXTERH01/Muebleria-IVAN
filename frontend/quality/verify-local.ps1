param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$names = @('SUPABASE_TEST_DATABASE_URL', 'SUPABASE_TEST_URL', 'SUPABASE_TEST_PUBLISHABLE_KEY', 'PHASE7_ML_REPORT')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }

function Invoke-LocalCheck {
    param([string]$Label, [scriptblock]$Command)
    Write-Host "Validando $Label..."
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "Falló $Label" }
}

Push-Location $repositoryRoot
try {
    # Capture status internally: it includes local keys and must not be logged.
    $localStatus = npx.cmd --yes supabase status -o json 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or -not $localStatus.DB_URL -or -not $localStatus.API_URL) {
        throw 'Inicia Supabase local antes de validar. No se ejecuta db reset automáticamente.'
    }
    foreach ($url in @($localStatus.DB_URL, $localStatus.API_URL)) {
        if (([Uri]$url).Host -notin @('localhost', '127.0.0.1', '[::1]', '::1')) {
            throw 'Solo se permite una base local desechable: estas pruebas crean datos ficticios.'
        }
    }
    $env:SUPABASE_TEST_DATABASE_URL = $localStatus.DB_URL -replace '^postgresql://', 'postgresql+psycopg://'
    $env:SUPABASE_TEST_URL = $localStatus.API_URL
    $env:SUPABASE_TEST_PUBLISHABLE_KEY = $localStatus.PUBLISHABLE_KEY
    if (-not $env:SUPABASE_TEST_PUBLISHABLE_KEY) { $env:SUPABASE_TEST_PUBLISHABLE_KEY = $localStatus.ANON_KEY }
    New-Item -ItemType Directory -Path (Join-Path $repositoryRoot 'output') -Force | Out-Null
    $env:PHASE7_ML_REPORT = Join-Path $repositoryRoot 'output/phase7-ml-performance.json'

    Invoke-LocalCheck 'restricciones y permisos SQL' { npx.cmd --yes supabase test db }
    Invoke-LocalCheck 'frontend, backend e integración PostgreSQL' { & ./scripts/verify.ps1 }
    Push-Location frontend
    try {
        Invoke-LocalCheck 'E2E con API controlada' { npm.cmd run test:e2e -- admin-quotes.spec.ts quote-flow.spec.ts }
        Invoke-LocalCheck 'taller con Auth, FastAPI y PostgreSQL reales' {
            npm.cmd run test:e2e -- --config playwright.integration.config.ts
        }
    }
    finally { Pop-Location }
    Write-Host 'Bloque local aprobado. Tiempos ML guardados en output/phase7-ml-performance.json.'
}
finally {
    Pop-Location
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process') }
}
