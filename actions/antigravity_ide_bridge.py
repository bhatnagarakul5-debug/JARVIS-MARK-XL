"""
actions/antigravity_ide_bridge.py — Antigravity IDE Action Bridge for JARVIS Mark XLI
Enables JARVIS voice chat and Telegram commands to read Antigravity IDE live workspace status
and dispatch coding instructions to the Antigravity IDE workspace.
"""

from core.antigravity_bridge import get_antigravity_status, dispatch_task_to_ide


def antigravity_ide_control(parameters: dict, player=None) -> str:
    """
    Action handler for Antigravity IDE Bridge.

    parameters:
        action : status | dispatch | plan
        task   : Instruction to dispatch to Antigravity IDE
    """
    params = parameters or {}
    action = (params.get("action") or "status").lower().strip()
    task = (params.get("task") or params.get("instruction") or params.get("query") or "").strip()

    if action in ("status", "plan", "walkthrough", "check"):
        res = get_antigravity_status()
        if player and hasattr(player, "write_log"):
            player.write_log("AGY-IDE-BRIDGE: Fetched live workspace status.")
        return res

    elif action in ("dispatch", "send", "run") or task:
        if not task:
            task = action
        res = dispatch_task_to_ide(task)
        if player and hasattr(player, "write_log"):
            player.write_log(f"AGY-IDE-BRIDGE: Dispatched task to IDE: '{task[:40]}'")
        return res

    return get_antigravity_status()
