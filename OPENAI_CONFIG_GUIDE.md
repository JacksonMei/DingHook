# OpenAI 客户端配置指南

## 概述

DingHook 现已统一使用 OpenAI 兼容客户端，支持：

- ✅ OpenAI API (官方)
- ✅ Azure OpenAI
- ✅ Ollama (本地)
- ✅ vLLM (本地)
- ✅ 其他兼容端点

## 必需的环境变量

### 1. OPENAI_API_KEY (必需)
```bash
export OPENAI_API_KEY=sk-your-api-key-here
```
- **OpenAI**: 从 https://platform.openai.com/api-keys 获取
- **Azure OpenAI**: 从 Azure 门户获取
- **Ollama/vLLM**: 通常无需真实 API Key，可设为任意值

### 2. OPENAI_API_BASE (可选，有默认值)
```bash
export OPENAI_API_BASE=https://api.openai.com/v1
```

**默认值**: `https://api.openai.com/v1`

**其他常用值**:
- Azure: `https://<resource-name>.openai.azure.com/`
- Ollama: `http://localhost:11434/v1`
- vLLM: `http://localhost:8000/v1`

### 3. OPENAI_MODEL (可选，有默认值)
```bash
export OPENAI_MODEL=gpt-4-turbo
```

**默认值**: `gpt-4-turbo`

**其他选项**:
- OpenAI: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Azure: `<deployment-name>`
- Ollama: `llama2`, `mistral`, etc.
- vLLM: 根据你部署的模型

## 快速开始

### 场景 1: 使用官方 OpenAI API

```bash
export OPENAI_API_KEY=sk-xxx-yyy-zzz
export OPENAI_API_BASE=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4-turbo

python -m dingbot.server
```

### 场景 2: 使用 Azure OpenAI

```bash
export OPENAI_API_KEY=<your-azure-key>
export OPENAI_API_BASE=https://my-resource.openai.azure.com/
export OPENAI_MODEL=<deployment-name>

python -m dingbot.server
```

### 场景 3: 使用本地 Ollama

```bash
# 首先启动 Ollama
ollama run llama2

# 然后在另一个终端配置并启动 DingHook
export OPENAI_API_KEY=local  # 任意值
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_MODEL=llama2

python -m dingbot.server
```

### 场景 4: 使用本地 vLLM

```bash
# 首先启动 vLLM
python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-2-7b-hf

# 然后在另一个终端配置并启动 DingHook
export OPENAI_API_KEY=local  # 任意值
export OPENAI_API_BASE=http://localhost:8000/v1
export OPENAI_MODEL=meta-llama/Llama-2-7b-hf

python -m dingbot.server
```

### 场景 5: 开发模式（Mock 模式）

```bash
export FORCE_MOCK_OPENAI=1

python -m dingbot.server
```

此时无需真实 API Key，服务使用 Mock 回复。

## 完整的 DingTalk 配置

```bash
# DingTalk 配置
export ACCESS_TOKEN=your_dingtalk_access_token
export SECRET=your_dingtalk_secret

# LLM 配置 (OpenAI)
export OPENAI_API_KEY=sk-xxx
export OPENAI_API_BASE=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4-turbo

# Mem0 配置
# Mem0 会自动使用 OPENAI_API_KEY 作为嵌入模型的 API Key

# 可选配置
export PORT=8080
export DATABASE_PATH=dingbot_memory.db
export CHECK_INTERVAL_SECONDS=60

# 启动服务
python -m dingbot.server
```

## API 密钥获取指南

### OpenAI API Key

1. 访问 https://platform.openai.com/api-keys
2. 点击 "Create new secret key"
3. 复制密钥，格式为 `sk-...`

### Azure OpenAI

1. 登录 Azure 门户
2. 创建 OpenAI 资源
3. 获取"密钥和端点"中的 Key 1
4. 获取"概览"中的端点 URL

### 本地模型 (Ollama)

1. 安装 Ollama: https://ollama.ai
2. 运行 `ollama run llama2`
3. API Key 可以是任意值 (本地不需要认证)
4. 默认地址: http://localhost:11434

