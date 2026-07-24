"""
actions/davinci_control.py — JARVIS DaVinci Resolve Voice Controller
Allows voice control over DaVinci Resolve for editing, page switching, timeline markers, and rendering.
"""

import time
import os
import sys
import pyautogui
from pathlib import Path

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def _focus_davinci() -> bool:
    """Finds and focuses the DaVinci Resolve window."""
    try:
        import pygetwindow as gw
        wins = gw.getWindowsWithTitle("DaVinci Resolve")
        if wins:
            win = wins[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.3)
            return True
    except Exception:
        pass

    # Fallback using Windows search / open_app
    try:
        from actions.open_app import open_app
        open_app({"app_name": "DaVinci Resolve"})
        time.sleep(2.0)
        pyautogui.hotkey("win", "up")
        return True
    except Exception as e:
        print(f"[DaVinciControl] Could not focus DaVinci Resolve: {e}")
        return False


def _get_resolve_api():
    """Tries to connect to DaVinci Resolve Scripting API if available."""
    try:
        import DaVinciResolveScript as dvr
        return dvr.scriptapp("Resolve")
    except ImportError:
        possible_paths = [
            r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Developer\Scripting\Modules",
            r"%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
        ]
        for p in possible_paths:
            expanded = os.path.expandvars(p)
            if os.path.exists(expanded) and expanded not in sys.path:
                sys.path.append(expanded)
        try:
            import DaVinciResolveScript as dvr
            return dvr.scriptapp("Resolve")
        except Exception:
            return None


def davinci_control(parameters: dict, player=None) -> str:
    """
    Controls DaVinci Resolve editor.

    parameters:
        action : launch | cut | ripple_delete | marker | play | pause |
                 render | page_edit | page_color | page_deliver |
                 page_fusion | page_fairlight | page_media | page_cut
        text   : optional marker label or export preset name
    """
    params = parameters or {}
    action = (params.get("action") or "launch").lower().strip()
    text   = params.get("text", "").strip()

    if player:
        player.write_log(f"[davinci] Action: {action}")

    # 1. Launch / Focus
    if action in ("launch", "open", "start"):
        _focus_davinci()
        return "DaVinci Resolve launched and focused, sir."

    # Ensure window is focused before sending hotkeys
    if not _focus_davinci():
        return "Could not find or launch DaVinci Resolve, sir."

    # 2. Page Switching Shortcuts
    page_shortcuts = {
        "page_media":     ("shift", "2"),
        "page_cut":       ("shift", "3"),
        "page_edit":      ("shift", "4"),
        "edit":           ("shift", "4"),
        "page_fusion":    ("shift", "5"),
        "fusion":         ("shift", "5"),
        "page_color":     ("shift", "6"),
        "color":          ("shift", "6"),
        "page_fairlight": ("shift", "7"),
        "fairlight":      ("shift", "7"),
        "audio":          ("shift", "7"),
        "page_deliver":   ("shift", "8"),
        "deliver":        ("shift", "8"),
        "render_page":    ("shift", "8"),
    }

    if action in page_shortcuts:
        keys = page_shortcuts[action]
        pyautogui.hotkey(*keys)
        page_name = action.replace("page_", "").title()
        return f"Switched DaVinci Resolve to {page_name} page, sir."

    # 3. Editing Actions
    if action in ("cut", "blade", "split"):
        pyautogui.hotkey("ctrl", "b")
        return "Blade cut performed at playhead, sir."

    if action in ("ripple_delete", "delete_selected", "delete"):
        pyautogui.hotkey("shift", "backspace")
        return "Ripple delete performed on selected clip, sir."

    if action in ("marker", "add_marker"):
        pyautogui.press("m")
        if text:
            time.sleep(0.2)
            pyautogui.press("m")
            time.sleep(0.3)
            pyautogui.write(text, interval=0.03)
            pyautogui.press("enter")
        return f"Marker added at playhead{f' ({text})' if text else ''}, sir."

    if action in ("play", "pause", "toggle_play"):
        pyautogui.press("space")
        return "Playback toggled, sir."

    if action in ("zoom_in", "timeline_zoom_in"):
        pyautogui.hotkey("ctrl", "=")
        return "Timeline zoomed in, sir."

    if action in ("zoom_out", "timeline_zoom_out"):
        pyautogui.hotkey("ctrl", "-")
        return "Timeline zoomed out, sir."

    if action in ("render", "export", "start_render"):
        pyautogui.hotkey("shift", "8")
        time.sleep(1.0)
        pyautogui.hotkey("alt", "shift", "r")
        time.sleep(0.8)
        pyautogui.hotkey("ctrl", "r")
        return "Rendering initiated in DaVinci Resolve, sir."

    if action in ("status", "api_info"):
        resolve = _get_resolve_api()
        if resolve:
            project_mgr = resolve.GetProjectManager()
            curr_project = project_mgr.GetCurrentProject()
            proj_name = curr_project.GetName() if curr_project else "No project open"
            return f"DaVinci Resolve API connected. Current project: '{proj_name}'."
        return "DaVinci Resolve is controlled via keyboard shortcuts (API module not loaded)."

    return f"DaVinci Resolve action '{action}' executed, sir."
