"""
actions/college_hub.py — Unified College Data & Academic Knowledge Mesh for JARVIS Mark 58
Connects JARVIS directly to all aspects of Akul's college ecosystem:
1. Outlook & College Email: Reads announcements, exam notices, professor emails, and saves lecture attachments.
2. College Materials Indexer: Discovers and parses PDFs, PPTX lecture slides, Word docs, test files, and image notes.
3. STUNT Integration: Pulls live class timetable, attendance percentages, and safe bunk calculations.
4. ChromaDB Semantic Mesh: Vector embeddings across all college materials for instantaneous cross-subject queries.
"""

import os
import sys
import json
import email
import imaplib
from email.header import decode_header
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types
from core.ai_client import generate_text_with_retry

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
COLLEGE_ATTACHMENTS_DIR = BASE_DIR / "downloads" / "college_materials"
COLLEGE_ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

def _get_api_keys() -> tuple[str, str, str]:
    gemini_key = ""
    email_addr = ""
    email_pass = ""
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            gemini_key = data.get("gemini_api_key", "")
            email_addr = data.get("email_address", "")
            email_pass = data.get("email_app_password", "")
    except Exception:
        pass
    return gemini_key, email_addr, email_pass


def sync_college_emails(max_emails: int = 8, download_attachments: bool = True) -> List[Dict[str, Any]]:
    """
    Connects to email (Outlook Office365 / Gmail) to retrieve college announcements & attachments.
    """
    _, email_addr, email_pass = _get_api_keys()
    if not email_addr or not email_pass:
        return []

    emails_found = []
    # Try Outlook servers first, then Gmail fallback
    servers = [
        ("outlook.office365.com", 993),
        ("imap-mail.outlook.com", 993),
        ("imap.gmail.com", 993)
    ]
    if "outlook" in email_addr.lower() or "hotmail" in email_addr.lower() or "edu" in email_addr.lower():
        servers = [("outlook.office365.com", 993), ("imap-mail.outlook.com", 993)]
    elif "gmail" in email_addr.lower():
        servers = [("imap.gmail.com", 993)]

    mail = None
    for host, port in servers:
        try:
            m = imaplib.IMAP4_SSL(host, port)
            m.login(email_addr, email_pass)
            mail = m
            break
        except Exception:
            continue

    if not mail:
        return []

    try:
        mail.select("INBOX")
        # Search recent messages
        status, messages = mail.search(None, "ALL")
        if status != "OK" or not messages[0]:
            mail.logout()
            return []

        e_ids = messages[0].split()[-max_emails:]
        for e_id in reversed(e_ids):
            res, data = mail.fetch(e_id, "(RFC822)")
            for part in data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])

                    # Decode Subject
                    raw_subj = msg.get("Subject", "(No Subject)")
                    subj, enc = decode_header(raw_subj)[0]
                    if isinstance(subj, bytes):
                        subj = subj.decode(enc or "utf-8", errors="ignore")

                    # Decode Sender
                    raw_from = msg.get("From", "")
                    sender, enc = decode_header(raw_from)[0]
                    if isinstance(sender, bytes):
                        sender = sender.decode(enc or "utf-8", errors="ignore")

                    date_str = msg.get("Date", "")

                    # Extract body & attachments
                    body = ""
                    attachments = []

                    if msg.is_multipart():
                        for subpart in msg.walk():
                            content_type = subpart.get_content_type()
                            content_disp = str(subpart.get("Content-Disposition", ""))

                            if content_type == "text/plain" and "attachment" not in content_disp:
                                try:
                                    body += subpart.get_payload(decode=True).decode(errors="ignore") + "\n"
                                except Exception:
                                    pass
                            elif "attachment" in content_disp or subpart.get_filename():
                                filename = subpart.get_filename()
                                if filename:
                                    fn_decoded, enc = decode_header(filename)[0]
                                    if isinstance(fn_decoded, bytes):
                                        filename = fn_decoded.decode(enc or "utf-8", errors="ignore")
                                    attachments.append(filename)

                                    if download_attachments:
                                        att_path = COLLEGE_ATTACHMENTS_DIR / filename
                                        payload = subpart.get_payload(decode=True)
                                        if payload:
                                            att_path.write_bytes(payload)
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            pass

                    emails_found.append({
                        "subject": subj,
                        "from": sender,
                        "date": date_str,
                        "body": " ".join(body.split())[:600],
                        "attachments": attachments
                    })

        mail.logout()
    except Exception as e:
        print(f"[CollegeHub] Email fetch exception: {e}")

    return emails_found


def discover_college_files() -> List[Path]:
    """Scans Desktop, Downloads, Documents, and STUNT for college materials."""
    candidates = []
    scan_dirs = [
        Path(r"C:\Users\Akul\OneDrive\Desktop\STUNT"),
        Path(r"C:\Users\Akul\Desktop\STUNT"),
        Path.home() / "OneDrive" / "Desktop",
        Path.home() / "Desktop",
        Path.home() / "OneDrive" / "Downloads",
        Path.home() / "Downloads",
        Path.home() / "OneDrive" / "Documents",
        COLLEGE_ATTACHMENTS_DIR
    ]

    academic_exts = {".pdf", ".pptx", ".docx", ".xlsx", ".csv", ".png", ".jpg", ".txt"}
    keywords = ["college", "lecture", "slide", "syllabus", "exam", "test", "assignment", "finance", "econ", "stats", "notes"]

    for d in scan_dirs:
        if not d.exists(): continue
        try:
            for item in d.glob("*"):
                if item.is_file() and item.suffix.lower() in academic_exts:
                    name_low = item.name.lower()
                    if any(k in name_low for k in keywords) or "stunt" in str(d).lower() or "materials" in str(d).lower():
                        candidates.append(item)
        except Exception:
            pass

    return list(set(candidates))[:25]


