@echo off
title ThreatShield — Unified Detector
color 0B

echo.
echo  ====================================================
echo   ThreatShield — Unified Threat Detector
echo  ====================================================
echo.

cd /d "%~dp0"

:: Install dependencies if needed
pip install -r requirements.txt --quiet

echo.
echo  Starting server at http://127.0.0.1:5000
echo  Press Ctrl+C to stop.
echo.

python app.py

pause
