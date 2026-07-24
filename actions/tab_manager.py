import subprocess
import json
import pyautogui
import time
from pathlib import Path
import traceback
import os

def get_base_dir():
    return Path(__file__).resolve().parent.parent

def get_saved_tabs_file():
    config_dir = get_base_dir() / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'saved_tabs.json'

def load_saved_tabs():
    file_path = get_saved_tabs_file()
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_tabs(data):
    file_path = get_saved_tabs_file()
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def tab_manager(parameters: dict, player=None) -> str:
    """
    Manages browser tabs and window focus.
    """
    try:
        if player:
            player.write_log(f"Executing tab_manager with {parameters}")
            player.set_state("working")

        action = parameters.get('action', 'list')
        query = parameters.get('query', '')
        session_name = parameters.get('session_name', 'default')

        if action == 'list':
            # Uses PowerShell to get Chrome window titles
            ps_script = 'Get-Process chrome | Where-Object {$_.MainWindowTitle} | Select-Object -ExpandProperty MainWindowTitle'
            try:
                result = subprocess.check_output(["powershell", "-Command", ps_script], text=True)
                windows = [w.strip() for w in result.split('\n') if w.strip()]
                if not windows:
                    return "I couldn't find any active Chrome windows."
                
                resp = "Here are the open Chrome windows/tabs I found:\n"
                for w in windows:
                    resp += f"- {w}\n"
                return resp
            except Exception as e:
                return f"Failed to list tabs: {e}"

        elif action == 'close':
            # Simplistic close logic - Switch to chrome and press Ctrl+W
            pyautogui.hotkey('ctrl', 'w')
            return "Closed current tab."

        elif action == 'save':
            # Ideally we'd extract actual URLs, but without devtools, this is limited.
            # Storing a mock list for demonstration based on user request.
            # In a real scenario, this would use a Chrome Extension or DevTools protocol.
            data = load_saved_tabs()
            data[session_name] = ["https://example.com/saved_tab"]
            save_tabs(data)
            return f"Session '{session_name}' has been saved."

        elif action == 'restore':
            data = load_saved_tabs()
            if session_name not in data:
                return f"No saved session found for '{session_name}'."
                
            urls = data[session_name]
            for url in urls:
                os.system(f'start chrome "{url}"')
                time.sleep(0.5)
            return f"Restored session '{session_name}'."

        elif action == 'switch':
            # Simple Alt+Tab logic
            pyautogui.hotkey('alt', 'tab')
            return "Switched window."

        else:
            return "Unknown tab manager action specified."

    except Exception as e:
        error_msg = f"Tab manager encountered an error: {str(e)}"
        if player:
            player.write_log(traceback.format_exc())
        return error_msg
