#!/bin/bash

# 阿里云 ECS Docker 外网访问诊断脚本

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║    阿里云 ECS Docker 外网访问诊断工具                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. 获取 IP 信息
echo "📍 机器信息"
echo "═══════════════════════════════════════════════════════════════"
HOSTNAME=$(hostname)
echo "主机名: $HOSTNAME"

# 获取内网 IP
PRIVATE_IP=$(ip addr show eth0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
if [ -z "$PRIVATE_IP" ]; then
    PRIVATE_IP=$(hostname -I | awk '{print $1}')
fi
echo "内网 IP: $PRIVATE_IP"

# 尝试获取公网 IP
PUBLIC_IP=$(curl -s --connect-timeout 2 http://ifconfig.me 2>/dev/null || echo "获取中...")
echo "公网 IP: $PUBLIC_IP (或在阿里云控制台查看)"

echo ""

# 2. 检查 Docker 容器
echo "🐳 Docker 容器状态"
echo "═══════════════════════════════════════════════════════════════"
if docker ps | grep -q dinghook-mem0; then
    echo "✅ 容器运行中"
    docker ps | grep dinghook-mem0 | awk '{print "   NAME: " $NF "\n   STATUS: " $5 "\n   PORTS: " $NF}'
else
    echo "❌ 容器未运行"
fi

echo ""

# 3. 检查端口监听
echo "🔌 端口监听状态"
echo "═══════════════════════════════════════════════════════════════"
if ss -tulpn 2>/dev/null | grep -q 9090 || netstat -tulpn 2>/dev/null | grep -q 9090; then
    echo "✅ 端口 9090 正在监听"
    (ss -tulpn 2>/dev/null || netstat -tulpn) | grep 9090 | head -2
else
    echo "❌ 端口 9090 未监听"
fi

echo ""

# 4. 检查防火墙
echo "🔥 防火墙状态"
echo "═══════════════════════════════════════════════════════════════"
if systemctl is-active firewalld >/dev/null 2>&1; then
    echo "⚠️  防火墙已启用，需要开放 9090 端口"
    firewall-cmd --list-ports
else
    echo "✅ 防火墙未启用 (或已关闭)"
fi

echo ""

# 5. 测试本地连接
echo "🧪 连接测试"
echo "═══════════════════════════════════════════════════════════════"

# 测试本地连接
echo "📌 本地连接测试: http://localhost:9090/health"
LOCAL_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/health 2>/dev/null)
if [ "$LOCAL_TEST" = "200" ]; then
    echo "✅ HTTP $LOCAL_TEST - 连接成功"
else
    echo "❌ 连接失败 (HTTP $LOCAL_TEST)"
fi

# 测试内网连接
echo ""
echo "📌 内网连接测试: http://$PRIVATE_IP:9090/health"
INTERNAL_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://$PRIVATE_IP:9090/health 2>/dev/null)
if [ "$INTERNAL_TEST" = "200" ]; then
    echo "✅ HTTP $INTERNAL_TEST - 连接成功"
else
    echo "❌ 连接失败 (HTTP $INTERNAL_TEST)"
fi

echo ""

# 6. 健康检查响应
echo "📊 服务健康检查"
echo "═══════════════════════════════════════════════════════════════"
HEALTH_RESPONSE=$(curl -s http://localhost:9090/health 2>/dev/null)
if [ -n "$HEALTH_RESPONSE" ]; then
    echo "✅ 健康检查响应:"
    echo "$HEALTH_RESPONSE" | python -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "❌ 无健康检查响应"
fi

echo ""

# 7. 外网访问说明
echo "🌐 外网访问配置"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "要启用外网访问，需要在阿里云控制台配置安全组:"
echo ""
echo "步骤:"
echo "  1. 登录阿里云控制台"
echo "  2. 进入 ECS → 实例 → $HOSTNAME"
echo "  3. 点击'安全组'"
echo "  4. 选择安全组 → 入站规则 → 添加规则"
echo "  5. 配置:"
echo "     - 协议类型: TCP"
echo "     - 端口范围: 9090/9090"
echo "     - 授权对象: 0.0.0.0/0"
echo "     - 描述: DingHook Mem0 API"
echo ""
echo "配置后可通过以下方式访问:"
echo "  curl http://<公网IP>:9090/health"
echo ""

# 8. 快速命令参考
echo "📝 常用命令"
echo "═══════════════════════════════════════════════════════════════"
cat << 'COMMANDS'
# 查看容器日志
docker logs -f dinghook-mem0-container

# 进入容器
docker exec -it dinghook-mem0-container bash

# 重启容器
docker restart dinghook-mem0-container

# 停止容器
docker stop dinghook-mem0-container

# 查看容器资源使用
docker stats dinghook-mem0-container

# 检查网络配置
docker network inspect bridge

# 本地测试
curl http://localhost:9090/
curl http://localhost:9090/health
curl http://localhost:9090/help
COMMANDS

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   诊断完成                                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ 本地环境: 正常"
echo "⏳ 外网访问: 需要配置阿里云安全组"
echo ""
echo "更多信息: 查看 ALICLOUD_ACCESS_GUIDE.md"
echo ""
