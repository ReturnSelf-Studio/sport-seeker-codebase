@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set "APP_NAME=SPORT SEEKER"
cd /d "%~dp0"

echo ========================================================
echo           CAI DAT %APP_NAME%
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
    echo chcp 65001 ^>nul
    echo echo Dang tai VC++ Redistributable...
    echo powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%REDIST_EXE%'"
    echo echo Dang cai dat...
    echo start /wait "" "%REDIST_EXE%" /install /quiet /norestart
    echo del /f /q "%REDIST_EXE%" 2^>nul
    echo echo.
    echo echo [XONG] Vui long dong cua so nay va chay lai file cai dat.
    echo pause
) > "%BAT_TEMP%"

powershell -Command "Start-Process cmd -ArgumentList '/k ""%BAT_TEMP%""' -Verb RunAs"

echo.
echo [THONG BAO] Vui long doi cua so Admin chay xong, sau do chay lai file nay.
pause
exit /b

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

echo [!] Thieu Build Tools. Dang mo cua so Admin de cai dat (3GB)...
echo [!] Vui long nhan 'Yes' o cua so UAC va cho doi.

set "BAT_TEMP=%TEMP%\ss_install_buildtools.bat"
set "BT_EXE=%TEMP%\vs_BuildTools.exe"
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo echo Dang tai VS Build Tools (3GB^), vui long cho...
    echo powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_BuildTools.exe' -OutFile '%BT_EXE%'"
    echo echo Dang cai dat am tham (co the mat 15-30 phut^)...
    echo start /wait "" "%BT_EXE%" --quiet --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended
    echo del /f /q "%BT_EXE%" 2^>nul
    echo echo.
    echo echo [XONG] Vui long dong cua so nay va chay lai file cai dat.
    echo pause
) > "%BAT_TEMP%"

powershell -Command "Start-Process cmd -ArgumentList '/k ""%BAT_TEMP%""' -Verb RunAs"

echo.
echo --------------------------------------------------------
echo [QUAN TRONG] Sau khi cua so Admin hoan tat,
echo hay chay lai file nay de tiep tuc.
echo --------------------------------------------------------
pause
exit /b

:: --------------------------------------------------------
:: BUOC 3: THIET LAP UV
:: --------------------------------------------------------
:step3
echo.
echo [3/4] Dang thiet lap engine Python (User Mode)...

if not exist "uv.exe" (
    echo     - Dang tai engine 'uv'...
    powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile 'uv.zip'"
    powershell -NoProfile -Command "Expand-Archive -Path 'uv.zip' -DestinationPath 'uv_tmp' -Force"
    copy /Y "uv_tmp\uv.exe" "." >nul
    rmdir /s /q "uv_tmp" >nul 2>&1
    del /f /q "uv.zip" >nul 2>&1
    echo     - [OK] uv da san sang.
) else (
    echo     - [OK] uv da co san.
)

:: --------------------------------------------------------
:: BUOC 4: CHAY PYTHON INSTALLER
:: pyproject.toml o thu muc nay → uv biet dung Python 3.11
:: tools\installer.py se tu tao venv va pip install vao backend\
:: --------------------------------------------------------
:step4
echo.
echo [4/4] Dang chay trinh cai dat chinh...

if not exist "tools\installer.py" (
    echo [LOI] Khong tim thay tools\installer.py.
    echo       Vui long giai nen lai goi cai dat day du.
    pause
    exit /b 1
)
if not exist "tools\core_utils.py" (
    echo [LOI] Khong tim thay tools\core_utils.py.
    echo       Vui long giai nen lai goi cai dat day du.
    pause
    exit /b 1
)

:: Env vars cho thu vien AI (set truoc khi installer chay)
set "KMP_DUPLICATE_LIB_OK=TRUE"
set "SPORT_SEEKER_MODELS_ROOT=%USERPROFILE%\SportSeeker\models"
set "INSIGHTFACE_HOME=%USERPROFILE%\SportSeeker\models"
set "HF_HOME=%USERPROFILE%\.cache\huggingface"
set "PYTHONUTF8=1"

call .\uv run tools\installer.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Cai dat that bai. Xem thu muc logs\ de biet chi tiet.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo [HOAN TAT] Cai dat thanh cong!
echo Ban co the mo ung dung tu Desktop.
echo ========================================================
pause
exit /b 0
