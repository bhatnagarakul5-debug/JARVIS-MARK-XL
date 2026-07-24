"""
actions/security_shield.py — Stark Cyber Security Shield & Sentry Mode Intruder Defense
Sends Telegram & WhatsApp alert messages FIRST, verifies HTTP delivery, and THEN locks Windows.
"""

import os
import sys
import time
import ctypes
import requests
import subprocess
import json

def _send_sentry_alert_sync(msg: str, player=None) -> bool:
    """
    Sends Telegram & WhatsApp alert messages BEFORE locking Windows.
    Returns True if alert was delivered.
    """
    telegram_sent = False
    whatsapp_sent = False

    # 1. Telegram Phone Alert (Synchronous POST before lock)
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "api_keys.json")
        bot_token = ""
        chat_id = ""

        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            bot_token = cfg.get("telegram_bot_token", "")
            chat_id = cfg.get("telegram_chat_id", "")

        if bot_token:
            if not chat_id:
                try:
                    upd_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates", timeout=3).json()
                    for update in upd_resp.get("result", []):
                        msg_obj = update.get("message") or update.get("edited_message") or update.get("channel_post") or {}
                        c_id = msg_obj.get("chat", {}).get("id")
                        if c_id:
                            chat_id = str(c_id)
                            break
                except Exception:
                    pass

            if chat_id:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                resp = requests.post(url, json={"chat_id": chat_id, "text": f"🚨 {msg}"}, timeout=4)
                if resp.status_code == 200:
                    telegram_sent = True
            else:
                if player and hasattr(player, "write_log"):
                    player.write_log("SECURITY NOTICE: Please text @AKULJARVIS_BOT once on Telegram to save your Chat ID for phone alerts!")
    except Exception as e:
        if player and hasattr(player, "write_log"):
            player.write_log(f"SECURITY: Telegram alert notice: {e}")

    # 2. WhatsApp Phone Alert
    try:
        from actions.send_message import send_message
        cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "api_keys.json")
        target_contact = "Akul"
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                target_contact = json.load(f).get("whatsapp_target_contact", "Akul")

        send_message({"recipient": target_contact, "message": f"🚨 {msg}"}, player=player)
        whatsapp_sent = True
    except Exception:
        pass

    if player and hasattr(player, "write_log"):
        status_msg = f"SECURITY: Sentry alert delivered via {'Telegram' if telegram_sent else 'Logs'}{' & WhatsApp (' + target_contact + ')' if whatsapp_sent else ''}."
        player.write_log(status_msg)

    # Give HTTP POST 0.4s to flush before locking
    time.sleep(0.4)
    return telegram_sent or whatsapp_sent


def trigger_intruder_lock(intruder_name: str = "Unknown", player=None) -> str:
    """
    Sends phone alert FIRST, then locks Windows desktop when an intruder is detected.
    """
    alert_msg = f"SECURITY ALERT: Workstation on Dell Inspiron 15 locked due to intruder attempt ({intruder_name})."

    if player and hasattr(player, "write_log"):
        player.write_log(f"SECURITY ALERT: Intruder '{intruder_name}' detected! Sending phone alert before lock...")

    # Send Message FIRST
    _send_sentry_alert_sync(alert_msg, player=player)

    try:
        # Lock Windows AFTER message is sent
        ctypes.windll.user32.LockWorkStation()
        return f"SECURITY SHIELD: Alert message sent to phone, workstation locked."
    except Exception as e:
        return f"Failed to lock workstation: {e}"


def trigger_sentry_mode(player=None) -> str:
    """
    Activates Sentry Mode: sends phone alert message FIRST, then locks Windows workstation.
    """
    timestamp = time.strftime("%I:%M %p")
    alert_msg = f"SENTRY MODE ENGAGED on Dell Inspiron 15 at {timestamp}. Workstation locked, perimeter security active, and phone alerts armed."

    if player and hasattr(player, "write_log"):
        player.write_log("SECURITY: SENTRY MODE ENGAGED -- Sending phone alert before locking workstation...")

    # Send Message FIRST
    _send_sentry_alert_sync(alert_msg, player=player)

    try:
        # Lock Windows AFTER message is sent
        ctypes.windll.user32.LockWorkStation()
        return "Sentry Mode engaged, Akul. Alert message sent to your phone, workstation locked."
    except Exception as e:
        return f"Sentry Mode error: {e}"


def scan_local_network(player=None) -> str:
    """
    Scans local Wi-Fi / LAN network for active connected devices.
    """
    if player and hasattr(player, "write_log"):
        player.write_log("SECURITY: Scanning local network for connected devices...")

    devices = []
    try:
        output = subprocess.check_output("arp -a", shell=True, text=True, timeout=5)
        lines = output.splitlines()
        for line in lines:
            if "dynamic" in line.lower() or "static" in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[0]
                    mac = parts[1]
                    if not ip.startswith("224.") and not ip.startswith("239."):
                        devices.append(f"• IP: {ip.ljust(15)} | MAC: {mac}")
    except Exception as e:
        return f"Network scan error: {e}"

    if not devices:
        return "Network scan complete — no active secondary dynamic IP leases found."

    summary = ["=== Local Network Security Scan ===", f"Total Connected Devices Detected: {len(devices)}"]
    summary.extend(devices[:10])

    report = "\n".join(summary)
    if player and hasattr(player, "write_log"):
        player.write_log("SECURITY: Network scan complete.")
    return report


def security_shield_control(parameters: dict, player=None) -> str:
    """
    Action handler for Stark Cyber Security Shield & Sentry Mode.

    parameters:
        action : lock | sentry | scan_network | intruder_check
        target : Intruder name or IP
    """
    params = parameters or {}
    action = (params.get("action") or "sentry").lower().strip()
    target = params.get("target", "Unknown").strip()

    if action in ("sentry", "sentry_mode", "arm"):
        return trigger_sentry_mode(player=player)
    elif action in ("lock", "intruder_lock", "intruder_check"):
        return trigger_intruder_lock(intruder_name=target, player=player)
    elif action in ("scan_network", "network", "scan"):
        return scan_local_network(player=player)

    return security_shield_control({"action": "sentry"}, player=player)
