@echo off
cd /d "%~dp0"
set PYTHON=.venv\Scripts\python.exe

echo ============================================================
echo  Clearing Monitor - LIVE (change-detection mode)
echo  Polls every %POLL_INTERVAL% minutes.
echo  Excel is updated ONLY when a change is detected,
echo  with the exact timestamp of the change.
echo  Press Ctrl+C to stop.
echo ============================================================
echo.
%PYTHON% main.py
