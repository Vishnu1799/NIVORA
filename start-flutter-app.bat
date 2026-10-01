@echo off
title NIVORA - Localhost Flutter Hot-Reload Launcher
echo ========================================================
echo        Starting NIVORA Localhost + Flutter Dev Server
echo ========================================================
echo.

echo [1/3] Starting Bank Simulator on port 8001...
start "NIVORA Bank Simulator (Port 8001)" cmd /k "cd /d %~dp0bank-simulator && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo [2/3] Starting Backend API on port 8000...
start "NIVORA Backend API (Port 8000)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [3/3] Launching Flutter App in Chrome...
start "NIVORA Flutter App" cmd /k "cd /d %~dp0flutter_app && flutter run -d chrome"

echo.
echo ========================================================
echo   Services are starting!
echo   - Bank Simulator Deck: http://localhost:8001
echo   - Backend API Docs:    http://localhost:8000/docs
echo   - Customer App:        Will open in Chrome automatically!
echo ========================================================
echo.
pause
