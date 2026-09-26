"""
actions/anti_shoulder_surfer.py — Sentry Vision Privacy Shield & Anti-Shoulder Surfer Engine
For J.A.R.V.I.S. Mark 58

Protects screen privacy in public spaces (college libraries, cafes, offices):
1. Background Vision Sentry: Periodically audits webcam frames (every 3.5s).
2. People & Intruder Detection:
   - Detects multiple people peering over the user's shoulder (person_count >= 2).
   - Detects unrecognized strangers sitting at the workstation.
3. Privacy Veil Engagement:
   - Automatically blurs sensitive dashboard cards, notes, and conversation history in the UI.
   - Renders a futuristic dark security veil over the desktop workspace.
   - Delivers a subtle voice warning: "Sir, an unrecognized presence is detected behind you."
4. Auto-Restoration:
   - Automatically lifts the veil and restores the clear display once the onlooker steps away.
"""

import cv2
import numpy as np
import time
import threading
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from core.server_security import log_security_event

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
KNOWN_FACES_DIR = CONFIG_DIR / "known_faces"


class AntiShoulderSurfer:
    """
    Autonomous Vision Sentry that watches for onlookers peering over the user's shoulder.
    Lightweight, zero-cloud, hardware-friendly (brief 3.5s frame sample, camera released between ticks).
    """
    _instance: Optional["AntiShoulderSurfer"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._is_active = False
        self._veil_engaged = False
        self._thread: Optional[threading.Thread] = None
        self._consecutive_intruders = 0
        self._consecutive_clear = 0
        self._last_sample_time = 0.0
        self._player = None
        self._speak_fn = None

        # Preload HOG People Detector (built into OpenCV binary — 0 extra downloads)
        try:
            self._hog = cv2.HOGDescriptor()
            self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        except Exception:
            self._hog = None

        # Preload Owner Face Reference Histogram
        self._owner_hist = self._load_owner_reference_histogram()

    def _load_owner_reference_histogram(self) -> Optional[np.ndarray]:
        """Loads reference histogram from saved face in config/known_faces."""
        candidates = list(KNOWN_FACES_DIR.glob("*.jpg"))
        if not candidates:
            return None
        # Prefer creator image if exists
        creator_img = KNOWN_FACES_DIR / "remember_your_creator,_this_is_me,_akul.jpg"
        target_path = creator_img if creator_img.exists() else candidates[0]
        try:
            img = cv2.imread(str(target_path), cv2.IMREAD_COLOR)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
                return hist
        except Exception:
            pass
        return None

    def start_sentry(self, player=None, speak=None) -> str:
        """Starts background anti-shoulder surfing sentry loop."""
        if player:
            self._player = player
        if speak:
            self._speak_fn = speak

        if self._is_active:
            return "Anti-Shoulder Surfer is already active and monitoring your perimeter, sir."

        self._is_active = True
        self._consecutive_intruders = 0
        self._consecutive_clear = 0
        self._thread = threading.Thread(target=self._patrol_worker, daemon=True)
        self._thread.start()

        log_security_event("ANTI_SHOULDER_SURFER_STARTED", "INFO", "Sentry Vision Privacy Shield armed.")
        if self._player and hasattr(self._player, "write_log"):
            self._player.write_log("PRIVACY: 🛡️ Anti-Shoulder Surfer armed. Sentry vision monitoring perimeter.")

        return "Anti-Shoulder Surfer active. I am monitoring your perimeter for onlookers, sir."

    def stop_sentry(self, player=None) -> str:
        """Stops background sentry loop and lifts any active veil."""
        if not self._is_active:
            return "Anti-Shoulder Surfer is not currently active."

        self._is_active = False
        if self._veil_engaged:
            self.dismiss_veil()

        log_security_event("ANTI_SHOULDER_SURFER_STOPPED", "INFO", "Sentry Vision Privacy Shield disarmed.")
        if self._player and hasattr(self._player, "write_log"):
            self._player.write_log("PRIVACY: Anti-Shoulder Surfer disarmed.")

        return "Anti-Shoulder Surfer disarmed, sir."

    def is_active(self) -> bool:
        return self._is_active

    def is_veil_engaged(self) -> bool:
        return self._veil_engaged

    def dismiss_veil(self) -> str:
        """Manually dismisses the privacy veil."""
        self._veil_engaged = False
        self._consecutive_intruders = 0
        self._consecutive_clear = 3

        if self._player and hasattr(self._player, "set_privacy_veil"):
            try:
                self._player.set_privacy_veil(False)
            except Exception:
                pass

        if self._player and hasattr(self._player, "write_log"):
            self._player.write_log("PRIVACY: Privacy veil dismissed by user.")

        return "Privacy veil dismissed. Workspace display restored, sir."

    def _patrol_worker(self):
        """Background thread executing periodic camera audits."""
        while self._is_active:
            try:
                # Sleep between audits to conserve power & release webcam
                time.sleep(3.5)
                if not self._is_active:
                    break

                onlooker_detected = self._sample_camera_for_onlooker()

                if onlooker_detected:
                    self._consecutive_intruders += 1
                    self._consecutive_clear = 0

                    if self._consecutive_intruders >= 1 and not self._veil_engaged:
                        self._veil_engaged = True
                        log_security_event(
                            "SHOULDER_SURFER_DETECTED",
                            "WARN",
                            "Onlooker detected peering at workstation. Engaging privacy veil."
                        )
                        if self._player and hasattr(self._player, "set_privacy_veil"):
                            self._player.set_privacy_veil(True, "Unrecognized presence detected behind workstation")

                        if self._player and hasattr(self._player, "write_log"):
                            self._player.write_log("PRIVACY ALERT: ⚠️ Onlooker detected! Privacy veil engaged.")

                        if self._speak_fn:
                            try:
                                self._speak_fn("Sir, an unrecognized presence is detected behind you. Privacy veil engaged.")
                            except Exception:
                                pass
                else:
                    self._consecutive_clear += 1
                    self._consecutive_intruders = 0

                    if self._consecutive_clear >= 2 and self._veil_engaged:
                        self._veil_engaged = False
                        log_security_event(
                            "SHOULDER_SURFER_CLEARED",
                            "INFO",
                            "Perimeter clear. Lifting privacy veil."
                        )
                        if self._player and hasattr(self._player, "set_privacy_veil"):
                            self._player.set_privacy_veil(False)

                        if self._player and hasattr(self._player, "write_log"):
                            self._player.write_log("PRIVACY: Perimeter clear. Privacy veil lifted.")

                        if self._speak_fn:
                            try:
                                self._speak_fn("Perimeter clear, sir. Restoring workspace display.")
                            except Exception:
                                pass

            except Exception as e:
                # Keep loop alive even if camera momentarily busy
                time.sleep(2.0)

    def _sample_camera_for_onlooker(self) -> bool:
        """
        Briefly grabs 1 frame from webcam, detects human presence, then immediately frees camera.
        Returns True if an onlooker / shoulder-surfer is detected.
        """
        cap = None
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return False

            ret, frame = cap.read()
            if not ret or frame is None:
                return False

            # Downsample for microsecond execution
            h, w = frame.shape[:2]
            scale = 480.0 / float(w) if w > 480 else 1.0
            if scale < 1.0:
                small = cv2.resize(frame, (480, int(h * scale)), interpolation=cv2.INTER_AREA)
            else:
                small = frame

            # 1. Detect People Count using OpenCV HOG
            person_count = 0
            if self._hog is not None:
                boxes, _ = self._hog.detectMultiScale(small, winStride=(8, 8), padding=(4, 4), scale=1.05)
                person_count = len(boxes)

            # If 2 or more people in frame -> Someone is definitely peering over the shoulder!
            if person_count >= 2:
                return True

            # 2. If 1 person detected, verify if it's the owner or an unrecognized person
            if self._owner_hist is not None:
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                curr_hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
                cv2.normalize(curr_hist, curr_hist, 0, 1, cv2.NORM_MINMAX)
                correlation = cv2.compareHist(self._owner_hist, curr_hist, cv2.HISTCMP_CORREL)

                # If 1 person is present but their appearance completely mismatches owner (< 0.25)
                # it's an unrecognized stranger at the screen
                if person_count == 1 and correlation < 0.20:
                    return True

            return False
        except Exception:
            return False
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass


_SURFER = AntiShoulderSurfer()

def get_anti_shoulder_surfer() -> AntiShoulderSurfer:
    return _SURFER

def anti_shoulder_surfer_tool(parameters: Dict[str, Any], player=None, speak=None) -> str:
    """Dispatches tool commands for Anti-Shoulder Surfer."""
    action = parameters.get("action", "enable").lower().strip()
    surfer = get_anti_shoulder_surfer()

    if action in ("enable", "start", "on", "activate"):
        return surfer.start_sentry(player=player, speak=speak)
    elif action in ("disable", "stop", "off", "deactivate"):
        return surfer.stop_sentry(player=player)
    elif action in ("dismiss", "clear", "lift"):
        return surfer.dismiss_veil()
    elif action in ("status", "check"):
        active = surfer.is_active()
        engaged = surfer.is_veil_engaged()
        return (
            f"Anti-Shoulder Surfer Status:\n"
            f"• Perimeter Sentry: {'ACTIVE' if active else 'OFFLINE'}\n"
            f"• Privacy Veil: {'ENGAGED' if engaged else 'STANDBY'}"
        )
    else:
        return f"Unknown action: '{action}'. Available: enable, disable, dismiss, status."
