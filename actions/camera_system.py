"""
actions/camera_system.py — Fail-Safe Telegram Face Profile Memory Engine for JARVIS Mark XL
Supports multimodal AI vision recognition with automatic fallback to local histogram feature matching.
Clean string encoding for Windows CMD.
"""

import cv2
import numpy as np
import os
import sys
import json
from pathlib import Path
from google import genai
from google.genai import types

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
FACES_DIR = BASE_DIR / "config" / "known_faces"

FACES_DIR.mkdir(parents=True, exist_ok=True)


def _get_api_key() -> str:
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("gemini_api_key", "")
    except Exception:
        pass
    return ""


def list_remembered_faces() -> list[str]:
    """Returns list of remembered face names."""
    if not FACES_DIR.exists():
        return []
    return [f.stem.replace("_", " ").title() for f in FACES_DIR.glob("*.jpg")]


def save_face_profile(name: str, img_bytes: bytes) -> str:
    """Saves photo image bytes as a remembered face profile."""
    if not name:
        name = "User Profile"

    clean_name = name.lower().strip().replace(" ", "_")
    file_path = FACES_DIR / f"{clean_name}.jpg"
    file_path.write_bytes(img_bytes)

    return f"Saved and remembered face profile for '{name.title()}', sir."


def _local_histogram_match(target_bytes: bytes) -> str:
    """Local OpenCV histogram similarity fallback if API hits rate limits."""
    try:
        nparr = np.frombuffer(target_bytes, np.uint8)
        target_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if target_img is None:
            return "Could not decode uploaded image."

        target_hist = cv2.calcHist([cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)], [0], None, [256], [0, 256])
        cv2.normalize(target_hist, target_hist, 0, 1, cv2.NORM_MINMAX)

        best_name = "Unknown"
        best_score = -1.0

        for img_path in FACES_DIR.glob("*.jpg"):
            person_name = img_path.stem.replace("_", " ").title()
            k_img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
            if k_img is not None:
                k_hist = cv2.calcHist([cv2.cvtColor(k_img, cv2.COLOR_BGR2GRAY)], [0], None, [256], [0, 256])
                cv2.normalize(k_hist, k_hist, 0, 1, cv2.NORM_MINMAX)
                score = cv2.compareHist(target_hist, k_hist, cv2.HISTCMP_CORREL)
                if score > best_score and score > 0.6:
                    best_score = score
                    best_name = person_name

        if best_name != "Unknown":
            return f"Recognized '{best_name}' (Feature Similarity: {best_score*100:.1f}%)!"
        return "Image processed, but did not match any stored face profile."
    except Exception as ex:
        print(f"[FaceEngine] Local fallback notice: {ex}")
        known = list_remembered_faces()
        return f"Face scan complete. Saved profiles: {', '.join(known)}."


def recognize_face_from_bytes(img_bytes: bytes) -> str:
    """
    Recognizes a person from an uploaded Telegram photo using Gemini AI Vision,
    with local histogram feature matching fallback.
    """
    saved_files = list(FACES_DIR.glob("*.jpg"))
    if not saved_files:
        return "No face profiles currently saved in memory. Upload a photo with a name caption (e.g. 'Akul') to save one!"

    api_key = _get_api_key()
    if not api_key:
        return _local_histogram_match(img_bytes)

    # 1. Try Gemini Vision models
    try:
        client = genai.Client(api_key=api_key)
        contents = ["You are JARVIS. Analyze the uploaded photo and identify if it matches any of the reference face profiles below.\n"]

        for idx, img_path in enumerate(saved_files, 1):
            person_name = img_path.stem.replace("_", " ").title()
            ref_bytes = img_path.read_bytes()
            contents.append(f"Reference Profile #{idx} [{person_name}]:")
            contents.append(types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg"))

        contents.append("\nUploaded Target Photo to Identify:")
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
        contents.append(
            "\nTask: Compare the Target Photo against the Reference Profiles. "
            "If there is a clear match, state 'Recognized [Name]!' and briefly describe the match. "
            "If it does not match any profile, state 'Unknown face — no match found in saved profiles.'"
        )

        for model_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                if response and response.text:
                    return response.text.strip()
            except Exception:
                continue
    except Exception as e:
        print(f"[FaceEngine] Gemini vision notice: {e}")

    # 2. Local Fallback
    return _local_histogram_match(img_bytes)


def camera_control(parameters: dict, player=None) -> str:
    """
    Action handler for face profile memory query.
    """
    faces = list_remembered_faces()
    if faces:
        names = ", ".join(faces)
        return f"Remembered Face Profiles in Memory: {names}. (Upload photos to @AKULJARVIS_BOT on Telegram to add or identify faces!)."
    return "No face profiles currently stored. Upload a photo with a name caption to @AKULJARVIS_BOT on Telegram to save a face profile!"


class CameraManager:
    """Compatibility manager wrapper."""
    def __init__(self):
        self.is_active = False
        self.security_active = False
        self.gesture_active = False

    def start_camera(self, *args, **kwargs):
        return "Laptop camera disabled. Upload photos to Telegram bot to remember or identify faces."

    def stop_camera(self, *args, **kwargs):
        return "Camera is OFF."


camera_mgr = CameraManager()
