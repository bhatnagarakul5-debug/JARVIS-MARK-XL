import threading
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import traceback
import re

def get_base_dir():
    return Path(__file__).resolve().parent.parent

# Module-level state
active_timers = {}

def get_schedules_file():
    config_dir = get_base_dir() / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'schedules.json'

def load_schedules():
    file_path = get_schedules_file()
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_schedules(schedules):
    file_path = get_schedules_file()
    with open(file_path, 'w') as f:
        json.dump(schedules, f, indent=4)

def parse_interval(interval_str):
    """Parses '30m', '1h', 'daily 09:00' to seconds from now."""
    interval_str = interval_str.lower().strip()
    
    if interval_str.endswith('m'):
        try:
            return int(interval_str[:-1]) * 60
        except ValueError:
            pass
    elif interval_str.endswith('h'):
        try:
            return int(interval_str[:-1]) * 3600
        except ValueError:
            pass
    elif interval_str.startswith('daily '):
        time_str = interval_str.replace('daily ', '').strip()
        try:
            target_time = datetime.strptime(time_str, '%H:%M').time()
            now = datetime.now()
            target_dt = datetime.combine(now.date(), target_time)
            if target_dt <= now:
                target_dt += timedelta(days=1)
            return (target_dt - now).total_seconds()
        except ValueError:
            pass
            
    return None

def start_scheduler(speak_callback):
    """Boot saved schedules on startup."""
    schedules = load_schedules()
    for task_name, info in schedules.items():
        if info.get('status') != 'paused':
            _schedule_internal(task_name, info['interval'], info['command'], speak_callback)

def _schedule_internal(task_name, interval_str, command, speak_callback):
    seconds = parse_interval(interval_str)
    if seconds is None:
        return False
        
    def callback():
        if speak_callback:
            speak_callback(command)
        if task_name in active_timers:
            del active_timers[task_name]
        # Reschedule repeating daily tasks
        if interval_str.lower().strip().startswith('daily '):
            _schedule_internal(task_name, interval_str, command, speak_callback)
            
    timer = threading.Timer(seconds, callback)
    timer.daemon = True
    timer.start()
    active_timers[task_name] = timer
    return True

def schedule_task(parameters: dict, player=None, speak=None) -> str:
    """
    Manages tasks and scheduling.
    """
    try:
        if player:
            player.write_log(f"Executing schedule_task with {parameters}")
            player.set_state("working")

        action = parameters.get('action', 'list')
        task_name = parameters.get('task_name')
        interval = parameters.get('interval')
        command = parameters.get('command')
        
        schedules = load_schedules()

        if action == 'add':
            if not task_name or not interval or not command:
                return "Missing required parameters to schedule a task."
                
            success = _schedule_internal(task_name, interval, command, speak)
            if not success:
                return f"Could not parse the interval format: {interval}"
                
            schedules[task_name] = {
                'interval': interval,
                'command': command,
                'status': 'active'
            }
            save_schedules(schedules)
            return f"Task '{task_name}' has been scheduled."
            
        elif action == 'list':
            if not schedules:
                return "You have no active schedules."
            
            result = "Here are your schedules:\n"
            for name, info in schedules.items():
                status = info.get('status', 'active')
                result += f"- {name} ({info['interval']}): {info['command']} [{status}]\n"
            return result.strip()
            
        elif action == 'remove':
            if not task_name or task_name not in schedules:
                return f"Schedule '{task_name}' not found."
                
            if task_name in active_timers:
                active_timers[task_name].cancel()
                del active_timers[task_name]
                
            del schedules[task_name]
            save_schedules(schedules)
            return f"Schedule '{task_name}' has been removed."
            
        elif action == 'pause':
            if not task_name or task_name not in schedules:
                return f"Schedule '{task_name}' not found."
                
            if task_name in active_timers:
                active_timers[task_name].cancel()
                del active_timers[task_name]
                
            schedules[task_name]['status'] = 'paused'
            save_schedules(schedules)
            return f"Schedule '{task_name}' paused."
            
        elif action == 'resume':
            if not task_name or task_name not in schedules:
                return f"Schedule '{task_name}' not found."
                
            if schedules[task_name]['status'] == 'paused':
                _schedule_internal(task_name, schedules[task_name]['interval'], schedules[task_name]['command'], speak)
                schedules[task_name]['status'] = 'active'
                save_schedules(schedules)
                return f"Schedule '{task_name}' resumed."
            return f"Schedule '{task_name}' is already active."
            
        else:
            return "Unknown scheduler action specified."
            
    except Exception as e:
        error_msg = f"Scheduler encountered an error: {str(e)}"
        if player:
            player.write_log(traceback.format_exc())
        return error_msg
