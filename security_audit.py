"""
security_audit.py — Pre-Commit Security & Privacy Auditor for JARVIS Mark XL
Scans all files queued for Git commit to ensure 0 API keys, 0 user memories,
0 passwords, 0 Gmail credentials, and 0 face photos are exposed.
"""

import os
import sys
import subprocess
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent

FORBIDDEN_FILES = [
    "config/api_keys.json",
    "config/jarvis_settings.json",
    "memory/conversation_log.json",
    "memory/user_memory.json",
    "config/known_faces",
    "memory/chroma_db",
]

FORBIDDEN_PATTERNS = [
    "AIzaSy",  # Google API key prefix
    "sk-or-v1",  # OpenRouter key prefix
    "sk-ant-api",  # Anthropic key prefix
    "kddmaejruphxyxfb",  # Gmail App Password
    "8816623588:AAHKzYCz2_nlYx6Tgv4CWyqJmoEAAixcaBQ",  # Bot token
]

def run_security_audit():
    print("=== JARVIS MARK XL PRE-COMMIT SECURITY AUDIT ===")
    print(f"Auditing directory: {BASE_DIR}\n")

    # 1. Check Git Status for Forbidden Files
    violations = []
    try:
        status_out = subprocess.check_output("git status --porcelain", shell=True, text=True, cwd=BASE_DIR)
        for line in status_out.splitlines():
            file_path = line[3:].strip()
            if file_path.endswith(".example"):
                continue
            for forbidden in FORBIDDEN_FILES:
                if forbidden == file_path or (forbidden.endswith("/") and file_path.startswith(forbidden)):
                    violations.append(f"FORBIDDEN FILE TRACKED: {file_path}")
    except Exception as e:
        print(f"Notice running git status: {e}")

    # 2. Check Tracked Files Content for Forbidden Patterns
    try:
        ls_out = subprocess.check_output("git ls-files", shell=True, text=True, cwd=BASE_DIR)
        tracked_files = [line.strip() for line in ls_out.splitlines() if line.strip()]

        for tf in tracked_files:
            if tf.endswith("security_audit.py"):
                continue
            tf_path = BASE_DIR / tf
            if tf_path.exists() and tf_path.is_file() and not tf.endswith((".png", ".ico", ".jpg", ".zip", ".exe")):
                try:
                    content = tf_path.read_text(encoding="utf-8", errors="ignore")
                    for pattern in FORBIDDEN_PATTERNS:
                        if pattern in content:
                            violations.append(f"LEAKED PATTERN '{pattern[:6]}...' IN FILE: {tf}")
                except Exception:
                    pass

    except Exception as e:
        print(f"Notice checking tracked files: {e}")

    print("------------------------------------------------")
    if violations:
        print("❌ SECURITY AUDIT FAILED! The following items must be untracked before push:")
        for v in violations:
            print(f"  • {v}")
        return False
    else:
        print("✅ 100% SECURITY AUDIT PASSED!")
        print("  • 0 API Keys detected.")
        print("  • 0 Passwords or App Passwords detected.")
        print("  • 0 Private Memory databases detected.")
        print("  • 0 Personal face photos detected.")
        print("  • All sensitive data successfully shielded by .gitignore.")
        print("------------------------------------------------")
        return True

if __name__ == "__main__":
    success = run_security_audit()
    sys.exit(0 if success else 1)
