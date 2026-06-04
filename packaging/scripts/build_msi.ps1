$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

$BundleDir = Join-Path $Root "dist\LexiFlow"
$Version = if ($env:WIX_VERSION) {
  $env:WIX_VERSION
} elseif ($env:LF_VERSION) {
  "$($env:LF_VERSION).0"
} else {
  "0.0.0.0"
}
$MsiName = if ($env:LF_INSTALLER_ARCH) {
  "LexiFlow-$($env:LF_VERSION)-$($env:LF_INSTALLER_ARCH).msi"
} else {
  "LexiFlow-$($env:LF_VERSION).msi"
}
$MsiPath = Join-Path $Root "dist\$MsiName"
$WxsPath = Join-Path $Root "packaging\wix\LexiFlow.wxs"
$HarvestPath = Join-Path $Root "packaging\wix\Harvest.wxs"
$WixObjDir = Join-Path $Root "packaging\wix\obj"

if (-not (Test-Path $BundleDir)) {
  throw "bundle directory missing: $BundleDir"
}

foreach ($tool in @("heat.exe", "candle.exe", "light.exe")) {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
    throw "WiX Toolset ($tool) is required to build the MSI"
  }
}

New-Item -ItemType Directory -Force -Path $WixObjDir | Out-Null

& heat.exe dir $BundleDir `
  -cg ProductComponents `
  -dr INSTALLFOLDER `
  -var env.LEXIFLOW_BUNDLE_DIR `
  -gg -sfrag -srd `
  -out $HarvestPath

$env:LEXIFLOW_BUNDLE_DIR = $BundleDir
$env:LEXIFLOW_MSI_PATH = $MsiPath

& candle.exe -nologo `
  -dVersion=$Version `
  -out (Join-Path $WixObjDir "LexiFlow.wixobj") `
  $WxsPath

& candle.exe -nologo `
  -dVersion=$Version `
  -out (Join-Path $WixObjDir "Harvest.wixobj") `
  $HarvestPath

& light.exe -nologo `
  -out $MsiPath `
  (Join-Path $WixObjDir "LexiFlow.wixobj") `
  (Join-Path $WixObjDir "Harvest.wixobj")

Write-Output $MsiPath
