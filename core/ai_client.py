"""
core/ai_client.py — High-Availability Gemini API Generation Client for JARVIS Mark 58
Provides automatic multi-model fallback and exponential backoff retry across:
1. gemini-3.8-flash
2. gemini-2.0-flash
3. gemini-2.0-flash-lite
Prevents 503 high demand or 429 rate limit exceptions from interrupting academic tutoring or research.
"""

import time
import json
from pathlib import Path
from typing import Optional, List, Union, Any
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent.parent

def get_api_key() -> str:
    cfg = BASE_DIR / "config" / "api_keys.json"
    if cfg.exists():
        try:
            return json.loads(cfg.read_text(encoding="utf-8")).get("gemini_api_key", "")
        except Exception:
            pass
    return ""

def get_gemini_client() -> Optional[genai.Client]:
    k = get_api_key()
    if not k:
        return None
    return genai.Client(api_key=k)

DEFAULT_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest"
]

def generate_text_with_retry(
    prompt_or_contents: Union[str, List[Any]],
    client: Optional[genai.Client] = None,
    models: Optional[List[str]] = None,
    max_retries_per_model: int = 2
) -> str:
    """
    Executes generate_content with multi-model fallback and backoff.
    """
    if client is None:
        client = get_gemini_client()
    if client is None:
        return "Gemini API key is missing. Please add it to config/api_keys.json."

    model_list = models or DEFAULT_MODELS

    last_err = ""
    for model_name in model_list:
        for attempt in range(max_retries_per_model):
            try:
                res = client.models.generate_content(
                    model=model_name,
                    contents=prompt_or_contents
                )
                if res and res.text:
                    return res.text.strip()
            except Exception as e:
                err_s = str(e)
                last_err = err_s
                if any(x in err_s for x in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                    time.sleep(1.0 * (attempt + 1))
                    continue
                # If 404 model not found, immediately break to next model
                if "404" in err_s or "NOT_FOUND" in err_s:
                    break
                break

    return f"Service temporarily busy across AI endpoints ({last_err[:100]}). Please try again in a few moments."
