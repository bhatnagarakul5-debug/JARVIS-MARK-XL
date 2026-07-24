"""
actions/ghost_protocol.py — Instant Stealth & Privacy Engine for JARVIS Mark XL
Minimizes all windows, mutes audio, clears clipboard, and hides sensitive UI.
"""

import os
import sys
import pyautogui
import pyperclip

def ghost_protocol(parameters: dict = None, player=None) -> str:
    """
    Triggers Ghost Protocol: instant stealth & privacy mode.
    - Minimizes all active desktop windows (Win + D)
    - Mutes system audio
    - Clears clipboard memory
    - Logs stealth notification
    """
    try:
        # 1. Minimize all desktop windows
        pyautogui.hotkey("win", "d")
        
        # 2. Mute audio
        pyautogui.press("volumemute")
        
        # 3. Clear clipboard
        try:
            pyperclip.copy("")
        except Exception:
            pass

        # 4. Notify UI log
        if player and hasattr(player, "write_log"):
            player.write_log("SYS: [GHOST PROTOCOL ACTIVATED] -- All windows minimized, audio muted, clipboard wiped.")
            if hasattr(player, "push_notification"):
                player.push_notification("GHOST PROTOCOL ENGAGED -- STEALTH MODE ACTIVE", "warning")

        return "Ghost Protocol engaged, Akul. All windows minimized, audio muted, and clipboard cleared. You are completely in stealth mode."

    except Exception as e:
        return f"Ghost Protocol error: {e}"
