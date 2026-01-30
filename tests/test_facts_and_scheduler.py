import os
import json
from types import SimpleNamespace

import dingbot.agent as agent
from dingbot import memory_file, facts_file, scheduler


def write_memory(tmp_path, user_id, msgs):
    f = tmp_path / "mem.jsonl"
    for m in msgs:
        memory_file.append_user_message(user_id, m)
    return str(f)


def test_extract_facts_parsing(monkeypatch, tmp_path):
    # Use a temporary memory file
    mf = tmp_path / "mem.jsonl"
    os.environ["MEMORY_FILE"] = str(mf)
    # append some messages
    memory_file.append_user_message('u1', '我喜欢猫和咖啡')
    memory_file.append_user_message('u1', '我在北京工作')

    # Mock _call_model to return JSON list
    monkeypatch.setattr(agent, "_call_model", lambda prompt, timeout=10: json.dumps([{"fact": "喜欢猫"}, {"fact": "在北京工作"}]))
    facts = agent.extract_facts_for_user('u1')
    assert isinstance(facts, list)
    assert any(f['fact'] == '喜欢猫' for f in facts)


def test_extract_facts_from_codeblock(monkeypatch, tmp_path):
    os.environ["MEMORY_FILE"] = str(tmp_path / "mem.jsonl")
    # write a sample message
    memory_file.append_user_message('uC', '今天我买了一个clawbot')
    # model returns markdown codeblock containing JSON
    md = '```json\n[ {"fact": "用户询问了关于clawbot发展趋势的问题"} ]\n```'
    monkeypatch.setattr(agent, "_call_model", lambda prompt, timeout=10: md)
    facts = agent.extract_facts_for_user('uC')
    assert isinstance(facts, list)
    assert len(facts) == 1
    assert facts[0]["fact"] == '用户询问了关于clawbot发展趋势的问题'


def test_scheduler_run_cycle(monkeypatch, tmp_path):
    mf = tmp_path / "mem.jsonl"
    os.environ["MEMORY_FILE"] = str(mf)

    # write two users' messages
    memory_file.append_user_message('u1', '我喜欢猫')
    memory_file.append_user_message('u2', '我喜欢徒步')

    # stub extract and push
    monkeypatch.setattr(agent, 'extract_facts_for_user', lambda uid: [{"fact": f"fact-for-{uid}"}])
    pushes = []
    monkeypatch.setattr(agent, 'generate_push_from_facts', lambda uid, facts: f"push for {uid}: {facts[0]['fact']}")
    monkeypatch.setattr(__import__('dingbot.sender', fromlist=['sender']), 'send_text_from_env', lambda text, at_user_ids=None: pushes.append(text))

    scheduler.run_cycle()
    # facts file should have entries for both users
    all_facts = facts_file.load_all_facts()
    assert 'u1' in all_facts and 'u2' in all_facts
    assert any('push for u1' in p for p in pushes)
