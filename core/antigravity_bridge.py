"""
core/antigravity_bridge.py — Antigravity IDE & AI Workspace Bridge for J.A.R.V.I.S. Mark XLI
Enables 2-way telemetry and context sharing between JARVIS and Antigravity AI pair programmer.
Allows JARVIS to inspect live plans, artifacts, walkthroughs, and active tasks.
"""

import time
import json
from pathlib import Path

# Path to local Antigravity brain artifacts directory
ANTIGRAVITY_BRAIN_DIR = Path(r"C:\Users\Akul\.gemini\antigravity\brain\4a17efd5-120c-4cda-8fe9-8dc1d371ba25")


def get_antigravity_status() -> str:
    """Reads live implementation plan and walkthrough from Antigravity IDE workspace."""
    try:
        plan_file = ANTIGRAVITY_BRAIN_DIR / "implementation_plan.md"
        walkthrough_file = ANTIGRAVITY_BRAIN_DIR / "walkthrough.md"

        status_parts = ["🤖 Antigravity IDE Workspace Live Telemetry:"]

        if plan_file.exists():
            plan_text = plan_file.read_text(encoding="utf-8")
            lines = [l.strip() for l in plan_text.splitlines() if l.strip() and not l.startswith("---")]
            first_few = " ".join(lines[:4])
            status_parts.append(f"• Active Plan: {first_few[:250]}...")

        if walkthrough_file.exists():
            wt_text = walkthrough_file.read_text(encoding="utf-8")
            wt_lines = [l.strip() for l in wt_text.splitlines() if l.strip() and not l.startswith("---")]
            first_wt = " ".join(wt_lines[:4])
            status_parts.append(f"• Recent Walkthrough: {first_wt[:250]}...")

        if len(status_parts) == 1:
            return "Antigravity IDE is online. Workspace session active."

        return "\n\n".join(status_parts)
    except Exception as e:
        return f"Antigravity Bridge status notice: {e}"


def dispatch_task_to_ide(instruction: str) -> str:
    """Dispatches a task instruction to the Antigravity IDE workspace task queue."""
    try:
        scratch_dir = ANTIGRAVITY_BRAIN_DIR / "scratch"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        
        queue_file = scratch_dir / "agent_instruction.json"
        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sender": "JARVIS Mark XLI",
            "instruction": instruction
        }
        queue_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return f"Dispatched task to Antigravity IDE workspace: '{instruction}'"
    except Exception as e:
        return f"Could not dispatch task to Antigravity IDE: {e}"
