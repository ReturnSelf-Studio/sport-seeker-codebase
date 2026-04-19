@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul

echo ==========================================
echo   HE THONG DON DEP MOI TRUONG SPORT SEEKER
echo ==========================================
echo.

set "BASE_DIR=%~dp0"
if "%BASE_DIR:~-1%"=="\" set "BASE_DIR=%BASE_DIR:~0,-1%"

echo [1] Dang don dep cache AI Models...
if exist "%USERPROFILE%\.paddleocr" rd /s /q "%USERPROFILE%\.paddleocr" >nul 2>&1
if exist "%USERPROFILE%\.paddlex" rd /s /q "%USERPROFILE%\.paddlex" >nul 2>&1
if exist "%USERPROFILE%\.insightface" rd /s /q "%USERPROFILE%\.insightface" >nul 2>&1

echo [2] Dang don dep du lieu tam (Logs, Temp)...
if exist "%BASE_DIR%\logs" rd /s /q "%BASE_DIR%\logs" >nul 2>&1
if exist "%BASE_DIR%\resource\backend\temp" rd /s /q "%BASE_DIR%\resource\backend\temp" >nul 2>&1

echo [3] Dang don dep cache giao dien Flutter...
if exist "%APPDATA%\sport_seeker" rd /s /q "%APPDATA%\sport_seeker" >nul 2>&1
if exist "%APPDATA%\com.aibus\sportSeeker" rd /s /q "%APPDATA%\com.aibus\sportSeeker" >nul 2>&1
if exist "%APPDATA%\com.example\sportSeeker" rd /s /q "%APPDATA%\com.example\sportSeeker" >nul 2>&1

echo.
echo [OK] Hoan tat! Du lieu cu da duoc xoa sach. Ban co the khoi dong lai app.
echo.

pause
endlocal
