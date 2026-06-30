#!/bin/bash
echo "=========================================="
echo "Starting FRIDAY OS"
echo "=========================================="

if [ ! -f ".venv/bin/activate" ]; then
    echo "Error: Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

source .venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
