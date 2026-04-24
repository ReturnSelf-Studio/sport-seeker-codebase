@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

cls
echo ===================================================
echo      SPORT SEEKER - GO CAI DAT (WINDOWS)
echo ===================================================
echo.
echo [!] CANH BAO: Thao tac nay se xoa TOAN BO du lieu cua Sport Seeker,
echo     bao gom:
echo     - Ung dung Sport Seeker (Flutter UI + Backend)
echo     - AI Models da tai ve
echo     - Toan bo du lieu du an va ket qua xu ly
echo     - Logs
echo.
echo     Thao tac nay KHONG THE HOAN TAC.
echo.
set /p CONFIRM="Ban co chac chan muon go cai dat? Go 'XOA' de xac nhan: "

if /i "!CONFIRM!" NEQ "XOA" (
    echo.
    echo [X] Da huy. Khong co gi bi xoa.
    timeout /t 2 >nul
    exit /b 0
)

echo.

:: --------------------------------------------------------
:: [1] Kill processes
:: --------------------------------------------------------
echo [1/5] Dang tat tien trinh Sport Seeker...
taskkill /f /im "Sport Seeker.exe" >nul 2>&1 || true
taskkill /f /im "SportSeekerAPI.exe" >nul 2>&1 || true
taskkill /f /t /fi "WINDOWTITLE eq Sport Seeker*" >nul 2>&1 || true
timeout /t 1 >nul
echo [OK] Xong.

:: --------------------------------------------------------
:: [2] Xoa app (Flutter UI + backend source)
:: Script nay nam trong thu muc cai dat → xoa chinh no
:: --------------------------------------------------------
echo.
echo [2/5] Dang xoa thu muc ung dung...
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

:: Xoa Desktop shortcut neu co
if exist "%USERPROFILE%\Desktop\Sport Seeker.lnk" (
    del /f /q "%USERPROFILE%\Desktop\Sport Seeker.lnk" >nul 2>&1
    echo [OK] Da xoa shortcut Desktop.
)
if exist "%PUBLIC%\Desktop\Sport Seeker.lnk" (
    del /f /q "%PUBLIC%\Desktop\Sport Seeker.lnk" >nul 2>&1
)

:: Xoa Start Menu shortcut neu co
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Sport Seeker.lnk" (
    del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Sport Seeker.lnk" >nul 2>&1
    echo [OK] Da xoa Start Menu shortcut.
)

:: Tu xoa chinh thu muc cai dat (deferred - sau khi script ket thuc)
echo [OK] Se xoa thu muc cai dat: !INSTALL_DIR!
echo [INFO] Thu muc se duoc xoa sau khi script ket thuc.

:: --------------------------------------------------------
:: [3] Xoa du lieu nguoi dung (models, projects, logs)
:: --------------------------------------------------------
echo.
echo [3/5] Dang xoa du lieu ung dung (models, projects, logs)...
set "SS_DIR=%USERPROFILE%\SportSeeker"
if exist "!SS_DIR!" (
    rd /s /q "!SS_DIR!" >nul 2>&1
    echo [OK] Da xoa: !SS_DIR!
) else (
    echo [--] Khong tim thay !SS_DIR!, bo qua.
)

:: --------------------------------------------------------
:: [4] Xoa Flutter prefs / AppData cache
:: --------------------------------------------------------
echo.
echo [4/5] Dang xoa cache va SharedPreferences...
if exist "%APPDATA%\com.aibus.sportSeeker" (
    rd /s /q "%APPDATA%\com.aibus.sportSeeker" >nul 2>&1
    echo [OK] Da xoa: %%APPDATA%%\com.aibus.sportSeeker
)
if exist "%APPDATA%\com.aibus" (
    rd /s /q "%APPDATA%\com.aibus" >nul 2>&1
    echo [OK] Da xoa: %%APPDATA%%\com.aibus
)
if exist "%APPDATA%\sport_seeker" (
    rd /s /q "%APPDATA%\sport_seeker" >nul 2>&1
    echo [OK] Da xoa: %%APPDATA%%\sport_seeker
)
if exist "%LOCALAPPDATA%\com.aibus.sportSeeker" (
    rd /s /q "%LOCALAPPDATA%\com.aibus.sportSeeker" >nul 2>&1
    echo [OK] Da xoa LocalAppData cache.
)

:: --------------------------------------------------------
:: [5] Xoa cache AI Models
:: --------------------------------------------------------
echo.
echo [5/5] Dang xoa cache AI Models...
if exist "%USERPROFILE%\.paddleocr" (
    rd /s /q "%USERPROFILE%\.paddleocr" >nul 2>&1
    echo [OK] Da xoa .paddleocr
)
if exist "%USERPROFILE%\.paddlex" (
    rd /s /q "%USERPROFILE%\.paddlex" >nul 2>&1
    echo [OK] Da xoa .paddlex
)
if exist "%USERPROFILE%\.insightface" (
    rd /s /q "%USERPROFILE%\.insightface" >nul 2>&1
    echo [OK] Da xoa .insightface
)

echo.
echo ===================================================
echo [HOAN TAT] Go cai dat thanh cong!
echo Sport Seeker da duoc xoa hoan toan khoi may.
echo ===================================================
echo.

:: Xoa chinh thu muc cai dat sau khi script thoat
:: Dung cmd /c de tach khoi process hien tai
start "" /b cmd /c "timeout /t 2 >nul & rd /s /q ""%INSTALL_DIR%"""

pause
endlocal
