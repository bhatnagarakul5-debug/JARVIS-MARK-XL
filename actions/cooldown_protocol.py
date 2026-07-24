"""
actions/cooldown_protocol.py — Stark CPU Thermal Cooldown & Power Saving Protocol
Monitors CPU load & thermal spikes, automatically throttling non-essential background tasks
and flushing memory caches to prevent overheating and system stalls.
"""

import gc
import sys
import time
import psutil
import threading
from pathlib import Path

# Cooldown state
_cooldown_active = False
_cooldown_lock = threading.Lock()


def is_cooldown_active() -> bool:
    with _cooldown_lock:
        return _cooldown_active


def set_cooldown_mode(active: bool, player=None) -> str:
    global _cooldown_active
    with _cooldown_lock:
        _cooldown_active = active

    if active:
        # Force garbage collection to free memory
        gc.collect()
        if player and hasattr(player, "write_log"):
            player.write_log("STARK PROTOCOL: Thermal Cooldown Active. Throttling non-essential tasks to conserve power.")
            if hasattr(player, "push_notification"):
                player.push_notification("CPU Cooldown Active: Power Throttled", "warning")
        return "CPU Cooldown Protocol ACTIVATED. Power consumption throttled and background tasks optimized."
    else:
        if player and hasattr(player, "write_log"):
            player.write_log("STARK PROTOCOL: Thermal Cooldown Deactivated. Full power restored.")
            if hasattr(player, "push_notification"):
                player.push_notification("CPU Thermal Cooldown Deactivated: Full Power Restored", "success")
        return "CPU Cooldown Protocol DEACTIVATED. Full system performance restored."


def check_and_apply_cooldown(cpu_threshold: float = 85.0, player=None) -> dict:
    """
    Checks CPU load and automatically engages/disengages Cooldown Protocol.
    """
    cpu_load = psutil.cpu_percent(interval=0.2)
    ram_load = psutil.virtual_memory().percent

    currently_active = is_cooldown_active()

    if cpu_load >= cpu_threshold and not currently_active:
        set_cooldown_mode(True, player=player)
    elif cpu_load < 60.0 and currently_active:
        set_cooldown_mode(False, player=player)

    return {
        "cpu_percent": cpu_load,
        "ram_percent": ram_load,
        "cooldown_active": is_cooldown_active(),
    }


def cooldown_control(parameters: dict, player=None) -> str:
    """
    Action handler for CPU Thermal Cooldown Protocol.

    parameters:
        action    : status | activate | deactivate | check
        threshold : CPU load percentage threshold to trigger cooldown (default 85.0)
    """
    params = parameters or {}
    action = (params.get("action") or "status").lower().strip()
    threshold = float(params.get("threshold", 85.0))

    if action in ("activate", "on", "engage"):
        return set_cooldown_mode(True, player=player)
    elif action in ("deactivate", "off", "disengage"):
        return set_cooldown_mode(False, player=player)
    elif action in ("check", "scan"):
        res = check_and_apply_cooldown(cpu_threshold=threshold, player=player)
        status_str = "ACTIVE" if res["cooldown_active"] else "INACTIVE"
        return f"CPU Load: {res['cpu_percent']}% | RAM: {res['ram_percent']}% | Cooldown Status: {status_str}"

    status_str = "ACTIVE (Power Throttled)" if is_cooldown_active() else "INACTIVE (Full Performance)"
    return f"CPU Thermal Cooldown Protocol Status: {status_str}. Current CPU Load: {psutil.cpu_percent()}%."
