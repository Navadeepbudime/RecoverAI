$ErrorActionPreference = "Stop"

$frontendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $frontendDir

$localVite = Join-Path $frontendDir "node_modules\.bin\vite.cmd"
if (Test-Path $localVite) {
    & $localVite --host 0.0.0.0 --port 5173
    exit $LASTEXITCODE
}

$codexNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
$codexPnpm = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\pnpm\bin\pnpm.mjs"

if ((Test-Path $codexNode) -and (Test-Path $codexPnpm)) {
    & $codexNode $codexPnpm install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $codexNode $codexPnpm run dev
    exit $LASTEXITCODE
}

Write-Host "Could not find local Vite or Codex's bundled pnpm."
Write-Host "Install pnpm globally with: corepack enable"
Write-Host "Then run: pnpm install; pnpm run dev"
exit 1
