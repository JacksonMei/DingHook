# DingHook + Mem0 集成文档

## 架构概述

这是一个基于 Mem0 个性化记忆层的智能钉钉机器人实现，实现了以下流程：

```
钉钉消息 → Mem0 add() → Mem0 search() → 拼接 Prompt → LLM → 钉钉回复
```

## 核心流程

### 1. 钉钉接收消息
用户通过钉钉应用发送消息到 webhook 端点 `/webhook`

### 2. Mem0 add() - 存入当前对话
```python
# agent.py - analyze_and_reply() 函数中
messages = [{"role": "user", "content": content}]
mem0_mgr.add_memory(messages, user_id)
```
将用户的当前消息和上下文存入 Mem0 的长期记忆数据库

### 3. Mem0 search() - 获取相关记忆
```python
# agent.py - analyze_and_reply() 函数中
relevant_memories = mem0_mgr.search_memories(content, user_id, limit=5)
```
根据当前消息内容，从 Mem0 搜索最相关的 5 条用户记忆

### 4. 拼接 Prompt
```python
# 将相关记忆格式化并注入到系统提示词中
prompt_parts = [
    "你是一个贴心且记忆力超群的助手...",
    "关于用户的相关信息（基于历史对话）：\n- 用户记忆1\n- 用户记忆2",
    f"用户消息:\n{content}",
    "请返回 JSON: {\"reply\": <回复文本>}"
]
prompt = "\n".join(prompt_parts)
```

### 5. 调用 LLM
```python
raw = _call_model(prompt)
parsed = json.loads(raw)
```
使用 Gemini 模型生成个性化回复

### 6. 返回给钉钉
```python
sender.send_text_from_env(reply, at_user_ids=[sender_id])
```
将回复发送回钉钉会话

## 关键文件说明

### dingbot/mem0_manager.py
Mem0 内存管理器，封装了 Mem0 SDK 的以下功能：
- `add_memory()` - 添加消息到用户的长期记忆
- `search_memories()` - 根据查询搜索相关记忆
- `format_memories_as_context()` - 将记忆格式化为提示词上下文
- `get_user_profile()` - 获取用户的个人资料摘要
- `build_system_prompt()` - 构建包含记忆的系统提示词

### dingbot/agent.py
主要的对话处理器。改进后包含：
1. Mem0 集成的 `analyze_and_reply()` 函数
2. 完整的流程：add → search → prompt → LLM
3. 后向兼容的本地内存支持

### dingbot/server.py
Flask webhook 服务器。改进包括：
- 初始化时调用 `init_mem0()`
- 支持原有的 `/remember`, `/forget`, `/memories` 命令
- 现在还支持 Mem0 驱动的自动记忆功能

## 安装和配置

### 前置条件
1. Python 3.8+
2. 钉钉应用的 ACCESS_TOKEN 和 SECRET
3. Gemini API Key（用于 LLM）
4. OpenAI API Key（用于 Mem0 的嵌入模型）

### 安装依赖
```bash
pip install -r dingbot/requirements.txt
```

### 环境变量配置
```bash
# 钉钉配置
export ACCESS_TOKEN=your_dingtalk_access_token
export SECRET=your_secret

# Gemini LLM 配置
export GEMINI_API_KEY=your_gemini_api_key

# Mem0 配置（使用 OpenAI embeddings）
export OPENAI_API_KEY=your_openai_api_key

# 其他配置（可选）
export PORT=8080
export DATABASE_PATH=dingbot_memory.db
export CHECK_INTERVAL_SECONDS=60
```

### 启动服务
```bash
python -m dingbot.server
```

或使用 Docker Compose：
```bash
docker-compose up
```

## 使用示例

### 基础对话（带自动记忆）
```
用户: 你好，我叫张三，我喜欢编程
机器人: 你好张三！很高兴认识你，编程确实很有趣！

用户: 最近在学什么呢？
机器人: 根据你之前的对话，我记得你喜欢编程。最近在学什么新的编程语言或框架吗？
```

