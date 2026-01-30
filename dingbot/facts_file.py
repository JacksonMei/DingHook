import json
import os
import threading
from typing import Dict, List, Any

FACTS_FILE = os.environ.get("FACTS_FILE", "dingbot_fact.json")
_lock = threading.Lock()


def load_all_facts() -> Dict[str, List[Any]]:
    if not os.path.exists(FACTS_FILE):
        return {}
    with _lock:
        with open(FACTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}


def set_user_facts(user_id: str, facts: List[Dict[str, Any]]):
    data = load_all_facts()
    data[user_id] = facts
    tmp = FACTS_FILE + ".tmp"
    with _lock:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, FACTS_FILE)


def get_user_facts(user_id: str) -> List[Dict[str, Any]]:
    return load_all_facts().get(user_id, [])
