@echo off
title CV Generator
echo ========================================
echo CV Generator - Launching...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first.
    pause
    exit /b 1
)

REM Launch GUI
python core\cv_generator_gui.py

if errorlevel 1 (
    echo.
    echo Error launching application. Make sure all dependencies are installed:
    echo pip install -r requirements.txt
    pause
)