### 命令功能（旧功能保留）
```
/help              - 显示帮助信息
/remember <n> <text> - 每 n 秒推送一条记忆
/memories          - 列出所有记忆
/forget <id>       - 删除指定记忆
/ping              - 测试机器人
/time              - 获取当前时间
```

## Mem0 工作原理

### 记忆存储
- 使用向量数据库存储用户交互的嵌入向量
- 支持多种后端：Qdrant, Pinecone, Chroma 等
- 默认使用本地文件存储（开发模式）

### 记忆检索
- 基于语义相似度搜索相关记忆
- 支持自定义的相关性评分
- 可配置返回结果数量

### 记忆优化
- 自动聚类相似的记忆
- 周期性清理过期记忆
- 支持用户级别的隐私控制

## 测试

运行集成测试验证整个流程：
```bash
pytest tests/test_mem0_integration.py -v -s
```

### 测试覆盖
1. Mem0Manager 初始化和基本操作
2. agent.analyze_and_reply 与 Mem0 集成
3. 完整的钉钉 → Mem0 → LLM → 钉钉流程
4. 内存搜索和上下文格式化
5. 错误处理和降级机制

## 性能优化

### 记忆搜索优化
- 默认限制搜索结果为 5 条，降低 token 消耗
- 使用向量相似度快速过滤
- 可根据需要调整搜索数量

### 并发处理
- 支持多用户并发对话
- 每个用户有独立的记忆空间
- 可配置超时防止长时间阻塞

### 成本控制
- 避免不必要的 LLM 调用
- 优化 token 使用
- 支持本地回退模式

## 常见问题

### Q: Mem0 需要什么向量数据库？
A: 默认使用本地文件存储。生产环境建议使用 Qdrant 或 Pinecone。

### Q: 如何清空用户的记忆？
A: 目前没有直接的 API，可以通过 Mem0 管理界面或数据库直接操作。

### Q: 记忆数据存在哪里？
A: 默认在本地文件系统。Mem0 支持多种存储后端配置。

### Q: 如何处理隐私敏感信息？
A: 建议在记忆前进行数据脱敏，或配置 Mem0 的隐私过滤。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      DingTalk 应用                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    POST /webhook
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Flask Server (server.py)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. 接收钉钉消息                                       │  │
│  │  2. 调用 agent.analyze_and_reply()                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Agent (agent.py)                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Mem0 add() - 存入当前对话                        │  │
│  │  2. Mem0 search() - 获取相关记忆                    │  │
│  │  3. 拼接 Prompt - 注入记忆上下文                    │  │
│  │  4. 调用 LLM - Gemini 生成回复                      │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
┌───────────▼──────────┐    ┌────────────▼─────────────┐
│  Mem0 Manager        │    │  LLM (Gemini)            │
│  (mem0_manager.py)   │    │  via _call_model()       │
│  ┌────────────────┐  │    │  ┌─────────────────────┐ │
│  │ add_memory()   │  │    │  │ Generate response   │ │
│  │ search_memory()│  │    │  │ with context        │ │
│  │ format()       │  │    │  └─────────────────────┘ │
│  └────────────────┘  │    └──────────────────────────┘
│  ┌────────────────┐  │
│  │ Mem0 SDK       │  │
│  │ (Vector DB)    │  │
│  └────────────────┘  │
└──────────────────────┘
            │
            │
┌───────────▼──────────────────────────────────────────────┐
│          DingTalk Sender (sender.py)                     │
│  将 AI 回复发送回钉钉会话                                  │
└──────────────────────────────────────────────────────────┘
```

## 未来改进

1. **多模态支持** - 支持图片和语音消息
2. **用户分组** - 针对不同用户组的个性化策略
3. **记忆优先级** - 按重要性加权记忆检索
4. **主动推送** - 基于用户行为的主动消息
5. **隐私增强** - 更完善的数据加密和隐私保护

## 参考资源

- [Mem0 官方文档](https://docs.mem0.ai/)
- [DingTalk API 文档](https://open.dingtalk.com/)
- [Gemini API 文档](https://ai.google.dev/)
