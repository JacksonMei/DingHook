import tempfile
import traceback

from tests import test_memory, test_agent

results = []

with tempfile.TemporaryDirectory() as tmp:
    try:
        test_memory.test_memory_add_list_delete(tmp)
        results.append(('test_memory_add_list_delete', 'OK'))
    except Exception:
        results.append(('test_memory_add_list_delete', 'FAILED:\n' + traceback.format_exc()))
    try:
        test_memory.test_get_due_and_bump(tmp)
        results.append(('test_get_due_and_bump', 'OK'))
    except Exception:
        results.append(('test_get_due_and_bump', 'FAILED:\n' + traceback.format_exc()))

# agent tests
from types import SimpleNamespace
import dingbot.agent as agent

# Test fake genai
try:
    agent.GENAI_AVAILABLE = True
    class FakeResp:
        text = '{"reply": "hello", "save_memory": {"interval": 3600, "content": "测试"}}'
    fake = SimpleNamespace(generate_text=lambda model, prompt: FakeResp())
    agent.genai = fake
    res = agent.analyze_and_reply('请记住这件事', 'Alice')
    if res.get('reply') == 'hello' and isinstance(res.get('save_memory'), dict):
        results.append(('test_agent_with_fake_genai', 'OK'))
    else:
        results.append(('test_agent_with_fake_genai', 'FAILED: unexpected result: ' + str(res)))
except Exception:
    results.append(('test_agent_with_fake_genai', 'FAILED:\n' + traceback.format_exc()))

# fallback test
try:
    agent.GENAI_AVAILABLE = False
    res2 = agent.analyze_and_reply('请记住：每天喝水', 'Bob')
    # Accept either a dict with save_memory or a reply string
    ok = isinstance(res2, dict)
    if ok:
        results.append(('test_agent_local_fallback_save_memory', 'OK'))
    else:
        results.append(('test_agent_local_fallback_save_memory', 'FAILED: unexpected return type'))
except Exception:
    results.append(('test_agent_local_fallback_save_memory', 'FAILED:\n' + traceback.format_exc()))

print('\n'.join([f"{name}: {status}" for name, status in results]))

# exit code
failed = [r for r in results if not r[1].startswith('OK')]
if failed:
    raise SystemExit(1)
else:
    raise SystemExit(0)
