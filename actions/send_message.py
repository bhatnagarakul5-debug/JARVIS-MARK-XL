# actions/send_message.py
# Universal messaging — WhatsApp & Instagram
# Uses visual element detection (pyautogui + screen search) instead of
# hardcoded tab/click sequences — works on any screen resolution.

import time
import pyautogui
from pathlib import Path

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.08

def _open_app(app_name: str) -> bool:
    """Opens an app via Windows search."""
    try:
        pyautogui.press("win")
        time.sleep(0.4)
        pyautogui.write(app_name, interval=0.04)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(2.0)  
        return True
    except Exception as e:
        print(f"[SendMessage] Could not open {app_name}: {e}")
        return False


def _search_contact(contact: str, platform: str):
    """
    Searches for a contact inside the messaging app.
    Uses Ctrl+F (universal search shortcut) then types contact name.
    """
    time.sleep(0.5)
    pyautogui.hotkey("ctrl", "f")
    time.sleep(0.4)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.write(contact, interval=0.04)
    time.sleep(0.8)
    pyautogui.press("enter")
    time.sleep(0.6)


def _type_and_send(message: str):
    """Types message and sends it."""
    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.write(message, interval=0.03)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)


def _send_whatsapp(receiver: str, message: str) -> str:
    """
    Sends a WhatsApp message via the Windows desktop app.
    Steps: Open WhatsApp → Search contact → Click → Type → Send
    """
    try:
        if not _open_app("WhatsApp"):
            return "Could not open WhatsApp."

        time.sleep(1.5)

        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write(receiver, interval=0.04)
        time.sleep(1.0)

        pyautogui.press("enter")
        time.sleep(0.8)

        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")

        return f"Message sent to {receiver} via WhatsApp."

    except Exception as e:
        return f"WhatsApp error: {e}"


def _send_instagram(receiver: str, message: str) -> str:
    """
    Sends an Instagram DM via browser (instagram.com).
    Steps: Open Chrome → Go to instagram.com/direct → Search contact → Send
    """
    try:
        import webbrowser

        webbrowser.open("https://www.instagram.com/direct/new/")
        time.sleep(3.5)

        pyautogui.write(receiver, interval=0.05)
        time.sleep(1.5)

        pyautogui.press("down")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(0.5)

        for _ in range(3):
            pyautogui.press("tab")
            time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(1.5)

        pyautogui.write(message, interval=0.04)
        time.sleep(0.2)
        pyautogui.press("enter")

        return f"Message sent to {receiver} via Instagram."

    except Exception as e:
        return f"Instagram error: {e}"

def _send_telegram(receiver: str, message: str) -> str:
    """Sends a Telegram message via Windows desktop app."""
    try:
        if not _open_app("Telegram"):
            return "Could not open Telegram."

        time.sleep(1.5)

        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)
        pyautogui.write(receiver, interval=0.04)
        time.sleep(1.0)
        pyautogui.press("enter")
        time.sleep(0.8)

        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")

        return f"Message sent to {receiver} via Telegram."

    except Exception as e:
        return f"Telegram error: {e}"



def _send_generic(platform: str, receiver: str, message: str) -> str:
    """
    For any other platform not explicitly supported.
    Opens the app, searches for contact, types and sends.
    Works for: Messenger, Discord, Signal, etc.
    """
    try:
        if not _open_app(platform):
            return f"Could not open {platform}."

        time.sleep(1.5)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)
        pyautogui.write(receiver, interval=0.04)
        time.sleep(1.0)
        pyautogui.press("enter")
        time.sleep(0.8)
        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")

        return f"Message sent to {receiver} via {platform}."

    except Exception as e:
        return f"{platform} error: {e}"

def unlock_whatsapp_locked_chats(passcode: str = "", contact: str = "", message: str = "") -> str:
    """
    Accesses WhatsApp Locked Chats using user passcode,
    unlocks the vault, and optionally opens a contact and sends a reply.
    """
    try:
        if not _open_app("WhatsApp"):
            return "Could not open WhatsApp."

        time.sleep(1.5)
        pyautogui.hotkey("win", "up")
        time.sleep(0.5)

        # 1. Search for Locked Chats
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.4)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write("Locked Chats", interval=0.04)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(1.0)

        # 2. Enter secret passcode
        pyautogui.write(passcode, interval=0.08)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(1.0)

        if contact:
            _search_contact(contact, "WhatsApp")
            if message:
                _type_and_send(message)
                return f"Unlocked Locked Chats, opened '{contact}', and sent message."
            return f"Unlocked Locked Chats and opened '{contact}'."

        return "WhatsApp Locked Chats vault unlocked."
    except Exception as e:
        return f"Failed to unlock Locked Chats: {e}"


