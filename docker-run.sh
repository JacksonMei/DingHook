#!/bin/bash

# DingHook Mem0 Docker 快速启动脚本

set -e

CONTAINER_NAME="dinghook-mem0-container"
IMAGE_NAME="dinghook-mem0:latest"
PORT="${PORT:-9090}"
INTERNAL_PORT="8080"

echo "═══════════════════════════════════════════════════════════"
echo "  DingHook + Mem0 + OpenAI Docker 启动脚本"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 检查 Docker 是否运行
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker 未运行或无权限，请先启动 Docker"
    exit 1
fi

# 查看现有容器
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  发现现有容器: $CONTAINER_NAME"
    read -p "是否删除它？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  删除容器..."
        docker rm -f $CONTAINER_NAME > /dev/null 2>&1
    fi
fi

# 检查镜像
if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}$"; then
    echo "📦 未发现镜像，开始构建..."
    docker build -t $IMAGE_NAME -f dingbot/Dockerfile . || exit 1
else
    echo "✅ 镜像已存在: $IMAGE_NAME"
fi

# 启动容器
echo ""
echo "🚀 启动容器..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:$INTERNAL_PORT \
  -e OPENAI_API_KEY="${OPENAI_API_KEY:-test-mock-key}" \
  -e OPENAI_API_BASE="${OPENAI_API_BASE:-https://api.openai.com/v1}" \
  -e OPENAI_MODEL="${OPENAI_MODEL:-gpt-4-turbo}" \
  -e OPENAI_REQUEST_TIMEOUT="${OPENAI_REQUEST_TIMEOUT:-30}" \
  -e FORCE_MOCK_OPENAI="${FORCE_MOCK_OPENAI:-1}" \
  -e FLASK_ENV="${FLASK_ENV:-development}" \
  -e ACCESS_TOKEN="${ACCESS_TOKEN:-}" \
  -e SECRET="${SECRET:-}" \
  -v dinghook_data:/data \
  $IMAGE_NAME

echo "✅ 容器启动成功！"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  📊 容器信息"
echo "═══════════════════════════════════════════════════════════"
echo ""
sleep 2
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🔗 访问信息"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📍 服务地址: http://localhost:$PORT"
echo ""
echo "📝 日志查看:"
echo "   docker logs -f $CONTAINER_NAME"
echo ""
echo "🧹 停止容器:"
echo "   docker stop $CONTAINER_NAME"
echo ""
echo "🗑️  删除容器:"
echo "   docker rm $CONTAINER_NAME"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✨ 快速测试:"
echo ""
echo "curl -X GET http://localhost:$PORT/"
echo ""
echo "═══════════════════════════════════════════════════════════"
