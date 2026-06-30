#!/bin/bash
echo "=========================================="
echo "FRIDAY OS Setup (Linux/macOS)"
echo "=========================================="

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found."
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment and installing dependencies..."
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"

echo "Setting up Playwright browsers..."
playwright install chromium

echo "Setup Complete!"
echo "Run './run.sh' to start the application."
