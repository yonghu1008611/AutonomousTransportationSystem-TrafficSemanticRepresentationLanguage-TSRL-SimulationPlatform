@echo off
title ATSISP Scenario Selector

echo ========================================
echo   ATSISP Traffic Simulation Scenario Selector
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not detected. Please install Python 3.9.0-3.11.0.
    echo Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Starting scenario selector...
echo.

REM Start Tkinter scenario selector
python tkinter_scenario_selector.py

if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to start scenario selector.
    echo Please make sure you have installed all dependencies.
    echo.
    pause
    exit /b 1
)

echo Scenario selector started.
pause