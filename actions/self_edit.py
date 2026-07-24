# actions/self_edit.py
# Lets JARVIS read and edit its own source code with safety measures

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def _get_project_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


PROJECT_DIR = _get_project_dir()
BACKUP_DIR  = PROJECT_DIR / ".backups"


def _get_api_key() -> str:
    config = PROJECT_DIR / "config" / "api_keys.json"
    with open(config, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _is_safe_path(path: Path) -> bool:
    """Only allow editing files within the project directory."""
    try:
        path.resolve().relative_to(PROJECT_DIR.resolve())
        return True
    except ValueError:
        return False


def _backup_file(path: Path) -> Path:
    """Creates a timestamped backup of a file before editing."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.stem}_{timestamp}{path.suffix}.bak"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(str(path), str(backup_path))
    return backup_path


def list_own_files() -> str:
    """Lists all editable source files in the project."""
    files = []
    for ext in ["*.py", "*.txt", "*.json"]:
        for f in PROJECT_DIR.rglob(ext):
            if ".backups" in str(f) or "__pycache__" in str(f) or ".git" in str(f):
                continue
            rel = f.relative_to(PROJECT_DIR)
            size = f.stat().st_size
            size_str = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} B"
            files.append(f"  {rel}  ({size_str})")
    files.sort()
    return f"Project files ({len(files)}):\n" + "\n".join(files)


def read_own_file(file_path: str) -> str:
    """Reads a source file from the project."""
    target = PROJECT_DIR / file_path
    if not target.exists():
        target = Path(file_path)
    if not target.exists():
        return f"File not found: {file_path}"
    if not _is_safe_path(target):
        return f"Access denied: {file_path} is outside the project directory."
    try:
        content = target.read_text(encoding="utf-8", errors="ignore")
        if len(content) > 5000:
            content = content[:5000] + f"\n\n... (truncated, {len(content)} total chars)"
        return f"Contents of {target.name}:\n{content}"
    except Exception as e:
        return f"Could not read file: {e}"


def edit_own_file(file_path: str, description: str, speak=None) -> str:
    """Uses Gemini to generate an edit for a source file."""
    target = PROJECT_DIR / file_path
    if not target.exists():
        target = Path(file_path)
    if not target.exists():
        return f"File not found: {file_path}"
    if not _is_safe_path(target):
        return f"Access denied: {file_path} is outside the project directory."
    if target.suffix not in (".py", ".txt", ".json", ".md", ".css", ".html", ".js"):
        return f"Cannot edit {target.suffix} files for safety."

    try:
        import google.generativeai as genai
        genai.configure(api_key=_get_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash")

        original = target.read_text(encoding="utf-8")

        # Create backup
        backup = _backup_file(target)
        if speak:
            speak(f"Backup created. Now editing {target.name}.")

        prompt = (
            f"You are editing a Python source file. Apply the following change:\n\n"
            f"CHANGE REQUEST: {description}\n\n"
            f"CURRENT FILE CONTENT:\n```\n{original}\n```\n\n"
            f"Return the COMPLETE modified file content. "
            f"Keep ALL existing code intact except for the requested change. "
            f"Return ONLY the code, no markdown backticks, no explanation."
        )

        response = model.generate_content(prompt)
        new_content = response.text.strip()
        new_content = re.sub(r"```(?:python|json|txt)?", "", new_content).strip().rstrip("`").strip()

        if not new_content or len(new_content) < 20:
            return "Edit failed: Generated content was empty or too short."

        # Basic safety check
        if target.suffix == ".py" and "import" not in new_content and len(original) > 100:
            return "Edit rejected: Generated code looks invalid (no imports found in a large file)."

        target.write_text(new_content, encoding="utf-8")
        return f"Successfully edited {target.name}. Backup saved at .backups/{backup.name}"

    except Exception as e:
        return f"Edit failed: {e}"


def rollback_file(file_path: str) -> str:
    """Restores a file from its most recent backup."""
    target = PROJECT_DIR / file_path
    if not target.exists():
        target = Path(file_path)
    if not _is_safe_path(target):
        return f"Access denied: {file_path} is outside the project directory."

    stem = target.stem
    backups = sorted(
        BACKUP_DIR.glob(f"{stem}_*.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not backups:
        return f"No backups found for {target.name}"

    latest = backups[0]
    shutil.copy2(str(latest), str(target))
    return f"Restored {target.name} from backup {latest.name}"


def self_edit(
    parameters: dict,
    response=None,
    player=None,
    speak=None,
    session_memory=None
) -> str:
    """Main dispatcher for self-edit actions."""
    action      = (parameters or {}).get("action", "").lower().strip()
    file_path   = (parameters or {}).get("file_path", "")
    description = (parameters or {}).get("description", "")

    result = "Unknown action."

    try:
        if action == "list":
            result = list_own_files()
        elif action == "read":
            if not file_path:
                return "Please specify which file to read."
            result = read_own_file(file_path)
        elif action == "edit":
            if not file_path or not description:
                return "Please specify the file path and what change to make."
            result = edit_own_file(file_path, description, speak=speak)
        elif action == "rollback":
            if not file_path:
                return "Please specify which file to rollback."
            result = rollback_file(file_path)
        else:
            result = f"Unknown self_edit action: '{action}'. Use: list, read, edit, rollback"
    except Exception as e:
        result = f"Self-edit error: {e}"

    if player:
        player.write_log(f"[self_edit] {result[:60]}")
    return result
