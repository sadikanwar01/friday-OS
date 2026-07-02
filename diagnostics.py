import asyncio
from pathlib import Path

# Diagnostics script for FRIDAY OS RC1

def check_voice_models():
    print("[*] Checking Voice Models...")
    models_dir = Path("data/voice_models")
    required = ["openwakeword_friday.tflite", "faster-whisper-base.en", "en_US-lessac-medium.onnx"]
    missing = []
    for model in required:
        if not (models_dir / model).exists() and not (models_dir / model).is_dir():
            missing.append(model)
    if missing:
        print(f"  [-] Missing Voice Models: {missing}")
        return False, missing
    print("  [+] Voice Models found.")
    return True, []

async def check_playwright():
    print("[*] Checking Playwright Binaries...")
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
            print("  [+] Playwright Chromium binaries found and working.")
            return True, None
    except Exception as e:
        if "Executable doesn't exist" in str(e):
            print("  [-] Playwright binaries missing.")
            return False, "Playwright binaries missing"
        print(f"  [-] Playwright error: {e}")
        return False, str(e)

async def check_ollama():
    print("[*] Checking Ollama Connection...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:11434/api/tags", timeout=3.0)
            if resp.status_code == 200:
                print("  [+] Ollama is running.")
                return True, None
            else:
                print(f"  [-] Ollama returned status {resp.status_code}")
                return False, f"Ollama returned {resp.status_code}"
    except Exception as e:
        print(f"  [-] Ollama connection failed: {e}")
        return False, "Ollama connection failed"

async def main():
    print("FRIDAY OS - Diagnostics RC1\n" + "="*40)
    missing_items = {}

    # Check Database
    print("[*] Checking Database...")
    try:
        from backend.database import init_database
        await init_database()
        print("  [+] Database initialized successfully.")
    except Exception as e:
        print(f"  [-] Database initialization failed: {e}")
        missing_items['database'] = str(e)

    # Check Voice Models
    v_ok, v_missing = check_voice_models()
    if not v_ok:
        missing_items['voice_models'] = v_missing

    # Check Playwright
    p_ok, p_err = await check_playwright()
    if not p_ok:
        missing_items['playwright'] = p_err

    # Check Ollama
    o_ok, o_err = await check_ollama()
    if not o_ok:
        missing_items['ollama'] = o_err

    print("\n" + "="*40)
    print("DIAGNOSTICS COMPLETE")
    print(f"Missing/Failed Checks: {len(missing_items)}")
    for k, v in missing_items.items():
        print(f" - {k}: {v}")

if __name__ == "__main__":
    asyncio.run(main())
