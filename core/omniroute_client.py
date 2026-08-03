"""
core/omniroute_client.py — J.A.R.V.I.S. Mark XLI OmniRoute Proxy & Rate-Limit Fallback Engine
Offloads heavy content generation (file processing, vision, document chat) to local OmniRoute
or fallback free providers whenever 429 rate limits occur on primary endpoints.
"""

import json
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

OMNIROUTE_URL = "http://localhost:20128/v1/chat/completions"

class OmniRouteClient:
    """Proxy manager for routing text/vision generation requests through local OmniRoute gateway."""

    def __init__(self):
        self.api_key = self._load_api_key()

    def _load_api_key(self) -> str:
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f).get("gemini_api_key", "")
        except Exception:
            pass
        return ""

    def is_omniroute_running(self) -> bool:
        """Checks if local OmniRoute gateway is active on port 20128."""
        try:
            r = requests.get("http://localhost:20128/v1/models", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False

    def generate_text_fallback(self, prompt: str, model_preference: str = "auto") -> str | None:
        """
        Routes prompt to local OmniRoute proxy if running, or returns None to let primary client retry.
        """
        if not self.is_omniroute_running():
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "Bearer dummy"
        }
        payload = {
            "model": model_preference,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            resp = requests.post(OMNIROUTE_URL, json=payload, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    if content:
                        return content.strip()
        except Exception as e:
            print(f"[OmniRouteClient] Proxy attempt notice: {e}")

        return None


omniroute_client = OmniRouteClient()
