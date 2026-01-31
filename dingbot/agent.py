"""Agent adapter to call Gemini-like model using API Key, with a simple fallback.

The adapter expects two environment variables when using a real model:
- GEMINI_API_KEY
- GEMINI_API_URL

It will send a JSON payload {"model": <name>, "input": <prompt>} and expect a plain text response.
"""

import json
import requests
from typing import List, Dict, Any, Optional

from . import config

import logging
import time
import concurrent.futures
import os

# Prefer the new official GenAI client if available: `from google import genai` and `from google.genai import types`
try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
    GENAI_CLIENT_AVAILABLE = True
except Exception:
    genai = None  # type: ignore
    types = None  # type: ignore
    GENAI_CLIENT_AVAILABLE = False

# Backwards-compatible alias for older test code
GENAI_AVAILABLE = GENAI_CLIENT_AVAILABLE

logger = logging.getLogger(__name__)


def _call_model(prompt: str, timeout: int = 8) -> str:
    """Call Gemini model using the official Google client with a timeout and clear logging.

    The function will try, in order:
    - Official `google.generativeai` client (if installed and API key present)
    - A configured `GEMINI_API_URL` HTTP endpoint
    - A local heuristic fallback

    Calls to remote services are executed in a worker thread and will be aborted after `timeout` seconds,
    returning the local fallback to keep the bot responsive.

    For local development you can set `FORCE_MOCK_GENAI=1` in the environment to force a fast mock reply.
    """
    # Development/testing shortcut: force a fast mock reply
    if os.getenv("FORCE_MOCK_GENAI"):
        logger.info("Agent: FORCE_MOCK_GENAI enabled, returning mock response")
        return json.dumps({"reply": "(mock) 我已看到你的消息并已记录。", "save_memory": {"interval": 3600, "content": "mock memory"}})

    # If an API key is present but the official SDK is not installed, return a clear JSON reply
    if config.GEMINI_API_KEY and not GENAI_CLIENT_AVAILABLE:
        logger.warning("Gemini API key present but official SDK not available; REST calls are disabled by policy."
                       " Please install 'google-genai' to enable Gemini.")
        return json.dumps({
            "reply": "抱歉，机器人未启用 Gemini SDK（缺少 'google-genai'）。管理员请安装并重启服务。",
        })

    start = time.perf_counter()

    def _resolve_model_name(preferred: Optional[str]) -> Optional[str]:
        """Resolve a user-provided model name to an available model via the SDK.

        If the SDK is available and an API key is present, this will list models and
        attempt to find the best match. It prefers exact matches, then substring
        matches (e.g., 'gemini-3' -> 'models/gemini-3-pro-preview'), then sensible
        fallbacks like gemini-2.5 models.
        """
        if not (GENAI_CLIENT_AVAILABLE and config.GEMINI_API_KEY):
            return preferred
        try:
            client = genai.Client()
            names = [getattr(m, "name", None) for m in client.models.list()]
            names = [n for n in names if n]
            if not names:
                return preferred

            # If preferred already looks like a full model resource or exact match, return it
            if not preferred:
                # pick a reasonable default: prefer gemini-3, then gemini-2.5, then first
                for n in names:
                    if "gemini-3" in n:
                        return n
                for n in names:
                    if "gemini-2.5" in n:
                        return n
                return names[0]

            if preferred in names or preferred.startswith("models/") or "/" in preferred:
                return preferred

            # substring / suffix match
            for n in names:
                if preferred in n:
                    return n
            bare = preferred.split('/')[-1]
            for n in names:
                if bare in n:
                    return n
            # fallback to first gemini-3 or first model
            for n in names:
                if "gemini-3" in n:
                    return n
            return names[0]
        except Exception:
            logger.exception("Agent: model resolution via list failed")
            return preferred

    def _call_official():
        # Use the official google.genai client if available
        # This follows the pattern:
        #   from google import genai
        #   from google.genai import types
        #   client = genai.Client()
        #   resp = client.models.generate_content(...)
        client = genai.Client()
        raw_model = config.GEMINI_MODEL or "gemini-3"
        model = _resolve_model_name(raw_model) or raw_model

        def _call_with_model(m: str):
            if types is not None:
                cfg = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low")
                )
                return client.models.generate_content(model=m, contents=prompt, config=cfg)
            else:
                return client.models.generate_content(model=m, contents=prompt)

        try:
            resp = _call_with_model(model)
        except Exception as e:
            # If the error suggests the model is not found, try to resolve with the SDK list
            msg = str(e).lower()
            if "not found" in msg or "is not found" in msg or "not supported" in msg:
                logger.warning("Agent: model '%s' not found, attempting to resolve a compatible model", model)
                fallback = _resolve_model_name(raw_model)
                if fallback and fallback != model:
                    logger.info("Agent: retrying with resolved model %s", fallback)
                    try:
                        resp = _call_with_model(fallback)
                    except Exception:
                        # re-raise original for outer handler
                        raise
                else:
                    raise
            else:
                # Re-raise so outer _call_model will handle logging and fallback
                raise

        # Many client responses expose `.text` or `.output`; try common accessors
        # Return `.text` even if it's empty so the caller can handle empty replies explicitly
        if hasattr(resp, "text"):
            return resp.text
        if hasattr(resp, "output") and resp.output:
            first = resp.output[0]
            if hasattr(first, "content") and isinstance(first.content, str):
                return first.content
        # Fallback to stringifying the response
        return str(resp)

    def _http_fallback():
        payload = {"model": config.GEMINI_MODEL, "input": prompt}
        headers = {"Authorization": f"Bearer {config.GEMINI_API_KEY}", "Content-Type": "application/json"}
        resp = requests.post(config.GEMINI_API_URL, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text

    # Try older genai.generate_text API (backwards compatibility)
    if getattr(genai, "generate_text", None):
        logger.info("Agent: calling older genai.generate_text API")
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(lambda: genai.generate_text(model=config.GEMINI_MODEL or "models/gemini-3", prompt=prompt))
                try:
                    resp = fut.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    logger.warning("legacy genai.generate_text timeout after %s seconds", timeout)
                    raise
            # extract text
            if hasattr(resp, "text") and resp.text:
                resp_text = resp.text
            elif isinstance(resp, dict):
                cands = resp.get("candidates") or []
                resp_text = (cands[0].get("content") if cands else json.dumps(resp))
            else:
                resp_text = str(resp)
            elapsed = time.perf_counter() - start
            logger.info("Agent: legacy genai returned in %.2fs", elapsed)
            return resp_text
        except Exception as e:
            logger.exception("Agent: legacy genai call failed: %s", e)
            # fall through to newer client / rest / fallback

    # Try modern google.genai client if available
    if GENAI_CLIENT_AVAILABLE and config.GEMINI_API_KEY:
        logger.info("Agent: calling google.genai client for model %s", config.GEMINI_MODEL)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_call_official)
                try:
                    resp = fut.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    logger.warning("Gemini client timeout after %s seconds", timeout)
                    raise
            # resp is expected to be a string already from _call_official
            resp_text = resp if isinstance(resp, str) else str(resp)
            elapsed = time.perf_counter() - start
            logger.info("Agent: google.genai client returned in %.2fs", elapsed)
            return resp_text
        except Exception as e:
            logger.exception("Agent: google.genai client call failed: %s", e)
            # fall through to REST or local fallback

    # NOTE: per project policy, we do NOT use the REST Generative Language API here.
    # The agent will use the official `google.genai` SDK client when available. If it is
    # not installed or an SDK call fails, we fall back to a local heuristic only (no REST).
    if config.GEMINI_API_KEY and not GENAI_CLIENT_AVAILABLE:
        logger.warning("Gemini API key present but official SDK not available; REST calls are disabled by policy. Install 'google-genai' to enable SDK usage.")

