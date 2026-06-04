# Build sqlite-vec vec0.dll for Windows ARM64 from upstream sources.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Version = "0.1.9"
$VendorDir = Join-Path $Root "packaging\vendor\sqlite_vec\sqlite_vec"
$DestDll = Join-Path $VendorDir "vec0.arm64.dll"
$SourceZip = Join-Path $env:TEMP "sqlite-vec-$Version.zip"
$SourceDir = Join-Path $env:TEMP "sqlite-vec-$Version-src"

New-Item -ItemType Directory -Force -Path $VendorDir | Out-Null

if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
  throw "MSVC cl.exe is required to build sqlite-vec for Windows ARM64"
}

$ArchiveUrl = "https://github.com/asg017/sqlite-vec/archive/refs/tags/v$Version.zip"
Invoke-WebRequest -Uri $ArchiveUrl -OutFile $SourceZip -Headers @{"User-Agent" = "LexiFlow-packaging"}

if (Test-Path $SourceDir) {
  Remove-Item -Recurse -Force $SourceDir
}
Expand-Archive -Path $SourceZip -DestinationPath (Split-Path $SourceDir -Parent) -Force
$Extracted = Get-ChildItem (Split-Path $SourceDir -Parent) -Directory |
  Where-Object { $_.Name -like "sqlite-vec-*" } |
  Select-Object -First 1
if (-not $Extracted) {
  throw "sqlite-vec source directory not found after extract"
}

Push-Location $Extracted.FullName
try {
  $SourceFile = Join-Path $Extracted.FullName "sqlite-vec.c"
  if (-not (Test-Path $SourceFile)) {
    throw "sqlite-vec.c missing in $($Extracted.FullName)"
  }
  $BuildDir = Join-Path $env:TEMP "sqlite-vec-arm64-build"
  if (Test-Path $BuildDir) {
    Remove-Item -Recurse -Force $BuildDir
  }
  New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
  Push-Location $BuildDir
  try {
    & cl.exe /nologo /LD /O2 /I "$($Extracted.FullName)\vendor" `
      "$SourceFile" /link /OUT:"vec0.dll"
    if (-not (Test-Path "vec0.dll")) {
      throw "vec0.dll was not produced"
    }
    Copy-Item -Force "vec0.dll" $DestDll
  } finally {
    Pop-Location
  }
} finally {
  Pop-Location
}

Write-Output $DestDll