### 本地模型 (vLLM)

1. 安装 vLLM: `pip install vllm`
2. 启动 vLLM 服务器
3. API Key 可以是任意值
4. 默认地址: http://localhost:8000

## 测试 API 连接

### 方法 1: 运行测试

```bash
cd /home/meijun/dinghook_mem0
export OPENAI_API_KEY=sk-your-key
export OPENAI_API_BASE=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4-turbo

python -m pytest tests/test_mem0_integration.py -v
```

### 方法 2: 使用 Mock 模式

```bash
export FORCE_MOCK_OPENAI=1
python -m dingbot.server
```

### 方法 3: 直接测试端点

```bash
# 测试 OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 测试 Ollama
curl http://localhost:11434/api/tags
```

## 常见问题

### Q: 如何切换不同的 OpenAI API 提供商？

A: 只需修改 `OPENAI_API_BASE` 和 `OPENAI_MODEL` 环境变量，无需修改代码。

```bash
# 从 OpenAI 切换到 Azure
export OPENAI_API_BASE=https://my-resource.openai.azure.com/
export OPENAI_MODEL=my-deployment

# 从 OpenAI 切换到 Ollama
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_MODEL=llama2
```

### Q: 支持哪些模型？

A: 取决于你的 API 提供商：
- **OpenAI**: gpt-4, gpt-4-turbo, gpt-3.5-turbo 等
- **Azure**: 你部署的任何模型
- **Ollama**: llama2, mistral, neural-chat 等
- **vLLM**: 任何支持的 LLM 模型

### Q: 如何使用本地模型？

A: 推荐使用 Ollama 或 vLLM：

```bash
# Ollama (最简单)
ollama run llama2
# 然后设置: OPENAI_API_BASE=http://localhost:11434/v1
```

### Q: 超时了怎么办？

A: 增加超时时间或检查网络连接：
- 本地模型可能需要更长时间
- 检查 API 端点是否正确
- 测试网络连接

### Q: 能否离线使用？

A: 可以，使用本地模型：
1. 安装 Ollama 或 vLLM
2. 下载本地模型
3. 启动本地服务
4. 配置 `OPENAI_API_BASE` 为本地地址

### Q: 如何处理 API 错误？

A: 检查以下几点：
- ✅ API Key 是否正确
- ✅ API Base URL 是否正确
- ✅ 模型名称是否存在
- ✅ 网络连接是否正常
- ✅ 账户是否有余额 (OpenAI)

## 环境变量总结

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | 无 | **必需**: API 认证密钥 |
| `OPENAI_API_BASE` | https://api.openai.com/v1 | API 端点 URL |
| `OPENAI_MODEL` | gpt-4-turbo | 使用的模型名称 |
| `FORCE_MOCK_OPENAI` | 无 | 设为 1 启用 Mock 模式 |

## 支持的端点

| 提供商 | API Base | 模型示例 | 认证 |
|-------|---------|--------|------|
| OpenAI | https://api.openai.com/v1 | gpt-4-turbo | API Key |
| Azure | https://\<name\>.openai.azure.com/ | \<deployment\> | API Key |
| Ollama | http://localhost:11434/v1 | llama2 | 可选 |
| vLLM | http://localhost:8000/v1 | 自定义 | 可选 |
| Hugging Face | https://api-inference.huggingface.co | 自定义 | Token |

## 故障排除

### 连接失败

```bash
# 检查 API Base
curl $OPENAI_API_BASE/models -H "Authorization: Bearer $OPENAI_API_KEY"

# 本地模型检查
curl http://localhost:11434/api/tags
```

### 认证失败

```bash
# 验证 API Key 格式
echo $OPENAI_API_KEY  # OpenAI 应该以 sk- 开头

# Azure: 检查密钥是否复制完整
```

### 模型不存在

```bash
# 列出可用模型
curl $OPENAI_API_BASE/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## 参考资源

- [OpenAI API 文档](https://platform.openai.com/docs)
- [Azure OpenAI 文档](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Ollama](https://ollama.ai)
- [vLLM](https://github.com/lm-sys/vllm)
