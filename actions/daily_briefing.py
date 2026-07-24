"""
actions/daily_briefing.py — JARVIS Morning & Evening Scheduled Briefing & Routine Engine
Provides Morning Briefing (Weather, Schedule, News, System Telemetry) and Evening Wrap-Up routines.
"""

import datetime
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from actions.weather_report import weather_action
except ImportError:
    weather_action = None

try:
    from actions.email_triage import email_triage
except ImportError:
    email_triage = None

try:
    from actions.calendar_manager import calendar_manager
except ImportError:
    calendar_manager = None


def get_news() -> str:
    try:
        response = requests.get('https://news.google.com/rss?hl=en-IN&gl=IN', timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            headlines = []
            for item in root.findall('./channel/item')[:5]:
                title = item.find('title').text
                headlines.append(title)
            return "Top Google News headlines:\n• " + "\n• ".join(headlines)
        return "Could not fetch headlines at this moment."
    except Exception as e:
        return f"Error fetching news: {e}"


def daily_briefing(parameters: dict, player=None) -> str:
    """
    Compiles Morning or Evening Daily Briefing / Wrap-up Routine.
    parameters:
        action / mode : morning | evening | wrap_up
        city : City for weather (default Delhi)
    """
    params = parameters or {}
    mode = (params.get("action") or params.get("mode") or "").lower().strip()
    hour = datetime.datetime.now().hour

    if not mode:
        if hour < 12:
            mode = "morning"
        elif hour >= 17:
            mode = "evening"
        else:
            mode = "afternoon"

    briefing_parts = []

    if mode == "morning":
        briefing_parts.append("Good morning, Akul. Here is your morning briefing and workstation telemetry.")
    elif mode in ["evening", "wrap_up", "night"]:
        briefing_parts.append("Good evening, Akul. Here is your end-of-day summary and workstation wrap-up.")
    else:
        briefing_parts.append("Here is your daily briefing, Akul.")

    # 1. Weather Report
    city = params.get('city', 'Delhi')
    if weather_action:
        try:
            w_res = weather_action({'city': city}, player=player)
            briefing_parts.append(f"🌤 Weather Status:\n{w_res}")
        except Exception as e:
            briefing_parts.append(f"Weather status: {e}")

    # 2. Calendar Schedule
    if calendar_manager:
        try:
            cal_act = "today" if mode == "morning" else "upcoming"
            c_res = calendar_manager({"action": cal_act}, player=player)
            if c_res and "No events" not in c_res:
                briefing_parts.append(f"📅 Schedule Overview:\n{c_res}")
        except Exception:
            pass

    # 3. Email Triage Overview
    if email_triage:
        try:
            e_res = email_triage(params, player=player)
            if e_res:
                briefing_parts.append(f"✉ Email Triage:\n{e_res}")
        except Exception:
            pass

    # 4. Global News Headlines
    news_res = get_news()
    briefing_parts.append(f"📰 News Intelligence:\n{news_res}")

    if mode in ["wrap_up", "evening", "night"]:
        briefing_parts.append("🌙 System Wrap-Up: Temporary memory caches flushed. Workstation standing by for evening rest.")

    compiled = "\n\n".join(briefing_parts)

    if player and hasattr(player, 'write_log'):
        player.write_log(f"SYS: Compiled {mode.title()} Routine Briefing.")

    return compiled
