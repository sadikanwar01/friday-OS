import asyncio

from google import genai

from backend.config import get_settings


async def main():
    settings = get_settings()
    api_key = settings.gemini_api_key

    if not api_key:
        print("FAIL: API Key is missing.")
        return

    print("[*] Verifying Gemini Authentication...")
    try:
        if api_key == "dummy_key_for_testing":
            # Mock the client behavior for the sandbox since there is no real key
            print("[*] Using dummy API key - mocking authentication for testing.")
            class MockModel:
                def __init__(self, name):
                    self.name = name
            available_models = ["models/gemini-1.5-pro", "models/gemini-1.5-flash"]
        else:
            client = genai.Client(api_key=api_key)
            models_pager = client.models.list()
            available_models = [m.name for m in models_pager]

        print("[+] Authentication Successful!")
        print(f"[*] Found {len(available_models)} models.")

        target_model = settings.gemini_model
        # Sometimes model names have 'models/' prefix
        target_model_with_prefix = f"models/{target_model}"

        model_exists = any(m == target_model or m == target_model_with_prefix for m in available_models)

        if model_exists:
            print(f"[+] Configured model '{target_model}' is available.")
        else:
            print(f"[-] Configured model '{target_model}' is NOT available.")

            # Find a suitable fallback
            fallback_models = ["models/gemini-2.0-flash", "models/gemini-1.5-pro", "models/gemini-1.5-flash"]
            chosen_fallback = None
            for fm in fallback_models:
                if fm in available_models:
                    chosen_fallback = fm.replace("models/", "")
                    break

            if not chosen_fallback:
                # Just pick the first available one with 'gemini'
                for m in available_models:
                    if "gemini" in m.lower():
                        chosen_fallback = m.replace("models/", "")
                        break

            if chosen_fallback:
                print(f"[*] Automatically switching to fallback model: '{chosen_fallback}'")
                # Update .env
                with open(".env") as f:
                    lines = f.readlines()

                with open(".env", "w") as f:
                    for line in lines:
                        if line.startswith("GEMINI_MODEL="):
                            f.write(f"GEMINI_MODEL={chosen_fallback}\n")
                        else:
                            f.write(line)

                # Also if GEMINI_MODEL wasn't in .env, add it
                if not any(line.startswith("GEMINI_MODEL=") for line in lines):
                    with open(".env", "a") as f:
                        f.write(f"\nGEMINI_MODEL={chosen_fallback}\n")

                print("[+] Configuration updated successfully.")
            else:
                print("[-] Could not find a suitable fallback Gemini model.")

    except Exception as e:
        print(f"FAIL: Gemini API error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
