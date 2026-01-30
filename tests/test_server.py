import json
import tempfile

import dingbot.server as server
import dingbot.config as config
import dingbot.memory as memory
from types import SimpleNamespace


def test_help_and_ping(monkeypatch, tmp_path):
    # Use a test DB and disable scheduler
    dbpath = str(tmp_path / "srv.db")
    original = config.DATABASE_PATH
    config.DATABASE_PATH = dbpath
    server.init_app(start_scheduler=False)

    # Mock sender to capture outgoing messages
    sent = []

    def fake_send(msg, at_user_ids=None):
        sent.append((msg, at_user_ids))
        return {"errcode": 0}

    monkeypatch.setattr(server.sender, "send_text_from_env", fake_send)

    client = server.app.test_client()

    payload = {"msgtype": "text", "text": {"content": "/help"}, "senderNick": "Alice", "senderId": "alice123"}
    r = client.post("/webhook", json=payload)
    assert r.status_code == 200
    assert sent, "help command should trigger send"
    # verify @ user id passed
    assert sent[-1][1] == ["alice123"]

    # ping
    sent.clear()
    payload["text"]["content"] = "/ping"
    r = client.post("/webhook", json=payload)
    assert r.status_code == 200
    assert sent and "pong" in sent[-1][0]

    config.DATABASE_PATH = original


def test_remember_and_normal_message(monkeypatch, tmp_path):
    dbpath = str(tmp_path / "srv2.db")
    original = config.DATABASE_PATH
    config.DATABASE_PATH = dbpath
    server.init_app(start_scheduler=False)

    # stub sender
    sent = []

    def fake_send(msg, at_user_ids=None):
        sent.append((msg, at_user_ids))
        return {"errcode": 0}

    monkeypatch.setattr(server.sender, "send_text_from_env", fake_send)

    # stub agent to return a reply and a save_memory suggestion
    def fake_agent(content, sender_name, memories=None):
        return {"reply": f"Echo: {content}", "save_memory": {"interval": 3600, "content": "自动记忆: %s" % content}}

    monkeypatch.setattr(server.agent, "analyze_and_reply", fake_agent)

    client = server.app.test_client()

    # Send remember command
    payload = {"msgtype": "text", "text": {"content": "/remember 5 喝水"}, "senderNick": "Bob", "senderId": "bobid"}
    r = client.post("/webhook", json=payload)
    assert r.status_code == 200

    # Memory should exist
    mems = memory.list_user_memories("bobid")
    assert any("喝水" in m["content"] for m in mems)

    # Send a normal message and expect agent reply and saved memory
    payload = {"msgtype": "text", "text": {"content": "hello bot"}, "senderNick": "Bob", "senderId": "bobid"}
    r = client.post("/webhook", json=payload)
    assert r.status_code == 200

    # agent suggested a save_memory so there should be a memory with '自动记忆'
    mems = memory.list_user_memories("bobid")
    assert any("自动记忆" in m["content"] for m in mems)

    # outgoing message was sent and @ bobid
    assert any(call for call in sent if call[1] == ["bobid"])

    config.DATABASE_PATH = original
