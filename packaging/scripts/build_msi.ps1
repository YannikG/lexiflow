$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root

$BundleDir = Join-Path $Root "dist\LexiFlow"
$WixProductVersion = (& uv run python packaging/scripts/wix_version.py).Trim()
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

$CandleDefine = "Version=$WixProductVersion"

& candle.exe -nologo `
  -d$CandleDefine `
  -out (Join-Path $WixObjDir "LexiFlow.wixobj") `
  $WxsPath

& candle.exe -nologo `
  -d$CandleDefine `
  -out (Join-Path $WixObjDir "Harvest.wixobj") `
  $HarvestPath

& light.exe -nologo `
  -out $MsiPath `
  (Join-Path $WixObjDir "LexiFlow.wixobj") `
  (Join-Path $WixObjDir "Harvest.wixobj")

Write-Output $MsiPath
