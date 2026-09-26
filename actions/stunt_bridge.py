"""
actions/stunt_bridge.py — JARVIS Mark 58 Bridge & Controller for STUNT
Complete Two-Way Voice & Application Control of the STUNT Platform on Akul's Laptop:
1. Application Lifecycle: Launch STUNT desktop app, close STUNT, bring to front, minimize.
2. Tab & Navigation Voice Control: Switch to Dashboard (Ctrl+1), CGPA Ledger (Ctrl+2),
   Syllabus (Ctrl+3), Tasks/Pomodoro (Ctrl+4), Attendance (Ctrl+5), Finances (Ctrl+6),
   Weekly Timetable (Ctrl+7), Memories (Ctrl+8), Milestones (Ctrl+9), Quick Task (Ctrl+T),
   Quick Attendance (Ctrl+A), and College Wingman (Ctrl+J).
3. Live SQLite Database Synchronization: Attendance logging with safe bunk calculations,
   Task creation and completion, Timetable additions and queries, Pomodoro focus sessions,
   Expense/Savings tracking, CGPA forecasting, and Academic transcript generation.
4. Multi-path database resolution: Automatically detects and syncs across Desktop and OneDrive.
"""

import os
import sys
import math
import time
import shutil
import sqlite3
import datetime
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

STUNT_CANDIDATE_DIRS = [
    Path(r"C:\Users\Akul\Desktop\STUNT"),
    Path(r"C:\Users\Akul\OneDrive\Desktop\STUNT"),
]

def get_stunt_paths():
    """Finds the existing STUNT directory and database path."""
    resolved_dir = None
    for d in STUNT_CANDIDATE_DIRS:
        if d.exists():
            resolved_dir = d
            break
    if not resolved_dir:
        resolved_dir = STUNT_CANDIDATE_DIRS[0]

    db_candidates = [
        resolved_dir / "stunt_database.db",
        Path(r"C:\Users\Akul\Desktop\STUNT\stunt_database.db"),
        Path(r"C:\Users\Akul\OneDrive\Desktop\STUNT\stunt_database.db"),
        Path(r"C:\Users\Akul\OneDrive\Desktop\STUNT\_internal\stunt_database.db"),
    ]
    resolved_db = None
    for db_c in db_candidates:
        if db_c.exists():
            resolved_db = db_c
            break
    if not resolved_db:
        resolved_db = resolved_dir / "stunt_database.db"

    return resolved_dir, resolved_db


def sync_secondary_dbs(primary_db: Path):
    """Syncs the updated database to all secondary copies on the laptop."""
    for cand in [
        Path(r"C:\Users\Akul\Desktop\STUNT\stunt_database.db"),
        Path(r"C:\Users\Akul\OneDrive\Desktop\STUNT\stunt_database.db"),
    ]:
        if cand != primary_db and cand.parent.exists():
            try:
                shutil.copy2(str(primary_db), str(cand))
            except Exception:
                pass


def get_stunt_connection():
    _, db_path = get_stunt_paths()
    if not db_path.exists():
        return None, db_path
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn, db_path


def parse_time_to_minutes(time_str: str):
    """Converts a time string like '09:00 AM', '10:30am', '14:00' to minutes from midnight."""
    if not time_str:
        return None
    time_str = time_str.strip().upper()
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M", "%I %p"):
        try:
            dt = datetime.datetime.strptime(time_str, fmt)
            return dt.hour * 60 + dt.minute
        except ValueError:
            pass
    return None


