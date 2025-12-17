@echo off
REM NEMIS Quick Start Script for Windows
echo ====================================
echo NEMIS Quick Start
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

REM Check if PostgreSQL is accessible
psql -U postgres -c "SELECT 1" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PostgreSQL not accessible!
    echo Please ensure PostgreSQL is installed and running.
    pause
    exit /b 1
)

echo [1/5] Checking database...
psql -U postgres -lqt | findstr /C:"NEMIS" >nul
if errorlevel 1 (
    echo Creating NEMIS database...
    psql -U postgres -c "CREATE DATABASE NEMIS;"
    if errorlevel 1 (
        echo ERROR: Could not create database
        pause
        exit /b 1
    )
    
    echo Loading schema...
    psql -U postgres -d NEMIS -f schema.sql
    if errorlevel 1 (
        echo ERROR: Could not load schema
        pause
        exit /b 1
    )
    echo Database created successfully!
) else (
    echo Database already exists.
)

echo.
echo [2/5] Creating virtual environment...
if not exist .venv (
    python -m venv .venv
)

echo.
echo [3/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [4/5] Installing dependencies...
pip install -r requirements.txt >nul 2>&1

echo.
echo [5/5] Starting NEMIS...
echo.
echo ====================================
echo NEMIS is starting!
echo ====================================
echo.
echo Access at: http://127.0.0.1:5000
echo.
echo Default Logins:
echo   Admin: AD123456
echo   Officer: EO123456
echo.
echo Press Ctrl+C to stop the server
echo ====================================
echo.

python nemis.py

pause
