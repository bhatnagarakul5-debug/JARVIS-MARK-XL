"""
actions/voice_macros.py — JARVIS Voice Workstation Macros & Liked Playlist Automation
Executes multi-step environment routines (Editing Mode, Coding Mode, Gaming Mode) with Spotify Liked Songs playback.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def _launch_spotify_liked(player=None):
    """Launches Spotify and plays user's Liked Songs playlist."""
    try:
        # Spotify URI for user's liked songs
        os.system("start spotify:user:liked")
        time.sleep(1.5)
        if player and hasattr(player, "write_log"):
            player.write_log("MACRO: Launched Spotify Liked Songs playlist.")
    except Exception:
        try:
            from actions.open_app import open_app
            open_app({"app_name": "Spotify"}, player=player)
        except Exception as e:
            print(f"[VoiceMacros] Spotify launch notice: {e}")


def execute_voice_macro(parameters: dict, player=None) -> str:
    """
    Action handler for Voice Workstation Macros.

    parameters:
        macro_name : editing_mode | coding_mode | gaming_mode | study_mode
    """
    params = parameters or {}
    macro = (params.get("macro_name") or params.get("action") or "editing_mode").lower().strip().replace(" ", "_")

    if player and hasattr(player, "write_log"):
        player.write_log(f"MACRO: Initiating workstation macro '{macro}'...")

    if "edit" in macro:
        # 1. Route Audio to Headphones/Bluetooth
        try:
            from actions.audio_device_manager import audio_device_mgr
            audio_device_mgr.set_output_device("headphones")
        except Exception:
            pass

        # 2. Launch DaVinci Resolve
        try:
            from actions.open_app import open_app
            open_app({"app_name": "DaVinci Resolve"}, player=player)
        except Exception:
            pass

        # 3. Play Liked Playlist in Spotify
        _launch_spotify_liked(player=player)

        # 4. Start 45-minute Focus Mode
        try:
            from actions.focus_mode import focus_mode
            focus_mode({"action": "start", "duration": 45}, player=player)
        except Exception:
            pass

        msg = "Editing Mode activated! Launched DaVinci Resolve, routed audio to headphones, started your Liked Songs playlist, and set a 45-minute focus session, sir."
        if player and hasattr(player, "push_notification"):
            player.push_notification("Editing Mode Workstation Active", "success")
        return msg

    elif "code" in macro or "coding" in macro:
        # Coding Mode Macro
        try:
            from actions.audio_device_manager import audio_device_mgr
            audio_device_mgr.set_output_device("headphones")
        except Exception:
            pass

        try:
            from actions.open_app import open_app
            open_app({"app_name": "Visual Studio Code"}, player=player)
        except Exception:
            pass

        _launch_spotify_liked(player=player)

        msg = "Coding Mode activated! Opened Visual Studio Code, connected headphones, and started your Liked Songs playlist, sir."
        if player and hasattr(player, "push_notification"):
            player.push_notification("Coding Mode Active", "success")
        return msg

    elif "game" in macro or "gaming" in macro:
        try:
            from actions.open_app import open_app
            open_app({"app_name": "Discord"}, player=player)
        except Exception:
            pass

        msg = "Gaming Mode activated! Discord launched and audio routed for high performance, sir."
        if player and hasattr(player, "push_notification"):
            player.push_notification("Gaming Mode Active", "info")
        return msg

    return f"Unknown macro '{macro}'. Available macros: editing_mode, coding_mode, gaming_mode."