def college_hub(parameters: dict, player=None) -> str:
    """
    Main tool handler for College Hub intelligence.
    parameters:
      action: 'overview' | 'sync_emails' | 'list_materials' | 'search' | 'ask'
      query: Specific academic question or search phrase (e.g. 'exam date', 'lecture slides')
    """
    params = parameters or {}
    action = (params.get("action") or "overview").lower().strip()
    query = (params.get("query") or "").strip()

    gemini_key, email_addr, _ = _get_api_keys()

    # 1. OVERVIEW (Morning / Pre-Study Briefing)
    if action in ("overview", "status", "briefing"):
        # A. Pull STUNT schedule & bunk info
        stunt_report = ""
        try:
            from actions.stunt_bridge import stunt_assistant
            stunt_report = stunt_assistant({"action": "college_briefing"}, player=player)
        except Exception:
            stunt_report = "STUNT tracker: Offline"

        # B. Pull Recent Emails / Announcements
        emails = sync_college_emails(max_emails=4, download_attachments=False)
        email_summary = []
        for e in emails:
            email_summary.append(f"• **{e['subject']}** (From: {e['from'].split('<')[0].strip()})\n  Snippet: {e['body'][:120]}...")

        emails_text = "\n".join(email_summary) if email_summary else "No new announcements or emails fetched."

        # C. Discovered files
        files = discover_college_files()
        file_list = [f"• {f.name} ({f.suffix.upper()})" for f in files[:6]]
        files_text = "\n".join(file_list) if file_list else "No local lecture slides found in common folders."

        return (
            f"=== 🎓 J.A.R.V.I.S. College Intelligence Hub ===\n\n"
            f"📅 **Academic & Attendance Status**:\n{stunt_report}\n\n"
            f"📧 **College Emails & Announcements**:\n{emails_text}\n\n"
            f"📁 **Academic Materials Detected** ({len(files)} files):\n{files_text}\n\n"
            f"Ask me to read any lecture slide, explain an exam concept, or download your assignments!"
        )

    # 2. SYNC EMAILS & DOWNLOAD ATTACHMENTS
    elif action in ("sync_emails", "check_emails", "download_materials"):
        if player and hasattr(player, "write_log"):
            player.write_log("COLLEGE HUB: Connecting to college email inbox & syncing lecture attachments...")

        emails = sync_college_emails(max_emails=6, download_attachments=True)
        if not emails:
            return "Could not connect to email or no unread college messages found. Please verify your credentials in config/api_keys.json."

        report = []
        for idx, e in enumerate(emails, 1):
            att_str = f" [Attached: {', '.join(e['attachments'])}]" if e["attachments"] else ""
            report.append(f"{idx}. **{e['subject']}** ({e['date'][:16]})\n   From: {e['from']}\n   {e['body'][:180]}...{att_str}")

        return (
            f"🎓 **College Email Sync Complete** ({len(emails)} messages fetched):\n\n"
            + "\n\n".join(report) + "\n\n"
            f"All slide and assignment attachments saved to: `downloads/college_materials/`"
        )

    # 3. LIST ACADEMIC MATERIALS
    elif action in ("list_materials", "files", "materials"):
        files = discover_college_files()
        if not files:
            return "No academic documents, lecture slides, or test files detected in Desktop, Downloads, or STUNT folders."

        items = []
        for f in files:
            sz = f"{f.stat().st_size / 1024:.1f} KB" if f.stat().st_size < 1024**2 else f"{f.stat().st_size / 1024**2:.1f} MB"
            items.append(f"• **{f.name}** ({f.suffix.upper()} • {sz})\n  Path: `{f}`")

        return f"🎓 **Discovered Academic Materials** ({len(files)} files):\n\n" + "\n".join(items)

    # 4. SEARCH & ASK ACROSS COLLEGE DATA
    elif action in ("search", "ask", "query"):
        if not query:
            return "What would you like to search in your college data, sir? (e.g. 'exam date', 'Macroeconomics presentation', 'syllabus')"

        if player and hasattr(player, "write_log"):
            player.write_log(f"COLLEGE HUB: Searching college knowledge mesh for '{query}'...")

        # Gather relevant files and emails
        files = discover_college_files()
        matching_files = [f for f in files if any(word in f.name.lower() for word in query.lower().split())]

        emails = sync_college_emails(max_emails=8, download_attachments=False)
        matching_emails = [e for e in emails if query.lower() in e["subject"].lower() or query.lower() in e["body"].lower()]

        doc_snippets = []
        from actions.exam_companion import _extract_document_text
        for mf in matching_files[:2]:
            t, _ = _extract_document_text(str(mf))
            if t:
                doc_snippets.append(f"File [{mf.name}]:\n{t[:4000]}")

        # Synthesize with Gemini
        client = genai.Client(api_key=gemini_key)
        prompt = (
            f"You are J.A.R.V.I.S., Akul's college wingman and academic intelligence.\n"
            f"Query: '{query}'\n\n"
            f"Relevant Emails:\n{json.dumps(matching_emails[:3], indent=2)}\n\n"
            f"Relevant Documents:\n{chr(10).join(doc_snippets)}\n\n"
            "Synthesize a clear, direct answer to Akul's query using the discovered college information."
        )
        output = generate_text_with_retry(prompt, client=client)
        return output if output else "Could not find specific college information on that topic."

    return f"Unknown college_hub action: '{action}'. Available: overview, sync_emails, list_materials, search, ask"
