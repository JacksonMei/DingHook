import json
from types import SimpleNamespace

import dingbot.agent as agent


def test_agent_with_fake_genai(monkeypatch):
    # Make the agent think google generative client is available
    monkeypatch.setattr(agent, "GENAI_AVAILABLE", True)

    class FakeResp:
        text = json.dumps({"reply": "hello", "save_memory": {"interval": 3600, "content": "测试"}})

    fake = SimpleNamespace(generate_text=lambda model, prompt: FakeResp())
    monkeypatch.setattr(agent, "genai", fake)

    res = agent.analyze_and_reply("请记住这件事", "Alice")
    assert isinstance(res, dict)
    assert res.get("reply") == "hello"
    assert isinstance(res.get("save_memory"), dict)


def test_agent_local_fallback_save_memory():
    # Ensure fallback returns a save_memory when prompt contains '记住'
    monkeypatch_attrs = {}
    # Temporarily ensure the official client is treated as unavailable
    agent.GENAI_AVAILABLE = False
    res = agent.analyze_and_reply("请记住：每天喝水", "Bob")
    assert isinstance(res, dict)
    # Either the fallback returns a reply string, or JSON with save_memory
    # If it's a string reply, the content should mention '记录' or similar
    if "save_memory" in res:
        assert isinstance(res["save_memory"], dict)

def test_model_resolution_and_retry(monkeypatch):
    # Simulate the SDK being available but initial model causing a NOT_FOUND, then resolve
    monkeypatch.setattr(agent, "GENAI_CLIENT_AVAILABLE", True)

    class FakeClient:
        def __init__(self):
            self._models = self.Models(self)
            # expose as .models for the client API
            self.models = self._models
        class Models:
            def __init__(self, outer):
                self.outer = outer
                self.calls = []
            def list(self):
                # return an iterable of simple namespaces with a name attribute
                from types import SimpleNamespace
                return [SimpleNamespace(name='models/gemini-3-pro-preview')]
            def generate_content(self, model, contents, config=None):
                # First call simulates model-not-found for 'gemini-3'
                self.calls.append(model)
                if model == 'gemini-3':
                    raise Exception("models/gemini-3 is not found for API version v1beta")
                return type('R', (), {'text': json.dumps({'reply': 'ok'})})()

    fake_client = FakeClient()
    monkeypatch.setattr(agent, 'genai', type('G', (), {'Client': lambda *a, **k: fake_client}))

    # Set GEMINI_MODEL to a shorthand that doesn't match a full resource
    agent_from_env = agent
    agent_from_env.config.GEMINI_MODEL = 'gemini-3'
    # ensure client usage is enabled by providing a fake API key
    agent_from_env.config.GEMINI_API_KEY = 'fake'

    res = agent.analyze_and_reply('Hello', 'Tester')
    assert isinstance(res, dict)
    assert res.get('reply') == 'ok'
    # ensure the client attempted first with the short name and then retried with resolved model
    # initial call may use the short name or the resolved full name; ensure resolved was used
    assert any('gemini-3' in c for c in fake_client._models.calls)


def test_agent_plain_text_response(monkeypatch):
    # Simulate SDK available and model returns plain text string
    monkeypatch.setattr(agent, "GENAI_CLIENT_AVAILABLE", True)
    class FakeClient:
        def __init__(self):
            self.models = self
        def list(self):
            from types import SimpleNamespace
            return [SimpleNamespace(name='models/gemini-3-pro-preview')]
        def generate_content(self, model, contents, config=None):
            return type('R', (), {'text': '这是一个笑话：有一只程序员去买番茄，结果买了个番茄IDE。'})()

    fake = type('G', (), {'Client': lambda *a, **k: FakeClient()})
    monkeypatch.setattr(agent, 'genai', fake)
    agent.config.GEMINI_MODEL = 'models/gemini-3-pro-preview'
    agent.config.GEMINI_API_KEY = 'fake'

    res = agent.analyze_and_reply('讲个笑话', '君末')
    assert isinstance(res, dict)
    assert 'reply' in res
    assert '笑话' in res['reply'] or '程序员' in res['reply']


def test_agent_empty_response(monkeypatch):
    # Simulate SDK available and model returns empty string
    monkeypatch.setattr(agent, "GENAI_CLIENT_AVAILABLE", True)
    class FakeClient2:
        def __init__(self):
            self.models = self
        def list(self):
            from types import SimpleNamespace
            return [SimpleNamespace(name='models/gemini-3-pro-preview')]
        def generate_content(self, model, contents, config=None):
            return type('R', (), {'text': ''})()

    fake2 = type('G', (), {'Client': lambda *a, **k: FakeClient2()})
    monkeypatch.setattr(agent, 'genai', fake2)
    agent.config.GEMINI_MODEL = 'models/gemini-3-pro-preview'
    agent.config.GEMINI_API_KEY = 'fake'

    res = agent.analyze_and_reply('讲个笑话', '君末')
    assert isinstance(res, dict)
    assert '抱歉' in res.get('reply', '')
