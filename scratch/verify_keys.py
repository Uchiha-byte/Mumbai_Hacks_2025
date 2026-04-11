import os
import requests
from dotenv import load_dotenv

# Clear existing env var to force reload
if "OPENAI_API_KEY" in os.environ:
    del os.environ["OPENAI_API_KEY"]

load_dotenv("backend/.env", override=True)

def verify_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or "your_" in api_key:
        return f"MISSING (Found: {api_key})"
    
    # Print first and last 4 chars for debugging
    key_display = f"{api_key[:10]}...{api_key[-4:]}"
    print(f"DEBUG: Using key: {key_display}")

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=5)
        if response.status_code == 200:
            return "VALID"
        else:
            return f"INVALID ({response.status_code}): {response.text}"
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    print("--- API Key Verification ---")
    print(f"OpenAI: {verify_openai()}")
