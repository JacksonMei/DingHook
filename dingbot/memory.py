"""Simple SQLite-backed memory store for user memories (reminders)

Table `memories`:
- id INTEGER PRIMARY KEY
- user_id TEXT
- content TEXT
- interval INTEGER (seconds)
- next_push INTEGER (unix timestamp)
- created_at INTEGER (unix timestamp)
"""

import sqlite3
import time
from typing import List, Dict, Any, Optional

from . import config

DB_PATH = config.DATABASE_PATH

_create_sql = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    content TEXT,
    interval INTEGER,
    next_push INTEGER,
    created_at INTEGER
)
"""


def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute(_create_sql)
    conn.commit()
    conn.close()


def add_memory(user_id: str, content: str, interval_seconds: int) -> int:
    now = int(time.time())
    next_push = now + interval_seconds
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO memories (user_id, content, interval, next_push, created_at) VALUES (?,?,?,?,?)",
        (user_id, content, interval_seconds, next_push, now),
    )
    conn.commit()
    memory_id = cur.lastrowid
    conn.close()
    return memory_id


def delete_memory(memory_id: int) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
    conn.commit()
    conn.close()


def list_user_memories(user_id: str) -> List[Dict[str, Any]]:
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM memories WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_due_memories(now: Optional[int] = None) -> List[Dict[str, Any]]:
    now = now or int(time.time())
    conn = _get_conn()
    cur = conn.execute("SELECT * FROM memories WHERE next_push<=?", (now,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def bump_next_push(memory_id: int, now: Optional[int] = None) -> None:
    """Advance next_push by adding interval until it's in the future."""
    now = now or int(time.time())
    conn = _get_conn()
    cur = conn.execute("SELECT next_push, interval FROM memories WHERE id=?", (memory_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return
    next_push = row[0]
    interval = row[1]
    if interval <= 0:
        # one-shot
        conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
    else:
        # advance
        while next_push <= now:
            next_push += interval
        conn.execute("UPDATE memories SET next_push=? WHERE id=?", (next_push, memory_id))
    conn.commit()
    conn.close()
