import time
import os
import tempfile

import dingbot.memory as memory
import dingbot.config as config


def test_memory_add_list_delete(tmp_path):
    # Use a temporary DB file
    dbpath = str(tmp_path / "mem.db")
    # ensure config points to test db
    original = config.DATABASE_PATH
    config.DATABASE_PATH = dbpath

    try:
        memory.init_db()
        uid = "user1"
        mid = memory.add_memory(uid, "test content", 60)
        mems = memory.list_user_memories(uid)
        assert any(m['id'] == mid for m in mems)

        # add a one-shot memory (interval=0) and ensure bump_next_push deletes it
        mid2 = memory.add_memory(uid, "one-shot", 0)
        mems = memory.list_user_memories(uid)
        assert any(m['id'] == mid2 for m in mems)

        # bump will remove it
        memory.bump_next_push(mid2, now=int(time.time()) + 10)
        mems_after = memory.list_user_memories(uid)
        assert not any(m['id'] == mid2 for m in mems_after)

    finally:
        config.DATABASE_PATH = original


def test_get_due_and_bump(tmp_path):
    dbpath = str(tmp_path / "mem2.db")
    original = config.DATABASE_PATH
    config.DATABASE_PATH = dbpath
    try:
        memory.init_db()
        uid = "user2"
        mid = memory.add_memory(uid, "soon", 1)
        # wait a bit
        time.sleep(2)
        due = memory.get_due_memories()
        assert any(d['id'] == mid for d in due)
        # bump next push moves it into future
        memory.bump_next_push(mid)
        due_after = memory.get_due_memories()
        assert not any(d['id'] == mid for d in due_after)
    finally:
        config.DATABASE_PATH = original
