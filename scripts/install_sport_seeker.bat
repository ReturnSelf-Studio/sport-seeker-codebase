@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Ép thư mục làm việc luôn là thư mục chứa file .bat này
cd /d "%~dp0"

echo ========================================================
echo      SPORT SEEKER - THIẾT LẬP ỨNG DỤNG (WINDOWS)
echo ========================================================

:: Chặn trường hợp user chạy thẳng file .bat từ trong file ZIP chưa giải nén
if not exist "resource\" (
    echo [LỖI] Không tìm thấy thư mục "resource".
    echo Vui lòng đảm bảo bạn đã GIẢI NÉN TOÀN BỘ file zip ra một thư mục trước khi chạy cài đặt.
    echo.
    pause
    exit /b 1
)

:: Thư mục cài đặt vĩnh viễn
set "INSTALL_ROOT=%APPDATA%\SportSeeker"
set "APP_DIR=%INSTALL_ROOT%\app"

echo [1/4] Đang di chuyển dữ liệu vào hệ thống AppData...
if exist "%INSTALL_ROOT%" rmdir /s /q "%INSTALL_ROOT%"
mkdir "%APP_DIR%"

xcopy /e /i /y "resource\*" "%APP_DIR%\" >nul

echo.
echo [2/4] Đang kiểm tra công cụ Python (uv)...
set "UV_CMD="

:: Thử tìm uv có sẵn trên hệ thống (Sẽ quét trúng uv trên máy Dev của bạn)
where uv >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "UV_CMD=uv"
    echo - Da tim thay cong cu 'uv' tren he thong.
) else (
    :: Nếu là máy khách hàng trống trơn, tiến hành tải bản standalone
    set "UV_CMD=%APP_DIR%\backend\uv.exe"
    if not exist "!UV_CMD!" (
        echo - May khach chua co uv. Dang tai uv cuc bo...
        powershell -Command "Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile 'uv.zip'"
        powershell -Command "Expand-Archive -Path 'uv.zip' -DestinationPath 'uv_temp' -Force"
        move /Y uv_temp\uv-x86_64-pc-windows-msvc\uv.exe "%APP_DIR%\backend\" >nul
        rmdir /s /q uv_temp
        del uv.zip
    )
)

echo.
echo [3/4] Khoi tao moi truong AI (Lan dau se mat 1-3 phut)...
cd /d "%APP_DIR%\backend"
:: Gọi biến UV_CMD (Nó sẽ linh hoạt là 'uv' hoặc '.\uv.exe' tùy máy)
!UV_CMD! venv --python 3.11
!UV_CMD! pip install -r requirements-windows.txt

echo.
echo [4/4] Tao loi tat truy cap...
set /p create_short="Ban co muon tao Shortcut ngoai man hinh Desktop khong? (Y/N): "
if /I "%create_short%"=="Y" (
    powershell -Command "$WShell = New-Object -ComObject WScript.Shell; $Shortcut = $WShell.CreateShortcut('%USERPROFILE%\Desktop\Sport Seeker.lnk'); $Shortcut.TargetPath = '%APP_DIR%\sport_seeker.exe'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Save()" 2>nul
    echo - Da tao shortcut ngoai Desktop.
)

:: Luôn tạo shortcut trong Start Menu
powershell -Command "$WShell = New-Object -ComObject WScript.Shell; $StartMenu = [Environment]::GetFolderPath('StartMenu'); $ShortcutPath = $StartMenu + '\Programs\Sport Seeker.lnk'; $Shortcut = $WShell.CreateShortcut($ShortcutPath); $Shortcut.TargetPath = '%APP_DIR%\sport_seeker.exe'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Save()" 2>nul
echo - Da tao shortcut trong Start Menu (Search 'Sport Seeker' de thay).

echo.
echo ========================================================
echo      CAI DAT THANH CONG!
echo ========================================================
echo Ban co the xoa thu muc giai nen nay. Hay mo App tu Desktop/Search.
echo.
pause
exit
