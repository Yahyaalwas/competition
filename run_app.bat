@echo off
REM ──────────────────────────────────────────────────────────────
REM GCC AI Intelligence Platform — One-Click Launcher (Windows)
REM ──────────────────────────────────────────────────────────────

echo.
echo   +======================================================+
echo   ^|        GCC AI Intelligence Platform                  ^|
echo   ^|   AI-Powered GCC Youth Employment Intelligence       ^|
echo   +======================================================+
echo.

REM ── Check Python ─────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Python not found.
    echo   Install Python 3.10+ from https://python.org
    echo   Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo   [OK] %%v

REM ── Check Streamlit ──────────────────────────────────────────
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [SETUP] Installing dependencies...
    python -m pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo   [ERROR] Dependency installation failed.
        echo   Try: pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo   [OK] Streamlit: ready

REM ── Validate data cache ───────────────────────────────────────
if exist "data\processed\youth_unemployment_rate.csv" (
    echo   [OK] Data cache: available (offline mode supported)
) else (
    echo   [WARN] Data cache not found. Use "Refresh Data" in the sidebar.
)

echo.
echo   Launching platform at http://localhost:8501
echo   Press Ctrl+C to stop
echo.

REM ── Launch ────────────────────────────────────────────────────
python -m streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause
