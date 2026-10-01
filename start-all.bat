@echo off
title NIVORA - Localhost All Services Launcher
echo ========================================================
echo        Starting NIVORA + AUREV AI Localhost System
echo ========================================================
echo.

echo [1/2] Starting Bank Simulator on port 8001...
start "NIVORA Bank Simulator (Port 8001)" cmd /k "cd /d %~dp0bank-simulator && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Backend API & App Server on port 8000...
start "NIVORA Backend API (Port 8000)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo.
echo ========================================================
echo   Localhost Services Running:
echo   - Customer Shopping App:      http://localhost:8000/app
echo   - Bank Simulator Deck:        http://localhost:8001
echo   - Merchant Portal:            http://localhost:8000/merchant
echo   - Backend API Docs:           http://localhost:8000/docs
echo   - Bank API Docs:              http://localhost:8001/docs
echo ========================================================
echo.
echo Opening browser tabs...
start http://localhost:8001
start http://localhost:8000/app
echo.
pause
