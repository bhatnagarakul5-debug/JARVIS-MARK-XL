import json
import os
import datetime

def get_base_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def _get_log_path():
    return os.path.join(get_base_dir(), 'memory', 'conversations.jsonl')

def log_exchange(user_text: str, jarvis_text: str) -> None:
    log_path = _get_log_path()
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user": user_text,
        "jarvis": jarvis_text
    }
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def search_history(query: str, limit: int = 20) -> list[dict]:
    log_path = _get_log_path()
    if not os.path.exists(log_path):
        return []
    
    results = []
    query_lower = query.lower()
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if query_lower in entry.get('user', '').lower() or query_lower in entry.get('jarvis', '').lower():
                        results.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
        
    return results[-limit:]

def get_recent(n: int = 20) -> list[dict]:
    log_path = _get_log_path()
    if not os.path.exists(log_path):
        return []
        
    entries = []
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
        
    return entries[-n:]

def get_all_dates() -> list[str]:
    log_path = _get_log_path()
    if not os.path.exists(log_path):
        return []
        
    dates = set()
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if 'timestamp' in entry:
                        date_str = entry['timestamp'].split('T')[0]
                        dates.add(date_str)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
        
    return sorted(list(dates))
