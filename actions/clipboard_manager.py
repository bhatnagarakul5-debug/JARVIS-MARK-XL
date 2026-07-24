import pyperclip
import threading
import time
from collections import deque
import traceback
from datetime import datetime
from pathlib import Path

def get_base_dir():
    return Path(__file__).resolve().parent.parent

# Module-level state
clipboard_history = deque(maxlen=30)
monitor_thread = None
monitor_active = False

def monitor_loop():
    global monitor_active
    last_clip = ""
    while monitor_active:
        try:
            current_clip = pyperclip.paste()
            if current_clip and current_clip != last_clip:
                last_clip = current_clip
                entry = {
                    "text": current_clip,
                    "timestamp": datetime.now().isoformat()
                }
                clipboard_history.append(entry)
        except:
            pass
        time.sleep(5)

def start_clipboard_monitor():
    global monitor_thread, monitor_active
    if not monitor_active:
        monitor_active = True
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

# Start automatically on import
start_clipboard_monitor()

def clipboard_manager(parameters: dict, player=None) -> str:
    """
    Manages and retrieves clipboard history.
    """
    try:
        if player:
            player.write_log(f"Executing clipboard_manager with {parameters}")
            player.set_state("working")

        action = parameters.get('action', 'list')
        index = parameters.get('index', 0)
        query = parameters.get('query', '').lower()

        if action == 'list':
            if not clipboard_history:
                return "The clipboard history is currently empty."
            
            history_list = list(clipboard_history)[-10:]
            result = "Here are the last clipboard entries:\n"
            for i, entry in enumerate(history_list):
                text_preview = entry['text'][:50].replace('\n', ' ') + ('...' if len(entry['text']) > 50 else '')
                result += f"{i}: {text_preview}\n"
            return result.strip()
            
        elif action == 'get':
            try:
                idx = int(index)
                history_list = list(clipboard_history)
                if idx < 0 or idx >= len(history_list):
                    return "Invalid clipboard index."
                
                text = history_list[idx]['text']
                pyperclip.copy(text) # put it back on active clipboard
                return f"I have restored the requested clipboard entry: {text[:100]}..."
            except ValueError:
                return "Please provide a valid index."
                
        elif action == 'search':
            if not query:
                return "Please provide a query to search the clipboard."
                
            matches = [entry for entry in clipboard_history if query in entry['text'].lower()]
            if not matches:
                return f"No clipboard entries found matching '{query}'."
                
            result = f"Found {len(matches)} matching entries:\n"
            for i, entry in enumerate(matches):
                text_preview = entry['text'][:50].replace('\n', ' ') + ('...' if len(entry['text']) > 50 else '')
                result += f"{i}: {text_preview}\n"
            return result.strip()
            
        elif action == 'clear':
            clipboard_history.clear()
            pyperclip.copy("")
            return "Clipboard history has been cleared."
            
        else:
            return "Unknown clipboard action specified."
            
    except Exception as e:
        error_msg = f"Clipboard manager encountered an error: {str(e)}"
        if player:
            player.write_log(traceback.format_exc())
        return error_msg
