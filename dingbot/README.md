# dingbot

轻量级钉钉机器人服务（Webhook 接收 + Gemini 驱动回复 + 本地记忆与事实提取）

主要组件

- `dingbot/server.py`：Flask webhook 服务器，接收钉钉群消息并调用 `agent` 生成回复。普通消息的 HTTP 响应返回纯文本（text/plain）。
- `dingbot/sender.py`：封装发送消息到钉钉自定义机器人（需要 `ACCESS_TOKEN` + `SECRET`）。
- `dingbot/agent.py`：模型适配器，优先使用官方 `google-genai` SDK（Gemini）；提供 `extract_facts_for_user`、`generate_push_from_facts` 等功能。
- `dingbot/memory_file.py`：以 `JSONL` 追加保存用户消息（默认 `dingbot_memory.jsonl`），轻量且便于调试。
- `dingbot/facts_file.py`：保存按用户提取的事实到 `dingbot_fact.json`。
- `dingbot/scheduler.py`：周期性（默认 60 秒）提取事实并基于事实生成推送消息（无 @）。

快速开始

1. 安装依赖：

   pip install -r dingbot/requirements.txt

2. 设置环境变量：

   - `ACCESS_TOKEN`：钉钉机器人 access_token
   - `SECRET`：钉钉机器人 secret
   - `GEMINI_API_KEY`（必需用于在线推理）：用于官方 Google GenAI SDK (`google-genai`) 的 API Key。
- `GEMINI_MODEL`：要使用的模型名称，推荐示例：`gemini-3` 或 `gemini-3-pro-preview`（可在 Google Gemini 文档中查找可用名称）

注意：本项目严格使用官方 SDK (`google-genai`) 来调用 Gemini，**不会**在运行时使用直接 REST 调用。请确保在运行服务前安装并配置 SDK（参见下面）。

安装官方 SDK（推荐）

    pip install google-genai

示例 SDK 使用方式

- 设置环境变量：

  export GEMINI_API_KEY=your_key_here
  export GEMINI_MODEL=gemini-3

- 启动服务：

  python -m dingbot.server

如果 SDK 未安装并且 `GEMINI_API_KEY` 存在，服务会记录一个警告并回退到本地简易策略，而不是使用 REST API。
   - `DATABASE_PATH`（可选）：SQLite 文件路径，默认 `dingbot_memory.db`

3. 运行 webhook 服务：

   export ACCESS_TOKEN=... SECRET=...
   pip install -r dingbot/requirements.txt  # 包括官方 Gemini client
   python -m dingbot.server

简单测试（示例）

- 添加记忆：
  curl -X POST http://localhost:8080/webhook -H 'Content-Type: application/json' \
       -d '{"msgtype":"text","text":{"content":"/remember 86400 喝水"},"senderNick":"Alice","senderId":"alice123"}'

- 列出记忆：
  curl -X POST http://localhost:8080/webhook -H 'Content-Type: application/json' \
       -d '{"msgtype":"text","text":{"content":"/memories"},"senderNick":"Alice","senderId":"alice123"}'

说明：
- 如果 `GEMINI_API_KEY` 已设置且安装了 `google-generative-ai`，代理会使用官方客户端调用 Gemini（推荐）。
- 若未设置 GEMINI 或在测试环境中，系统会使用本地的回退逻辑，不会导致服务失败。

说明

- 如果 `GEMINI_API_KEY` 和 `GEMINI_API_URL` 未设置，系统会使用简易的本地逻辑作为回退。
- 回复消息会 @ 发送者（如果 webhook 中包含可识别的用户 id），主动推送（定时提醒）不 @ 任何人。

重要变化（存储与调度）

- **本地记忆**: 用户消息追加保存为 JSONL（默认 `dingbot_memory.jsonl`），方便审计和调试。请通过 `MEMORY_FILE` 环境变量自定义位置。
- **事实文件**: 调度器每分钟会提取用户事实写入 `dingbot_fact.json`（可通过 `FACTS_FILE` 配置），这些事实可用于后续上下文增强。
- **调度间隔**: 默认每 60 秒运行一次（可通过 `CHECK_INTERVAL_SECONDS` 调整）。

简单测试（示例）

- 发送普通消息（服务器将返回纯文本 reply）:
  curl -s -X POST http://localhost:8080/webhook \
    -H 'Content-Type: application/json' \
    -d '{"msgtype":"text","text":{"content":"讲个笑话"},"senderNick":"君末","senderId":"user-123"}'

- 查看本地记忆:
  tail -n 50 dingbot_memory.jsonl

- 手动触发一次事实提取并推送:
  python -c "from dingbot import scheduler; scheduler.run_cycle()"

安全建议（必读）

- **不要在仓库或注释中提交真实密钥**。如果发现误提交，请立即在相应平台撤销/替换该密钥（rotate），并从 Git 历史中移除（例如使用 `git filter-repo`）。
- `.env.example` 用来说明需要哪些环境变量，不应包含真实凭证。

测试

    env PYTHONPATH=. pytest -q

常见问题

- 模型返回非 JSON 或空字符串时，agent 会把原始文本作为回复处理（不抛异常）。
- 如需真实 E2E 测试，请确保 `GEMINI_API_KEY` 在环境中，并使用 `client.models.list()` 检查账号可用模型。

---

安全提醒：仓库已移除明显示例凭证并在 README 中增加密钥管理说明。

