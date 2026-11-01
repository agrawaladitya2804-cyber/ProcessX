@echo off
setlocal EnableExtensions
title ProcessX 2.0
cd /d "%~dp0"

echo ===================================================
echo   ProcessX 2.0 - CPU Scheduling Visualizer
echo ===================================================

rem ---- 1. Is Python installed? ------------------------------------------
set "PY="
python --version >nul 2>&1
if not errorlevel 1 set "PY=python"
if not defined PY (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
    echo.
    echo [ERROR] Python 3 was not found on this computer.
    echo         Install it from https://www.python.org/downloads/
    echo         and tick "Add python.exe to PATH" in the installer.
    echo.
    pause
    exit /b 1
)

rem ---- 2. Create the virtual environment if it does not exist ----------
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment, first run only...
    %PY% -m venv venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
)

rem ---- 3. Activate it ----------------------------------------------------
call "venv\Scripts\activate.bat"

rem ---- 4. Install requirements if needed ---------------------------------
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements, first run only. This needs an internet connection...
    python -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Could not install the requirements. Check your internet connection and try again.
        pause
        exit /b 1
    )
)

rem ---- 5. Open the browser a few seconds from now, then start Flask -----
if not defined PORT set "PORT=5000"
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:%PORT%'"

echo.
echo Starting ProcessX at http://127.0.0.1:%PORT%
echo Keep this window open while you use the app. Press Ctrl+C to stop it.
echo.
python app.py

echo.
echo ProcessX has stopped.
pause
