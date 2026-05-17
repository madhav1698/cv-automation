@echo off
setlocal enabledelayedexpansion

title ApplyCraft - Launcher
echo ========================================
echo   ApplyCraft ^| Launcher
echo ========================================
echo.

cd /d "%~dp0"

:: 1. Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10 or newer from python.org and re-run this script.
    pause
    exit /b 1
)

:: 2. First-time setup if no venv exists. The setup script creates the
::    venv, installs requirements, and seeds user_config.json from the
::    example so the GUI has a usable config on first launch.
if not exist "venv\Scripts\python.exe" (
    echo No venv detected. Running first-run setup...
    python setup_applycraft.py
    if errorlevel 1 (
        echo Setup failed. See messages above.
        pause
        exit /b 1
    )
) else (
    :: Quietly refresh deps in case requirements.txt changed since last launch.
    call venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
)

:: 3. Launch the GUI using the venv interpreter (no global state needed).
echo Launching ApplyCraft...
echo.
"venv\Scripts\python.exe" core\cv_generator_gui.py

if errorlevel 1 (
    echo.
    echo App closed with an error. See logs\ for details.
    pause
)
