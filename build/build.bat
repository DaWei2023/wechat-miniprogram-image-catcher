@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo 正在构建 Windows 安装包，请稍候...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_installer.ps1"
if errorlevel 1 (
    echo.
    echo 构建失败。请确认已安装 Python 3.11+ 。
    pause
    exit /b 1
)
pause
