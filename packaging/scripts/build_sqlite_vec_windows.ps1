# Build sqlite-vec vec0.dll for Windows ARM64 from official amalgamation + SQLite headers.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Version = "0.1.9"
$VendorDir = Join-Path $Root "packaging\vendor\sqlite_vec\sqlite_vec"
$DestDll = Join-Path $VendorDir "vec0.arm64.dll"
$WorkDir = Join-Path $env:TEMP "sqlite-vec-arm64-build-$Version"

New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null

if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
  throw "MSVC cl.exe is required to build sqlite-vec for Windows ARM64"
}

$PrepareScript = Join-Path $Root "packaging\scripts\prepare_sqlite_vec_windows_arm64.py"
python $PrepareScript $WorkDir
if ($LASTEXITCODE -ne 0) {
  throw "prepare_sqlite_vec_windows_arm64.py failed"
}

Push-Location $WorkDir
try {
  & cl.exe /nologo /LD /O2 `
    /I "$WorkDir" `
    /I "$WorkDir\vendor" `
    sqlite-vec.c `
    /link /OUT:vec0.dll
  if (-not (Test-Path "vec0.dll")) {
    throw "vec0.dll was not produced"
  }
  Copy-Item -Force "vec0.dll" $DestDll
} finally {
  Pop-Location
}

Write-Output $DestDll
