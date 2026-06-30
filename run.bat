@echo off
echo ==========================================
echo Starting FRIDAY OS
echo ==========================================

IF NOT EXIST ".venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
