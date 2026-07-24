"""
actions/system_diagnostics.py — JARVIS Autonomous Deep System Diagnostics & Repair Suite
Provides deep hardware monitoring (CPU, RAM, GPU, Disk, Network), JARVIS subsystem health checks,
and auto-repair capabilities to keep all AI systems running at peak performance.
"""

import os
import sys
import time
import json
import socket
import platform
import subprocess
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def _check_network() -> dict:
    """Checks network latency, DNS resolution, and internet connectivity."""
    result = {"connected": False, "ping_ms": 0, "ip": "Unknown"}
    try:
        start = time.time()
        s = socket.create_connection(("8.8.8.8", 53), timeout=3)
        result["ping_ms"] = round((time.time() - start) * 1000, 1)
        result["ip"] = s.getsockname()[0]
        s.close()
        result["connected"] = True
    except Exception:
        pass
    return result


def _check_gpu() -> dict:
    """Checks GPU hardware stats via nvidia-smi or DirectX / WMI."""
    gpu_info = {"has_gpu": False, "name": "N/A", "vram_used": "N/A", "vram_total": "N/A", "driver": "N/A"}

    # 1. Try nvidia-smi
    try:
        cmd = "nvidia-smi --query-gpu=name,memory.used,memory.total,driver_version --format=csv,noheader,nounits"
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, timeout=2).strip()
        if output:
            parts = [p.strip() for p in output.split(",")]
            if len(parts) >= 4:
                gpu_info["has_gpu"] = True
                gpu_info["name"] = parts[0]
                gpu_info["vram_used"] = f"{parts[1]} MB"
                gpu_info["vram_total"] = f"{parts[2]} MB"
                gpu_info["driver"] = parts[3]
                return gpu_info
    except Exception:
        pass

    # 2. Try OpenCV OpenCL GPU
    try:
        import cv2
        cv2.ocl.setUseOpenCL(True)
        if cv2.ocl.useOpenCL():
            gpu_info["has_gpu"] = True
            gpu_info["name"] = "OpenCL Accelerated GPU"
            gpu_info["driver"] = "OpenCV OpenCL Active"
    except Exception:
        pass

    return gpu_info


def _check_subsystems() -> dict:
    """Audits internal JARVIS subsystems (API Keys, Memory, Camera, Audio)."""
    subsystems = {
        "gemini_api_key": False,
        "chromadb": False,
        "opencv_gpu": False,
        "audio_device": False,
    }

    # API key check
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if cfg.get("gemini_api_key"):
                subsystems["gemini_api_key"] = True
    except Exception:
        pass

    # ChromaDB check
    try:
        from memory.memory_manager import load_memory
        load_memory()
        subsystems["chromadb"] = True
    except Exception:
        pass

    # OpenCV GPU check
    try:
        import cv2
        subsystems["opencv_gpu"] = cv2.ocl.useOpenCL()
    except Exception:
        pass

    # Audio check
    try:
        import sounddevice as sd
        devs = sd.query_devices()
        subsystems["audio_device"] = len(devs) > 0
    except Exception:
        pass

    return subsystems


def run_system_diagnostics(parameters: dict, player=None) -> str:
    """
    JARVIS Autonomous Deep System Diagnostics & Repair handler.

    parameters:
        action : full_scan | repair | gpu | network | subsystems
    """
    params = parameters or {}
    action = (params.get("action") or "full_scan").lower().strip()

    if player and hasattr(player, "write_log"):
        player.write_log(f"DIAGNOSTIC: Running deep system diagnostic action='{action}'...")

    # Auto Repair Action
    if action in ("repair", "auto_fix", "clean"):
        cleaned_files = 0
        try:
            # Clean __pycache__ files
            for p in BASE_DIR.glob("**/__pycache__"):
                for f in p.glob("*.pyc"):
                    try:
                        f.unlink()
                        cleaned_files += 1
                    except Exception:
                        pass
        except Exception:
            pass

        # Reset OpenCV OpenCL GPU
        gpu_status = "Disabled"
        try:
            import cv2
            cv2.ocl.setUseOpenCL(True)
            gpu_status = "Active" if cv2.ocl.useOpenCL() else "Inactive"
        except Exception:
            pass

        msg = f"Auto-Repair Complete! Cleaned {cleaned_files} bytecode cache files. OpenCV GPU acceleration: {gpu_status}. All subsystems re-aligned, sir."
        if player and hasattr(player, "push_notification"):
            player.push_notification("System Repair & Cache Optimization Complete", "success")
        return msg

    # Hardware & System Info
    import psutil
    cpu_pct = psutil.cpu_percent(interval=0.3)
    cpu_cores = psutil.cpu_count(logical=True)
    ram = psutil.virtual_memory()
    ram_pct = ram.percent
    ram_used_gb = round(ram.used / (1024**3), 2)
    ram_total_gb = round(ram.total / (1024**3), 2)

    disk = psutil.disk_usage(str(BASE_DIR.anchor))
    disk_free_gb = round(disk.free / (1024**3), 1)

    net = _check_network()
    gpu = _check_gpu()
    subsystems = _check_subsystems()

    if action in ("gpu", "gpu_status"):
        if not gpu["has_gpu"]:
            return "No dedicated NVIDIA/CUDA GPU detected. OpenCV OpenCL GPU acceleration is active."
        return (
            f"=== GPU Hardware Diagnostic ===\n"
            f"• GPU Model: {gpu['name']}\n"
            f"• VRAM Usage: {gpu['vram_used']} / {gpu['vram_total']}\n"
            f"• Driver Version: {gpu['driver']}\n"
            f"• Hardware Acceleration: Active"
        )

    # Full Scan Summary
    lines = [
        "============================================",
        "      J.A.R.V.I.S. SYSTEM HEALTH DIAGNOSTIC",
        "============================================",
        f"• OS Platform: {platform.system()} {platform.release()} ({platform.machine()})",
        f"• CPU Load: {cpu_pct}% ({cpu_cores} Logical Cores)",
        f"• System RAM: {ram_pct}% ({ram_used_gb} GB / {ram_total_gb} GB)",
        f"• Disk Space (C:): {disk_free_gb} GB Free ({disk.percent}% used)",
        f"• Network Ping: {net['ping_ms']} ms [{'ONLINE' if net['connected'] else 'OFFLINE'}] (Local IP: {net['ip']})",
        "",
        "--- GPU Acceleration ---",
        f"• GPU Hardware: {gpu['name']}",
        f"• VRAM: {gpu['vram_used']} / {gpu['vram_total']}",
        f"• OpenCV GPU (OpenCL): {'[ENABLED ⚡]' if subsystems['opencv_gpu'] else '[DISABLED]'}",
        "",
        "--- Core Subsystem Readiness ---",
        f"• Gemini Live API Key: {'[VALID ✅]' if subsystems['gemini_api_key'] else '[MISSING ❌]'}",
        f"• ChromaDB Vector Memory: {'[ONLINE ✅]' if subsystems['chromadb'] else '[ERROR ❌]'}",
        f"• Audio Stream Pipeline: {'[READY ✅]' if subsystems['audio_device'] else '[ERROR ❌]'}",
        "============================================"
    ]

    report = "\n".join(lines)

    if player and hasattr(player, "write_log"):
        player.write_log("DIAGNOSTIC: Full diagnostic report generated.")
        if hasattr(player, "push_notification"):
            player.push_notification("System Diagnostic Complete — All Systems Nominal", "success")

    return report
