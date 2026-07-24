"""
actions/search_memory.py — Instant Memory Vault Engine for JARVIS Mark XL
Saves & searches long-term memories, facts, notes, and reminders in ChromaDB vector memory.
"""

import json
import sys
import datetime
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()

def search_memory(parameters: dict, player=None) -> str:
    """
    Searches or saves memories into the ChromaDB Instant Memory Vault.
    parameters:
        action : search | save | remember | query
        query  : Search term or memory text to save
        category : optional category tag (identity, notes, reminders, preferences)
    """
    params = parameters or {}
    action = (params.get("action") or "search").lower().strip()
    query = (params.get("query") or params.get("text") or "").strip()
    category = (params.get("category") or "notes").lower().strip()

    if not query:
        return "Please provide a memory query or note to remember, Akul."

    try:
        from memory.memory_manager import update_memory, load_memory
        
        if action in ["save", "remember", "store", "add"]:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            fact_entry = f"[{now_str}] {query}"
            update_memory(category, f"note_{int(datetime.datetime.now().timestamp())}", fact_entry)
            
            if player and hasattr(player, "write_log"):
                player.write_log(f"SYS: [MEMORY VAULT] Saved memory under {category}: '{query}'")
            return f"Saved to Instant Memory Vault under '{category}', Akul: '{query}'."

        # Search Memory Vault
        import chromadb
        from chromadb import Documents, EmbeddingFunction, Embeddings
        from google import genai
        
        cfg_path = BASE_DIR / "config" / "api_keys.json"
        if not cfg_path.exists():
            return "API keys configuration missing."

        with open(cfg_path, "r", encoding="utf-8") as f:
            api_key = json.load(f)["gemini_api_key"]
            
        class CustomGeminiEmbeddingFunction(EmbeddingFunction):
            def __init__(self, key: str):
                self.client = genai.Client(api_key=key)
            def __call__(self, input: Documents) -> Embeddings:
                response = self.client.models.embed_content(
                    model='gemini-embedding-2',
                    contents=input
                )
                return [e.values for e in response.embeddings]
                
        ef = CustomGeminiEmbeddingFunction(key=api_key)
        client = chromadb.PersistentClient(path=str(BASE_DIR / "memory" / "chroma_db"))
        
        try:
            collection = client.get_collection(name="jarvis_memory", embedding_function=ef)
        except Exception:
            return "Memory Vault is currently empty."
            
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        
        if not results or not results['documents'] or not results['documents'][0]:
            # Fallback to local memory JSON search
            local_mem = load_memory()
            matches = []
            for cat, val in local_mem.items():
                if isinstance(val, dict):
                    for k, v in val.items():
                        if query.lower() in str(v).lower():
                            matches.append(f"{cat}/{k}: {v}")
            if matches:
                return "Found in local memory vault:\n• " + "\n• ".join(matches[:5])
            return "No relevant memories found in vault."
            
        found_facts = results['documents'][0]
        return "I retrieved the following memories from your vault, Akul:\n• " + "\n• ".join(found_facts)
        
    except Exception as e:
        return f"Memory Vault search error: {e}"
