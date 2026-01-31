"""Agent adapter to call LLM models using OpenAI client.

Unified LLM provider using OpenAI API (compatible with OpenAI and OpenAI-compatible endpoints)
Environment variables:
- OPENAI_API_KEY: API key for authentication
- OPENAI_API_BASE: API base URL (default: https://api.openai.com/v1)
- OPENAI_MODEL: Model name (default: gpt-4-turbo)

Supports OpenAI, Azure OpenAI, Ollama, and other compatible endpoints.
"""

import json
from typing import List, Dict, Any, Optional

from . import config
from .memory_file import get_user_memories
from .mem0_manager import get_mem0_manager

import logging
import time
import concurrent.futures
import os

# Try to import OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


def _call_model(prompt: str, timeout: int = 8) -> str:
    """Call LLM model using OpenAI client with a timeout.

    Supports:
    - OpenAI API (https://api.openai.com/v1)
    - Azure OpenAI
    - Ollama (http://localhost:11434/v1)
    - Other OpenAI-compatible endpoints

    Configuration via environment variables:
    - OPENAI_API_KEY: API key
    - OPENAI_API_BASE: API base URL (default: https://api.openai.com/v1)
    - OPENAI_MODEL: Model name (default: gpt-4-turbo)

    For local development, set `FORCE_MOCK_OPENAI=1` to force mock responses.
    """
    # Development/testing shortcut: force a fast mock reply
    if os.getenv("FORCE_MOCK_OPENAI") or os.getenv("FORCE_MOCK_GENAI"):
        logger.info("Agent: Mock mode enabled, returning mock response")
        return json.dumps({"reply": "(mock) 我已看到你的消息并已记录。", "save_memory": {"interval": 3600, "content": "mock memory"}})

    # Validate API key
    if not config.OPENAI_API_KEY:
        logger.error("Agent: OPENAI_API_KEY not configured")
        return json.dumps({
            "reply": "抱歉，LLM 服务未启用。请配置 OPENAI_API_KEY 环境变量。",
        })

    # Check if OpenAI is available
    if not OPENAI_AVAILABLE:
        logger.error("Agent: openai package not installed. Install via: pip install openai")
        return json.dumps({
            "reply": "抱歉，LLM 客户端未安装。请安装 openai 包。",
        })

    start = time.perf_counter()

    def _call_openai():
        """Call OpenAI-compatible API."""
        try:
            client = OpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_API_BASE
            )
            
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024,
                timeout=timeout
            )
            
            # Extract response text
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                logger.warning("Agent: No choices in OpenAI response")
                return None
                
        except Exception as e:
            logger.exception(f"Agent: OpenAI API call failed: {e}")
            raise

    # Execute the call with timeout protection
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_openai)
            try:
                response_text = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.warning(f"Agent: OpenAI request timeout after {timeout} seconds")
                raise TimeoutError(f"Request timeout after {timeout}s")
        
        elapsed = time.perf_counter() - start
        logger.info(f"Agent: OpenAI responded in {elapsed:.2f}s")
        
        if response_text:
            return response_text
        else:
            logger.warning("Agent: OpenAI returned empty response")
            return json.dumps({"reply": "抱歉，未能生成回复。"})
            
    except TimeoutError:
        logger.warning("Agent: Request timeout")
        return json.dumps({"reply": "抱歉，请求超时。请稍候重试。"})
    except Exception as e:
        logger.exception(f"Agent: Failed to call LLM: {e}")
        return json.dumps({"reply": "抱歉，调用 LLM 失败。"})


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
