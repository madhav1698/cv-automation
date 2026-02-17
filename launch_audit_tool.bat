@echo off
title Application Audit
echo ========================================
echo Application Audit - Launching...
echo ========================================
echo.

python core\application_audit.py

if errorlevel 1 (
    echo.
    echo Error launching application.
    pause
)
