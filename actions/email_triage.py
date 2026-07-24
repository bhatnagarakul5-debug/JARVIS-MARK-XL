import imaplib
import email
from email.header import decode_header
import json
import sys
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def _get_email_credentials():
    try:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("email_address"), data.get("email_app_password")
    except Exception:
        return None, None

def _clean_text(text: str) -> str:
    if not text: return ""
    return " ".join(text.split())[:300] # Limit size for token efficiency

def email_triage(parameters: dict, player=None) -> str:
    """
    Connects to email via IMAP to read unread messages and summarizes them.
    Requires 'email_address' and 'email_app_password' in config/api_keys.json
    """
    email_user, email_pass = _get_email_credentials()
    
    if not email_user or not email_pass:
        return (
            "Email credentials not found. Please add 'email_address' and "
            "'email_app_password' to your config/api_keys.json file."
        )

    try:
        if player:
            player.write_log("SYS: Connecting to email server...")
            
        # Default to Gmail IMAP, could be made configurable later
        imap_server = "imap.gmail.com"
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return "Failed to search for unread emails."

        email_ids = messages[0].split()
        if not email_ids:
            return "Inbox is clear. You have no unread emails."

        # Process the last 5 unread emails
        recent_ids = email_ids[-5:]
        results = []

        for e_id in recent_ids:
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode Subject
                    raw_subject = msg.get("Subject", "(No Subject)")
                    if raw_subject is None:
                        raw_subject = "(No Subject)"
                    subject, encoding = decode_header(raw_subject)[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                        
                    # Decode Sender
                    from_header, encoding = decode_header(msg.get("From", ""))[0]
                    if isinstance(from_header, bytes):
                        from_header = from_header.decode(encoding if encoding else "utf-8", errors="ignore")

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                                except Exception:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            pass

                    results.append(
                        f"From: {from_header}\n"
                        f"Subject: {subject}\n"
                        f"Preview: {_clean_text(body)}\n"
                        f"---"
                    )

        mail.logout()
        
        final_report = f"Found {len(email_ids)} unread emails. Here are the latest {len(results)}:\n\n" + "\n".join(results)
        
        if player:
            player.write_log(f"SYS: Fetched {len(email_ids)} unread emails.")
            
        return final_report

    except imaplib.IMAP4.error as e:
        return f"IMAP authentication failed. Are you sure you used an App Password? Error: {e}"
    except Exception as e:
        return f"Email triage failed: {e}"
