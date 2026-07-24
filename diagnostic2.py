import json
from google import genai

with open("config/api_keys.json", "r") as f:
    api_key = json.load(f)["gemini_api_key"]

client = genai.Client(api_key=api_key)

try:
    response = client.models.embed_content(
        model='gemini-embedding-2',
        contents="Hello world!"
    )
    print("   [OK] gemini-embedding-2 worked!")
except Exception as e:
    print(f"   [FAIL] {e}")

try:
    response = client.models.embed_content(
        model='gemini-embedding-001',
        contents="Hello world!"
    )
    print("   [OK] gemini-embedding-001 worked!")
except Exception as e:
    print(f"   [FAIL] {e}")

try:
    response = client.models.embed_content(
        model='text-embedding-004',
        contents="Hello world!"
    )
    print("   [OK] text-embedding-004 worked!")
except Exception as e:
    print(f"   [FAIL] {e}")
