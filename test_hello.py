import asyncio

from google import genai

from backend.config import get_settings


async def main():
    settings = get_settings()
    api_key = settings.gemini_api_key
    model = settings.gemini_model

    if not api_key:
        print("FAIL: API Key is missing.")
        return

    print(f"[*] Verifying Gemini Authentication with model {model}...")
    try:
        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model=f"models/{model}" if not model.startswith("models/") else model,
                contents="Hello"
            )
            print("[+] Authentication Successful!")
            print(f"[+] Response: {response.text}")
        except Exception as e:
            if "404" in str(e):
                print(f"[!] Model {model} not found. Attempting to list available models...")
                models = client.models.list_models()
                for m in models:
                    print(f" - {m.name}")
            else:
                raise e
    except Exception as e:
        print(f"FAIL: Gemini API error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
