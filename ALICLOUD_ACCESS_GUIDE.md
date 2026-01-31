# 阿里云 ECS Docker 外网访问配置指南

## 📍 当前机器信息

- **主机名**: iZt4n1bw4r5tt4ag7uenn2Z
- **内网 IP**: 172.24.223.120
- **Docker 服务端口**: 9090 (主机) → 8080 (容器)
- **容器状态**: ✅ 运行中 (healthy)

## 🔧 网络配置状态

### ✅ 本地配置
- ✅ Docker 容器: 正在监听 `0.0.0.0:9090`
- ✅ 防火墙: 未启用 (inactive)
- ✅ 网络接口: eth0 活跃 (172.24.223.120)

### ⚠️ 需要配置的内容

需要在 **阿里云 ECS 控制台** 配置安全组规则：

1. 登录阿里云控制台
2. 进入 ECS 实例管理
3. 找到当前实例 (主机名: iZt4n1bw4r5tt4ag7uenn2Z)
4. 点击"安全组"
5. 添加入站规则:
   - **协议类型**: TCP
   - **端口范围**: 9090/9090
   - **授权对象**: 0.0.0.0/0 (允许所有外网访问)
   - **描述**: DingHook Mem0 API

## 🌐 外网访问方式

### 获取公网 IP

在阿里云控制台查看实例详情，找到 **公网 IP** 字段。

假设公网 IP 为: `8.222.215.42`

### 访问 API

#### 1. 基础健康检查
```bash
curl http://8.222.215.42:9090/health
```

响应:
```json
{
  "status": "ok",
  "message": "DingBot Server is healthy"
}
```

#### 2. 服务状态检查
```bash
curl http://8.222.215.42:9090/
```

响应:
```json
{
  "status": "ok",
  "message": "DingBot Server is running"
}
```

#### 3. 获取帮助
```bash
curl http://8.222.215.42:9090/help
```

## 📊 完整的访问流程

### 步骤 1: 配置安全组（仅需一次）

在阿里云控制台添加入站规则:
```
协议: TCP
端口: 9090
来源: 0.0.0.0/0
```

### 步骤 2: 测试连接

从本地机器或其他地方:
```bash
# 测试 TCP 连接
nc -zv 8.222.215.42 9090

# 或使用 curl 测试 HTTP
curl -I http://8.222.215.42:9090/health
```

### 步骤 3: 集成到应用

```python
import requests

BASE_URL = "http://8.222.215.42:9090"

# 健康检查
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 获取帮助
response = requests.get(f"{BASE_URL}/help")
print(response.text)
```

## 🐳 Docker 容器监听信息

```
✅ IPv4: 0.0.0.0:9090 → LISTEN
✅ IPv6: [::]:9090 → LISTEN
✅ 进程: docker-proxy
✅ 状态: 健康
```

Docker 已配置为监听所有网络接口 (`0.0.0.0`)，因此：
- ✅ 本地访问: `localhost:9090` ✅ 正常
- ✅ 内网访问: `172.24.223.120:9090` ✅ 正常
- ⏳ 外网访问: 需要阿里云安全组配置

## 🔐 安全建议

### 推荐配置

#### 方案 1: 限制来源（更安全）
```
协议: TCP
端口: 9090
来源: 你的 IP/32 (或你的公司 IP 段)
```

#### 方案 2: 限制特定地域
```
协议: TCP
端口: 9090
来源: 阿里云内 (仅允许阿里云内部)
```

#### 方案 3: 开放访问（测试用）
```
协议: TCP
端口: 9090
来源: 0.0.0.0/0 (所有地方)
```

## 📈 监控和故障排查

### 检查容器状态
```bash
docker ps | grep dinghook
docker logs -f dinghook-mem0-container
```

### 测试端口连接

本地测试:
```bash
# 本地访问
curl http://localhost:9090/health

# 内网访问
curl http://172.24.223.120:9090/health
```

外网测试:
```bash
# 从其他机器测试（需要配置安全组）
curl http://YOUR_PUBLIC_IP:9090/health
```

### 检查防火墙

```bash
# 本地防火墙状态
systemctl status firewalld

# 检查监听端口
netstat -tulpn | grep 9090
# 或
ss -tulpn | grep 9090

# 检查 Docker 网络
docker network inspect bridge | grep -A 5 9090
```

## 🚀 常见问题

### Q: 配置了安全组但仍无法访问？

**A:** 检查以下几点：
1. 确认实例公网 IP 正确
2. 确认规则中的端口是 9090
3. 确认来源包含你的 IP
4. 等待 1-2 分钟让规则生效
5. 检查 Docker 容器是否运行: `docker ps`

### Q: 如何获取公网 IP？

**A:** 
1. 登录阿里云控制台
2. 点击 ECS 实例
3. 查看"实例详情"中的"公网 IP"字段
4. 或运行: `curl http://ifconfig.me`（需要网络连接）

### Q: 能否修改端口？

**A:** 可以，修改启动命令:
```bash
docker run -d \
  -p 8888:8080 \  # 改为 8888
  -e OPENAI_API_KEY="..." \
  dinghook-mem0:latest
```

然后在阿里云安全组中打开 8888 端口。

### Q: 如何用 HTTPS？

**A:** 使用 Nginx 反向代理:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    ssl_certificate /path/to/cert;
    ssl_certificate_key /path/to/key;
    
    location / {
        proxy_pass http://172.24.223.120:9090;
    }
}
```

## 📝 快速参考

| 操作 | 命令 |
|------|------|
| 查看公网 IP | 阿里云控制台 → ECS → 实例详情 |
| 配置安全组 | 阿里云控制台 → ECS → 安全组 → 添加规则 |
| 测试本地连接 | `curl http://localhost:9090/health` |
| 测试内网连接 | `curl http://172.24.223.120:9090/health` |
| 查看容器日志 | `docker logs -f dinghook-mem0-container` |
| 进入容器 | `docker exec -it dinghook-mem0-container bash` |

## 🎯 完整配置示例

### 前提条件
- ✅ Docker 容器运行中
- ✅ 阿里云 ECS 实例配置完成
- ✅ 需要阿里云控制台权限

### 一步步配置

1. **在阿里云控制台添加安全组规则**
   - 进入 ECS 实例 → 安全组
   - 添加入站规则
   - 协议: TCP, 端口: 9090, 来源: 0.0.0.0/0
   - 保存并等待生效 (1-2 分钟)

2. **获取公网 IP**
   - 在实例详情中查看公网 IP
   - 例如: 8.222.215.42

3. **从外网访问**
   ```bash
   curl http://8.222.215.42:9090/health
   ```

4. **成功！**
   ```json
   {
     "status": "ok",
     "message": "DingBot Server is healthy"
   }
   ```

## 📞 支持

遇到问题？检查以下资源：
- Docker 文档: https://docs.docker.com/
- 阿里云 ECS 文档: https://help.aliyun.com/
- 项目 README: [README.md](../README.md)

---

**文档更新**: 2026-01-31  
**状态**: ✅ Docker 容器运行正常，准备外网接入
