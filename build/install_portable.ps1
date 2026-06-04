#Requires -Version 5.1
<#
.SYNOPSIS
  简易安装脚本 — 在没有 Inno Setup 时，将便携版安装到本地目录并创建快捷方式。

  用法: 以普通用户运行
    .\build\install_portable.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Source = Join-Path $ProjectRoot "dist\wx-mp-catcher"
$Target = Join-Path $env:LOCALAPPDATA "WxMpCatcher"
$Exe = Join-Path $Target "wx-mp-catcher.exe"

if (-not (Test-Path $Source)) {
    Write-Error "请先运行 build\build_installer.ps1 或 pyinstaller build\wx_mp_catcher.spec 生成 dist\wx-mp-catcher"
}

Write-Host "安装到: $Target"
if (Test-Path $Target) { Remove-Item $Target -Recurse -Force }
New-Item -ItemType Directory -Path $Target -Force | Out-Null
Copy-Item -Path "$Source\*" -Destination $Target -Recurse -Force

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$StartMenu = [Environment]::GetFolderPath("StartMenu") + "\Programs"
$Shortcut = $WshShell.CreateShortcut((Join-Path $Desktop "微信小程序图片抓取.lnk"))
$Shortcut.TargetPath = $Exe
$Shortcut.WorkingDirectory = $Target
$Shortcut.Save()
$Shortcut2 = $WshShell.CreateShortcut((Join-Path $StartMenu "微信小程序图片抓取.lnk"))
$Shortcut2.TargetPath = $Exe
$Shortcut2.WorkingDirectory = $Target
$Shortcut2.Save()

Write-Host "安装完成！桌面与开始菜单已创建快捷方式。" -ForegroundColor Green
Start-Process $Exe
