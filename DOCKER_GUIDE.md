# Docker 部署指南

## 📦 镜像构建

### 自动构建脚本
```bash
bash docker-run.sh
```

### 手动构建
```bash
docker build -t dinghook-mem0:latest -f dingbot/Dockerfile .
```

## 🚀 快速启动

### 1. Mock 模式（开发）
用于测试，不需要真实 API 密钥：

```bash
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  -e OPENAI_API_KEY="test-mock-key" \
  -e OPENAI_MODEL="gpt-4-turbo" \
  -e OPENAI_REQUEST_TIMEOUT="30" \
  -e FORCE_MOCK_OPENAI="1" \
  -e FLASK_ENV="development" \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

### 2. NVIDIA GLM4.7（生产）
使用 NVIDIA 的免费 API 端点：

```bash
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  -e OPENAI_API_KEY="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" \
  -e OPENAI_API_BASE="https://integrate.api.nvidia.com/v1" \
  -e OPENAI_MODEL="z-ai/glm4.7" \
  -e OPENAI_REQUEST_TIMEOUT="90" \
  -e FLASK_ENV="production" \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

### 3. OpenAI 官方（生产）
使用 OpenAI 官方 API：

```bash
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  -e OPENAI_API_KEY="sk-YOUR_API_KEY_HERE" \
  -e OPENAI_API_BASE="https://api.openai.com/v1" \
  -e OPENAI_MODEL="gpt-4-turbo" \
  -e OPENAI_REQUEST_TIMEOUT="30" \
  -e FLASK_ENV="production" \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

### 4. Azure OpenAI（生产）
使用 Azure 部署的 OpenAI：

```bash
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  -e OPENAI_API_KEY="your-azure-key" \
  -e OPENAI_API_BASE="https://your-resource.openai.azure.com/" \
  -e OPENAI_MODEL="your-deployment-name" \
  -e OPENAI_REQUEST_TIMEOUT="30" \
  -e FLASK_ENV="production" \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

### 5. Ollama 本地模型（开发）
使用本地 Ollama 模型服务：

```bash
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  -e OPENAI_API_KEY="dummy" \
  -e OPENAI_API_BASE="http://ollama:11434/v1" \
  -e OPENAI_MODEL="llama2" \
  -e OPENAI_REQUEST_TIMEOUT="120" \
  -e FLASK_ENV="development" \
  -v dinghook_data:/data \
  --network host \
  dinghook-mem0:latest
```

## 📋 环境变量说明

| 变量 | 必需 | 默认值 | 说明 |
|-----|------|--------|------|
| `OPENAI_API_KEY` | ✅ | 无 | LLM API 密钥 |
| `OPENAI_API_BASE` | ❌ | https://api.openai.com/v1 | API 端点 URL |
| `OPENAI_MODEL` | ❌ | gpt-4-turbo | 模型名称 |
| `OPENAI_REQUEST_TIMEOUT` | ❌ | 30 | 请求超时秒数 |
| `FORCE_MOCK_OPENAI` | ❌ | 0 | 1=启用模拟模式，0=真实 API |
| `FLASK_ENV` | ❌ | production | production 或 development |
| `ACCESS_TOKEN` | ❌ | 无 | DingTalk AccessToken（可选） |
| `SECRET` | ❌ | 无 | DingTalk Secret（可选） |

## 🛠️ 容器管理命令

### 查看容器状态
```bash
docker ps -a | grep dinghook
```

### 查看容器日志
```bash
# 实时查看
docker logs -f dinghook-mem0-container

# 查看最后 100 行
docker logs --tail 100 dinghook-mem0-container

# 查看特定时间范围的日志
docker logs --since 10m dinghook-mem0-container
```

### 进入容器
```bash
docker exec -it dinghook-mem0-container bash
```

### 停止容器
```bash
docker stop dinghook-mem0-container
```

### 重启容器
```bash
docker restart dinghook-mem0-container
```

### 删除容器
```bash
docker rm dinghook-mem0-container
```

