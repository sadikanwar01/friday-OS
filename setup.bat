@echo off
echo ==========================================
echo FRIDAY OS Setup (Windows)
echo ==========================================

echo Checking Python installation...
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment and installing dependencies...
call .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"

echo Setting up Playwright browsers...
playwright install chromium

echo Setup Complete!
echo Run 'run.bat' to start the application.
pause
