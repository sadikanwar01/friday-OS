# Installation Guide for FRIDAY OS

## Prerequisites
- Python 3.12+
- Git

## Windows Setup
1. Clone the repository: `git clone <repository_url>`
2. Run the automated setup script:
   ```cmd
   setup.bat
   ```
3. Run the application:
   ```cmd
   run.bat
   ```

## Linux/macOS Setup
1. Clone the repository: `git clone <repository_url>`
2. Make the scripts executable:
   ```bash
   chmod +x setup.sh run.sh
   ```
3. Run the automated setup script:
   ```bash
   ./setup.sh
   ```
4. Run the application:
   ```bash
   ./run.sh
   ```

## Manual Installation
```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Start the application
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
