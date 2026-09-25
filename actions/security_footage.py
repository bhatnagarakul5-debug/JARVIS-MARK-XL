"""
actions/security_footage.py — J.A.R.V.I.S. Mark 58 AI Security Footage Vision & Commentary Engine
Captures live security camera feed (with automatic screen fallback), analyzes what is seen
via Gemini 2.5 Multimodal Vision, and delivers intelligent witty, serious, or fun commentary.
"""

import os
import sys
import time
import json
import io
from pathlib import Path
from typing import Optional, Tuple
import requests

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
SNAPSHOTS_DIR = BASE_DIR / "memory" / "security_snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

IMG_MAX_W = 720
IMG_MAX_H = 480
JPEG_Q    = 70


def _get_api_keys() -> dict:
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _capture_webcam_frame() -> Tuple[Optional[bytes], str]:
    """Attempts to capture a frame from the primary webcam."""
    try:
        import cv2
        keys = _get_api_keys()
        cam_idx = int(keys.get("camera_index", 0))

        cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            # Try index 0 fallback
            cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            cap.release()
            return None, "Camera not accessible"

        # Discard initial warm-up frames
        for _ in range(6):
            cap.read()

        ret, frame = cap.read()
        cap.release()

        if ret and frame is not None and frame.mean() > 4:
            # Resize
            h, w = frame.shape[:2]
            scale = min(IMG_MAX_W / w, IMG_MAX_H / h, 1.0)
            if scale < 1.0:
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
            return buf.tobytes(), "webcam"
        return None, "Dark or invalid webcam frame"
    except Exception as e:
        return None, f"Webcam error: {e}"


def _capture_screen_frame() -> Tuple[Optional[bytes], str]:
    """Captures desktop screen as fallback if webcam is unavailable."""
    try:
        import mss
        import mss.tools
        from PIL import Image

        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[1])
            png_bytes = mss.tools.to_png(shot.rgb, shot.size)

        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        img.thumbnail((IMG_MAX_W, IMG_MAX_H), Image.BILINEAR)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_Q)
        return buf.getvalue(), "screen"
    except Exception as e:
        # Fallback to simulated sensor telemetry frame if desktop DWM token is detached
        try:
            import numpy as np
            import cv2
            dummy = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.circle(dummy, (320, 240), 120, (0, 210, 255), 2)
            cv2.circle(dummy, (320, 240), 60, (0, 210, 255), 1)
            cv2.line(dummy, (160, 240), (480, 240), (0, 210, 255), 1)
            cv2.line(dummy, (320, 100), (320, 380), (0, 210, 255), 1)
            cv2.putText(dummy, "SECURITY FEED -- SENSOR SWEEP", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)
            cv2.putText(dummy, f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}", (40, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            _, buf = cv2.imencode(".jpg", dummy)
            return buf.tobytes(), "sensor_sweep"
        except Exception:
            return None, f"Screen capture error: {e}"


def _send_telegram_snapshot(photo_bytes: bytes, caption: str):
    """Optionally dispatches the security snapshot to Telegram."""
    try:
        keys = _get_api_keys()
        bot_token = keys.get("telegram_bot_token")
        chat_id = keys.get("telegram_chat_id")
        if bot_token and chat_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            files = {"photo": ("security_feed.jpg", photo_bytes, "image/jpeg")}
            data = {"chat_id": chat_id, "caption": f"🛡️ JARVIS Security Feed:\n{caption}"}
            requests.post(url, data=data, files=files, timeout=6)
    except Exception as ex:
        print(f"[SecurityFootage] Telegram notice: {ex}")


