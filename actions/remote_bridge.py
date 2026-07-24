"""
actions/remote_bridge.py — Telegram Remote Control & Face Memory Bridge for JARVIS Mark XL
Supports Telegram AI conversation, remote commands, AND direct photo upload for face profile memory!
Zero webcam requirement on laptop.
"""

import os
import sys
import time
import json
import requests
import threading
from pathlib import Path
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
FACES_DIR = BASE_DIR / "config" / "known_faces"

FACES_DIR.mkdir(parents=True, exist_ok=True)


def _get_api_keys() -> tuple[str, str]:
    tg_token = ""
    gm_key = ""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            tg_token = data.get("telegram_bot_token", "")
            gm_key = data.get("gemini_api_key", "")
    except Exception:
        pass
    return tg_token, gm_key


class TelegramRemoteBridge:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_bridge()
            return cls._instance

    def _init_bridge(self):
        self.last_update_id = 0
        self.is_running = False
        self.player = None
        self.bot_token, self.gemini_key = _get_api_keys()

    def start_polling(self, player=None):
        if self.is_running:
            return "Telegram Remote Bridge is already running."
        
        self.player = player
        self.bot_token, self.gemini_key = _get_api_keys()

        if not self.bot_token:
            return "Telegram Remote Bridge: No 'telegram_bot_token' configured in api_keys.json."

        self.is_running = True
        thread = threading.Thread(target=self._poll_loop, daemon=True)
        thread.start()

        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log("REMOTE: Telegram Remote PC Control & Face Memory Bridge ONLINE.")

        return "Telegram Remote Bridge activated! Send photos or commands to JARVIS from Telegram."

    def _poll_loop(self):
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        headers = {"User-Agent": "Mozilla/5.0"}

        while self.is_running:
            try:
                params = {"offset": self.last_update_id + 1, "timeout": 4}
                resp = requests.get(url, params=params, headers=headers, timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        self.last_update_id = update.get("update_id", self.last_update_id)
                        msg = update.get("message", {})
                        chat_id = msg.get("chat", {}).get("id")

                        if not chat_id:
                            continue

                        # Save chat_id to config/api_keys.json for automated alerts
                        try:
                            cfg_p = os.path.join(os.path.dirname(__file__), "..", "config", "api_keys.json")
                            if os.path.exists(cfg_p):
                                with open(cfg_p, "r", encoding="utf-8") as f:
                                    c_data = json.load(f)
                                if str(c_data.get("telegram_chat_id")) != str(chat_id):
                                    c_data["telegram_chat_id"] = str(chat_id)
                                    with open(cfg_p, "w", encoding="utf-8") as f:
                                        json.dump(c_data, f, indent=4)
                        except Exception:
                            pass

                        # 1. Handle Photo Upload for Face Profile Memory
                        if "photo" in msg:
                            caption = msg.get("caption", "").strip()
                            self._handle_photo_upload(chat_id, msg["photo"], caption)
                            continue

                        # 2. Handle Text Commands & Chat
                        text = msg.get("text", "").strip()
                        if text:
                            self._handle_remote_command(chat_id, text)
            except Exception:
                pass
            time.sleep(2)

    def _handle_photo_upload(self, chat_id: int, photos: list, caption: str):
        """Processes photo upload on Telegram for face recognition or registration."""
        try:
            # Pick highest resolution photo
            photo = photos[-1]
            file_id = photo.get("file_id")

            # Get Telegram file path
            file_url = f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={file_id}"
            res = requests.get(file_url, timeout=5).json()

            if res.get("ok"):
                file_path = res["result"]["file_path"]
                dl_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                img_data = requests.get(dl_url, timeout=8).content

                cap_low = caption.lower().strip()

                # If caption asks to identify or is empty, perform AI Vision Face Recognition
                if not caption or any(k in cap_low for k in ["who", "identify", "recognize", "scan", "check"]):
                    from actions.camera_system import recognize_face_from_bytes
                    res_str = recognize_face_from_bytes(img_data)
                    self._send_reply(chat_id, f"🔍 Telegram AI Face Recognition:\n\n{res_str}")
                    return

                # Otherwise, register & save face profile under the provided name
                name = caption.replace("remember", "").replace("face", "").replace("save", "").replace("as", "").strip() or "User Profile"
                from actions.camera_system import save_face_profile
                msg = save_face_profile(name, img_data)

                self._send_reply(chat_id, f"📸 {msg}")

                if self.player and hasattr(self.player, "write_log"):
                    self.player.write_log(f"REMOTE: Saved face profile for '{name.title()}' via Telegram photo upload.")
                    if hasattr(self.player, "push_notification"):
                        self.player.push_notification(f"Telegram Face Saved: {name.title()}", "success")
        except Exception as e:
            print(f"[RemoteBridge] Photo upload notice: {e}")
            self._send_reply(chat_id, f"Could not process photo upload: {e}")

    def _send_reply(self, chat_id: int, text: str):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            safe_text = text.encode("utf-8", errors="ignore").decode("utf-8")
            requests.post(url, json={"chat_id": chat_id, "text": safe_text}, timeout=5)
        except Exception as e:
            print(f"[RemoteBridge] Send reply notice: {e}")

    def _handle_remote_command(self, chat_id: int, text: str):
        cmd = text.lower().strip()
        if self.player and hasattr(self.player, "write_log"):
            try:
                self.player.write_log(f"REMOTE: Received phone command '{text[:40]}'")
            except Exception:
                pass

        if cmd in ("/status", "status", "health"):
            from actions.system_diagnostics import run_system_diagnostics
            res = run_system_diagnostics({"action": "full_scan"}, player=self.player)
            self._send_reply(chat_id, f"📱 JARVIS Remote Telemetry Report:\n\n{res}")

        elif cmd in ("/lock", "lock"):
            from actions.security_shield import trigger_intruder_lock
            res = trigger_intruder_lock(intruder_name="Remote Request", player=self.player)
            self._send_reply(chat_id, f"🔒 {res}")

        elif cmd in ("/news", "news"):
            from actions.news_intel import fetch_news_intel
            res = fetch_news_intel({"action": "top_headlines", "category": "world"}, player=self.player)
            self._send_reply(chat_id, f"📰 Live World News:\n\n{res[:1000]}")

        elif cmd in ("/edit", "editing"):
            from actions.voice_macros import execute_voice_macro
            res = execute_voice_macro({"macro_name": "editing_mode"}, player=self.player)
            self._send_reply(chat_id, f"🎬 {res}")

        elif cmd in ("/cooldown", "cooldown"):
            from actions.cooldown_protocol import set_cooldown_mode
            res = set_cooldown_mode(True, player=self.player)
            self._send_reply(chat_id, f"⚡ {res}")

        elif cmd in ("/faces", "faces", "remembered_faces"):
            known = [f.stem.replace("_", " ").title() for f in FACES_DIR.glob("*.jpg")]
            if known:
                self._send_reply(chat_id, "👤 Remembered Face Profiles:\n• " + "\n• ".join(known))
            else:
                self._send_reply(chat_id, "No face profiles currently saved. Upload a photo with a caption to save one!")

        elif cmd in ("/start", "start"):
            self._send_reply(
                chat_id,
                "J.A.R.V.I.S. Remote Bridge Online, sir!\n"
                "• Send any PHOTO with a caption (e.g. 'Akul') to save & remember face profile.\n"
                "• /faces — View remembered face profiles\n"
                "• /status — Health telemetry\n"
                "• /lock — Remote Windows lock\n"
                "• /news — Breaking world news\n"
                "• /edit — Activate Editing Mode\n"
                "• /cooldown — Engage Thermal Cooldown Protocol"
            )

        else:
            if self.gemini_key:
                try:
                    client = genai.Client(api_key=self.gemini_key)
                    prompt = (
                        "You are J.A.R.V.I.S., Tony Stark's AI assistant. "
                        "The user is messaging you on Telegram from their phone. "
                        "Respond concisely, politely, and with classic dry British wit. "
                        f"User message: {text}"
                    )
                    res = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    if res and res.text:
                        self._send_reply(chat_id, res.text.strip())
                        return
                except Exception as ex:
                    print(f"[RemoteBridge] Gemini chat error: {ex}")

            self._send_reply(chat_id, f"Command received, sir: '{text}'")


remote_bridge_mgr = TelegramRemoteBridge()


def remote_bridge_control(parameters: dict, player=None) -> str:
    """
    Action handler for Telegram Remote Control & Face Memory Bridge.
    """
    params = parameters or {}
    action = (params.get("action") or "start").lower().strip()
    return remote_bridge_mgr.start_polling(player=player)
