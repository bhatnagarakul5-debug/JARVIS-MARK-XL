"""
actions/spotify_control.py — AI Voice DJ & Spotify Mood Sync Engine for JARVIS Mark XL
Supports playback controls, mood playlists (war_mode, coding, chill, focus, workout), URI search, and volume control.
"""

import os
import time
import platform
import urllib.parse
import pyautogui

# Preset Spotify Mood Search Queries
MOOD_PLAYLISTS = {
    "war_mode": "Heavy Metal Rock Workout Epic",
    "war": "Heavy Rock Cyberpunk Hype",
    "coding": "Lofi Beats Coding Focus Chill",
    "code": "Lofi Coding Music",
    "chill": "Chill Lofi Vibes Relax",
    "focus": "Deep Focus Synthwave Instrumentals",
    "workout": "Phonk Hype Workout",
    "party": "Top Hits Party Dance"
}

def spotify_control(parameters: dict, player=None) -> str:
    """
    Controls Spotify playback, searches for music, adjusts volume, or plays mood playlists.
    
    parameters:
        action (str): play | pause | next | prev | search | mood | volume_up | volume_down | mute
        query (str) : Song/Artist query or search text
        mood (str)  : war_mode | coding | chill | focus | workout | party
    """
    params = parameters or {}
    action = (params.get("action") or "").lower().strip()
    query  = params.get("query", "").strip()
    mood   = (params.get("mood") or "").lower().strip()

    if player and hasattr(player, "write_log"):
        player.write_log(f"SYS: Spotify -> action={action}, query='{query}', mood='{mood}'")

    # 1. Volume Controls
    if action in ["volume_up", "vol_up"]:
        for _ in range(5):
            pyautogui.press("volumeup")
        return "Increased system volume."
    elif action in ["volume_down", "vol_down"]:
        for _ in range(5):
            pyautogui.press("volumedown")
        return "Decreased system volume."
    elif action in ["mute", "vol_mute"]:
        pyautogui.press("volumemute")
        return "Muted system volume."

    # 2. Mood Playlists
    if mood or action in ["mood", "dj"]:
        target_mood = mood or query or "coding"
        search_term = MOOD_PLAYLISTS.get(target_mood, f"{target_mood} playlist")
        action = "search"
        query = search_term

    # 3. Playback Controls
    if action in ["pause", "playpause", "stop"]:
        pyautogui.press("playpause")
        return "Toggled Spotify play/pause."

    elif action == "play":
        if query:
            action = "search"
        else:
            pyautogui.press("playpause")
            return "Resumed Spotify playback."

    elif action in ["next", "skip"]:
        pyautogui.press("nexttrack")
        return "Skipped to next track."

    elif action in ["prev", "previous", "back"]:
        pyautogui.press("prevtrack")
        return "Went back to previous track."

    # 4. Search & Open Spotify URI
    if action == "search" and query:
        encoded = urllib.parse.quote(query)
        uri = f"spotify:search:{encoded}"
        
        try:
            if platform.system() == "Windows":
                os.startfile(uri)
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.Popen(["open", uri])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", uri])
            
            time.sleep(2.5)
            pyautogui.press("tab")
            time.sleep(0.2)
            pyautogui.press("enter")
            
            return f"Playing '{query}' on Spotify."
        except Exception as e:
            return f"Failed to search Spotify: {e}"

    return f"Unhandled Spotify action: {action}"
