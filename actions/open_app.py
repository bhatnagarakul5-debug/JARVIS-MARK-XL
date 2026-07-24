# actions/open_app.py
# MARK XL — Cross-Platform Universal App Launcher

import time
import subprocess
import platform
import shutil
from pathlib import Path

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

_APP_ALIASES = {
    "whatsapp":           {"Windows": "WhatsApp",               "Darwin": "WhatsApp",            "Linux": "whatsapp"},
    "chrome":             {"Windows": "chrome",                 "Darwin": "Google Chrome",       "Linux": "google-chrome"},
    "google chrome":      {"Windows": "chrome",                 "Darwin": "Google Chrome",       "Linux": "google-chrome"},
    "firefox":            {"Windows": "firefox",                "Darwin": "Firefox",             "Linux": "firefox"},
    "spotify":            {"Windows": "Spotify",                "Darwin": "Spotify",             "Linux": "spotify"},
    "vscode":             {"Windows": "code",                   "Darwin": "Visual Studio Code",  "Linux": "code"},
    "visual studio code": {"Windows": "code",                   "Darwin": "Visual Studio Code",  "Linux": "code"},
    "discord":            {"Windows": "Discord",                "Darwin": "Discord",             "Linux": "discord"},
    "telegram":           {"Windows": "Telegram",               "Darwin": "Telegram",            "Linux": "telegram"},
    "instagram":          {"Windows": "Instagram",              "Darwin": "Instagram",           "Linux": "instagram"},
    "tiktok":             {"Windows": "TikTok",                 "Darwin": "TikTok",              "Linux": "tiktok"},
    "notepad":            {"Windows": "notepad.exe",            "Darwin": "TextEdit",            "Linux": "gedit"},
    "calculator":         {"Windows": "calc.exe",               "Darwin": "Calculator",          "Linux": "gnome-calculator"},
    "terminal":           {"Windows": "cmd.exe",                "Darwin": "Terminal",            "Linux": "gnome-terminal"},
    "cmd":                {"Windows": "cmd.exe",                "Darwin": "Terminal",            "Linux": "bash"},
    "explorer":           {"Windows": "explorer.exe",           "Darwin": "Finder",              "Linux": "nautilus"},
    "file explorer":      {"Windows": "explorer.exe",           "Darwin": "Finder",              "Linux": "nautilus"},
    "paint":              {"Windows": "mspaint.exe",            "Darwin": "Preview",             "Linux": "gimp"},
    "word":               {"Windows": "winword",                "Darwin": "Microsoft Word",      "Linux": "libreoffice --writer"},
    "excel":              {"Windows": "excel",                  "Darwin": "Microsoft Excel",     "Linux": "libreoffice --calc"},
    "powerpoint":         {"Windows": "powerpnt",               "Darwin": "Microsoft PowerPoint","Linux": "libreoffice --impress"},
    "vlc":                {"Windows": "vlc",                    "Darwin": "VLC",                 "Linux": "vlc"},
    "zoom":               {"Windows": "Zoom",                   "Darwin": "zoom.us",             "Linux": "zoom"},
    "slack":              {"Windows": "Slack",                  "Darwin": "Slack",               "Linux": "slack"},
    "steam":              {"Windows": "steam",                  "Darwin": "Steam",               "Linux": "steam"},
    "task manager":       {"Windows": "taskmgr.exe",            "Darwin": "Activity Monitor",    "Linux": "gnome-system-monitor"},
    "settings":           {"Windows": "ms-settings:",           "Darwin": "System Preferences",  "Linux": "gnome-control-center"},
    "powershell":         {"Windows": "powershell.exe",         "Darwin": "Terminal",            "Linux": "bash"},
    "edge":               {"Windows": "msedge",                 "Darwin": "Microsoft Edge",      "Linux": "microsoft-edge"},
    "brave":              {"Windows": "brave",                  "Darwin": "Brave Browser",       "Linux": "brave-browser"},
    "obsidian":           {"Windows": "Obsidian",               "Darwin": "Obsidian",            "Linux": "obsidian"},
    "notion":             {"Windows": "Notion",                 "Darwin": "Notion",              "Linux": "notion"},
    "blender":            {"Windows": "blender",                "Darwin": "Blender",             "Linux": "blender"},
    "capcut":             {"Windows": "CapCut",                 "Darwin": "CapCut",              "Linux": "capcut"},
    "postman":            {"Windows": "Postman",                "Darwin": "Postman",             "Linux": "postman"},
    "figma":              {"Windows": "Figma",                  "Darwin": "Figma",               "Linux": "figma"},
    "obs":                {"Windows": "OBS Studio",              "Darwin": "OBS",                 "Linux": "obs"},
    "obs studio":         {"Windows": "OBS Studio",              "Darwin": "OBS",                 "Linux": "obs"},
    "audacity":           {"Windows": "Audacity",                "Darwin": "Audacity",            "Linux": "audacity"},
    "git bash":           {"Windows": "git-bash",                "Darwin": "Terminal",            "Linux": "bash"},
    "android studio":     {"Windows": "Android Studio",          "Darwin": "Android Studio",      "Linux": "android-studio"},
    "unity":              {"Windows": "Unity Hub",               "Darwin": "Unity Hub",           "Linux": "unityhub"},
    "unreal engine":      {"Windows": "Unreal Engine",           "Darwin": "Unreal Engine",       "Linux": "unreal"},
    "teams":              {"Windows": "Microsoft Teams",         "Darwin": "Microsoft Teams",     "Linux": "teams"},
    "microsoft teams":    {"Windows": "Microsoft Teams",         "Darwin": "Microsoft Teams",     "Linux": "teams"},
    "skype":              {"Windows": "Skype",                   "Darwin": "Skype",               "Linux": "skype"},
    "photoshop":          {"Windows": "Adobe Photoshop",         "Darwin": "Adobe Photoshop",     "Linux": "photoshop"},
    "premiere":           {"Windows": "Adobe Premiere Pro",      "Darwin": "Adobe Premiere Pro",  "Linux": "premiere"},
    "after effects":      {"Windows": "Adobe After Effects",     "Darwin": "Adobe After Effects", "Linux": "aftereffects"},
    "illustrator":        {"Windows": "Adobe Illustrator",       "Darwin": "Adobe Illustrator",   "Linux": "illustrator"},
    "lightroom":          {"Windows": "Adobe Lightroom",         "Darwin": "Adobe Lightroom",     "Linux": "lightroom"},
    "davinci resolve":    {"Windows": "DaVinci Resolve",         "Darwin": "DaVinci Resolve",     "Linux": "resolve"},
    "gimp":               {"Windows": "GIMP",                    "Darwin": "GIMP",                "Linux": "gimp"},
    "inkscape":           {"Windows": "Inkscape",                "Darwin": "Inkscape",            "Linux": "inkscape"},
    "krita":              {"Windows": "Krita",                   "Darwin": "Krita",               "Linux": "krita"},
    "libreoffice":        {"Windows": "LibreOffice",             "Darwin": "LibreOffice",         "Linux": "libreoffice"},
    "onenote":            {"Windows": "OneNote",                 "Darwin": "Microsoft OneNote",   "Linux": "onenote"},
    "outlook":            {"Windows": "Outlook",                 "Darwin": "Microsoft Outlook",   "Linux": "outlook"},
    "visual studio":      {"Windows": "Visual Studio",           "Darwin": "Visual Studio",       "Linux": "visualstudio"},
    "pycharm":            {"Windows": "PyCharm",                 "Darwin": "PyCharm",             "Linux": "pycharm"},
    "intellij":           {"Windows": "IntelliJ IDEA",           "Darwin": "IntelliJ IDEA",       "Linux": "idea"},
    "sublime":            {"Windows": "Sublime Text",            "Darwin": "Sublime Text",        "Linux": "subl"},
    "sublime text":       {"Windows": "Sublime Text",            "Darwin": "Sublime Text",        "Linux": "subl"},
    "cursor":             {"Windows": "Cursor",                  "Darwin": "Cursor",              "Linux": "cursor"},
    "windsurf":           {"Windows": "Windsurf",                "Darwin": "Windsurf",            "Linux": "windsurf"},
    "epic games":         {"Windows": "Epic Games Launcher",     "Darwin": "Epic Games Launcher", "Linux": "epic"},
    "xbox":               {"Windows": "Xbox",                    "Darwin": "Xbox",                "Linux": "xbox"},
    "valorant":           {"Windows": "VALORANT",                "Darwin": "VALORANT",            "Linux": "valorant"},
    "minecraft":          {"Windows": "Minecraft Launcher",      "Darwin": "Minecraft",           "Linux": "minecraft"},
    "phone link":         {"Windows": "Phone Link",              "Darwin": "Phone Link",          "Linux": "phone-link"},
    "snipping tool":      {"Windows": "SnippingTool",            "Darwin": "Screenshot",          "Linux": "gnome-screenshot"},
    "control panel":      {"Windows": "control",                 "Darwin": "System Preferences",  "Linux": "gnome-control-center"},
    "device manager":     {"Windows": "devmgmt.msc",             "Darwin": "System Information",  "Linux": "lshw"},
    "task scheduler":     {"Windows": "taskschd.msc",            "Darwin": "crontab",             "Linux": "crontab"},
    "system info":        {"Windows": "msinfo32",                "Darwin": "system_profiler",     "Linux": "neofetch"},
    "disk management":    {"Windows": "diskmgmt.msc",            "Darwin": "Disk Utility",        "Linux": "gnome-disks"},
    "recycle bin":        {"Windows": "shell:RecycleBinFolder",  "Darwin": "Trash",               "Linux": "trash"},
    "this pc":            {"Windows": "explorer shell:MyComputerFolder", "Darwin": "Finder", "Linux": "nautilus"},
    "downloads":          {"Windows": "explorer shell:Downloads", "Darwin": "open ~/Downloads", "Linux": "nautilus ~/Downloads"},
    "tally":              {"Windows": "Tally.ERP 9",             "Darwin": "Tally",               "Linux": "tally"},
    "tally prime":        {"Windows": "TallyPrime",              "Darwin": "TallyPrime",          "Linux": "tallyprime"},
}


