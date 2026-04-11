import requests
import os
from dotenv import load_dotenv

BASE_URL = "http://localhost:8000"

# Check API Keys First
load_dotenv(os.path.join("backend", ".env"))
print("=== Checking API Keys ===")
required_keys = [
    "GOOGLE_API_KEY", "HUGGINGFACE_API_TOKEN", "TAVILY_API_KEY",
    "GOOGLE_FACTCHECK_API_KEY", "NEWS_API_KEY", "OPENAI_API_KEY",
    "SUPABASE_URL", "SUPABASE_ANON_KEY"
]
missing = []
for key in required_keys:
    val = os.getenv(key)
    if not val or "your_" in val or "CHANGE_THIS" in val:
        missing.append(key)

if missing:
    print(f"[FAIL] Missing or Default API Keys: {', '.join(missing)}")
else:
    print(f"[OK] All required API Keys configured.")
print("=========================\n")

routes = [
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/api/v1"),
    ("GET", "/favicon.ico"),
    ("GET", "/docs"),
    ("POST", "/api/v1/analyze"),
    ("POST", "/api/v1/quick-analyze"),
    ("POST", "/api/v1/feedback"),
    ("GET", "/api/v1/stats"),
]

payloads = {
    "/api/v1/analyze": {
        "content": "Test news content",
        "content_type": "text"
    },
    "/api/v1/quick-analyze": {
        "content": "Test quick analysis content",
        "content_type": "text",
        "metadata": {}
    },
    "/api/v1/feedback": {
        "analysis_id": "test-id",
        "original_content": "Test content",
        "predicted_verdict": "FAKE",
        "user_verdict": "VERIFIED",
        "user_confidence": 4,
        "comments": "Test comment"
    }
}

for method, route in routes:
    url = BASE_URL + route
    try:
        if method == "GET":
            r = requests.get(url)
        else:
            r = requests.post(url, json=payloads.get(route, {}))

        status = r.status_code
        if status >= 500:
            print(f"[ERROR] {method} {route} -> {status} (Server Error)")
        elif status == 404:
            print(f"[NOT FOUND] {method} {route} -> {status}")
        elif status >= 400:
            print(f"[FAIL] {method} {route} -> {status}")
        else:
            print(f"[OK] {method} {route} -> {status}")

    except Exception as e:
        print(f"[EXCEPTION] {method} {route} -> {e}")