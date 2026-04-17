@echo off
:: Khoi dong lai bang cmd.exe neu user click dup
if not defined CMDCMDLINE (
    cmd.exe /c "%~f0" %*
    exit /b %ERRORLEVEL%
)

:: 1. Ep Console su dung UTF-8
chcp 65001 >nul

:: 2. Ep Python su dung UTF-8
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================================
echo      SPORT SEEKER - BOOTSTRAPPER (WINDOWS)
echo ========================================================

if not exist "resource\" (
    echo [LOI] Vui long GIAI NEN TOAN BO file zip ra mot thu muc truoc khi chay.
    pause
    exit /b 1
)

:: 3. Kiem tra Visual C++
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo Dang tai va cai dat Visual C++ Redistributable...
    powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'vc_redist.x64.exe'"
    vc_redist.x64.exe /install /quiet /norestart
    del /f /q "vc_redist.x64.exe"
)

:: 4. Kiem tra UV (Chong gay link, tai ban portable)
set "UV_CMD=uv"
where uv >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    if not exist "uv.exe" (
        echo Dang tai cong cu quan ly moi truong AI uv...
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile 'uv.zip'"
        powershell -Command "Expand-Archive -Path 'uv.zip' -DestinationPath 'uv_temp' -Force"
        copy /Y "uv_temp\uv.exe" "uv.exe" >nul
        rmdir /s /q "uv_temp"
        del /f /q "uv.zip"
    )
    set "UV_CMD=%~dp0uv.exe"
)

:: 5. Uy quyen cho Python CLI chay script cai dat
echo Dang chuyen giao cho Trinh cai dat Python...
!UV_CMD! run --python 3.11 tools\installer.py

echo.
pause
exit /b 0