def _normalize(raw: str) -> str:
    system = platform.system()
    key    = raw.lower().strip()
    if key in _APP_ALIASES:
        return _APP_ALIASES[key].get(system, raw)
    for alias_key, os_map in _APP_ALIASES.items():
        if alias_key in key or key in alias_key:
            return os_map.get(system, raw)
    return raw


def _is_running(app_name: str) -> bool:
    if not _PSUTIL:
        return True
    app_lower = app_name.lower().replace(" ", "").replace(".exe", "")
    try:
        for proc in psutil.process_iter(["name"]):
            try:
                proc_name = proc.info["name"].lower().replace(" ", "").replace(".exe", "")
                if app_lower in proc_name or proc_name in app_lower:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return False


def _try_registry_launch(app_name: str) -> bool:
    """Try to find and launch an app via Windows Registry."""
    try:
        import winreg
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                key = winreg.OpenKey(
                    root,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\" + app_name + ".exe"
                )
                path = winreg.QueryValue(key, None)
                if path and Path(path.strip('"')).exists():
                    subprocess.Popen(
                        [path.strip('"')],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    time.sleep(1.5)
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _try_where_launch(app_name: str) -> bool:
    """Try to find and launch app via 'where' command."""
    try:
        result = subprocess.run(
            ["where", app_name], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            exe = result.stdout.strip().split("\n")[0].strip()
            subprocess.Popen(
                [exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(1.5)
            return True
    except Exception:
        pass
    return False


def _launch_windows(app_name: str) -> bool:
    # 1. Try Windows Registry
    if _try_registry_launch(app_name):
        return True

    # 2. Try 'where' command
    if _try_where_launch(app_name):
        return True

    # 3. Try Start Menu search (pyautogui)
    try:
        import pyautogui
        pyautogui.PAUSE = 0.1
        pyautogui.press("win")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(3.0)
        return True
    except Exception as e:
        print(f"[open_app] ⚠️ Windows launch failed: {e}")
        return False

def _launch_macos(app_name: str) -> bool:
    try:
        result = subprocess.run(["open", "-a", app_name], capture_output=True, timeout=8)
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    try:
        result = subprocess.run(["open", "-a", f"{app_name}.app"], capture_output=True, timeout=8)
        if result.returncode == 0:
            time.sleep(1.0)
            return True
    except Exception:
        pass

    try:
        import pyautogui
        pyautogui.hotkey("command", "space")
        time.sleep(0.6)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(1.5)
        return True
    except Exception as e:
        print(f"[open_app] ⚠️ macOS Spotlight failed: {e}")
        return False



def _launch_linux(app_name: str) -> bool:
    binary = (
        shutil.which(app_name) or
        shutil.which(app_name.lower()) or
        shutil.which(app_name.lower().replace(" ", "-"))
    )
    if binary:
        try:
            subprocess.Popen([binary], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.0)
            return True
        except Exception:
            pass

    try:
        subprocess.run(["xdg-open", app_name], capture_output=True, timeout=5)
        return True
    except Exception:
        pass

    try:
        desktop_name = app_name.lower().replace(" ", "-")
        subprocess.run(["gtk-launch", desktop_name], capture_output=True, timeout=5)
        return True
    except Exception:
        pass

    return False


_OS_LAUNCHERS = {
    "Windows": _launch_windows,
    "Darwin":  _launch_macos,
    "Linux":   _launch_linux,
}


def open_app(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    app_name = (parameters or {}).get("app_name", "").strip()

    if not app_name:
        return "Please specify which application to open, sir."

    system   = platform.system()
    launcher = _OS_LAUNCHERS.get(system)

    if launcher is None:
        return f"Unsupported OS: {system}"

    normalized = _normalize(app_name)
    print(f"[open_app] 🚀 Launching: {app_name} → {normalized} ({system})")

    if player:
        player.write_log(f"[open_app] {app_name}")

    try:
        success = launcher(normalized)

        if success:
            return f"Opened {app_name} successfully, sir."

        if normalized != app_name:
            success = launcher(app_name)
            if success:
                return f"Opened {app_name} successfully, sir."

        return (
            f"I tried to open {app_name}, sir, but couldn't confirm it launched. "
            f"It may still be loading or might not be installed."
        )

    except Exception as e:
        print(f"[open_app] ❌ {e}")
        return f"Failed to open {app_name}, sir: {e}"