from .memory_file import get_user_memories
from .mem0_manager import get_mem0_manager

def analyze_and_reply(content: str, sender_name: str, user_id: str = None) -> Dict[str, Any]:
    """Return a dict with keys: reply (str), optional save_memory dict {interval, content}.

    流程:
    1. 调用 Mem0 add() 存入当前对话
    2. 调用 Mem0 search() 获取相关记忆
    3. 拼接 Prompt 喂给 LLM
    4. 返回回复
    """
    if not user_id:
        user_id = sender_name
    
    # 1. 将当前消息加入 Mem0 记忆
    mem0_mgr = get_mem0_manager()
    if mem0_mgr:
        try:
            messages = [
                {"role": "user", "content": content}
            ]
            mem0_mgr.add_memory(messages, user_id)
            logger.info(f"Added message to Mem0 for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to add memory to Mem0: {e}")
    
    # 2. 从 Mem0 search() 获取相关记忆
    relevant_memories = []
    if mem0_mgr:
        try:
            relevant_memories = mem0_mgr.search_memories(content, user_id, limit=5)
            logger.info(f"Found {len(relevant_memories)} relevant memories for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to search memories from Mem0: {e}")
    
    # 3. 拼接 Prompt
    prompt_parts = [f"你是一个贴心且记忆力超群的助手。请简洁、自然地回复用户 '{sender_name}'。"]
    
    # 添加 Mem0 的相关记忆
    if relevant_memories:
        memories_text = mem0_mgr.format_memories_as_context(relevant_memories) if mem0_mgr else ""
        if memories_text:
            prompt_parts.append(f"关于用户的相关信息（基于历史对话）：\n{memories_text}")
    
    # 添加用户当前消息
    prompt_parts.append(f"\n用户消息:\n{content}")
    
    # 添加本地历史（保持向后兼容）
    memories = get_user_memories(user_id, limit=5) if user_id else []
    if memories:
        prompt_parts.append("最近消息摘要：")
        for m in memories[:3]:  # 只取最近 3 条本地消息
            prompt_parts.append(f"- {m['content']}")
    
    prompt_parts.append("\n请返回 JSON: {\"reply\": <回复文本>}，不要包含其它内容。")
    prompt = "\n".join(prompt_parts)

    try:
        # 4. 调用 LLM 获取回复
        raw = _call_model(prompt)
        if raw is None or not str(raw).strip():
            logger.warning("Agent: model returned empty response for prompt")
            return {"reply": "抱歉，未收到模型回复，请稍候再试。"}
        raw_s = str(raw).strip()
        try:
            parsed = json.loads(raw_s)
            if isinstance(parsed, dict):
                return parsed
            return {"reply": parsed if isinstance(parsed, str) else json.dumps(parsed)}
        except json.JSONDecodeError:
            logger.info("Agent: model returned non-JSON text; using it as reply")
            return {"reply": raw_s}
    except Exception as e:
        logger.exception("Agent: analyze_and_reply failed: %s", e)
        return {"reply": "抱歉，处理失败。"}