### 删除镜像
```bash
docker rmi dinghook-mem0:latest
```

## 📊 容器信息查询

### 查看容器占用的资源
```bash
docker stats dinghook-mem0-container
```

### 查看容器详细信息
```bash
docker inspect dinghook-mem0-container
```

### 查看容器网络
```bash
docker inspect -f '{{json .NetworkSettings.Networks}}' dinghook-mem0-container | python -m json.tool
```

## 🌐 API 访问

### 基础健康检查
```bash
curl http://localhost:9090/
```

### 获取帮助
```bash
curl http://localhost:9090/help
```

## 📦 Docker 数据卷

### 查看数据卷
```bash
docker volume ls | grep dinghook
```

### 查看数据卷详情
```bash
docker volume inspect dinghook_data
```

### 备份数据
```bash
docker run --rm -v dinghook_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/dinghook_backup.tar.gz -C /data .
```

### 恢复数据
```bash
docker run --rm -v dinghook_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/dinghook_backup.tar.gz -C /data
```

## 🐳 Docker Compose 启动

如果安装了 docker-compose：

```bash
# 使用 .env 文件配置
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 删除所有数据
docker-compose down -v
```

## 🔧 性能优化

### 限制容器资源
```bash
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  -e OPENAI_API_KEY="..." \
  --cpus="2" \
  --memory="1g" \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

### 设置重启策略
```bash
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  -e OPENAI_API_KEY="..." \
  --restart=unless-stopped \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

## 🚨 故障排查

### 容器无法启动
```bash
# 查看启动错误
docker logs dinghook-mem0-container

# 尝试交互式启动
docker run -it --rm \
  -e OPENAI_API_KEY="..." \
  dinghook-mem0:latest \
  bash
```

### API 无响应
```bash
# 检查容器是否运行
docker ps | grep dinghook

# 检查端口是否开放
netstat -tulpn | grep 9090

# 测试容器内的网络
docker exec dinghook-mem0-container curl http://localhost:8080/
```

### 内存使用过高
```bash
# 查看内存使用
docker stats dinghook-mem0-container

# 重启容器
docker restart dinghook-mem0-container
```

## 📈 监控和日志

### 设置日志驱动
```bash
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  -e OPENAI_API_KEY="..." \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

## 🌍 网络配置

### 连接到自定义网络
```bash
# 创建网络
docker network create dinghook-net

# 运行容器在网络中
docker run -d \
  --name dinghook-mem0-container \
  --network dinghook-net \
  -p 9090:8080 \
  -e OPENAI_API_KEY="..." \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

## 📝 配置文件

使用 `.env` 文件简化配置：

```bash
# .env 文件示例
cat > .env << EOF
OPENAI_API_KEY=nvapi-YOUR_KEY_HERE
OPENAI_API_BASE=https://integrate.api.nvidia.com/v1
OPENAI_MODEL=z-ai/glm4.7
OPENAI_REQUEST_TIMEOUT=90
FLASK_ENV=production
EOF

# 使用 env 文件
docker run -d \
  --name dinghook-mem0-container \
  -p 9090:8080 \
  --env-file .env \
  -v dinghook_data:/data \
  dinghook-mem0:latest
```

## 🎯 快速参考

| 操作 | 命令 |
|------|------|
| 构建镜像 | `docker build -t dinghook-mem0:latest -f dingbot/Dockerfile .` |
| 启动容器 | `docker run -d -p 9090:8080 -e OPENAI_API_KEY="..." dinghook-mem0:latest` |
| 查看日志 | `docker logs -f dinghook-mem0-container` |
| 停止容器 | `docker stop dinghook-mem0-container` |
| 删除容器 | `docker rm dinghook-mem0-container` |
| 进入容器 | `docker exec -it dinghook-mem0-container bash` |
| 查看资源 | `docker stats dinghook-mem0-container` |
| 删除镜像 | `docker rmi dinghook-mem0:latest` |

---

**生成时间**: 2026-01-31
**版本**: 1.0
**状态**: ✅ 生产就绪
