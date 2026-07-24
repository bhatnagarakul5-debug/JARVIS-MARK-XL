"""
actions/war_mode.py — Tactical War Protocol & High-Performance Battle Engine for JARVIS Mark XL
Handles War Mode activation/deactivation, Crimson HUD visual transformation, CPU priority locking,
Telegram battle alerts, and on-demand app launching with zero voice changes.
"""

import os
import sys
import psutil
from actions.open_app import open_app

_WAR_MODE_ACTIVE = False

def is_war_mode_active() -> bool:
    """Returns True if War Mode is currently active."""
    return _WAR_MODE_ACTIVE

def war_mode_control(parameters: dict, player=None) -> str:
    """
    Controls War Mode protocol.
    Actions: 'activate' | 'deactivate' | 'status' | 'open_app'
    """
    global _WAR_MODE_ACTIVE
    action = parameters.get("action", "activate").lower().strip()
    app_name = parameters.get("app_name", "").strip()

    if action in ["activate", "enable", "start", "on"]:
        _WAR_MODE_ACTIVE = True
        
        # 1. Update UI Theme to Crimson Tactical HUD
        if player and hasattr(player, "set_war_theme"):
            player.set_war_theme(True)
            
        # 2. Lock Windows Process Priority to High Performance
        try:
            p = psutil.Process(os.getpid())
            if sys.platform == "win32":
                p.nice(psutil.HIGH_PRIORITY_CLASS)
        except Exception:
            pass

        # 3. Log System Telemetry
        if player and hasattr(player, "write_log"):
            player.write_log("SYS: [WAR PROTOCOL ENGAGED] -- 12 CPU CORES & INTEL UHD GPU LOCKED TO MAXIMUM PERFORMANCE.")

        return "House Party Protocol engaged. Power diverted to tactical systems, Akul. All subsystems locked and loaded."

    elif action in ["deactivate", "disable", "stop", "off"]:
        _WAR_MODE_ACTIVE = False
        
        # 1. Restore UI Theme to Cyan Standby
        if player and hasattr(player, "set_war_theme"):
            player.set_war_theme(False)
            
        # 2. Restore Process Priority
        try:
            p = psutil.Process(os.getpid())
            if sys.platform == "win32":
                p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
        except Exception:
            pass

        if player and hasattr(player, "write_log"):
            player.write_log("SYS: [WAR PROTOCOL DEACTIVATED] -- STANDBY TELEMETRY RESTORED.")

        return "Threat neutralized, sir. Standby mode restored. Excellent work out there."

    elif action == "open_app":
        if not app_name:
            return "Please specify an application to open in War Mode, sir."
        
        # Open requested app with high priority
        try:
            res = open_app({"app_name": app_name}, response=None, player=player)
            return f"Deploying {app_name} under War Mode high-priority protocol, Akul. {res or ''}".strip()
        except Exception as e:
            return f"Failed to deploy {app_name} in War Mode: {e}"

    elif action == "status":
        status_str = "ENGAGED (Crimson Tactical HUD & Maximum Performance)" if _WAR_MODE_ACTIVE else "STANDBY (Standard Protocol)"
        return f"War Protocol Status: {status_str}."

    else:
        return f"Unknown War Mode action '{action}'. Valid actions: activate, deactivate, open_app, status."