def generate_push_message(memory: Dict[str, Any]) -> str:
    """Generate a personalized push message for a memory using the model (or a simple template)."""
    content = memory.get("content")
    prompt = f"Write a friendly short reminder message for: {content}\nOutput only the message text."
    try:
        raw = _call_model(prompt)
        # if model returned JSON, try parse; else return raw
        try:
            parsed = json.loads(raw)
            return parsed.get("reply") or json.dumps(parsed)
        except Exception:
            return raw.strip()
    except Exception:
        return f"提醒: {content}"


def extract_facts_for_user(user_id: str, max_messages: int = 50) -> List[Dict[str, Any]]:
    """Use the model to extract objective facts from a user's recent messages.

    Returns a list of dicts representing facts (e.g., [{"fact": "喜欢猫"}, ...])
    """
    from .memory_file import get_user_memories
    msgs = get_user_memories(user_id, limit=max_messages)
    if not msgs:
        return []
    prompt_parts = ["从以下用户消息中提取客观事实（不包含主观判断）。\n请以 JSON 数组的形式返回，每个元素为 {\"fact\": <简短事实文本>} 。\n消息列表："]
    for m in msgs:
        prompt_parts.append(f"- {m.get('content')}")
    prompt = "\n".join(prompt_parts)
    try:
        raw = _call_model(prompt, timeout=10)
        if not raw or not str(raw).strip():
            return []
        raw_s = str(raw).strip()
        try:
            parsed = json.loads(raw_s)
            # normalize to list of dicts
            if isinstance(parsed, list):
                res = []
                for item in parsed:
                    if isinstance(item, str):
                        res.append({"fact": item})
                    elif isinstance(item, dict) and "fact" in item:
                        res.append({"fact": item["fact"]})
                return res
            elif isinstance(parsed, dict) and "facts" in parsed:
                arr = parsed.get("facts") or []
                return [{"fact": f} if isinstance(f, str) else f for f in arr]
            else:
                return [{"fact": str(parsed)}]
        except json.JSONDecodeError:
            # Try to extract JSON inside markdown/code fences like ```json ... ```
            import re
            m = re.search(r"```(?:json)?\s*(\[.*\]|\{.*\})\s*```", raw_s, flags=re.S)
            if m:
                candidate = m.group(1)
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, list):
                        return [{"fact": (i.get('fact') if isinstance(i, dict) else str(i))} for i in parsed]
                    elif isinstance(parsed, dict) and 'facts' in parsed:
                        arr = parsed.get('facts') or []
                        return [{"fact": f} if isinstance(f, str) else f for f in arr]
                    else:
                        return [{"fact": str(parsed)}]
                except Exception:
                    pass

            # Try to find a JSON array or object substring
            first_array = raw_s.find('[')
            last_array = raw_s.rfind(']')
            if first_array != -1 and last_array != -1 and last_array > first_array:
                try:
                    candidate = raw_s[first_array:last_array+1]
                    parsed = json.loads(candidate)
                    if isinstance(parsed, list):
                        return [{"fact": (i.get('fact') if isinstance(i, dict) else str(i))} for i in parsed]
                except Exception:
                    pass
            first_obj = raw_s.find('{')
            last_obj = raw_s.rfind('}')
            if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
                try:
                    candidate = raw_s[first_obj:last_obj+1]
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict) and 'facts' in parsed:
                        arr = parsed.get('facts') or []
                        return [{"fact": f} if isinstance(f, str) else f for f in arr]
                except Exception:
                    pass

            # fallback: try to extract quoted text after "fact": patterns
            facts = []
            for line in raw_s.splitlines():
                line = line.strip()
                if not line:
                    continue
                m2 = re.search(r'"fact"\s*:\s*"([^"]+)"', line)
                if m2:
                    facts.append({"fact": m2.group(1)})
                else:
                    # keep line as a single fact candidate
                    facts.append({"fact": line})
            # If the parse above produced many tiny tokens like '{' or '[' single chars, join into a single fact
            if len(facts) > 3 and all(len(f['fact']) <= 3 for f in facts):
                combined = ' '.join(f['fact'] for f in facts if f['fact'] not in ['{','}','[',']','```','json'])
                return [{"fact": combined.strip()}] if combined.strip() else []
            return facts
    except Exception:
        logger.exception("Agent: extract_facts_for_user failed for %s", user_id)
        return []


def generate_push_from_facts(user_id: str, facts: List[Dict[str, Any]]) -> str:
    """Generate a short push message for a user using their facts as context."""
    if not facts:
        return "提醒: 保持关注，今天也要注意身体哦。"
    facts_text = "\n".join([f"- {f.get('fact')}" for f in facts])
    prompt = f"为用户写一段友好的、简短的推送消息，基于以下事实（不要@用户，输出仅为消息文本）：\n{facts_text}\n请仅输出最终消息。"
    try:
        raw = _call_model(prompt, timeout=8)
        if not raw or not str(raw).strip():
            return "提醒: 保持关注，今天也要注意身体哦。"
        try:
            parsed = json.loads(raw)
            return parsed.get("reply") or (parsed.get("message") if isinstance(parsed, dict) else str(parsed))
        except Exception:
            return str(raw).strip()
    except Exception:
        return "提醒: 保持关注，今天也要注意身体哦。"