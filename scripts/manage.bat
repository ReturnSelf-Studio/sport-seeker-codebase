@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: LOG SETUP
:: ============================================================
set "LOG_DIR=%~dp0..\logs"
if not exist "%LOG_DIR%\" mkdir "%LOG_DIR%"
for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TIMESTAMP=%%T"
set "LOG_FILE=%LOG_DIR%\manage_%TIMESTAMP%.log"

:: Tee macro: in ra console va ghi vao log
:: Su dung bang cach: call :log "message"
goto :main

:log
echo %~1
echo [%time%] %~1 >> "!LOG_FILE!"
goto :eof

:log_only
echo [%time%] %~1 >> "!LOG_FILE!"
goto :eof

:: ============================================================
:: MAIN
:: ============================================================
:main
cd /d "%~dp0\.."

call :log "=========================================="
call :log "  SPORT SEEKER CLI TOOL (WINDOWS)"
call :log "  Log: !LOG_FILE!"
call :log "=========================================="

:: ============================================================
:: BUOC 1: TIM HOAC CAI UV
:: ============================================================
call :log ""
call :log "[1/4] Tim kiem uv..."

set "UV_CMD="
uv --version >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    set "UV_CMD=uv"
    goto :uv_found
)

if exist "%~dp0uv.exe" (
    set "UV_CMD=%~dp0uv.exe"
    goto :uv_found
)

if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "UV_CMD=%USERPROFILE%\.local\bin\uv.exe"
    set "PATH=%USERPROFILE%\.local\bin;!PATH!"
    goto :uv_found
)

if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
    set "PATH=%USERPROFILE%\.cargo\bin;!PATH!"
    goto :uv_found
)

call :log "[INFO] uv chua duoc cai dat. Dang tai uv portable..."
powershell -NoProfile -Command ^
    "Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile '%TEMP%\uv.zip'" ^
    >> "!LOG_FILE!" 2>&1
if !ERRORLEVEL! NEQ 0 (
    call :log "[LOI] Khong tai duoc uv. Kiem tra ket noi Internet."
    exit /b 1
)
powershell -NoProfile -Command ^
    "Expand-Archive -Path '%TEMP%\uv.zip' -DestinationPath '%TEMP%\uv_tmp' -Force" ^
    >> "!LOG_FILE!" 2>&1
copy /Y "%TEMP%\uv_tmp\uv.exe" "%~dp0uv.exe" >nul
rmdir /s /q "%TEMP%\uv_tmp" >nul 2>&1
del /f /q "%TEMP%\uv.zip" >nul 2>&1

set "UV_CMD=%~dp0uv.exe"
call :log "[OK] uv portable da san sang (scripts\uv.exe)."

:uv_found
call :log "[OK] Su dung uv: !UV_CMD!"

:: ============================================================
:: BUOC 2: KHOI TAO VENV
:: ============================================================
call :log ""
call :log "[2/4] Khoi tao virtual environment Python 3.11..."

if not exist ".venv\" (
    "!UV_CMD!" venv --python 3.11 >> "!LOG_FILE!" 2>&1
    if !ERRORLEVEL! NEQ 0 (
        call :log "[LOI] Khong tao duoc virtual environment."
        exit /b 1
    )
    call :log "[OK] Virtual environment da tao."
) else (
    call :log "[OK] Virtual environment da ton tai, bo qua."
)

:: ============================================================
:: BUOC 3: KIEM TRA FLUTTER + VS BUILD TOOLS
:: Chi thuc hien khi lenh la "build" hoac "build-ui"
:: ============================================================
set "NEED_FLUTTER=0"
if "%~1"=="build" set "NEED_FLUTTER=1"
if "%~1"=="build-ui" set "NEED_FLUTTER=1"

if "!NEED_FLUTTER!"=="0" goto :run_cli

call :log ""
call :log "[3/4] Kiem tra Flutter build environment..."