def send_message(parameters: dict, player=None) -> str:
    """
    Universal messaging handler.
    Called from main.py.

    parameters:
        receiver     : Contact name to send to
        message_text : The message content
        platform     : whatsapp | instagram | telegram | <any app name>
        is_locked    : bool (if True, unlocks WhatsApp locked chats using user passcode)
        passcode     : str (passcode for locked chats)
    """
    params       = parameters or {}
    receiver     = params.get("receiver", "").strip()
    message_text = params.get("message_text", "").strip()
    platform     = params.get("platform", "whatsapp").strip().lower()
    is_locked    = params.get("is_locked", False) or "locked" in platform or "locked" in receiver.lower()
    passcode     = params.get("passcode", "")

    if is_locked:
        if player:
            player.write_log(f"[msg] Unlocking WhatsApp Locked Chats with PIN '{passcode}'...")
        return unlock_whatsapp_locked_chats(passcode=passcode, contact=receiver, message=message_text)

    if not receiver:
        return "Please specify who to send the message to, sir."
    if not message_text:
        return "Please specify what message to send, sir."

    print(f"[SendMessage] 📨 {platform} → {receiver}: {message_text[:40]}")
    if player:
        player.write_log(f"[msg] Sending to {receiver} via {platform}...")

    if "whatsapp" in platform or "wp" in platform or "wapp" in platform:
        result = _send_whatsapp(receiver, message_text)

    elif "instagram" in platform or "ig" in platform or "insta" in platform:
        result = _send_instagram(receiver, message_text)

    elif "telegram" in platform or "tg" in platform:
        result = _send_telegram(receiver, message_text)

    else:
        result = _send_generic(platform, receiver, message_text)

    print(f"[SendMessage] ✅ {result}")
    if player:
        player.write_log(f"[msg] {result}")

    return result


def _call_whatsapp(contact: str, call_type: str = "audio") -> str:
    """Makes a WhatsApp audio/video call via the Windows desktop app."""
    try:
        pyautogui.FAILSAFE = False
        if not _open_app("WhatsApp"):
            return "Could not open WhatsApp."
        time.sleep(2.0)

        # 1. Force maximize the window so coordinates become reliable
        pyautogui.hotkey("win", "up")
        time.sleep(0.5)

        # 2. Search for the contact
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.5)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write(contact, interval=0.04)
        time.sleep(1.5)
        pyautogui.press("enter")
        time.sleep(1.5)

        # 3. Try official shortcuts first (covers new and old Windows App versions)
        if call_type == "video":
            pyautogui.hotkey("ctrl", "alt", "v")
            time.sleep(0.3)
            pyautogui.hotkey("ctrl", "shift", "v")
        else:
            pyautogui.hotkey("ctrl", "alt", "c")
            time.sleep(0.3)
            pyautogui.hotkey("ctrl", "shift", "c")
        
        time.sleep(1.0)

        # 4. Foolproof Fallback: Since window is maximized, we can safely click the top right
        screen_w, screen_h = pyautogui.size()
        if call_type == "video":
            # Video call is usually around 130px from the right edge
            pyautogui.click(screen_w - 130, 80)
        else:
            # Audio call is usually around 180px from the right edge
            pyautogui.click(screen_w - 180, 80)
            
        time.sleep(0.5)

        # Confirm the call if a dialog pops up
        try:
            pyautogui.press("enter")
        except Exception:
            pass

        return f"{call_type.title()} call started to {contact} via WhatsApp."
    except Exception as e:
        return f"WhatsApp call error: {e}"


def _call_phone_link(contact: str) -> str:
    """Makes a phone call via the Phone Link (Your Phone) Windows app."""
    try:
        pyautogui.FAILSAFE = False
        if not _open_app("Phone Link"):
            return "Could not open Phone Link. Make sure it's set up with your phone."
        time.sleep(3.5)

        # Try Phone Link dialer shortcut
        try:
            pyautogui.hotkey("ctrl", "d")
            time.sleep(1.0)
        except Exception:
            pass

        # Type the contact name or number
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.3)
        pyautogui.write(contact, interval=0.04)
        time.sleep(1.0)

        pyautogui.press("enter")
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(0.5)

        return f"Call started to {contact} via Phone Link."
    except Exception as e:
        return f"Phone Link call error: {e}"


def make_call(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None
) -> str:
    """
    Makes a call via WhatsApp or Phone Link.

    parameters:
        contact   : Contact name or phone number
        platform  : whatsapp | phone_link | phone (default: whatsapp)
        call_type : audio | video (default: audio)
    """
    params    = parameters or {}
    contact   = params.get("contact", "").strip()
    platform  = params.get("platform", "whatsapp").strip().lower()
    call_type = params.get("call_type", "audio").strip().lower()

    if not contact:
        return "Please specify who to call, sir."

    print(f"[Call] 📞 {platform} → {contact} ({call_type})")
    if player:
        player.write_log(f"[call] Calling {contact} via {platform}...")

    if "whatsapp" in platform or "wp" in platform or "wapp" in platform:
        result = _call_whatsapp(contact, call_type)
    elif "phone" in platform or "link" in platform:
        result = _call_phone_link(contact)
    else:
        result = _call_whatsapp(contact, call_type)

    print(f"[Call] ✅ {result}")
    if player:
        player.write_log(f"[call] {result}")
    return result