@echo off
echo =======================================
echo  Clearing Monitor - Setup
echo =======================================
echo.
echo  Virtual environment already created and packages installed.
echo  Python: .venv\Scripts\python.exe
echo.
echo  Verifying installation...

cd /d "%~dp0"
.venv\Scripts\python.exe -c "import selenium, openpyxl, bs4, schedule, requests; print('  All packages OK')"
if errorlevel 1 (
    echo.
    echo  ERROR: packages missing. Re-running install...
    .venv\Scripts\python.exe -m pip install selenium webdriver-manager beautifulsoup4 lxml openpyxl requests schedule
)

echo.
echo =======================================
echo  Setup verified. Ready to run.
echo  Next: double-click debug_scrape.bat
echo =======================================
pause
