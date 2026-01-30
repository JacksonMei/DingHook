import json
import os
import threading
from typing import List, Dict, Any

MEMORY_FILE = os.environ.get("MEMORY_FILE", "dingbot_memory.jsonl")
_lock = threading.Lock()

def append_user_message(user_id: str, content: str, timestamp: int = None):
    """Append a user message to the memory file."""
    import time
    entry = {
        "user_id": user_id,
        "content": content,
        "timestamp": timestamp or int(time.time())
    }
    with _lock:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def get_user_memories(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent messages for a user from the memory file."""
    if not os.path.exists(MEMORY_FILE):
        return []
    result = []
    with _lock:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
            for line in reversed(lines):
                try:
                    entry = json.loads(line)
                    if entry.get("user_id") == user_id:
                        result.append(entry)
                        if len(result) >= limit:
                            break
                except Exception:
                    continue
    return list(reversed(result))


def list_users() -> List[str]:
    """Return unique user_ids present in the memory file."""
    if not os.path.exists(MEMORY_FILE):
        return []
    users = set()
    with _lock:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    uid = entry.get("user_id")
                    if uid:
                        users.add(uid)
                except Exception:
                    continue
    return sorted(users)
