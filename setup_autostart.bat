@echo off
cd /d "%~dp0"
echo ============================================================
echo  CLEARING MONITOR – Auto-start Setup
echo  Registers the monitor to start automatically when Windows
echo  boots, and to restart itself if it ever crashes.
echo ============================================================
echo.

:: Full paths needed by Task Scheduler
set SCRIPT_DIR=%~dp0
set PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe
set MAIN=%SCRIPT_DIR%main.py
set LOG=%SCRIPT_DIR%logs\taskscheduler.log

echo Python : %PYTHON%
echo Script : %MAIN%
echo.

:: Delete old task if it exists
schtasks /delete /tn "ClearingMonitor" /f >nul 2>&1

:: Create the task
:: /sc ONLOGON   - runs when THIS user logs in (Chrome needs a logged-in session)
:: /delay 0001:30 - 90 second delay after login (let Windows settle)
:: /rl HIGHEST   - highest available privilege for this user
schtasks /create ^
  /tn "ClearingMonitor" ^
  /tr "\"%PYTHON%\" \"%MAIN%\" >> \"%LOG%\" 2>&1" ^
  /sc ONLOGON ^
  /delay 0001:30 ^
  /rl HIGHEST ^
  /f

if errorlevel 1 (
    echo.
    echo ERROR: Could not create task. Try running this bat file
    echo        as Administrator (right-click → Run as administrator).
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Task created successfully: "ClearingMonitor"
echo.
echo  The monitor will now start automatically every time you
echo  log into Windows. No action needed on clearing day.
echo.
echo  To check it is running: double-click check_status.bat
echo  To stop it permanently: run remove_autostart.bat
echo  To stop it just now:    open Task Manager → Details
echo                          → find python.exe → End task
echo ============================================================

:: Also configure Windows power settings to prevent sleep
echo.
echo Configuring power settings to prevent the PC sleeping...
powercfg /change standby-timeout-ac 0   >nul 2>&1
powercfg /change monitor-timeout-ac 0   >nul 2>&1
echo Power settings updated (screen and sleep timers disabled on AC power).
echo.
pause
