$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $env:UV_CACHE_DIR) {
    $env:UV_CACHE_DIR = Join-Path $repoRoot ".uv-cache"
}

if (-not (Test-Path -LiteralPath $env:UV_CACHE_DIR)) {
    New-Item -ItemType Directory -Path $env:UV_CACHE_DIR | Out-Null
}

Push-Location $repoRoot
try {
    & uv run pytest @args
}
finally {
    Pop-Location
}
