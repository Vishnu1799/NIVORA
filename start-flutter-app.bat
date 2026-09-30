@echo off
title NIVORA - Start Flutter App & Services
echo ========================================================
echo        Starting NIVORA Flutter App + AUREV AI
echo ========================================================
echo.

echo [1/3] Starting Bank Simulator on port 8001...
start "NIVORA Bank Simulator (Port 8001)" cmd /k "cd /d %~dp0bank-simulator && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo [2/3] Starting Backend API on port 8000...
start "NIVORA Backend API (Port 8000)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Flutter App on Chrome...
start "NIVORA Flutter App" cmd /k "cd /d %~dp0flutter_app && flutter run -d chrome"

echo.
echo ========================================================
echo   Services are running!
echo   - Flutter app will open in Chrome automatically.
echo   - To run on Windows Desktop: cd flutter_app && flutter run -d windows
echo   - To run on connected Phone: cd flutter_app && flutter run
echo ========================================================
echo.
pause
