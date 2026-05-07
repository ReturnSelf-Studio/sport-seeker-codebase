@echo off
setlocal enabledelayedexpansion
:: Thiet lap code page 65001 de hien thi tieng Viet co dau neu file duoc luu dung format UTF-8
chcp 65001 >nul

set "APP_NAME=SPORT SEEKER"
cd /d "%~dp0"

echo ========================================================
echo            CAI DAT %APP_NAME%
echo ========================================================

:: --------------------------------------------------------
:: BUOC 1: KIEM TRA WINDOWS RUNTIME (VC++ Redistributable)
:: --------------------------------------------------------
echo [1/4] Kiem tra Windows Runtime...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Runtime da co san.
    goto :step2
)

echo [!] Thieu VC++ Redist. Dang mo cua so Admin de cai dat...
set "BAT_TEMP=%TEMP%\ss_install_redist.bat"
set "REDIST_EXE=%TEMP%\vc_redist.x64.exe"
(
    echo @echo off
    echo echo Dang tai VC++ Redistributable...
    echo powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%REDIST_EXE%'"
    echo echo Dang cai dat...
    echo start /wait "" "%REDIST_EXE%" /install /quiet /norestart
    echo del /f /q "%REDIST_EXE%" 2^>nul
    echo echo [XONG] Cua so nay se tu dong dong.
) > "%BAT_TEMP%"
:: Dung /c va -Wait de doi cai xong moi chay tiep, khong exit /b
powershell -Command "Start-Process cmd -ArgumentList '/c ""%BAT_TEMP%""' -Verb RunAs -Wait"

:: --------------------------------------------------------
:: BUOC 2: KIEM TRA C++ BUILD TOOLS
:: --------------------------------------------------------
:step2
echo.
echo [2/4] Kiem tra C++ Compiler (Build Tools)...
set "MSVC_CHECK=0"
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\SxS\VS7" /v "17.0" >nul 2>nul
if %ERRORLEVEL% EQU 0 set "MSVC_CHECK=1"
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" set "MSVC_CHECK=1"
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC" set "MSVC_CHECK=1"

if "%MSVC_CHECK%"=="1" (
    echo [OK] Build Tools da co san.
    goto :step3
)

echo [!] Thieu Build Tools. Dang mo cua so Admin de cai dat...
set "BAT_TEMP=%TEMP%\ss_install_buildtools.bat"
set "BT_EXE=%TEMP%\vs_BuildTools.exe"
(
    echo @echo off
    echo echo Dang tai VS Build Tools (3GB^), vui long cho...
    echo powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_BuildTools.exe' -OutFile '%BT_EXE%'"
    echo echo Dang cai dat am tham (co the mat 15-30 phut^)...
    echo start /wait "" "%BT_EXE%" --quiet --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended
    echo del /f /q "%BT_EXE%" 2^>nul
    echo echo [XONG] Cua so nay se tu dong dong.
) > "%BAT_TEMP%"
powershell -Command "Start-Process cmd -ArgumentList '/c ""%BAT_TEMP%""' -Verb RunAs -Wait"

:: --------------------------------------------------------
:: BUOC 3: THIET LAP UV ENGINE
:: --------------------------------------------------------
:step3
echo.
echo [3/4] Dang thiet lap engine Python...

:: Goi file PowerShell de xu ly moi logic (Check Global, Check Cache, Download)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_uv.ps1"

:: Xu ly ket qua tra ve tu PowerShell (Exit Code)
if %ERRORLEVEL% EQU 2 (
    set "UV_CMD=uv"
) else if %ERRORLEVEL% EQU 0 (
    set "UV_CMD=%USERPROFILE%\SportSeeker\bin\uv.exe"
) else (
    echo.
    echo [LOI] Khong the thiet lap uv. Vui long kiem tra ket noi mang.
    pause
    exit /b 1
)

:: --------------------------------------------------------
:: BUOC 4: CHAY PYTHON INSTALLER
:: --------------------------------------------------------
:step4
echo.
echo [4/4] Dang chay trinh cai dat chinh...

:: Kiem tra file script mồi
if not exist "tools\installer.py" (
    echo [LOI] Khong tim thay tools\installer.py.
    pause
    exit /b 1
)

:: Thiet lap bien moi truong cho AI/Python
set "KMP_DUPLICATE_LIB_OK=TRUE"
set "SPORT_SEEKER_MODELS_ROOT=%USERPROFILE%\SportSeeker\models"
set "INSIGHTFACE_HOME=%USERPROFILE%\SportSeeker\models"
set "HF_HOME=%USERPROFILE%\.cache\huggingface"
set "PYTHONUTF8=1"

:: Chay installer thong qua uv da duoc xac dinh o Buoc 3
"%UV_CMD%" run tools\installer.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Cai dat that bai. Vui long kiem tra file log.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [HOAN TAT] Cai dat thanh cong %APP_NAME%!
echo ========================================================
pause
exit /b 0