def format_minutes_to_time(minutes: int) -> str:
    h = (minutes // 60) % 24
    m = minutes % 60
    period = "AM" if h < 12 else "PM"
    display_h = h if h <= 12 else h - 12
    if display_h == 0:
        display_h = 12
    return f"{display_h}:{m:02d} {period}"


def get_friend_greeting(user_name: str = "Akul") -> str:
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return f"Morning bro {user_name}! ☀️ Hope you got some decent sleep."
    elif 12 <= hour < 17:
        return f"Hey {user_name}! ⚡ Midday hustle time."
    elif 17 <= hour < 22:
        return f"Evening {user_name}! 🌆 Lectures should be wrapped up for today."
    else:
        return f"Late night grind, {user_name}! 🌙 Don't stay up too late or tomorrow's 9 AM will hurt."


# ====================================================================
# 1. APPLICATION LIFECYCLE & WINDOW CONTROL
# ====================================================================

def is_stunt_running() -> bool:
    try:
        import psutil
        for p in psutil.process_iter(['name', 'cmdline']):
            name = (p.info['name'] or '').lower()
            if 'stunt.exe' in name:
                return True
            cmd = " ".join(p.info['cmdline'] or []).lower()
            if 'stunt' in cmd and 'main.py' in cmd:
                return True
    except Exception:
        pass
    return False


def focus_stunt_window() -> bool:
    """Brings STUNT window to front using WScript.Shell AppActivate and win32gui."""
    try:
        import win32com.client
        w = win32com.client.Dispatch("WScript.Shell")
        if w.AppActivate("STUNT"):
            return True
        if w.AppActivate("Student Tracker"):
            return True
    except Exception:
        pass

    try:
        import win32gui, win32con
        found_hwnd = None
        def cb(hwnd, _):
            nonlocal found_hwnd
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "stunt" in title.lower():
                    found_hwnd = hwnd
        win32gui.EnumWindows(cb, None)
        if found_hwnd:
            win32gui.ShowWindow(found_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(found_hwnd)
            return True
    except Exception:
        pass
    return False


def launch_stunt_app() -> str:
    """Launches the STUNT application on Akul's laptop."""
    stunt_dir, _ = get_stunt_paths()

    if is_stunt_running():
        focus_stunt_window()
        return "STUNT Platform is already active, bro! Brought it right to your front screen."

    # Look for launcher, pythonw, or exe
    exe_path = stunt_dir / "dist" / "STUNT.exe"
    launcher_bat = stunt_dir / "STUNT_Launcher.bat"
    main_py = stunt_dir / "main.py"

    try:
        if exe_path.exists():
            subprocess.Popen([str(exe_path)], cwd=str(stunt_dir), creationflags=subprocess.DETACHED_PROCESS)
        elif launcher_bat.exists():
            subprocess.Popen(["cmd.exe", "/c", str(launcher_bat)], cwd=str(stunt_dir), creationflags=subprocess.DETACHED_PROCESS)
        elif main_py.exists():
            # Use system python or pythonw
            subprocess.Popen(["pythonw", "main.py"], cwd=str(stunt_dir), creationflags=subprocess.DETACHED_PROCESS)
        else:
            return f"Couldn't locate STUNT executable in {stunt_dir}, bro!"

        time.sleep(1.5)
        focus_stunt_window()
        return "🚀 STUNT Platform launched successfully on your laptop, bro! Dashboard is loading."
    except Exception as e:
        return f"Error launching STUNT: {e}"


def close_stunt_app() -> str:
    """Gracefully terminates the STUNT process."""
    try:
        import psutil
        closed_count = 0
        for p in psutil.process_iter(['name', 'cmdline']):
            name = (p.info['name'] or '').lower()
            cmd = " ".join(p.info['cmdline'] or []).lower()
            if 'stunt.exe' in name or ('stunt' in cmd and 'main.py' in cmd):
                p.terminate()
                closed_count += 1
        if closed_count > 0:
            return "STUNT Platform has been closed, bro."
        return "STUNT isn't currently running, bro."
    except Exception as e:
        return f"Could not close STUNT: {e}"


def switch_stunt_tab(target_tab: str) -> str:
    """
    Switches to a specific tab in STUNT using keyboard shortcuts:
    Ctrl+1: Overview Dashboard
    Ctrl+2: Academic CGPA Ledger
    Ctrl+3: Syllabus & Revision Matrix
    Ctrl+4: Tasks & Pomodoro Focus
    Ctrl+5: Attendance & Bunk Calculator
    Ctrl+6: Finance & Savings Goals
    Ctrl+7: Weekly Timetable
    Ctrl+8: Campus Memories Vault
    Ctrl+9: Academic Milestones
    Ctrl+T: Quick Create Task
    Ctrl+A: Quick Log Attendance
    Ctrl+J: College Wingman
    """
    key_map = {
        "dashboard": "1", "overview": "1", "home": "1",
        "cgpa": "2", "grades": "2", "ledger": "2", "gpa": "2",
        "syllabus": "3", "revision": "3", "units": "3",
        "tasks": "4", "pomodoro": "4", "focus": "4", "timer": "4",
        "attendance": "5", "bunk": "5", "bunks": "5", "classes": "5",
        "finances": "6", "finance": "6", "savings": "6", "budget": "6", "money": "6",
        "timetable": "7", "schedule": "7", "routine": "7",
        "memories": "8", "photos": "8", "vault": "8",
        "milestones": "9", "achievements": "9",
        "quick_task": "t",
        "quick_attendance": "a",
        "wingman": "j", "jarvis": "j"
    }

    tab_key = key_map.get(target_tab.lower().strip(), "1")

    # If STUNT isn't running, launch it first
    if not is_stunt_running():
        launch_stunt_app()
        time.sleep(2.0)

    focused = focus_stunt_window()
    time.sleep(0.3)

    try:
        import pyautogui
        pyautogui.hotkey('ctrl', tab_key)
        return f"Switched STUNT to the **{target_tab.title()}** tab on your screen, bro!"
    except Exception:
        # Fallback using WScript SendKeys
        try:
            import win32com.client
            w = win32com.client.Dispatch("WScript.Shell")
            w.SendKeys(f"^{tab_key}")
            return f"Switched STUNT to **{target_tab.title()}**, bro!"
        except Exception as e:
            return f"Focused STUNT window, but couldn't send hotkey: {e}"


# ====================================================================
# 2. MAIN TOOL HANDLER & DISPATCHER
# ====================================================================

def stunt_assistant(parameters: dict = None, player=None) -> str:
    """
    JARVIS tool for controlling the STUNT student tracker desktop app and database.
    parameters:
        action:
            # Application Control:
            - 'launch_app' | 'open_stunt' | 'start_stunt'
            - 'close_app' | 'close_stunt' | 'exit_stunt'
            - 'focus_app' | 'show_stunt' | 'switch_to_stunt'
            - 'switch_tab' (tab: 'dashboard' | 'cgpa' | 'syllabus' | 'tasks' | 'pomodoro' | 'attendance' | 'finances' | 'timetable' | 'memories' | 'milestones')

            # Academic & Attendance Operations:
            - 'log_attendance' (subject, status: 'Present'|'Absent'|'Cancelled', date)
            - 'bunk_check' (subject)
            - 'get_schedule' (day: 'Monday'..'Sunday')
            - 'get_next_class'
            - 'add_task' (title, category, dueDate, dueTime, priority, desc)
            - 'complete_task' (title)
            - 'list_tasks'
            - 'add_timetable_slot' (subject, day, start, end, location, instructor, sem)
            - 'start_pomodoro' (minutes)
            - 'log_expense' (amount, category, desc, type: 'Expense'|'Income')
            - 'add_savings_goal' (title, targetAmount, targetDate, category)
            - 'check_budget'
            - 'get_cgpa'
            - 'export_transcript'
            - 'college_briefing'
    """
    params = parameters or {}
    action = (params.get("action") or "college_briefing").lower().strip()
    target_subject = (params.get("subject") or "").strip()
    status = (params.get("status") or "Present").strip().capitalize()
    if status not in ("Present", "Absent", "Cancelled"):
        status = "Present"

    today = datetime.date.today()
    today_str = params.get("date") or today.isoformat()
    now_dt = datetime.datetime.now()
    now_mins = now_dt.hour * 60 + now_dt.minute
    day_name = now_dt.strftime("%A")

    # ----------------------------------------------------
    # APPLICATION LIFECYCLE & WINDOW ACTIONS
    # ----------------------------------------------------
    if action in ("launch_app", "open_stunt", "start_stunt", "launch_stunt", "run_stunt"):
        return launch_stunt_app()

    if action in ("close_app", "close_stunt", "exit_stunt", "kill_stunt"):
        return close_stunt_app()

    if action in ("focus_app", "show_stunt", "bring_to_front", "switch_to_stunt"):
        if is_stunt_running():
            focus_stunt_window()
            return "Brought STUNT right to the front of your desktop, bro!"
        return launch_stunt_app()

    if action in ("switch_tab", "change_tab", "navigate_tab", "show_tab"):
        tab_name = params.get("tab") or target_subject or "dashboard"
        return switch_stunt_tab(tab_name)

    # ----------------------------------------------------
    # CONNECT TO DATABASE
    # ----------------------------------------------------
    conn, db_path = get_stunt_connection()
    if not conn:
        return (
            f"Hey Akul, I couldn't connect to the STUNT database at {db_path}. "
            f"Make sure STUNT is installed on your Desktop, bro!"
        )

    cursor = conn.cursor()

    # Profile metadata
    cursor.execute("SELECT * FROM profile WHERE id = 1")
    profile_row = cursor.fetchone()
    user_name = profile_row["name"] if profile_row and profile_row["name"] else "Akul"
    college_name = profile_row["college"] if profile_row and profile_row["college"] else "College"
    course_name = profile_row["course"] if profile_row and profile_row["course"] else "Degree"
    target_pct = profile_row["targetAttendancePct"] if profile_row and profile_row["targetAttendancePct"] else 75.0
    budget_cap = profile_row["monthlyBudgetCap"] if profile_row and profile_row["monthlyBudgetCap"] else 5000.0

    greeting = get_friend_greeting(user_name.split()[0])

    # ----------------------------------------------------
    # ACTION: LOG ATTENDANCE
    # ----------------------------------------------------
    if action in ("log_attendance", "mark_attendance", "attendance_log"):
        if not target_subject:
            conn.close()
            return (
                f"{greeting} Which subject did you attend or miss today, bro? "
                f"Tell me something like: 'log attendance in International Finance as Present'."
            )

        cursor.execute("SELECT * FROM subjects")
        subjects = cursor.fetchall()
        matched_sub = None
        for s in subjects:
            if target_subject.lower() in s["name"].lower() or s["name"].lower() in target_subject.lower():
                matched_sub = s
                break

        if not matched_sub:
            sub_id = f"sub-{int(now_dt.timestamp())}"
            sub_name = target_subject.title()
            cursor.execute("""
                INSERT INTO subjects (id, sem, name, code, faculty, targetPct, color)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sub_id, 1, sub_name, sub_name[:6].upper(), "Faculty", target_pct, "#6366f1"))
            conn.commit()
            sub_id_used = sub_id
            sub_name_used = sub_name
        else:
            sub_id_used = matched_sub["id"]
            sub_name_used = matched_sub["name"]

        att_id = f"att-{int(now_dt.timestamp() * 1000)}-{os.urandom(3).hex()}"
        cursor.execute("""
            INSERT INTO attendance_logs (id, sem, subjectId, subjectName, date, status, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (att_id, 1, sub_id_used, sub_name_used, today_str, status, "Logged via JARVIS Voice/Chat"))
        conn.commit()

        cursor.execute("SELECT status FROM attendance_logs WHERE subjectId = ?", (sub_id_used,))
        logs = cursor.fetchall()
        total_classes = len(logs)
        present_count = sum(1 for l in logs if l["status"] == "Present")
        current_pct = (present_count / total_classes * 100.0) if total_classes > 0 else 100.0

        target_decimal = target_pct / 100.0
        safe_bunks = math.floor((present_count - target_decimal * total_classes) / target_decimal) if target_decimal > 0 else 0
        classes_needed = math.ceil((target_decimal * total_classes - present_count) / (1.0 - target_decimal)) if target_decimal < 1.0 else 0

        conn.close()
        sync_secondary_dbs(db_path)

        if status == "Present":
            bunk_note = (
                f"You've got {safe_bunks} safe bunk(s) in reserve."
                if safe_bunks > 0
                else f"⚠️ Careful bro, attendance is at {current_pct:.1f}% (target: {target_pct:.0f}%). Don't bunk next time!"
            )
            return (
                f"{greeting} Logged! ✅ Marked you **Present** in **{sub_name_used}** for today ({today_str}). "
                f"Your attendance is now **{current_pct:.1f}%** ({present_count}/{total_classes} lectures). {bunk_note}"
            )
        elif status == "Absent":
            if safe_bunks >= 0:
                advice = f"You still have {safe_bunks} safe bunk(s) remaining before dipping under {target_pct:.0f}%, but take it easy!"
            else:
                advice = f"🚨 Watch out bro! You are now BELOW your target {target_pct:.0f}%. You must attend the next {classes_needed} classes straight to recover!"
            return (
                f"{greeting} Got it, marked you **Absent / Bunked** ❌ in **{sub_name_used}** for today ({today_str}). "
                f"Attendance dropped to **{current_pct:.1f}%** ({present_count}/{total_classes}). {advice}"
            )
        else:
            return (
                f"{greeting} Logged **{sub_name_used}** as **Cancelled** ⚠️ for today. "
                f"No hit to your attendance percentage ({current_pct:.1f}%)."
            )

    # ----------------------------------------------------
    # ACTION: BUNK CHECK
    # ----------------------------------------------------
    if action in ("bunk_check", "safe_bunk", "can_i_bunk", "bunk_calculator"):
        cursor.execute("SELECT * FROM subjects")
        subjects = cursor.fetchall()

        if not subjects:
            conn.close()
            return f"{greeting} You haven't added any subjects to STUNT yet! Pop open STUNT or let me log your first class."

        matched_sub = None
        if target_subject:
            for s in subjects:
                if target_subject.lower() in s["name"].lower() or s["name"].lower() in target_subject.lower():
                    matched_sub = s
                    break

        if matched_sub:
            cursor.execute("SELECT status FROM attendance_logs WHERE subjectId = ?", (matched_sub["id"],))
            logs = cursor.fetchall()
            total = len(logs)
            presents = sum(1 for l in logs if l["status"] == "Present")
            pct = (presents / total * 100.0) if total > 0 else 100.0
            target_dec = target_pct / 100.0

            safe_bunks = math.floor((presents - target_dec * total) / target_dec) if target_dec > 0 else 0
            needed = math.ceil((target_dec * total - presents) / (1.0 - target_dec)) if target_dec < 1.0 else 0
            conn.close()

            if safe_bunks > 0:
                return (
                    f"{greeting} Here's the verdict on **{matched_sub['name']}**:\n"
                    f"• Current Attendance: **{pct:.1f}%** ({presents}/{total} attended)\n"
                    f"• Target Attendance: **{target_pct:.0f}%**\n"
                    f"• Safe Bunks Remaining: **{safe_bunks} lecture{'s' if safe_bunks > 1 else ''}** ✅\n"
                    f"You have a green light buffer, bro! You can skip if needed, but don't blow through your safety cushion too quickly."
                )
            elif safe_bunks == 0 and pct >= target_pct:
                return (
                    f"{greeting} Careful bro! In **{matched_sub['name']}**, you're at **{pct:.1f}%** ({presents}/{total}). "
                    f"You have **0 safe bunks**! If you miss even ONE single class, your attendance drops below your {target_pct:.0f}% requirement. Sit in class today!"
                )
            else:
                return (
                    f"{greeting} 🚨 RED ALERT BRO! DO NOT BUNK **{matched_sub['name']}**!\n"
                    f"• Current Attendance: **{pct:.1f}%** ({presents}/{total})\n"
                    f"• Target Attendance: **{target_pct:.0f}%**\n"
                    f"• Deficit: You must attend the next **{needed} classes consecutively** to get back to {target_pct:.0f}%\n"
                    f"Get your shoes on and get to lecture hall, professor is taking roll call!"
                )
        else:
            cursor.execute("""
                SELECT s.name, s.targetPct,
                       COUNT(a.id) as total,
                       SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as presents
                FROM subjects s
                LEFT JOIN attendance_logs a ON s.id = a.subjectId
                GROUP BY s.id
            """)
            rows = cursor.fetchall()
            conn.close()

            report = []
            for r in rows:
                tot = r["total"] or 0
                prs = r["presents"] or 0
                pct = (prs / tot * 100.0) if tot > 0 else 100.0
                tgt = r["targetPct"] or target_pct
                tgt_dec = tgt / 100.0
                safe = math.floor((prs - tgt_dec * tot) / tgt_dec) if tgt_dec > 0 else 0
                if safe > 0:
                    status_emoji = f"🟢 ({safe} safe bunks)"
                elif pct >= tgt:
                    status_emoji = "🟡 (0 safe bunks)"
                else:
                    needed = math.ceil((tgt_dec * tot - prs) / (1.0 - tgt_dec)) if tgt_dec < 1.0 else 0
                    status_emoji = f"🔴 (Need +{needed} classes)"
                report.append(f"• **{r['name']}**: {pct:.1f}% {status_emoji}")

            return (
                f"{greeting} Here is your complete Bunk & Attendance Audit across all subjects:\n"
                + "\n".join(report) + "\n"
                f"Keep that attendance above {target_pct:.0f}% so you stay eligible for finals with zero stress!"
            )

    # ----------------------------------------------------
    # ACTION: GET SCHEDULE
    # ----------------------------------------------------
    if action in ("get_schedule", "timetable", "today_schedule", "schedule"):
        query_day = params.get("day") or day_name
        cursor.execute("SELECT * FROM timetable WHERE LOWER(day) = LOWER(?) ORDER BY start", (query_day,))
        slots = cursor.fetchall()
        conn.close()

        if not slots:
            if query_day.lower() in ("saturday", "sunday"):
                return f"{greeting} It's {query_day}, bro! 🎉 Zero lectures scheduled in your timetable. Enjoy your weekend or catch up on your side projects!"
            return (
                f"{greeting} You don't have any classes scheduled in your STUNT timetable for {query_day}. "
                f"Pop open STUNT and click '+ Add Class Slot' in the Timetable tab!"
            )

        schedule_items = []
        for s in slots:
            sub = s["subject"]
            time_span = f"{s['start']} - {s['end']}"
            loc = f" at {s['location']}" if s["location"] else ""
            inst = f" ({s['instructor']})" if s["instructor"] else ""
            schedule_items.append(f"• **{sub}**: {time_span}{loc}{inst}")

        classes_list = "\n".join(schedule_items)
        return (
            f"{greeting} Here's your lecture lineup for **{query_day}** ({len(slots)} class{'es' if len(slots) > 1 else ''}):\n"
            f"{classes_list}\n"
            f"Want me to log attendance for any of these once they wrap up?"
        )

    # ----------------------------------------------------
    # ACTION: GET NEXT CLASS
    # ----------------------------------------------------
    if action in ("get_next_class", "next_class", "next_lecture"):
        cursor.execute("SELECT * FROM timetable WHERE LOWER(day) = LOWER(?)", (day_name,))
        slots = cursor.fetchall()
        conn.close()

        if not slots:
            return f"{greeting} No classes scheduled for today ({day_name}), bro! You're completely free."

        active_slot = None
        next_slot = None
        min_diff = 999999

        for s in slots:
            start_m = parse_time_to_minutes(s["start"])
            end_m = parse_time_to_minutes(s["end"])
            if start_m is None or end_m is None:
                continue

            if start_m <= now_mins <= end_m:
                active_slot = s
                break

            diff = start_m - now_mins
            if 0 < diff < min_diff:
                min_diff = diff
                next_slot = s

        if active_slot:
            end_m = parse_time_to_minutes(active_slot["end"])
            rem = (end_m - now_mins) if end_m else 0
            loc = f" in {active_slot['location']}" if active_slot['location'] else ""
            inst = f" with {active_slot['instructor']}" if active_slot['instructor'] else ""
            return (
                f"{greeting} You're currently in **{active_slot['subject']}**{loc}{inst}! "
                f"Class wraps up at {active_slot['end']} (about {rem} minutes remaining). "
                f"Hang in there bro, pay attention or take sneaky notes!"
            )
        elif next_slot:
            loc = f" in {next_slot['location']}" if next_slot['location'] else ""
            inst = f" with {next_slot['instructor']}" if next_slot['instructor'] else ""
            hours = min_diff // 60
            mins = min_diff % 60
            countdown = f"{hours}h {mins}m" if hours > 0 else f"{mins} minutes"
            return (
                f"{greeting} Next up is **{next_slot['subject']}** at **{next_slot['start']}**{loc}{inst}. "
                f"Starts in **{countdown}**. Don't be late!"
            )
        else:
            return (
                f"{greeting} All your lectures for today ({day_name}) are officially finished! 🎓 "
                f"Great job making it through the day. Time to kick back or crush some tasks."
            )

    # ----------------------------------------------------
    # ACTION: ADD TASK
    # ----------------------------------------------------
    if action in ("add_task", "create_task", "new_task"):
        task_title = params.get("title") or target_subject or "College Assignment"
        category = params.get("category") or "Assignment"
        due_date = params.get("dueDate") or params.get("due_date") or today.isoformat()
        due_time = params.get("dueTime") or params.get("due_time") or "23:59"
        priority = (params.get("priority") or "Medium").capitalize()
        desc = params.get("desc") or "Added via JARVIS Voice"

        task_id = f"task-{int(now_dt.timestamp() * 1000)}"
        cursor.execute("""
            INSERT INTO tasks (id, title, category, dueDate, dueTime, priority, status, desc)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)
        """, (task_id, task_title, category, due_date, due_time, priority, desc))
        conn.commit()
        conn.close()
        sync_secondary_dbs(db_path)

        return f"{greeting} Added new task to STUNT! 🎯 **{task_title}** [{category}] due on **{due_date}** at {due_time} ({priority} Priority)."

    # ----------------------------------------------------
    # ACTION: COMPLETE TASK
    # ----------------------------------------------------
    if action in ("complete_task", "finish_task", "mark_task_completed"):
        task_title = params.get("title") or target_subject
        if not task_title:
            conn.close()
            return f"{greeting} Which task did you finish, bro?"

        cursor.execute("SELECT * FROM tasks WHERE status != 'Completed' AND LOWER(title) LIKE LOWER(?)", (f"%{task_title}%",))
        t_row = cursor.fetchone()
        if t_row:
            cursor.execute("UPDATE tasks SET status = 'Completed' WHERE id = ?", (t_row["id"],))
            conn.commit()
            conn.close()
            sync_secondary_dbs(db_path)
            return f"{greeting} Fantastic work, bro! 🎉 Marked task **'{t_row['title']}'** as **Completed** in STUNT. XP points awarded!"
        conn.close()
        return f"{greeting} Couldn't find a pending task matching '{task_title}' in STUNT, bro."

    # ----------------------------------------------------
    # ACTION: LIST TASKS
    # ----------------------------------------------------
    if action in ("list_tasks", "get_tasks", "tasks", "pending_tasks"):
        cursor.execute("SELECT * FROM tasks WHERE status != 'Completed' ORDER BY dueDate, dueTime")
        tasks = cursor.fetchall()
        conn.close()

        if not tasks:
            return f"{greeting} Clean slate! You don't have any pending tasks or assignments in STUNT right now. 🚀"

        t_lines = []
        for t in tasks:
            due = f" (Due {t['dueDate']})" if t['dueDate'] else ""
            prio = f" [{t['priority']}]" if t['priority'] else ""
            t_lines.append(f"• **{t['title']}** - {t['category']}{due}{prio}")

        return f"{greeting} Here are your pending STUNT tasks ({len(tasks)} items):\n" + "\n".join(t_lines)

    # ----------------------------------------------------
    # ACTION: ADD TIMETABLE SLOT
    # ----------------------------------------------------
    if action in ("add_timetable_slot", "add_class", "add_lecture"):
        sub_name = target_subject or params.get("name") or "New Lecture"
        slot_day = params.get("day") or day_name
        start_t = params.get("start") or "09:00 AM"
        end_t = params.get("end") or "10:30 AM"
        loc = params.get("location") or "Lecture Hall"
        instructor = params.get("instructor") or "Professor"
        sem = params.get("sem") or 1

        slot_id = f"tt-{int(now_dt.timestamp() * 1000)}"
        cursor.execute("""
            INSERT INTO timetable (id, sem, day, subject, start, end, location, instructor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (slot_id, sem, slot_day.capitalize(), sub_name.title(), start_t, end_t, loc, instructor))
        conn.commit()
        conn.close()
        sync_secondary_dbs(db_path)

        return f"{greeting} Added to your STUNT timetable! 📅 **{sub_name.title()}** on **{slot_day.capitalize()}** from {start_t} to {end_t} in {loc}."

    # ----------------------------------------------------
    # ACTION: START POMODORO FOCUS SESSION
    # ----------------------------------------------------
    if action in ("start_pomodoro", "pomodoro", "focus_session"):
        switch_stunt_tab("pomodoro")
        return f"{greeting} Pomodoro focus mode activated in STUNT! ⏱️ 25 minutes on the clock. Put your phone on silent, eliminate distractions, and let's crush this session!"

    # ----------------------------------------------------
    # ACTION: LOG EXPENSE / INCOME
    # ----------------------------------------------------
    if action in ("log_expense", "log_income", "add_transaction"):
        amount = float(params.get("amount") or 0.0)
        ftype = "Income" if "income" in action else "Expense"
        category = params.get("category") or ("General" if ftype == "Expense" else "Allowance")
        desc = params.get("desc") or target_subject or "Logged via JARVIS"

        fin_id = f"fin-{int(now_dt.timestamp() * 1000)}"
        cursor.execute("""
            INSERT INTO finances (id, type, category, amount, desc, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (fin_id, ftype, category, amount, desc, today_str))
        conn.commit()
        conn.close()
        sync_secondary_dbs(db_path)

        return f"{greeting} Logged {ftype} in STUNT Ledger: 💰 **₹{amount:,.2f}** for **{desc}** [{category}]."

    # ----------------------------------------------------
    # ACTION: ADD SAVINGS GOAL
    # ----------------------------------------------------
    if action in ("add_savings_goal", "new_savings_goal", "save_goal"):
        goal_title = params.get("title") or target_subject or "Savings Goal"
        target_amt = float(params.get("targetAmount") or params.get("amount") or 5000.0)
        target_date = params.get("targetDate") or (today + datetime.timedelta(days=90)).isoformat()
        category = params.get("category") or "Tech"

        sg_id = f"sg-{int(now_dt.timestamp() * 1000)}"
        cursor.execute("""
            INSERT INTO savings_goals (id, title, targetAmount, currentSaved, targetDate, category, notes)
            VALUES (?, ?, ?, 0.0, ?, ?, 'Created via JARVIS')
        """, (sg_id, goal_title, target_amt, target_date, category))
        conn.commit()
        conn.close()
        sync_secondary_dbs(db_path)

        return f"{greeting} New savings goal set in STUNT! 🎯 **{goal_title}** — Target: **₹{target_amt:,.2f}** by {target_date}."

    # ----------------------------------------------------
    # ACTION: CHECK BUDGET
    # ----------------------------------------------------
    if action in ("check_budget", "budget_status", "monthly_budget"):
        month_prefix = today.strftime("%Y-%m")
        cursor.execute("SELECT SUM(amount) FROM finances WHERE type = 'Expense' AND date LIKE ?", (f"{month_prefix}%",))
        spent = cursor.fetchone()[0] or 0.0
        rem = budget_cap - spent
        conn.close()

        status_msg = (
            f"You have **₹{rem:,.2f}** remaining this month. Safe zone!"
            if rem >= 0
            else f"⚠️ Budget exceeded by **₹{abs(rem):,.2f}**! Ease up on unnecessary expenses, bro."
        )
        return (
            f"{greeting} Monthly Budget Status for **{today.strftime('%B %Y')}**:\n"
            f"• Spending Cap: **₹{budget_cap:,.2f}**\n"
            f"• Spent so far: **₹{spent:,.2f}**\n"
            f"• {status_msg}"
        )

    # ----------------------------------------------------
    # ACTION: CGPA / SGPA STATUS
    # ----------------------------------------------------
    if action in ("get_cgpa", "cgpa_status", "grades", "sgpa"):
        cursor.execute("SELECT * FROM grades ORDER BY sem ASC")
        grades = cursor.fetchall()
        target_cgpa = profile_row["targetCgpa"] if profile_row and profile_row["targetCgpa"] else 8.5
        total_sems = profile_row["totalSemesters"] if profile_row and profile_row["totalSemesters"] else 10

        if not grades:
            conn.close()
            return f"{greeting} No semester grades logged in STUNT yet! Target CGPA is set to **{target_cgpa:.1f}**. Pop open STUNT (Ctrl+2) to log grades!"

        sem_map = {}
        for g in grades:
            s = g["sem"]
            c = g["credits"]
            gp = g["gradePoints"]
            sem_map.setdefault(s, {"credits": 0, "points": 0})
            sem_map[s]["credits"] += c
            sem_map[s]["points"] += (c * gp)

        tot_pts = sum(v["points"] for v in sem_map.values())
        tot_creds = sum(v["credits"] for v in sem_map.values())
        current_cgpa = (tot_pts / tot_creds) if tot_creds > 0 else 0.0
        sems_done = len(sem_map)
        sems_rem = max(total_sems - sems_done, 0)

        pred_msg = ""
        if sems_rem > 0:
            req_sgpa = (target_cgpa * total_sems - (current_cgpa * sems_done)) / sems_rem
            if req_sgpa <= 10.0:
                pred_msg = f"To graduate with **{target_cgpa:.1f} CGPA**, you need an average SGPA of **{max(req_sgpa, 0.0):.2f}** across remaining {sems_rem} semesters."
            else:
                pred_msg = f"Mathematically, achieving {target_cgpa:.1f} would require >10.0 SGPA. Aim for maximum SGPA to get as close as possible!"

        conn.close()
        return (
            f"{greeting} Academic CGPA Summary:\n"
            f"• Current CGPA: **{current_cgpa:.2f}** ({sems_done}/{total_sems} semesters logged, {tot_creds} credits)\n"
            f"• Target CGPA: **{target_cgpa:.1f}**\n"
            f"• {pred_msg}"
        )

    # ----------------------------------------------------
    # ACTION: EXPORT ACADEMIC TRANSCRIPT
    # ----------------------------------------------------
    if action in ("export_transcript", "generate_transcript"):
        cursor.execute("SELECT * FROM grades ORDER BY sem ASC")
        grades = cursor.fetchall()
        cursor.execute("SELECT * FROM tasks WHERE status = 'Completed'")
        done_tasks = len(cursor.fetchall())
        cursor.execute("SELECT status FROM attendance_logs")
        att = cursor.fetchall()
        prs = sum(1 for a in att if a["status"] == "Present")
        pct = (prs / len(att) * 100.0) if att else 100.0
        conn.close()

        from actions.file_generator import create_word_document
        out_dir = Path.home() / "OneDrive" / "Desktop" if (Path.home() / "OneDrive" / "Desktop").exists() else Path.home() / "Desktop"
        doc_res = create_word_document(
            filename="STUNT_Academic_Transcript.docx",
            title=f"Academic & Degree Transcript — {user_name}",
            subtitle=f"{college_name} • {course_name} • Generated by J.A.R.V.I.S.",
            sections=[
                {"heading": "1. Degree Overview", "content": f"Student: {user_name}\nInstitution: {college_name}\nProgram: {course_name}"},
                {"heading": "2. Attendance & Conduct", "content": f"Overall Attendance: {pct:.1f}% ({prs}/{len(att)} sessions attended).\nTasks Completed: {done_tasks} items."},
                {"heading": "3. Grades Ledger", "content": f"Total courses evaluated: {len(grades)} subjects."}
            ],
            output_dir=out_dir,
            open_after=True
        )
        return f"{greeting} Exported your full STUNT Academic Transcript to Word! 📄 Saved on Desktop: {doc_res}"

    # ----------------------------------------------------
    # ACTION: COLLEGE BRIEFING (DEFAULT)
    # ----------------------------------------------------
    cursor.execute("SELECT * FROM timetable WHERE LOWER(day) = LOWER(?) ORDER BY start", (day_name,))
    today_slots = cursor.fetchall()

    cursor.execute("SELECT status FROM attendance_logs")
    all_att = cursor.fetchall()
    overall_pct = (sum(1 for a in all_att if a["status"] == "Present") / len(all_att) * 100.0) if all_att else 100.0

    cursor.execute("SELECT * FROM tasks WHERE status != 'Completed' ORDER BY dueDate, dueTime")
    pending_tasks = cursor.fetchall()
    conn.close()

    schedule_snippet = ""
    if today_slots:
        schedule_snippet = f"You have **{len(today_slots)} lecture{'s' if len(today_slots) > 1 else ''}** today ({day_name}). First class is **{today_slots[0]['subject']}** at {today_slots[0]['start']}."
    else:
        schedule_snippet = f"No classes scheduled for today ({day_name})! Enjoy the breathing room."

    task_snippet = ""
    if pending_tasks:
        top_task = pending_tasks[0]
        due = f" (due {top_task['dueDate']})" if top_task["dueDate"] else ""
        task_snippet = f"Top priority task: **{top_task['title']}**{due}."
    else:
        task_snippet = "No urgent assignments or tasks pending. Clean slate!"

    stunt_status = "🟢 Active" if is_stunt_running() else "⚪ Offline (Say 'Open STUNT' to launch)"

    return (
        f"{greeting} Here's your college briefing for **{college_name}** ({course_name}):\n"
        f"🖥️ **STUNT Platform**: {stunt_status}\n"
        f"📅 **Schedule**: {schedule_snippet}\n"
        f"📊 **Overall Attendance**: **{overall_pct:.1f}%** (Target: {target_pct:.0f}%)\n"
        f"🎯 **Tasks**: {len(pending_tasks)} pending. {task_snippet}\n"
        f"Say **'Open STUNT'**, **'Show Timetable'**, **'Log Attendance'**, or **'Can I bunk'** whenever you're ready!"
    )
