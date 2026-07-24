import json
import sys
import os
from pathlib import Path

# 1. Test Config Parsing
print("1. Testing Config Parsing...")
try:
    with open("config/api_keys.json", "r") as f:
        config = json.load(f)
    print("   [OK] Config parsed successfully.")
    print(f"   [INFO] Email configured: {config.get('email_address')}")
except Exception as e:
    print(f"   [FAIL] Config parsing error: {e}")

# 2. Test Email Authentication
print("\n2. Testing Email Authentication...")
try:
    import imaplib
    email = config.get("email_address")
    pw = config.get("email_app_password")
    if email and pw and "YOUR_" not in email:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email, pw)
        print("   [OK] Successfully logged into Gmail using App Password!")
        mail.logout()
    else:
        print("   [SKIP] Email or App Password not set properly.")
except Exception as e:
    print(f"   [FAIL] Email authentication error: {e}")

# 3. Test ChromaDB Initialization
print("\n3. Testing ChromaDB (Vector Memory)...")
try:
    import chromadb
    from chromadb import Documents, EmbeddingFunction, Embeddings
    from google import genai
    class CustomGeminiEmbeddingFunction(EmbeddingFunction):
        def __init__(self, key: str):
            self.client = genai.Client(api_key=key)
        def __call__(self, input: Documents) -> Embeddings:
            response = self.client.models.embed_content(
                model='gemini-embedding-2',
                contents=input
            )
            return [e.values for e in response.embeddings]
            
    ef = CustomGeminiEmbeddingFunction(key=config.get("gemini_api_key"))
    client = chromadb.PersistentClient(path="memory/chroma_db")
    collection = client.get_or_create_collection(name="jarvis_memory", embedding_function=ef)
    print("   [OK] ChromaDB initialized successfully.")
except Exception as e:
    print(f"   [FAIL] ChromaDB error: {e}")

print("\n--- DIAGNOSTIC COMPLETE ---")
