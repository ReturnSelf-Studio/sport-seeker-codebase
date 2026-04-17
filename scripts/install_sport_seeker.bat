@echo off
if not defined CMDCMDLINE (
    cmd.exe /c "%~f0" %*
    exit /b %ERRORLEVEL%
)

chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================================
echo      SPORT SEEKER - THIET LAP UNG DUNG (WINDOWS)
echo ========================================================

if not exist "resource\" (
    echo [LOI] Khong tim thay thu muc "resource".
    echo Vui long GIAI NEN TOAN BO file zip ra mot thu muc truoc khi chay.
    echo.
    pause
    exit /b 1
)

set "INSTALL_ROOT=%APPDATA%\SportSeeker"
set "APP_DIR=%INSTALL_ROOT%\app"
set "MODELS_DIR=%USERPROFILE%\SportSeeker\models"

echo.
echo [0/5] Kiem tra Visual C++ Redistributable 2015-2022...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo - Da co Visual C++ Redistributable. Bo qua.
) else (
    echo - Chua co Visual C++ Redistributable. Dang tai va cai dat...
    powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'vc_redist.x64.exe'"
    if not exist "vc_redist.x64.exe" (
        echo [LOI] Khong tai duoc vc_redist.x64.exe. Kiem tra ket noi mang.
        pause
        exit /b 1
    )
    vc_redist.x64.exe /install /quiet /norestart
    del /f /q "vc_redist.x64.exe"
    echo - Da cai dat Visual C++ Redistributable thanh cong.
)

echo.
echo [1/5] Dang di chuyen du lieu vao AppData...
if exist "%INSTALL_ROOT%" rmdir /s /q "%INSTALL_ROOT%"
mkdir "%APP_DIR%"
robocopy "resource" "%APP_DIR%" /E /XD "models_bundle" /NFL /NDL /NJH /NJS >nul
if %ERRORLEVEL% GEQ 8 (
    echo [LOI] Khong the copy files vao AppData. Kiem tra quyen ghi.
    pause
    exit /b 1
)
echo - Backend da sao chep vao: %APP_DIR%

echo.
echo [2/5] Dang cai dat AI Models...
if exist "resource\models_bundle\" (
    if exist "resource\models_bundle\models\" (
        echo - Cai dat InsightFace...
        mkdir "%MODELS_DIR%\models" 2>nul
        robocopy "resource\models_bundle\models" "%MODELS_DIR%\models" /E /NFL /NDL /NJH /NJS >nul
        echo - InsightFace OK.
    )
    if exist "resource\models_bundle\paddleocr\" (
        echo - Cai dat PaddleOCR...
        robocopy "resource\models_bundle\paddleocr" "%USERPROFILE%\.paddleocr" /E /NFL /NDL /NJH /NJS >nul
        echo - PaddleOCR OK.
    )
    if exist "resource\models_bundle\paddlex\" (
        echo - Cai dat PaddleX...
        robocopy "resource\models_bundle\paddlex" "%USERPROFILE%\.paddlex" /E /NFL /NDL /NJH /NJS >nul
        echo - PaddleX OK.
    )
    if exist "resource\models_bundle\huggingface\" (
        echo - Cai dat HuggingFace models...
        mkdir "%USERPROFILE%\.cache\huggingface" 2>nul
        robocopy "resource\models_bundle\huggingface" "%USERPROFILE%\.cache\huggingface" /E /NFL /NDL /NJH /NJS >nul
        echo - HuggingFace OK.
    )
    echo - Toan bo AI Models da duoc cai dat vao: %MODELS_DIR% va he thong cache.
) else (
    echo - Khong tim thay models_bundle. App van chay, nhung lan dau mo se tu tai AI Models ^(~5-10 phut^).
)

echo.
echo [3/5] Kiem tra cong cu Python (uv)...
set "UV_CMD="
where uv >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "UV_CMD=uv"
    echo - Da tim thay 'uv' tren he thong.
) else (
    if not exist "%APP_DIR%\backend\" mkdir "%APP_DIR%\backend"
    set "UV_CMD=%APP_DIR%\backend\uv.exe"
    if not exist "!UV_CMD!" (
        echo - Chua co uv. Dang tai...
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile 'uv.zip'"
        if not exist "uv.zip" (
            echo [LOI] Khong tai duoc uv. Kiem tra ket noi mang.
            pause
            exit /b 1
        )
        powershell -Command "Expand-Archive -Path 'uv.zip' -DestinationPath 'uv_temp' -Force"
        if not exist "uv_temp\uv.exe" (
            echo [LOI] Giai nen uv.zip that bai.
            pause
            exit /b 1
        )
        copy /Y "uv_temp\uv.exe" "%APP_DIR%\backend\uv.exe" >nul 2>nul
        if not exist "%APP_DIR%\backend\uv.exe" (
            echo [LOI] Khong the copy uv.exe vao thu muc backend.
            pause
            exit /b 1
        )
        rmdir /s /q "uv_temp"
        del /f /q "uv.zip"
        echo - Da cai dat uv thanh cong.
    ) else (
        echo - Da co uv tai: !UV_CMD!
    )
)

echo.
echo [4/5] Khoi tao moi truong AI (lan dau mat 3-10 phut, tuy mang)...
cd /d "%APP_DIR%\backend"
!UV_CMD! venv --python 3.11
if %ERRORLEVEL% NEQ 0 (
    echo [LOI] Khong the tao Python venv.
    echo Vui long tai Python 3.11 tai: https://www.python.org/downloads/
    pause
    exit /b 1
)

set "KMP_DUPLICATE_LIB_OK=TRUE"
set "OMP_NUM_THREADS=1"
set "TOKENIZERS_PARALLELISM=false"
set "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=TRUE"
set "HF_HUB_DISABLE_TELEMETRY=1"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "SPORT_SEEKER_MODELS_ROOT=%MODELS_DIR%"

!UV_CMD! pip install -r requirements-windows.txt
if %ERRORLEVEL% NEQ 0 (
    echo [LOI] Cai dat thu vien that bai. Xem log ben tren de biet chi tiet.
    pause
    exit /b 1
)
echo - Moi truong AI da san sang.
cd /d "%~dp0"

echo.
echo [5/5] Tao loi tat truy cap...
set /p create_short="Ban co muon tao Shortcut ngoai man hinh Desktop khong? (Y/N): "
if /I "%create_short%"=="Y" (
    powershell -Command "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\Sport Seeker.lnk'); $s.TargetPath = '%APP_DIR%\sport_seeker.exe'; $s.WorkingDirectory = '%APP_DIR%'; $s.Save()"
    echo - Da tao shortcut ngoai Desktop.
)
powershell -Command "$sh = New-Object -ComObject WScript.Shell; $s = $sh.CreateShortcut([Environment]::GetFolderPath('StartMenu') + '\Programs\Sport Seeker.lnk'); $s.TargetPath = '%APP_DIR%\sport_seeker.exe'; $s.WorkingDirectory = '%APP_DIR%'; $s.Save()"
echo - Da tao shortcut trong Start Menu.

echo.
echo ========================================================
echo      CAI DAT THANH CONG!
echo ========================================================
echo AI Models: %MODELS_DIR%
echo App:       %APP_DIR%
echo.
echo Ban co the xoa thu muc giai nen nay.
echo Mo ung dung tu Desktop hoac Search "Sport Seeker".
echo.
pause
exit /b 0
