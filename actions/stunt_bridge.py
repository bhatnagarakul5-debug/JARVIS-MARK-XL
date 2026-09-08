"""
actions/stunt_bridge.py — JARVIS Mark-XL Bridge for STUNT (Student Tracker)
Connects JARVIS directly to Akul's STUNT database (stunt_database.db).
Provides time-aware college schedule intelligence, 1-click attendance logging,
safe bunk calculations, and a warm, loyal 'Proper Friend' persona.
"""

import os
import sqlite3
import datetime
import math
from pathlib import Path

STUNT_DIR = Path(r"C:\Users\Akul\Desktop\STUNT")
DB_PATH = STUNT_DIR / "stunt_database.db"

def get_stunt_connection():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

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

def stunt_assistant(parameters: dict = None, player=None) -> str:
    """
    JARVIS tool for interacting with STUNT student tracker.
    parameters:
        action: 'get_schedule' | 'get_next_class' | 'log_attendance' | 'bunk_check' | 'attendance_status' | 'college_briefing'
        subject: Subject name (e.g. 'Finance', 'Economics', 'Marketing', 'Business Law')
        status: 'Present' | 'Absent' | 'Cancelled' (defaults to 'Present')
        date: 'YYYY-MM-DD' (defaults to today)
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

    conn = get_stunt_connection()
    if not conn:
        return (
            f"Hey Akul, I couldn't connect to the STUNT database at {DB_PATH}. "
            f"Make sure STUNT is installed on your Desktop, bro!"
        )

    cursor = conn.cursor()

    # 1. Fetch Profile
    cursor.execute("SELECT * FROM profile WHERE id = 1")
    profile_row = cursor.fetchone()
    user_name = profile_row["name"] if profile_row and profile_row["name"] else "Akul"
    college_name = profile_row["college"] if profile_row and profile_row["college"] else "College"
    course_name = profile_row["course"] if profile_row and profile_row["course"] else "Degree"
    target_pct = profile_row["targetAttendancePct"] if profile_row and profile_row["targetAttendancePct"] else 85.0

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
            else:
                return (
                    f"{greeting} You don't have any classes scheduled in your STUNT timetable for {query_day}. "
                    f"If you have lectures today, pop open STUNT and click '+ Add Class Slot' or 'Load Sample Schedule' in the Timetable tab!"
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
    # ACTION: BUNK CHECK
    # ----------------------------------------------------
    if action in ("bunk_check", "safe_bunk", "can_i_bunk", "bunk_calculator"):
        cursor.execute("SELECT * FROM subjects")
        subjects = cursor.fetchall()

        if not subjects:
            conn.close()
            return f"{greeting} You haven't added any subjects to STUNT yet! Add your subjects in STUNT or let me log your first class, and I'll calculate your exact safe bunks."

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
                    f"• Deficit: You must attend the next **{needed} classes consecutively** without missing a single one to get back to {target_pct:.0f}%\n"
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

    return (
        f"{greeting} Here's your college briefing for **{college_name}** ({course_name}):\n"
        f"📅 **Schedule**: {schedule_snippet}\n"
        f"📊 **Overall Attendance**: **{overall_pct:.1f}%** (Target: {target_pct:.0f}%)\n"
        f"🎯 **Tasks**: {len(pending_tasks)} pending. {task_snippet}\n"
        f"I'm here in your corner, bro. Let me know when you want to log attendance or check class timings!"
    )
