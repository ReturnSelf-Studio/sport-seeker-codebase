@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo ==========================================
echo   🚀 SPORT SEEKER CLI TOOL (WINDOWS)
echo ==========================================

:: 1. Check Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [LỖI] Python chưa được cài đặt hoặc chưa thêm vào PATH. Vui lòng cài Python 3.11+.
    exit /b 1
)

:: 2. Check/Install uv
uv --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] uv chưa được cài đặt. Đang tiến hành cài đặt uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

:: 3. Setup Virtual Environment (Minimal)
if not exist ".venv\" (
    echo [INFO] Đang tạo virtual environment...
    call uv venv --python 3.11
)

:: 4. Activate Virtual Environment
call .venv\Scripts\activate.bat

:: 5. Chuyển giao toàn bộ quyền điều khiển cho Python CLI
python scripts\cli.py %*