:: --- 3a. Kiem tra Flutter ---
where flutter >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    call :log "[LOI] Khong tim thay flutter tren PATH."
    call :log "      Cai dat Flutter tai: https://docs.flutter.dev/get-started/install/windows"
    exit /b 1
)
call :log "[OK] Flutter da san sang."

:: --- 3b. Kiem tra VS Build Tools (Flutter Windows yeu cau MSVC) ---
:: Tim Visual C++ qua registry (an toan hon for /d tren may moi)
set "VCTOOLS_FOUND=0"
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7" >nul 2>nul
if !ERRORLEVEL! EQU 0 set "VCTOOLS_FOUND=1"
if exist "C:\Program Files\Microsoft Visual Studio" (
    for /d %%V in ("C:\Program Files\Microsoft Visual Studio\*") do (
        for /d %%E in ("%%V\*") do (
            if exist "%%E\VC\Tools\MSVC" set "VCTOOLS_FOUND=1"
        )
    )
)
if exist "C:\Program Files (x86)\Microsoft Visual Studio" (
    for /d %%V in ("C:\Program Files (x86)\Microsoft Visual Studio\*") do (
        for /d %%E in ("%%V\*") do (
            if exist "%%E\VC\Tools\MSVC" set "VCTOOLS_FOUND=1"
        )
    )
)

if "!VCTOOLS_FOUND!"=="1" (
    call :log "[OK] Visual Studio Build Tools da co san."
    goto :flutter_ok
)

call :log "[INFO] Visual Studio Build Tools chua duoc cai dat."
call :log "[INFO] Flutter yeu cau Visual Studio Community (khong dung Build Tools standalone)."
call :log "[INFO] Dang tai Visual Studio Community (~5-7GB, mat 15-30 phut)..."
call :log "[INFO] Vui long KHONG DONG cua so nay trong qua trinh cai dat."

powershell -NoProfile -Command ^
    "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_community.exe' -OutFile '%TEMP%\vs_installer.exe'" ^
    >> "!LOG_FILE!" 2>&1
if !ERRORLEVEL! NEQ 0 (
    call :log "[LOI] Khong tai duoc VS Installer. Kiem tra ket noi Internet."
    exit /b 1
)

call :log "[INFO] Dang cai dat Visual Studio Community (co the mat 15-30 phut)..."
"%TEMP%\vs_installer.exe" --quiet --wait --norestart ^
    --add Microsoft.VisualStudio.Workload.NativeDesktop ^
    --includeRecommended >> "!LOG_FILE!" 2>&1

if !ERRORLEVEL! NEQ 0 (
    call :log "[LOI] Cai dat Visual Studio that bai. Ma loi: !ERRORLEVEL!"
    call :log "      Xem chi tiet tai: !LOG_FILE!"
    del /f /q "%TEMP%\vs_installer.exe" >nul 2>&1
    exit /b 1
)

del /f /q "%TEMP%\vs_installer.exe" >nul 2>&1
call :log "[OK] VS Build Tools da cai dat thanh cong."
call :log "[INFO] Khoi dong lai script de load MSVC environment..."
cmd /c ""%~f0" %*"
exit /b !ERRORLEVEL!

:flutter_ok
call :log "[OK] Flutter build environment san sang."
goto :run_cli

:: ============================================================
:: BUOC 4: CHAY CLI
:: ============================================================
:run_cli
call :log ""
call :log "[4/4] Chay lenh: %*"
call :log "------------------------------------------"

:: Chay cli, stderr -> log, stdout -> console (giu exit code chinh xac)
"!UV_CMD!" run --active scripts\cli.py %* 2>>"!LOG_FILE!"

set "EXIT_CODE=!ERRORLEVEL!"
call :log "------------------------------------------"
call :log "[DONE] Exit code: !EXIT_CODE!"
call :log "       Log luu tai: !LOG_FILE!"
exit /b !EXIT_CODE!
