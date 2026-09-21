"""
actions/file_watcher.py — Smart Downloads & Desktop File Watcher for JARVIS Mark XLII
Monitors the Downloads directory in real time for newly downloaded files.
Auto-organizes new files, parses documents/PDFs, and notifies the user via HUD log and Telegram!
"""

import os
import time
import shutil
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_downloads_dir() -> Path:
    candidates = [
        Path.home() / "OneDrive" / "Downloads",
        Path.home() / "Downloads"
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path.home() / "Downloads"


class SmartFileWatcher:
    """Real-time Downloads Folder Monitor & Auto-Organizer."""

    def __init__(self):
        self.is_running = False
        self.seen_files = set()
        self.downloads_dir = _get_downloads_dir()

    def start_watcher(self, player=None):
        """Starts background file watcher thread."""
        if self.is_running:
            return
        self.is_running = True

        # Pre-seed existing files so we only react to newly downloaded files
        if self.downloads_dir.exists():
            try:
                self.seen_files = set(f.name for f in self.downloads_dir.iterdir() if f.is_file())
            except Exception:
                pass

        def _watcher_loop():
            while self.is_running:
                time.sleep(4)  # Poll every 4 seconds
                try:
                    if not self.downloads_dir.exists():
                        continue

                    current_files = set(f.name for f in self.downloads_dir.iterdir() if f.is_file())
                    new_files = current_files - self.seen_files

                    for fname in new_files:
                        fpath = self.downloads_dir / fname
                        # Ignore partial downloads (.crdownload, .tmp, .part)
                        if fpath.suffix.lower() in [".crdownload", ".tmp", ".part", ".download"]:
                            continue

                        self.seen_files.add(fname)
                        self._process_new_file(fpath, player=player)

                except Exception as e:
                    print(f"[FileWatcher] Loop notice: {e}")

        t = threading.Thread(target=_watcher_loop, daemon=True)
        t.start()

    def _process_new_file(self, fpath: Path, player=None):
        """Processes newly arrived file: logs arrival, summarizes PDFs/docs, and auto-organizes."""
        try:
            name = fpath.name
            size_mb = fpath.stat().st_size / (1024 * 1024)
            ext = fpath.suffix.lower()

            if player and hasattr(player, "write_log"):
                player.write_log(f"FILE-WATCHER: 📥 New download detected: '{name}' ({size_mb:.2f} MB)")

            # Auto-organization category mapping
            doc_exts = [".pdf", ".docx", ".txt", ".csv", ".xlsx", ".pptx"]
            img_exts = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"]
            archive_exts = [".zip", ".rar", ".7z", ".tar", ".gz"]

            target_subfolder = None
            if ext in doc_exts:
                target_subfolder = "Documents"
            elif ext in img_exts:
                target_subfolder = "Images"
            elif ext in archive_exts:
                target_subfolder = "Archives"

            # Generate Document Summary for PDFs / Docs
            summary_msg = ""
            if ext == ".pdf":
                summary_msg = self._summarize_pdf(fpath)

            # Move to subfolder if applicable
            if target_subfolder:
                dest_dir = self.downloads_dir / target_subfolder
                dest_dir.mkdir(exist_ok=True)
                dest_path = dest_dir / name
                shutil.move(str(fpath), str(dest_path))
                if player and hasattr(player, "write_log"):
                    player.write_log(f"FILE-WATCHER: 📁 Organized '{name}' ➔ Downloads/{target_subfolder}/")

            # Dispatch Telegram Notice
            self._notify_telegram(name, size_mb, target_subfolder, summary_msg)

        except Exception as e:
            print(f"[FileWatcher] Process file error: {e}")

    def _summarize_pdf(self, fpath: Path) -> str:
        """Extracts text from PDF and generates a quick summary."""
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(fpath))
            text = ""
            for page in reader.pages[:3]:  # First 3 pages
                text += page.extract_text() or ""

            if len(text.strip()) > 50:
                snippet = text.strip()[:300].replace("\n", " ")
                return f"PDF Preview: {snippet}..."
        except Exception:
            pass
        return ""

    def _notify_telegram(self, fname: str, size_mb: float, subfolder: str | None, summary: str):
        """Sends new file arrival notification to Telegram chat."""
        try:
            import json, requests
            cfg_path = BASE_DIR / "config" / "api_keys.json"
            if not cfg_path.exists():
                return
            with open(cfg_path, "r", encoding="utf-8") as f:
                c = json.load(f)
            token = c.get("telegram_bot_token")
            chat_id = c.get("telegram_chat_id")

            if token and chat_id:
                msg = f"📥 NEW DOWNLOAD DETECTED\n\n• File: {fname}\n• Size: {size_mb:.2f} MB"
                if subfolder:
                    msg += f"\n• Folder: Downloads/{subfolder}/"
                if summary:
                    msg += f"\n\n📄 {summary}"

                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=5)
        except Exception:
            pass

    def stop(self):
        self.is_running = False


smart_file_watcher = SmartFileWatcher()


def file_watcher_control(parameters: dict, player=None) -> str:
    """Action handler for File Watcher status & folder organizer."""
    params = parameters or {}
    action = (params.get("action") or "status").lower().strip()

    if action in ("organize", "clean"):
        dw = _get_downloads_dir()
        if not dw.exists():
            return "Downloads folder not found."
        count = 0
        for f in list(dw.iterdir()):
            if f.is_file():
                ext = f.suffix.lower()
                if ext in [".pdf", ".docx", ".txt", ".csv", ".xlsx"]:
                    sub = "Documents"
                elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
                    sub = "Images"
                elif ext in [".zip", ".rar", ".7z"]:
                    sub = "Archives"
                else:
                    continue
                dest = dw / sub
                dest.mkdir(exist_ok=True)
                shutil.move(str(f), str(dest / f.name))
                count += 1
        return f"File Watcher: Organized {count} download files into structured subfolders."

    return f"File Watcher: Active and monitoring '{_get_downloads_dir()}' in real time."
