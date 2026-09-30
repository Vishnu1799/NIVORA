@echo off
title NIVORA - Start All Services
echo ========================================================
echo        Starting NIVORA + AUREV AI System
echo ========================================================
echo.

echo [1/3] Starting Bank Simulator on port 8001...
start "NIVORA Bank Simulator (Port 8001)" cmd /k "cd /d %~dp0bank-simulator && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo [2/3] Starting Backend API on port 8000...
start "NIVORA Backend API (Port 8000)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Expo Mobile App...
start "NIVORA Mobile App (Expo)" cmd /k "cd /d %~dp0mobile && npx expo start"

echo.
echo ========================================================
echo   All 3 services launched!
echo   - Bank Simulator: http://localhost:8001/docs
echo   - Backend API:    http://localhost:8000/docs
echo   - Mobile App:     Check the Expo terminal window!
echo ========================================================
echo.
pause
