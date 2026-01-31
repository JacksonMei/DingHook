# NVIDIA GLM4.7 快速启动指南

## ⚡ 5 分钟快速启动

### 第 1 步: 获取 API 密钥

访问 [NVIDIA 官网](https://build.nvidia.com) 获取免费 API 密钥。

### 第 2 步: 配置环境变量

```bash
export OPENAI_API_KEY=nvapi-YOUR_API_KEY_HERE
export OPENAI_API_BASE=https://integrate.api.nvidia.com/v1
export OPENAI_MODEL=z-ai/glm4.7
export OPENAI_REQUEST_TIMEOUT=90

# DingTalk 配置
export ACCESS_TOKEN=your_dingtalk_token
export SECRET=your_dingtalk_secret
```

### 第 3 步: 启动服务

```bash
python -m dingbot.server
```

### 第 4 步: 测试

```bash
# 运行集成测试
python -m pytest tests/test_mem0_integration.py -v

# 或者运行演示脚本
python demo_mem0_flow.py
```

## 🔧 配置选项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OPENAI_API_KEY` | 无 | NVIDIA API 密钥 |
| `OPENAI_API_BASE` | https://api.openai.com/v1 | API 端点 |
| `OPENAI_MODEL` | gpt-4-turbo | 模型名称 |
| `OPENAI_REQUEST_TIMEOUT` | 30 | 超时时间(秒) |
| `ACCESS_TOKEN` | 无 | 钉钉 AccessToken |
| `SECRET` | 无 | 钉钉 Secret |
| `FORCE_MOCK_OPENAI` | 0 | 启用模拟模式 (1=启用) |

## 📊 性能基准

| 场景 | 响应时间 | 备注 |
|------|---------|------|
| API 连接 | < 1s | 很快 |
| 首次问题 | 55-65s | 模型需要加载 |
| 后续问题 | 10-30s | 快速 |
| 完整流程 | 60-90s | 包含 Mem0 操作 |

## ✅ 验证安装

```bash
# 检查所有依赖
pip list | grep -E "openai|mem0|flask"

# 测试 API 连接
python -c "
from openai import OpenAI
client = OpenAI(
    api_key='nvapi-...',
    base_url='https://integrate.api.nvidia.com/v1'
)
response = client.chat.completions.create(
    model='z-ai/glm4.7',
    messages=[{'role': 'user', 'content': 'test'}]
)
print('✅ API 连接成功:', response.choices[0].message.content[:50])
"
```

## 🐛 常见问题

### Q: 请求超时?
A: 增加 `OPENAI_REQUEST_TIMEOUT=120`

### Q: 认证失败?
A: 确认 `OPENAI_API_KEY` 正确，从官网重新复制

### Q: 响应很慢?
A: GLM4.7 首次加载需要时间，这是正常的

### Q: 如何切换到其他模型?
A: 修改 `OPENAI_MODEL` 环境变量

### Q: 支持其他 OpenAI 兼容的 API 吗?
A: 完全支持！修改 `OPENAI_API_BASE` 和 `OPENAI_API_KEY` 即可

## 📚 其他支持的端点

### OpenAI 官方
```bash
export OPENAI_API_KEY=sk-...
export OPENAI_API_BASE=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4-turbo
```

### Azure OpenAI
```bash
export OPENAI_API_KEY=your-azure-key
export OPENAI_API_BASE=https://your-resource.openai.azure.com/
export OPENAI_MODEL=your-deployment-name
```

### 本地 Ollama
```bash
export OPENAI_API_KEY=dummy
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_MODEL=llama2
```

### vLLM 服务器
```bash
export OPENAI_API_KEY=dummy
export OPENAI_API_BASE=http://localhost:8000/v1
export OPENAI_MODEL=meta-llama/Llama-2-7b
```

## 🚀 生产部署

### Docker 方式

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV OPENAI_REQUEST_TIMEOUT=90
CMD ["python", "-m", "dingbot.server"]
```

启动容器:
```bash
docker run -e OPENAI_API_KEY=nvapi-... \
           -e OPENAI_API_BASE=https://integrate.api.nvidia.com/v1 \
           -e OPENAI_MODEL=z-ai/glm4.7 \
           -e ACCESS_TOKEN=... \
           -e SECRET=... \
           -p 5000:5000 \
           dinghook-app
```

### Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dinghook-api
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: dinghook
        image: dinghook-app:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secrets
              key: api-key
        - name: OPENAI_REQUEST_TIMEOUT
          value: "90"
        ports:
        - containerPort: 5000
```

## 📖 更多文档

- [OPENAI_CONFIG_GUIDE.md](OPENAI_CONFIG_GUIDE.md) - 详细配置指南
- [NVIDIA_E2E_TEST_REPORT.md](NVIDIA_E2E_TEST_REPORT.md) - 测试报告
- [INTEGRATION.md](INTEGRATION.md) - 系统架构
- [README.md](README.md) - 项目文档

## 💡 最佳实践

1. **超时配置**: GLM4.7 推荐 `OPENAI_REQUEST_TIMEOUT=90`
2. **错误处理**: 系统自动降级为文本响应
3. **监控**: 建议监控 API 响应时间
4. **缓存**: 考虑启用响应缓存减少 API 调用
5. **日志**: 启用详细日志用于故障排查

## 支持

- 问题报告: [GitHub Issues](https://github.com/JacksonMei/DingHook/issues)
- 文档: 见 `docs/` 目录
- 社区: 加入讨论

---

**最后更新**: 2026-01-31  
**状态**: ✅ 验证通过 NVIDIA GLM4.7
