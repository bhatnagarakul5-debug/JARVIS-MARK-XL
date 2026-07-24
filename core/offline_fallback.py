"""
core/offline_fallback.py — J.A.R.V.I.S. Mark XLI "Bones" Offline Cyber Fallback Engine
Monitors internet connectivity and handles local system macros when offline.
"""

import time
import socket
import threading

class OfflineFallbackEngine:
    """Monitors online status and handles local command execution during offline mode."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.is_online = True
            cls._instance.last_check = 0
            cls._instance._start_monitor()
        return cls._instance

    def _start_monitor(self):
        def _loop():
            while True:
                try:
                    socket.setdefaulttimeout(3.0)
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
                    self.is_online = True
                except Exception:
                    self.is_online = False
                time.sleep(10.0)

        threading.Thread(target=_loop, daemon=True).start()

    def check_online(self) -> bool:
        """Returns True if internet connectivity is active."""
        return self.is_online

    def execute_offline_command(self, text: str) -> str:
        """Handles basic system controls offline using PyAutoGUI & OS commands."""
        text_lower = text.lower().strip()
        
        if "lock" in text_lower or "workstation" in text_lower:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "[OFFLINE ENGINE] Workstation locked."

        if "mute" in text_lower:
            import pyautogui
            pyautogui.press("volumemute")
            return "[OFFLINE ENGINE] Muted audio."

        if "volume up" in text_lower:
            import pyautogui
            for _ in range(5): pyautogui.press("volumeup")
            return "[OFFLINE ENGINE] Volume increased."

        if "volume down" in text_lower:
            import pyautogui
            for _ in range(5): pyautogui.press("volumedown")
            return "[OFFLINE ENGINE] Volume decreased."

        return f"[OFFLINE ENGINE] System online check: {'ONLINE 🌐' if self.is_online else 'OFFLINE ⚠️'}"


offline_fallback = OfflineFallbackEngine()
