"""
actions/remote_bridge.py — Telegram Remote Control Bridge 2.0 for J.A.R.V.I.S.
Provides full remote command center functionality over Telegram:
- Screenshots (/snap) & Webcam Photos (/cam)
- File Download (/get <filepath>) & Document Analysis
- Voice Note Processing (transcribes voice messages & executes commands)
- Remote App Launcher (/launch <app>) & Process Killer (/kill <proc>)
- System Telemetry (/status), Sentry Lock (/lock /sentry)
- Audit Logging to memory/telegram_audit.log
"""

import os
import sys
import time
import json
import requests
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
FACES_DIR = BASE_DIR / "config" / "known_faces"
AUDIT_LOG_PATH = BASE_DIR / "memory" / "telegram_audit.log"

FACES_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


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


def _audit_log(event_text: str):
    """Appends timestamped event to memory/telegram_audit.log"""
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{now_str}] {event_text}\n")
    except Exception:
        pass


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
            return "Telegram Remote Bridge 2.0 is already active."
        
        self.player = player
        self.bot_token, self.gemini_key = _get_api_keys()

        if not self.bot_token:
            return "Telegram Remote Bridge: No 'telegram_bot_token' configured in api_keys.json."

        self.is_running = True
        thread = threading.Thread(target=self._poll_loop, daemon=True)
        thread.start()

        # Send Telegram boot greeting & remote feature menu
        self._send_startup_menu()

        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log("REMOTE: Telegram Remote Control Bridge 2.0 ONLINE.")

        _audit_log("Bridge 2.0 initialized and started polling.")
        return "Telegram Remote Bridge 2.0 active! Full remote control enabled."

    def _send_startup_menu(self):
        """Sends startup greeting and full feature menu to Telegram chat on boot with 1-tap buttons."""
        try:
            self._register_bot_commands()

            cfg_path = BASE_DIR / "config" / "api_keys.json"
            chat_id = ""
            if cfg_path.exists():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    chat_id = json.load(f).get("telegram_chat_id", "")
            
            if chat_id and self.bot_token:
                menu_msg = (
                    "⚡ J.A.R.V.I.S. MARK XLI ONLINE\n\n"
                    "Good day sir! All laptop systems are operational. Tap any button below for 1-click remote control:"
                )
                self._send_menu_buttons(chat_id, menu_msg)
                _audit_log("Sent startup greeting & 1-tap menu buttons to Telegram.")

        except Exception as e:
            print(f"[RemoteBridge] Boot menu notice: {e}")

        # Start 10-minute video security patrol daemon
        self._start_10min_video_patrol()

    def _register_bot_commands(self):
        """Registers official Telegram bot menu commands for easy selection."""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/setMyCommands"
            cmds = [
                {"command": "start", "description": "⚡ Open Remote Command Center Menu"},
                {"command": "snap", "description": "📸 Desktop Screenshot"},
                {"command": "cam", "description": "📷 Webcam Photo"},
                {"command": "video", "description": "🎥 Record 10s Video Clip"},
                {"command": "warn", "description": "📢 Speak Loud Warning on Laptop"},
                {"command": "status", "description": "📊 CPU, RAM & Battery Status"},
                {"command": "lock", "description": "🔒 Lock Laptop Workstation"},
                {"command": "vol", "description": "🔊 Set Speaker Volume (e.g. /vol 50)"},
                {"command": "clip", "description": "📝 Read/Write Laptop Clipboard"},
                {"command": "net", "description": "🌐 Wi-Fi & Network Telemetry"},
                {"command": "agenda", "description": "🗓️ Today's Calendar & Reminders"},
                {"command": "sleep", "description": "😴 Put Laptop to Sleep"}
            ]
            requests.post(url, json={"commands": cmds}, timeout=5)
        except Exception as e:
            print(f"[RemoteBridge] Register bot commands notice: {e}")

    def _send_menu_buttons(self, chat_id: int, text: str):
        """Sends message with 1-tap Interactive Inline Keyboard Buttons."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        keyboard = {
            "inline_keyboard": [
                [{"text": "📸 Screenshot", "callback_data": "/snap"}, {"text": "📷 Cam Photo", "callback_data": "/cam"}, {"text": "🎥 Video Clip", "callback_data": "/video 10"}],
                [{"text": "📊 PC Status", "callback_data": "/status"}, {"text": "🔒 Lock Laptop", "callback_data": "/lock"}, {"text": "🌐 Net Speed", "callback_data": "/net"}],
                [{"text": "📝 Clipboard", "callback_data": "/clip"}, {"text": "🗓️ Agenda", "callback_data": "/agenda"}, {"text": "🔊 Mute/Unmute", "callback_data": "/mute"}],
                [{"text": "🎵 Play Spotify", "callback_data": "/play starboy"}, {"text": "⏭️ Next Song", "callback_data": "/next"}, {"text": "😴 Sleep PC", "callback_data": "/sleep"}]
            ]
        }
        try:
            safe_text = text.encode("utf-8", errors="ignore").decode("utf-8")
            requests.post(url, json={"chat_id": chat_id, "text": safe_text, "reply_markup": keyboard}, timeout=6)
        except Exception as e:
            print(f"[RemoteBridge] Send menu buttons notice: {e}")

    def _start_10min_video_patrol(self):
        """Starts background daemon that records & sends 10-second video clips to Telegram every 10 minutes."""
        if getattr(self, "_video_patrol_started", False):
            return
        self._video_patrol_started = True

        def _patrol_loop():
            while self.is_running:
                time.sleep(600)  # 10 minutes (600 seconds)
                try:
                    cfg_path = BASE_DIR / "config" / "api_keys.json"
                    chat_id = ""
                    if cfg_path.exists():
                        with open(cfg_path, "r", encoding="utf-8") as f:
                            chat_id = json.load(f).get("telegram_chat_id", "")
                    
                    if chat_id and self.bot_token:
                        vid_bytes = self._record_video_clip(duration_sec=10)
                        if vid_bytes:
                            url_v = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
                            files_v = {"video": ("patrol_10m.mp4", vid_bytes, "video/mp4")}
                            data_v = {"chat_id": chat_id, "caption": "🎥 Automated 10-Minute Video Security Patrol Clip"}
                            requests.post(url_v, data=data_v, files=files_v, timeout=15)
                            _audit_log("Sent 10-minute automated video patrol clip to Telegram.")
                except Exception as e:
                    print(f"[RemoteBridge] Video patrol loop notice: {e}")

        t = threading.Thread(target=_patrol_loop, daemon=True)
        t.start()

    def _record_video_clip(self, duration_sec: int = 10) -> bytes | None:
        """Records a video clip from webcam and returns MP4 bytes."""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return None

            out_path = BASE_DIR / "downloads" / "temp_patrol.mp4"
            out_path.parent.mkdir(parents=True, exist_ok=True)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 15
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480

            out = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
            start_t = time.time()

            while (time.time() - start_t) < duration_sec:
                ret, frame = cap.read()
                if ret:
                    out.write(frame)
                time.sleep(1 / fps)

            cap.release()
            out.release()

            if out_path.exists():
                data = out_path.read_bytes()
                try:
                    out_path.unlink()
                except Exception:
                    pass
                return data
        except Exception as e:
            print(f"[RemoteBridge] Video capture exception: {e}")
        return None

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

                        # Handle 1-Tap Inline Keyboard Button Taps
                        if "callback_query" in update:
                            cb = update["callback_query"]
                            cb_id = cb.get("id")
                            cb_data = cb.get("data", "")
                            chat_id = cb.get("message", {}).get("chat", {}).get("id")

                            # Answer callback query to acknowledge button tap
                            try:
                                requests.post(f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery", json={"callback_query_id": cb_id}, timeout=3)
                            except Exception:
                                pass

                            if chat_id and cb_data:
                                self._handle_remote_command(chat_id, cb_data)
                            continue

                        msg = update.get("message", {})
                        chat_id = msg.get("chat", {}).get("id")

                        if not chat_id:
                            continue

                        # Update telegram_chat_id in config
                        self._save_chat_id(chat_id)

                        # 1. Handle Voice Notes
                        if "voice" in msg or "audio" in msg:
                            voice_obj = msg.get("voice") or msg.get("audio")
                            self._handle_voice_note(chat_id, voice_obj)
                            continue

                        # 2. Handle Photo Uploads
                        if "photo" in msg:
                            caption = msg.get("caption", "").strip()
                            self._handle_photo_upload(chat_id, msg["photo"], caption)
                            continue

                        # 3. Handle Document Uploads
                        if "document" in msg:
                            doc = msg.get("document")
                            self._handle_document_upload(chat_id, doc)
                            continue

                        # 4. Handle Text Commands & Chat
                        text = msg.get("text", "").strip()
                        if text:
                            self._handle_remote_command(chat_id, text)
            except Exception as e:
                print(f"[RemoteBridge] Poll loop notice: {e}")
            time.sleep(2)

    def _save_chat_id(self, chat_id: int):
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                if str(c_data.get("telegram_chat_id")) != str(chat_id):
                    c_data["telegram_chat_id"] = str(chat_id)
                    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                        json.dump(c_data, f, indent=4)
        except Exception:
            pass

    def _send_reply(self, chat_id: int, text: str):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            safe_text = text.encode("utf-8", errors="ignore").decode("utf-8")
            requests.post(url, json={"chat_id": chat_id, "text": safe_text}, timeout=5)
        except Exception as e:
            print(f"[RemoteBridge] Send reply notice: {e}")

    def _send_photo(self, chat_id: int, photo_bytes: bytes, caption: str = ""):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        try:
            files = {"photo": ("snapshot.jpg", photo_bytes, "image/jpeg")}
            data = {"chat_id": chat_id, "caption": caption}
            requests.post(url, data=data, files=files, timeout=10)
        except Exception as e:
            print(f"[RemoteBridge] Send photo notice: {e}")

    def _send_document(self, chat_id: int, file_path: Path):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        try:
            with open(file_path, "rb") as f:
                files = {"document": (file_path.name, f)}
                data = {"chat_id": chat_id, "caption": f"📄 File: {file_path.name}"}
                requests.post(url, data=data, files=files, timeout=15)
        except Exception as e:
            print(f"[RemoteBridge] Send document notice: {e}")

    def _handle_voice_note(self, chat_id: int, voice_obj: dict):
        """Transcribes incoming Telegram voice message and executes as command."""
        try:
            file_id = voice_obj.get("file_id")
            file_url = f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={file_id}"
            res = requests.get(file_url, timeout=5).json()

            if res.get("ok"):
                f_path = res["result"]["file_path"]
                dl_url = f"https://api.telegram.org/file/bot{self.bot_token}/{f_path}"
                audio_data = requests.get(dl_url, timeout=10).content

                if self.gemini_key:
                    client = genai.Client(api_key=self.gemini_key)
                    # Use Gemini Vision / Audio to transcribe
                    res_ai = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[
                            {"mime_type": "audio/ogg", "data": audio_data},
                            "Transcribe this voice note exactly into text."
                        ]
                    )
                    transcription = res_ai.text.strip() if (res_ai and res_ai.text) else ""
                    if transcription:
                        self._send_reply(chat_id, f"🎙️ Voice Note Transcribed: '{transcription}'")
                        _audit_log(f"Voice note transcribed: '{transcription}'")
                        self._handle_remote_command(chat_id, transcription)
                        return

            self._send_reply(chat_id, "Could not process voice note transcription.")
        except Exception as e:
            self._send_reply(chat_id, f"Voice note error: {e}")

    def _handle_photo_upload(self, chat_id: int, photos: list, caption: str):
        try:
            photo = photos[-1]
            file_id = photo.get("file_id")
            file_url = f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={file_id}"
            res = requests.get(file_url, timeout=5).json()

            if res.get("ok"):
                file_path = res["result"]["file_path"]
                dl_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                img_data = requests.get(dl_url, timeout=8).content

                cap_low = caption.lower().strip()
                if not caption or any(k in cap_low for k in ["who", "identify", "recognize", "scan", "check"]):
                    from actions.camera_system import recognize_face_from_bytes
                    res_str = recognize_face_from_bytes(img_data)
                    self._send_reply(chat_id, f"🔍 Telegram AI Face Recognition:\n\n{res_str}")
                    return

                name = caption.replace("remember", "").replace("face", "").replace("save", "").replace("as", "").strip() or "User Profile"
                from actions.camera_system import save_face_profile
                msg = save_face_profile(name, img_data)
                self._send_reply(chat_id, f"📸 {msg}")
                _audit_log(f"Saved face profile: '{name}'")
        except Exception as e:
            self._send_reply(chat_id, f"Could not process photo: {e}")

    def _handle_document_upload(self, chat_id: int, doc: dict):
        try:
            file_name = doc.get("file_name", "uploaded_doc")
            file_id = doc.get("file_id")
            file_url = f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={file_id}"
            res = requests.get(file_url, timeout=5).json()

            if res.get("ok"):
                f_path = res["result"]["file_path"]
                dl_url = f"https://api.telegram.org/file/bot{self.bot_token}/{f_path}"
                doc_data = requests.get(dl_url, timeout=12).content

                # Save to downloads
                save_p = BASE_DIR / "downloads" / file_name
                save_p.parent.mkdir(parents=True, exist_ok=True)
                save_p.write_bytes(doc_data)

                self._send_reply(chat_id, f"📥 Document saved to laptop: {save_p.name}")
                _audit_log(f"Saved document: {file_name}")
        except Exception as e:
            self._send_reply(chat_id, f"Document upload error: {e}")

    def _handle_remote_command(self, chat_id: int, text: str):
        cmd = text.strip()
        cmd_low = cmd.lower()

        _audit_log(f"Command received: '{cmd}'")

        if self.player and hasattr(self.player, "write_log"):
            try:
                self.player.write_log(f"REMOTE: Received command '{cmd[:40]}'")
            except Exception:
                pass

        # 📸 Screen Snapshot
        if cmd_low in ("/snap", "snap", "screenshot"):
            try:
                import pyautogui
                import io
                screenshot = pyautogui.screenshot()
                buf = io.BytesIO()
                screenshot.save(buf, format="JPEG", quality=85)
                self._send_photo(chat_id, buf.getvalue(), "📸 Live Desktop Screenshot")
                _audit_log("Sent screenshot via Telegram.")
            except Exception as e:
                self._send_reply(chat_id, f"Could not capture screenshot: {e}")

        # 📷 Webcam Photo
        elif cmd_low in ("/cam", "cam", "webcam", "camera"):
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    _, buf = cv2.imencode(".jpg", frame)
                    self._send_photo(chat_id, buf.tobytes(), "📷 Live Webcam Snapshot")
                    _audit_log("Sent webcam photo via Telegram.")
                else:
                    self._send_reply(chat_id, "Webcam feed unavailable.")
            except Exception as e:
                self._send_reply(chat_id, f"Could not capture webcam photo: {e}")

        # 📁 File Fetcher (/get <filepath>)
        elif cmd_low.startswith("/get ") or cmd_low.startswith("get "):
            target_str = cmd.split(" ", 1)[1].strip()
            target_path = Path(target_str).expanduser()

            # Handle relative shortcuts
            if not target_path.exists():
                target_path = BASE_DIR / target_str

            if target_path.exists() and target_path.is_file():
                self._send_document(chat_id, target_path)
                _audit_log(f"Sent file '{target_path.name}' to Telegram.")
            else:
                self._send_reply(chat_id, f"File not found: '{target_str}'")

        # 📊 System Status
        elif cmd_low in ("/status", "status", "health"):
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory().percent
            battery = getattr(psutil, "sensors_battery", lambda: None)()
            bat_str = f"{battery.percent}%" if battery else "N/A (AC Power)"
            msg_status = (
                f"📱 JARVIS Laptop Telemetry:\n"
                f"• CPU Load: {cpu}%\n"
                f"• RAM Usage: {mem}%\n"
                f"• Battery: {bat_str}\n"
                f"• System Status: NOMINAL 🌐"
            )
            self._send_reply(chat_id, msg_status)

        # 🔒 Lock / Sentry
        elif cmd_low in ("/lock", "lock", "/sentry", "sentry"):
            from actions.security_shield import trigger_intruder_lock
            res = trigger_intruder_lock(intruder_name="Remote Telegram Request", player=self.player)
            self._send_reply(chat_id, f"🔒 {res}")

        # 🚀 Launch App (/launch <app>)
        elif cmd_low.startswith("/launch ") or cmd_low.startswith("launch "):
            app_name = cmd.split(" ", 1)[1].strip()
            try:
                os.system(f"start {app_name}")
                self._send_reply(chat_id, f"🚀 Launched application: '{app_name}'")
                _audit_log(f"Launched app: '{app_name}'")
            except Exception as e:
                self._send_reply(chat_id, f"Could not launch '{app_name}': {e}")

        # 🛑 Kill Process (/kill <proc>)
        elif cmd_low.startswith("/kill ") or cmd_low.startswith("kill "):
            proc_name = cmd.split(" ", 1)[1].strip()
            try:
                os.system(f"taskkill /f /im {proc_name}.exe")
                self._send_reply(chat_id, f"🛑 Terminated process: '{proc_name}'")
                _audit_log(f"Killed process: '{proc_name}'")
            except Exception as e:
                self._send_reply(chat_id, f"Could not kill '{proc_name}': {e}")

        # 🌐 Web Search (/search <query>)
        elif cmd_low.startswith("/search ") or cmd_low.startswith("search "):
            query = cmd.split(" ", 1)[1].strip()
            from actions.web_search import web_search_action
            res = web_search_action({"query": query}, player=self.player)
            self._send_reply(chat_id, f"🌐 Search Results for '{query}':\n\n{res[:1000]}")

        # 💻 Antigravity Code Engine (/code <prompt>)
        elif cmd_low.startswith("/code ") or cmd_low.startswith("code "):
            code_prompt = cmd.split(" ", 1)[1].strip()
            self._send_reply(chat_id, f"💻 Antigravity Coder Engine engaged: '{code_prompt}'...\nExecuting task in background.")
            from actions.antigravity_coder import antigravity_coder
            res = antigravity_coder({"prompt": code_prompt}, player=self.player)
            self._send_reply(chat_id, res)
            _audit_log(f"Executed Antigravity code task: '{code_prompt}'")

        # 🚀 Antigravity IDE Workspace Bridge (/ide [task])
        elif cmd_low.startswith("/ide") or cmd_low.startswith("ide"):
            parts = cmd.split(" ", 1)
            from actions.antigravity_ide_bridge import antigravity_ide_control
            if len(parts) > 1 and parts[1].strip():
                ide_task = parts[1].strip()
                res = antigravity_ide_control({"action": "dispatch", "task": ide_task}, player=self.player)
                self._send_reply(chat_id, f"🚀 {res}")
            else:
                res = antigravity_ide_control({"action": "status"}, player=self.player)
                self._send_reply(chat_id, f"🚀 {res}")

        # 📞 Autonomous Phone Call Manager (/call <target> <objective>)
        elif cmd_low.startswith("/call ") or cmd_low.startswith("call "):
            call_args = cmd.split(" ", 1)[1].strip()
            parts = call_args.split(" ", 1)
            target = parts[0].strip()
            objective = parts[1].strip() if len(parts) > 1 else "General Inquiry"

            from actions.call_manager import call_manager_control
            res = call_manager_control({"action": "make_call", "phone_number": target, "objective": objective}, player=self.player)
            self._send_reply(chat_id, f"📞 {res}")
            _audit_log(f"Initiated call to {target} | Objective: '{objective}'")

        # 🎙️ Call Takeover (/takeover)
        elif cmd_low.startswith("/takeover") or cmd_low.startswith("takeover"):
            from actions.call_manager import call_manager_control
            res = call_manager_control({"action": "takeover"}, player=self.player)
            self._send_reply(chat_id, f"🎙️ {res}")
            _audit_log("Executed call takeover.")

        # ⏰ Reminder Sync (/remind <time> <msg>)
        elif cmd_low.startswith("/remind ") or cmd_low.startswith("remind "):
            rem_str = cmd.split(" ", 1)[1].strip()
            from actions.reminder import reminder
            res = reminder({"action": "set", "query": rem_str}, player=self.player)
            self._send_reply(chat_id, f"⏰ {res}")

        # 🔊 Volume Control (/vol <0-100>, /mute, /unmute)
        elif cmd_low.startswith("/vol ") or cmd_low.startswith("vol "):
            vol_val = cmd.split(" ", 1)[1].strip()
            from actions.computer_control import set_master_volume
            res = set_master_volume(vol_val, player=self.player)
            self._send_reply(chat_id, f"🔊 {res}")

        elif cmd_low in ("/mute", "mute"):
            from actions.computer_control import toggle_mute
            res = toggle_mute(True, player=self.player)
            self._send_reply(chat_id, f"🔇 {res}")

        elif cmd_low in ("/unmute", "unmute"):
            from actions.computer_control import toggle_mute
            res = toggle_mute(False, player=self.player)
            self._send_reply(chat_id, f"🔊 {res}")

        # 🔋 Power Control (/sleep, /hibernate)
        elif cmd_low in ("/sleep", "sleep"):
            self._send_reply(chat_id, "😴 Putting laptop to sleep...")
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

        elif cmd_low in ("/hibernate", "hibernate"):
            self._send_reply(chat_id, "💤 Hibernating laptop...")
            os.system("shutdown /h")

        # 📝 Clipboard Control (/clip, /clip <text>)
        elif cmd_low.startswith("/clip") or cmd_low.startswith("clip"):
            parts = cmd.split(" ", 1)
            from actions.clipboard_manager import clipboard_manager
            if len(parts) > 1 and parts[1].strip():
                txt_val = parts[1].strip()
                import pyperclip
                pyperclip.copy(txt_val)
                self._send_reply(chat_id, f"📋 Copied to laptop clipboard: '{txt_val}'")
            else:
                res = clipboard_manager({"action": "get"}, player=self.player)
                self._send_reply(chat_id, f"📋 Laptop Clipboard:\n\n{res}")

        # 📄 Document & PDF Reader (/read <filepath>)
        elif cmd_low.startswith("/read ") or cmd_low.startswith("read "):
            doc_path = cmd.split(" ", 1)[1].strip()
            from actions.file_processor import process_file
            res = process_file({"file_path": doc_path, "query": "Summarize this document in bullet points"}, player=self.player)
            self._send_reply(chat_id, f"📄 Document Summary:\n\n{res[:1200]}")

        # 🎵 Spotify Music Control (/play <song>, /pause, /next)
        elif cmd_low.startswith("/play ") or cmd_low.startswith("play "):
            song_query = cmd.split(" ", 1)[1].strip()
            from actions.spotify_control import spotify_control
            res = spotify_control({"action": "play", "query": song_query}, player=self.player)
            self._send_reply(chat_id, f"🎵 {res}")

        elif cmd_low in ("/pause", "pause"):
            from actions.spotify_control import spotify_control
            res = spotify_control({"action": "pause"}, player=self.player)
            self._send_reply(chat_id, f"⏸ {res}")

        elif cmd_low in ("/next", "next"):
            from actions.spotify_control import spotify_control
            res = spotify_control({"action": "next"}, player=self.player)
            self._send_reply(chat_id, f"⏭ {res}")

        # 🌐 Network Inspector (/net)
        elif cmd_low in ("/net", "net", "wifi"):
            from actions.security_shield import scan_local_network
            res = scan_local_network(player=self.player)
            self._send_reply(chat_id, f"🌐 Network Telemetry:\n\n{res}")

        # 🗓️ Agenda Sync (/agenda, /calendar)
        elif cmd_low in ("/agenda", "agenda", "/calendar", "calendar"):
            from actions.calendar_manager import calendar_manager
            res = calendar_manager({"action": "today"}, player=self.player)
            self._send_reply(chat_id, f"🗓️ Today's Agenda:\n\n{res}")

        # 🎥 Video Recording Clip (/video <sec>)
        elif cmd_low.startswith("/video") or cmd_low.startswith("video"):
            try:
                sec_val = 10
                parts = cmd.split(" ")
                if len(parts) > 1 and parts[1].isdigit():
                    sec_val = int(parts[1])

                self._send_reply(chat_id, f"🎥 Recording {sec_val}-second video clip from laptop webcam...")
                vid_bytes = self._record_video_clip(duration_sec=sec_val)
                if vid_bytes:
                    url_v = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
                    files_v = {"video": ("patrol.mp4", vid_bytes, "video/mp4")}
                    data_v = {"chat_id": chat_id, "caption": f"🎥 {sec_val}-Second Laptop Security Patrol Video"}
                    requests.post(url_v, data=data_v, files=files_v, timeout=15)
                    _audit_log(f"Sent {sec_val}s video clip to Telegram.")
                else:
                    self._send_reply(chat_id, "Could not capture video clip — webcam busy.")
            except Exception as e:
                self._send_reply(chat_id, f"Video recording error: {e}")

        # 📢 Remote Loud Speaker Warning (/warn <details>)
        elif cmd_low.startswith("/warn ") or cmd_low.startswith("warn "):
            warn_details = cmd.split(" ", 1)[1].strip()
            full_warning = f"ATTENTION! INTRUDER IDENTIFIED! WARNING: {warn_details} STEP AWAY FROM AKUL BHATNAGAR'S WORKSTATION IMMEDIATELY!"
            
            from actions.security_shield import speak_loud_warning
            res = speak_loud_warning(full_warning)
            self._send_reply(chat_id, f"📢 {res}")
            _audit_log(f"Spoke loud warning on laptop speakers: '{full_warning}'")

        # ❓ Start & Help
        elif cmd_low in ("/start", "start", "/help", "help"):
            self._send_reply(
                chat_id,
                "J.A.R.V.I.S. Remote Bridge 2.0 Command Center Active, sir!\n\n"
                "📸 /snap — Capture live desktop screenshot\n"
                "📷 /cam — Take webcam snapshot\n"
                "🎥 /video <sec> — Record video clip\n"
                "📢 /warn <details> — Speak loud intruder warning on laptop\n"
                "📁 /get <filepath> — Download file from laptop\n"
                "📄 /read <filepath> — Read & summarize document\n"
                "📝 /clip [text] — Read or set laptop clipboard\n"
                "🔊 /vol <0-100> | /mute | /unmute — Volume control\n"
                "🎵 /play <song> | /pause | /next — Spotify music\n"
                "📊 /status | 🌐 /net | 🗓️ /agenda — System telemetry\n"
                "🔒 /lock | /sentry | 😴 /sleep | 💤 /hibernate — Power & Sentry\n"
                "🚀 /launch <app> | 🛑 /kill <proc> — App controller\n"
                "🎙️ Voice Notes — Send any voice note to run commands!"
            )

        # 💬 AI Conversational Fallback via Gemini
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
    """Action handler for Telegram Remote Control Bridge 2.0."""
    params = parameters or {}
    return remote_bridge_mgr.start_polling(player=player)
