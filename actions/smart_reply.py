import time
import json
import io
import sys
import pyautogui
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def smart_reply(parameters: dict, player=None) -> str:
    """
    Reads the screen, drafts a contextual reply using Gemini, and sends it.
    If 'contact' is provided, it tries to switch to that chat first.
    """
    params = parameters or {}
    contact = params.get("contact", "").strip()

    if player:
        if contact:
            player.write_log(f"SYS: Navigating to {contact} for smart reply...")
        else:
            player.write_log("SYS: Reading screen for smart reply...")

    # 1. Switch to contact if specified (assuming WhatsApp/generic messaging app is open)
    if contact:
        try:
            # Universal search shortcut
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.4)
            pyautogui.hotkey("ctrl", "a")
            pyautogui.write(contact, interval=0.04)
            time.sleep(1.0)
            pyautogui.press("enter")
            time.sleep(1.0)
        except Exception as e:
            print(f"[SmartReply] Error navigating to contact: {e}")

    # 2. Capture Screenshot
    try:
        import mss
        import mss.tools
        import PIL.Image
    except ImportError:
        return "Missing required libraries (mss, Pillow). Please install them."

    try:
        with mss.mss() as sct:
            # Grab primary monitor
            monitor = sct.monitors[1]
            shot = sct.grab(monitor)
            png_bytes = mss.tools.to_png(shot.rgb, shot.size)
        
        img = PIL.Image.open(io.BytesIO(png_bytes))
    except Exception as e:
        return f"Failed to capture screenshot: {e}"

    # 3. Analyze with Gemini
    try:
        from google import genai
        client = genai.Client(api_key=_get_api_key())
        
        prompt = (
            "You are JARVIS acting on behalf of the user. "
            "Read the latest messages in the chat currently visible on the screen. "
            "Draft a short, natural, and contextual reply to the conversation. "
            "Output ONLY the raw text of the reply to be typed. "
            "Do not include any quotes, markdown, prefixes, or explanations. "
            "Just the exact text to type."
        )

        if player:
            player.write_log("SYS: Analyzing conversation...")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[img, prompt]
        )
        
        reply_text = response.text.strip()
        
        if not reply_text:
            return "Failed to generate a reply. Vision model returned empty."

    except Exception as e:
        return f"AI analysis failed: {e}"

    # 4. Type and send the reply
    try:
        if player:
            player.write_log(f"SYS: Replying: {reply_text}")

        # Try to focus chat input box (often Tab or just clicking)
        # Assuming the chat input is already focused, or we can just tab once (WhatsApp desktop often focuses input on chat selection)
        # We will just write directly, as after 'enter' on a search, the chat box is usually active.
        pyautogui.write(reply_text, interval=0.03)
        time.sleep(0.3)
        pyautogui.press("enter")
        
        return f"Successfully sent contextual reply: '{reply_text[:30]}...'"
    except Exception as e:
        return f"Failed to type reply: {e}"
