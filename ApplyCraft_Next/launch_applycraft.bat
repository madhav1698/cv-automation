@echo off
setlocal enabledelayedexpansion

title ApplyCraft NEXT - Launcher
echo ========================================
echo   ApplyCraft NEXT ^| Deployment Test
echo ========================================
echo.

:: 1. Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10 or newer.
    pause
    exit /b 1
)

:: 2. Setup Virtual Environment
if not exist "venv" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create venv.
        pause
        exit /b 1
    )
)

:: 3. Install/Update Dependencies
echo [2/3] Verifying dependencies...
call venv\Scripts\activate
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo Warning: Some dependencies failed to install.
    echo The app might not run correctly.
)

:: 4. Launch Application
echo [3/3] Launching ApplyCraft...
echo.
python core\cv_generator_gui.py

if errorlevel 1 (
    echo.
    echo App closed with an error.
    pause
)