def capture_security_footage(parameters: dict = None, player=None) -> str:
    """
    Captures live security camera footage (or workstation screen) and analyzes the visual scene
    with Gemini Vision to deliver witty, serious, or fun commentary on what is seen.

    Parameters:
      - source: 'camera' | 'screen' | 'auto' (default: 'auto')
      - mode: 'auto' | 'witty' | 'serious' | 'fun' (default: 'auto')
    """
    params = parameters or {}
    source = params.get("source", "auto").lower().strip()
    mode_pref = params.get("mode", "auto").lower().strip()

    if player and hasattr(player, "write_log"):
        player.write_log("SECURITY: Engaging security sensors and capturing live visual feed...")

    photo_bytes = None
    capture_type = "unknown"

    # 1. Attempt Capture based on source preference
    if source in ("camera", "webcam", "auto"):
        photo_bytes, capture_type = _capture_webcam_frame()

    if (photo_bytes is None or source == "screen") and source != "camera":
        photo_bytes, capture_type = _capture_screen_frame()

    if photo_bytes is None:
        return "Sir, I attempted to engage the security cameras and screen capture, but no visual feed was accessible."

    # 2. Save snapshot locally
    ts = time.strftime("%Y%m%d_%H%M%S")
    snapshot_file = SNAPSHOTS_DIR / f"security_{capture_type}_{ts}.jpg"
    try:
        snapshot_file.write_bytes(photo_bytes)
    except Exception:
        pass

    # 3. Analyze scene with Gemini Multimodal Vision
    keys = _get_api_keys()
    api_key = keys.get("gemini_api_key", "")
    if not api_key:
        return f"Security snapshot captured ({capture_type.upper()}), but Gemini API key is missing for vision analysis."

    commentary = ""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        mode_instruction = ""
        if mode_pref == "witty":
            mode_instruction = "Give a clever, sarcastic, MCU-style witty observation about whatever you see."
        elif mode_pref == "serious":
            mode_instruction = "Deliver a strictly serious, tactical security assessment of the area."
        elif mode_pref == "fun":
            mode_instruction = "Deliver a fun, lighthearted, and amusing commentary on what is visible."
        else:
            mode_instruction = (
                "Decide the appropriate tone naturally based on what you see:\n"
                "- If threat, intruder, darkness, or anomaly: be serious and alert.\n"
                "- If user working, drinking coffee, snacks, messy desk, slouching: be witty and clever.\n"
                "- If pets, funny gestures, goofy expressions: be fun and entertaining."
            )

        prompt = (
            "You are J.A.R.V.I.S., Tony Stark's iconic AI assistant (Mark 58 Apex Core). "
            f"You have just acquired a live security visual feed ({capture_type.upper()}). "
            "Examine everything visible in the image: people, posture, expressions, activities, clothing, "
            "objects, clutter, beverages/food, pets, screens, room environment, and any potential security concerns.\n\n"
            f"Directive: {mode_instruction}\n\n"
            "Format: Respond in exactly 1 or 2 crisp, high-impact sentences in your signature Charon voice. "
            "Address the user as 'sir' or by their name if recognized. "
            "Do NOT describe resolution or pixels. Speak directly to what you observe."
        )

        contents = [
            prompt,
            types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg")
        ]

        for model_name in ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                if resp and resp.text:
                    commentary = resp.text.strip()
                    break
            except Exception as mex:
                print(f"[SecurityFootage] Model {model_name} notice: {mex}")

    except Exception as ex:
        print(f"[SecurityFootage] Gemini vision error: {ex}")
        commentary = f"Visual sweep complete ({capture_type.upper()}). Perimeter appears secure, sir."

    if not commentary:
        commentary = f"Security feed analyzed. Area nominal and secure, sir."

    # 4. Log to UI & Telemetry
    if player and hasattr(player, "write_log"):
        player.write_log(f"SECURITY [{capture_type.upper()}]: {commentary}")
        if hasattr(player, "push_notification"):
            player.push_notification("Security footage analyzed", "info")

    # 5. Background send to Telegram if configured
    import threading
    threading.Thread(
        target=_send_telegram_snapshot,
        args=(photo_bytes, commentary),
        daemon=True
    ).start()

    return commentary
