"""
actions/whatsapp_reader.py — WhatsApp Intelligent Chat Engine & Locked Vault Inspector
Handles locked chat vault unlocking via search bar passcode (123450), contact search, message delivery, and unread chat inspection.
"""

import os
import sys
import time
import json
import pyautogui
import pyperclip
from pathlib import Path
from google import genai

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def _get_passcode() -> str:
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("whatsapp_locked_chats_passcode", "123450")
    except Exception:
        pass
    return "123450"


def _get_api_key() -> str:
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("gemini_api_key", "")
    except Exception:
        pass
    return ""


def _focus_whatsapp() -> bool:
    """Focuses or launches WhatsApp Desktop."""
    try:
        import pygetwindow as gw
        wins = gw.getWindowsWithTitle("WhatsApp")
        if wins:
            win = wins[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.3)
            return True
    except Exception:
        pass

    try:
        from actions.open_app import open_app
        open_app({"app_name": "WhatsApp"})
        time.sleep(2.5)
        pyautogui.hotkey("win", "up")
        return True
    except Exception as e:
        print(f"[WhatsAppEngine] Could not launch WhatsApp: {e}")
        return False


def unlock_locked_chats(passcode: str = "123450", player=None) -> bool:
    """
    Unlocks WhatsApp Locked Chats vault based on exact UI interaction:
    1. Ctrl + F to focus Search Bar ('Search or start a new chat')
    2. Types passcode '123450' in Search Bar
    3. Clicks / selects the 'Locked chats' option that appears below
    """
    if not _focus_whatsapp():
        return False

    time.sleep(0.4)
    actual_code = passcode or _get_passcode()

    # 1. Focus Search Bar
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.3)
    
    # Clear any text in search bar
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.2)

    # 2. Type passcode '123450' directly in Search Bar
    pyautogui.write(str(actual_code), interval=0.04)
    time.sleep(0.5)

    # 3. Select 'Locked chats' option that appears below in search results
    screen_w, screen_h = pyautogui.size()
    # Click the 'Locked chats' result entry (approx 22% from left, 52% from top)
    pyautogui.click(int(screen_w * 0.22), int(screen_h * 0.52))
    time.sleep(0.3)
    
    # Backup keyboard navigation: Down Arrow -> Enter
    pyautogui.press("down")
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.8)

    if player and hasattr(player, "write_log"):
        player.write_log("WHATSAPP: Vault passcode entered in search bar and Locked Chats opened.")
    return True


def send_whatsapp_message(contact: str, message: str, is_locked: bool = False, passcode: str = "123450", player=None) -> str:
    """
    Delivers a WhatsApp message to a contact (handling locked chats vault & normal chats).
    """
    if not contact or not message:
        return "Please specify both contact name and message text, sir."

    if player and hasattr(player, "write_log"):
        vault_tag = " [LOCKED CHATS VAULT]" if is_locked else ""
        player.write_log(f"WHATSAPP: Delivering message to '{contact}'{vault_tag}...")

    if not _focus_whatsapp():
        return "Could not open WhatsApp Desktop."

    time.sleep(0.4)

    # If message is for a locked chat, unlock vault first by putting passcode in search bar
    if is_locked or "locked" in contact.lower():
        unlock_locked_chats(passcode=passcode, player=player)
        time.sleep(0.5)

    # Search for contact
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")
    time.sleep(0.2)

    pyautogui.write(contact, interval=0.03)
    time.sleep(0.6)
    pyautogui.press("enter")
    time.sleep(0.6)

    # Type & deliver message in active chat pane
    pyperclip.copy(message)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)
    pyautogui.press("enter") # Deliver message
    time.sleep(0.4)

    result_str = f"Message successfully delivered to '{contact}': \"{message}\""
    if player and hasattr(player, "write_log"):
        player.write_log(f"WHATSAPP: Delivered -> {result_str}")
        if hasattr(player, "push_notification"):
            player.push_notification(f"WhatsApp Delivered to {contact}", "success")

    return result_str


def read_whatsapp_messages(parameters: dict, player=None) -> str:
    """
    Reads, summarizes, and handles WhatsApp chat operations.

    parameters:
        action     : read | send | reply_unread | locked_chats
        contact    : Contact name
        message    : Message text to deliver
        is_locked  : Set True if reading/messaging locked chat
        passcode   : Vault passcode (default '123450')
        auto_reply : Set True for AI auto-reply
    """
    params = parameters or {}
    action = (params.get("action") or "read").lower().strip()
    contact = params.get("contact", "").strip()
    message = params.get("message", "").strip()
    is_locked = bool(params.get("is_locked", False))
    passcode = params.get("passcode") or _get_passcode()
    auto_reply = bool(params.get("auto_reply", False))

    # Send / Deliver Action
    if action in ("send", "write", "deliver") or (contact and message and action != "read"):
        return send_whatsapp_message(contact=contact, message=message, is_locked=is_locked, passcode=passcode, player=player)

    # Unlock Vault Action
    if action in ("locked_chats", "unlock_vault"):
        unlock_locked_chats(passcode=passcode, player=player)
        return "Entered passcode in search bar and opened Locked Chats vault."

    if player and hasattr(player, "write_log"):
        vault_tag = " [LOCKED VAULT]" if is_locked else ""
        player.write_log(f"WHATSAPP: Reading messages for contact='{contact or 'unread'}'{vault_tag}...")

    if not _focus_whatsapp():
        return "Could not focus WhatsApp Desktop."

    time.sleep(0.5)

    if is_locked:
        unlock_locked_chats(passcode=passcode, player=player)
        time.sleep(0.5)

    if contact:
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")
        time.sleep(0.2)
        pyautogui.write(contact, interval=0.03)
        time.sleep(0.6)
        pyautogui.press("enter")
        time.sleep(0.6)

    # Copy chat text
    screen_w, screen_h = pyautogui.size()
    pyautogui.click(screen_w // 2, screen_h // 2)
    time.sleep(0.3)

    pyperclip.copy("")
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.3)
    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.4)

    chat_text = pyperclip.paste().strip()
    pyautogui.press("escape")

    if not chat_text or len(chat_text) < 5:
        return f"Opened WhatsApp chat for '{contact or 'Unread Chat'}', but could not extract text directly."

    # Gemini Summary & Auto-Reply
    api_key = _get_api_key()
    summary = chat_text[-350:]
    smart_reply = ""

    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                f"Analyze these recent WhatsApp messages. "
                f"1) Summarize what the contact said in 2 sentences. "
                f"2) Suggest a smart, helpful reply as Akul Bhatnagar.\n\n{chat_text[-1200:]}"
            )
            res = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            if res and res.text:
                summary = res.text.strip()
        except Exception as e:
            print(f"[WhatsAppEngine] Gemini chat analysis notice: {e}")

    result_msg = f"WhatsApp Inspection ({contact or 'Active Chat'}):\n\n{summary}"
    if player and hasattr(player, "write_log"):
        player.write_log("WHATSAPP: Inspection complete.")
    return result_msg
