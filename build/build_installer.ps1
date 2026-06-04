#Requires -Version 5.1
<#
.SYNOPSIS
  一键构建 Windows 安装包 WxMpCatcher-Setup-0.1.0.exe

.DESCRIPTION
  1. 创建虚拟环境并安装依赖
  2. PyInstaller 打包应用目录
  3. Inno Setup 编译安装程序

  用法（PowerShell 管理员或普通用户均可）:
    cd wechat-miniprogram-image-catcher
    .\build\build_installer.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "=== 微信小程序图片抓取工具 — Windows 安装包构建 ===" -ForegroundColor Cyan
Write-Host "项目目录: $ProjectRoot"

# 1. Python 环境
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    Write-Error "未找到 Python。请先安装 Python 3.11+ 并勾选 Add to PATH。"
}

$Venv = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $Venv)) {
    Write-Host "创建虚拟环境..."
    & python -m venv $Venv
}
$Py = Join-Path $Venv "Scripts\python.exe"
$Pip = Join-Path $Venv "Scripts\pip.exe"

Write-Host "安装依赖..."
& $Pip install -q -U pip
& $Pip install -q -e ".[dev]"

# 2. PyInstaller
Write-Host "PyInstaller 打包..."
& $Py -m PyInstaller build\wx_mp_catcher.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 失败" }

$AppDir = Join-Path $ProjectRoot "dist\wx-mp-catcher"
if (-not (Test-Path (Join-Path $AppDir "wx-mp-catcher.exe"))) {
    throw "未找到 dist\wx-mp-catcher\wx-mp-catcher.exe"
}
Write-Host "应用打包完成: $AppDir" -ForegroundColor Green

# 3. Inno Setup
$Iscc = $null
$candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    (Get-Command iscc -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
)
foreach ($c in $candidates) {
    if ($c -and (Test-Path $c)) { $Iscc = $c; break }
}

if (-not $Iscc) {
    Write-Host "未检测到 Inno Setup，尝试 winget 安装..." -ForegroundColor Yellow
    winget install --id JRSoftware.InnoSetup -e --accept-source-agreements --accept-package-agreements
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { $Iscc = $c; break }
    }
}

if (-not $Iscc) {
    Write-Host ""
    Write-Host "Inno Setup 未安装。请先安装: https://jrsoftware.org/isdl.php" -ForegroundColor Red
    Write-Host "或手动运行: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe`" build\installer.iss"
    Write-Host ""
    Write-Host "便携版已可用: dist\wx-mp-catcher\wx-mp-catcher.exe" -ForegroundColor Yellow
    exit 0
}

Write-Host "Inno Setup 编译安装包..."
& $Iscc "build\installer.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup 编译失败" }

$SetupExe = Join-Path $ProjectRoot "dist\WxMpCatcher-Setup-0.1.0.exe"
Write-Host ""
Write-Host "=== 构建成功 ===" -ForegroundColor Green
Write-Host "安装包: $SetupExe"
Write-Host "双击安装包即可在 Windows 上安装使用，无需 Python。"
