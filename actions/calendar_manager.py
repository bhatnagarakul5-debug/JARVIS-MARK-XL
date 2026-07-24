import json
import datetime
from pathlib import Path

def get_base_dir():
    return Path(__file__).resolve().parent.parent

def get_calendar_file():
    return get_base_dir() / 'config' / 'calendar_events.json'

def load_calendar():
    cal_file = get_calendar_file()
    if not cal_file.exists():
        cal_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cal_file, 'w') as f:
            json.dump([], f)
        return []
    with open(cal_file, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_calendar(events):
    cal_file = get_calendar_file()
    cal_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cal_file, 'w') as f:
        json.dump(events, f, indent=4)

def clean_old_events(events):
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=30)
    cleaned = []
    for e in events:
        try:
            dt = datetime.datetime.strptime(f"{e['date']} {e['time']}", "%Y-%m-%d %H:%M")
            if dt >= cutoff:
                cleaned.append(e)
        except (ValueError, KeyError):
            cleaned.append(e)
    return cleaned

def calendar_manager(parameters: dict, player=None) -> str:
    action = parameters.get('action', 'today').lower()
    
    events = load_calendar()
    original_count = len(events)
    events = clean_old_events(events)
    if len(events) != original_count:
        save_calendar(events)
    
    if action == 'today':
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        today_events = [e for e in events if e.get('date') == today]
        if not today_events:
            return "You have no events scheduled for today, sir."
        res = "Events for today:\n"
        for e in today_events:
            res += f"- {e.get('time')}: {e.get('title')} ({e.get('description', '')})\n"
        return res
        
    elif action == 'upcoming':
        now = datetime.datetime.now()
        upcoming = []
        for e in events:
            try:
                dt = datetime.datetime.strptime(f"{e.get('date')} {e.get('time')}", "%Y-%m-%d %H:%M")
                if now <= dt <= now + datetime.timedelta(days=7):
                    upcoming.append(e)
            except ValueError:
                pass
        if not upcoming:
            return "You have no upcoming events for the next 7 days, sir."
        upcoming.sort(key=lambda x: f"{x.get('date')} {x.get('time')}")
        res = "Upcoming events:\n"
        for e in upcoming:
            res += f"- {e.get('date')} {e.get('time')}: {e.get('title')}\n"
        return res
        
    elif action == 'create':
        title = parameters.get('title')
        date = parameters.get('date')
        time = parameters.get('time')
        description = parameters.get('description', '')
        if not title or not date or not time:
            return "Sir, I need a title, date, and time to create an event."
        events.append({
            'title': title,
            'date': date,
            'time': time,
            'description': description
        })
        save_calendar(events)
        if player and hasattr(player, 'write_log'):
            player.write_log(f"Event created: {title}")
        return f"I have scheduled '{title}' for {date} at {time}, sir."
        
    elif action == 'delete':
        title = parameters.get('title')
        if not title:
            return "Please specify the title of the event to delete."
        initial_len = len(events)
        events = [e for e in events if e.get('title', '').lower() != title.lower()]
        if len(events) < initial_len:
            save_calendar(events)
            if player and hasattr(player, 'write_log'):
                player.write_log(f"Event deleted: {title}")
            return f"Event '{title}' has been deleted, sir."
        return f"I could not find an event titled '{title}', sir."
        
    elif action == 'search':
        query = parameters.get('query', '').lower()
        if not query:
            return "Please provide a search query, sir."
        matches = [e for e in events if query in e.get('title', '').lower() or query in e.get('description', '').lower()]
        if not matches:
            return f"No events found matching '{query}', sir."
        res = f"Events matching '{query}':\n"
        for e in matches:
            res += f"- {e.get('date')} {e.get('time')}: {e.get('title')}\n"
        return res
        
    return "Invalid calendar action requested."
