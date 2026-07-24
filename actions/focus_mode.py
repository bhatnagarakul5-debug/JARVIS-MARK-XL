import threading
import time
from pathlib import Path

def get_base_dir():
    return Path(__file__).resolve().parent.parent

_focus_active = False
_focus_thread = None
_stop_event = threading.Event()
_focus_end_time = None

def is_focus_active() -> bool:
    global _focus_active
    return _focus_active

def _timer_worker(duration_minutes: int, speak_callback, player):
    global _focus_active
    
    # Wait for the duration or until stopped
    stopped = _stop_event.wait(duration_minutes * 60)
    
    _focus_active = False
    
    if not stopped:
        # timer expired naturally
        msg = f"Focus session complete, sir. You worked for {duration_minutes} minutes."
        if speak_callback:
            try:
                speak_callback(msg)
            except Exception:
                pass
                
        if player and hasattr(player, 'write_log'):
            player.write_log("Focus mode completed naturally.")
        if player and hasattr(player, 'set_state'):
            player.set_state("Idle")

def focus_mode(parameters: dict, player=None, speak=None) -> str:
    global _focus_active, _focus_thread, _stop_event, _focus_end_time
    
    action = parameters.get('action', 'start').lower()
    
    if action == 'start':
        if _focus_active:
            return "Sir, focus mode is already active."
            
        duration = parameters.get('duration', 25)
        try:
            duration = int(duration)
        except ValueError:
            duration = 25
            
        _focus_active = True
        _stop_event.clear()
        _focus_end_time = time.time() + (duration * 60)
        
        _focus_thread = threading.Thread(
            target=_timer_worker,
            args=(duration, speak, player),
            daemon=True
        )
        _focus_thread.start()
        
        if player and hasattr(player, 'set_state'):
            player.set_state("Focus Mode")
        if player and hasattr(player, 'write_log'):
            player.write_log(f"Started focus mode for {duration} minutes.")
            
        return f"Focus mode activated for {duration} minutes, sir. I will minimize distractions."
        
    elif action == 'stop':
        if not _focus_active:
            return "Focus mode is not currently active, sir."
            
        _stop_event.set()
        _focus_active = False
        _focus_end_time = None
        
        if player and hasattr(player, 'set_state'):
            player.set_state("Idle")
        if player and hasattr(player, 'write_log'):
            player.write_log("Focus mode manually stopped.")
            
        return "Focus mode has been deactivated, sir."
        
    elif action == 'status':
        if not _focus_active or not _focus_end_time:
            return "Focus mode is not currently active, sir."
            
        remaining = _focus_end_time - time.time()
        if remaining <= 0:
            return "Focus session is just completing now."
            
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        return f"Sir, you have {mins} minutes and {secs} seconds remaining in your focus session."
        
    return "Invalid focus mode action."
