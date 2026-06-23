@echo off
cd /d "%~dp0"
set PYTHON=.venv\Scripts\python.exe

echo ============================================================
echo  Inject a fake change to test the detection pipeline
echo ============================================================
echo.
echo This will modify the saved state so the next poll detects
echo a change and writes it to Excel with the exact timestamp.
echo.
echo Example injections:
echo   - Makes Bitcoin appear to jump to $99999 (massive rise)
echo   - Makes a UCAS course appear to drop to 50 points
echo.

echo [1] Injecting fake change: CoinGecko - Bitcoin price spike...
%PYTHON% inject_change.py COINGECKO "Bitcoin" "99999"
if errorlevel 1 goto :end

echo.
echo [2] Now running a single poll to detect and record the change...
%PYTHON% main.py --once --uni COINGECKO

echo.
echo [3] Opening Excel to see the recorded change...
start "" "%~dp0clearing_data.xlsx"

:end
echo.
pause
