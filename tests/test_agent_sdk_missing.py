import dingbot.agent as agent
import dingbot.config as config


def test_api_key_but_sdk_missing(monkeypatch, tmp_path):
    # Simulate API key present but SDK unavailable
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(agent, "GENAI_CLIENT_AVAILABLE", False)

    res = agent.analyze_and_reply("请记住：测试记忆", "Tester")
    assert isinstance(res, dict)
    assert "未启用 Gemini SDK" in res["reply"] or "缺少 'google-genai'" in res["reply"]
