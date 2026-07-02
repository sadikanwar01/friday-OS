$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FRIDAY OS RC1 - Missing Dependencies Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Voice Models Setup
$modelsDir = "data\voice_models"
if (!(Test-Path -Path $modelsDir)) {
    New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null
}

Write-Host "`n[*] Checking Voice Models in $modelsDir..." -ForegroundColor Yellow

$models = @(
    "openwakeword_friday.tflite",
    "faster-whisper-base.en",
    "en_US-lessac-medium.onnx"
)

foreach ($model in $models) {
    $modelPath = Join-Path $modelsDir $model
    if (Test-Path -Path $modelPath) {
        Write-Host "  [+] Model found: $model" -ForegroundColor Green
    } else {
        Write-Host "  [-] Model missing: $model. (Download required)" -ForegroundColor Red
        # In a real scenario, this would download from huggingface/github releases.
        Write-Host "      -> To resolve, download this model into data/voice_models/" -ForegroundColor Gray
    }
}

# 2. Ollama Setup
Write-Host "`n[*] Checking Ollama Connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction Stop
    Write-Host "  [+] Ollama is running and accessible." -ForegroundColor Green
} catch {
    Write-Host "  [-] Ollama connection failed. It is either not installed or not running." -ForegroundColor Red
    Write-Host "      -> 1. Download Ollama from https://ollama.com" -ForegroundColor Gray
    Write-Host "      -> 2. Run 'ollama run llama3' to start the service and download the default model." -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SETUP SCRIPT COMPLETE" -ForegroundColor Cyan
Write-Host "Please manually resolve the highlighted issues before running friday.py." -ForegroundColor Cyan
