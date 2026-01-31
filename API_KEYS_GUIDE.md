# DingHook + Mem0 API 密钥配置指南

## 📋 概述

DingHook + Mem0 集成需要 4 个主要的 API 密钥。本指南将详细说明如何获取和配置它们。

## 🔑 所需的 API 密钥

### 1. ⭐ ACCESS_TOKEN（钉钉访问令牌）

**用途：** 钉钉应用认证

**获取步骤：**

1. 访问 [钉钉开发者平台](https://open.dingtalk.com/)
2. 登录你的钉钉账号
3. 创建或选择现有的应用
4. 进入应用设置
5. 找到 "应用凭证" 或 "凭证管理"
6. 复制 **AppID** 和 **AppSecret**
7. 使用这些信息生成 AccessToken：
   ```bash
   # 使用钉钉 API 获取 AccessToken
   curl https://oapi.dingtalk.com/gettoken \
     -X GET \
     -d "appid=YOUR_APP_ID" \
     -d "appsecret=YOUR_APP_SECRET"
   ```
8. 从响应中获取 `access_token` 字段

**示例：**
```
ACCESS_TOKEN=12345678901234567890abcdefghij.klmnopqrstuvwxyz1234567890ABCDEFGH
```

---

### 2. ⭐ SECRET（钉钉应用秘密）

**用途：** 钉钉消息签名验证

**获取步骤：**

1. 在钉钉开发者平台
2. 进入应用设置 → "安全设置"
3. 找到 "Webhook" 或 "回调" 配置
4. 启用 Webhook 功能
5. 获取回调秘钥（Secret）
6. 或从 "应用凭证" 中复制应用的 Secret 密钥

**示例：**
```
SECRET=SUP_E_T_S_3CRE_7K3Y_EXA_4567890
```

---

### 3. ⭐ GEMINI_API_KEY（Google Gemini API 密钥）

**用途：** LLM 大语言模型调用

**获取步骤：**

1. 访问 [Google AI Studio](https://ai.google.dev/)
2. 点击 "Get API Key"
3. 选择或创建 Google Cloud 项目
4. 系统会自动生成 API 密钥
5. 复制 API 密钥

**替代方案（完整 Google Cloud）：**

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目
3. 启用 "Generative Language API"
4. 进入 "凭证" → "创建凭证" → "API 密钥"
5. 复制生成的 API 密钥

**获取模型名称：**
```bash
# 使用 API 列出可用模型
curl https://generativelanguage.googleapis.com/v1beta/models \
  -H "x-goog-api-key: YOUR_GEMINI_API_KEY"
```

**示例：**
```
GEMINI_API_KEY=AIzaSyD_L8q_Y9z0K1L2M3N4O5P6Q7R8S9T0U1V2W
```

---

### 4. ⭐ OPENAI_API_KEY（OpenAI API 密钥）

**用途：** Mem0 的向量嵌入模型

**获取步骤：**

1. 访问 [OpenAI 平台](https://platform.openai.com/)
2. 注册或登录账号
3. 进入 "API Keys" 页面
4. 点击 "Create new secret key"
5. 选择权限范围（建议 "Read & Write"）
6. 复制生成的密钥
7. 存储在安全的地方（注意：密钥只显示一次）

**获取或切换组织：**
- 如果你有多个组织，可以在创建密钥时选择特定组织
- 确保选择有有效订阅的组织

**确保有足够的额度：**
- 登录 OpenAI 账户
- 进入 "Billing" → "Usage"
- 确认有足够的 API 使用配额

**示例：**
```
OPENAI_API_KEY=sk-proj-1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQ
```

---

## 🛠️ 配置方式

### 方式 1：导出环境变量（推荐用于开发）

```bash
export ACCESS_TOKEN="your_access_token_here"
export SECRET="your_secret_here"
export GEMINI_API_KEY="your_gemini_key_here"
export OPENAI_API_KEY="your_openai_key_here"

# 然后启动服务
python -m dingbot.server
```

### 方式 2：.env 文件配置

创建 `dingbot/.env` 文件：

```dotenv
# DingTalk credentials
ACCESS_TOKEN=your_access_token_here
SECRET=your_secret_here

# LLM Configuration (Gemini)
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=models/gemini-3

# Mem0 Configuration
OPENAI_API_KEY=your_openai_key_here

# Local database
DATABASE_PATH=dingbot_memory.db
PORT=8080
CHECK_INTERVAL_SECONDS=60
```

然后启动服务：
```bash
python -m dingbot.server
```

### 方式 3：Docker Compose 配置

编辑 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  dingbot:
    build: .
    ports:
      - "8080:8080"
    environment:
      ACCESS_TOKEN: your_access_token_here
      SECRET: your_secret_here
      GEMINI_API_KEY: your_gemini_key_here
      OPENAI_API_KEY: your_openai_key_here
      GEMINI_MODEL: models/gemini-3
      PORT: 8080
      DATABASE_PATH: dingbot_memory.db
```

然后启动：
```bash
docker-compose up
```

### 方式 4：Kubernetes Secrets（生产环境）

创建 secret：

```bash
kubectl create secret generic dinghook-secrets \
  --from-literal=access_token=your_access_token \
  --from-literal=secret=your_secret \
  --from-literal=gemini_api_key=your_gemini_key \
  --from-literal=openai_api_key=your_openai_key
```

在 Deployment 中引用：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dingbot
spec:
  containers:
  - name: dingbot
    image: dingbot:latest
    env:
    - name: ACCESS_TOKEN
      valueFrom:
        secretKeyRef:
          name: dinghook-secrets
          key: access_token
    - name: SECRET
      valueFrom:
        secretKeyRef:
          name: dinghook-secrets
          key: secret
    - name: GEMINI_API_KEY
      valueFrom:
        secretKeyRef:
          name: dinghook-secrets
          key: gemini_api_key
    - name: OPENAI_API_KEY
      valueFrom:
        secretKeyRef:
          name: dinghook-secrets
          key: openai_api_key
```

---

## ✅ 验证配置

### 验证 1：环境变量是否正确设置

```bash
echo "ACCESS_TOKEN: ${ACCESS_TOKEN}"
echo "SECRET: ${SECRET:0:10}..."  # 只显示前10个字符
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
```

### 验证 2：启动服务并测试

```bash
# 启动服务
python -m dingbot.server

# 在另一个终端测试
python3 test_end_to_end.py
```

### 验证 3：检查日志输出

服务启动时会输出日志：

```
INFO:dingbot.mem0_manager:Mem0 Memory instance initialized successfully
INFO:dingbot.scheduler:Scheduler started
```

如果看到错误日志（如 `Failed to initialize Mem0`），说明密钥配置有问题。

---

## 🔒 安全建议

### 1. 密钥管理

- ✅ 使用环境变量存储密钥，而不是硬编码
- ✅ 使用密钥管理服务（如 AWS Secrets Manager、HashiCorp Vault）
- ✅ 定期轮换密钥
- ✅ 为不同环境使用不同的密钥
- ❌ 不要在代码仓库中提交密钥
- ❌ 不要在日志中输出密钥

### 2. 访问控制

- ✅ 限制 API 密钥的权限范围
- ✅ 为每个应用使用独立的 API 密钥
- ✅ 在 API 平台中设置 IP 白名单
- ✅ 设置速率限制

### 3. 监控和审计

```bash
# 监控 API 使用情况
# Google Cloud Console → API & Services → Dashboard
# OpenAI Platform → Billing → Usage

# 启用审计日志
# 定期检查异常的 API 调用
```

---

## 🐛 常见问题

### Q1: 启动时提示 "token is not exist"

**原因：** 钉钉 ACCESS_TOKEN 无效或过期

**解决方案：**
1. 重新生成 AccessToken
2. 确保 AppID 和 AppSecret 正确
3. 检查 Token 是否过期（钉钉 Token 有 7200 秒的有效期）

### Q2: Mem0 初始化失败

**原因：** OPENAI_API_KEY 未设置或无效

**解决方案：**
1. 确保 OPENAI_API_KEY 环境变量已正确设置
2. 验证密钥有效性：
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```
3. 检查 OpenAI 账户是否有有效的付款方式

### Q3: Gemini API 返回 403 错误

**原因：** GEMINI_API_KEY 无效或项目没有启用 API

**解决方案：**
1. 验证密钥是否正确
2. 在 Google Cloud Console 启用 "Generative Language API"
3. 检查是否超过 API 配额

### Q4: 如何测试 API 密钥的有效性？

**答：** 运行测试脚本：
```bash
python3 test_end_to_end.py
```

---

## 📊 API 配额和成本

### OpenAI API

- **定价：** 根据使用量计算（Embedding 和 ChatCompletion）
- **免费额度：** $5 试用额度（3 个月）
- **估计月成本：** $5-50（取决于使用量）

### Google Gemini API

- **定价：** 部分免费（Gemini 1.5 Flash）
- **免费配额：** 每分钟 60 次请求
- **付费配额：** 按使用量付费
- **估计月成本：** $0-30

### 钉钉 API

- **价格：** 免费（基于企业版钉钉）
- **配额：** 根据企业版等级而定

---

## 🚀 生产部署检查清单

- [ ] 所有 API 密钥已获取并验证
- [ ] 密钥使用环境变量存储，未硬编码
- [ ] 已启用 HTTPS/TLS 加密
- [ ] 已设置日志监控
- [ ] 已配置告警机制
- [ ] 已进行安全审计
- [ ] 已备份数据库
- [ ] 已测试故障恢复
- [ ] 已准备回滚方案
- [ ] 已文档化配置和部署步骤

---

## 📞 获取支持

- 钉钉开发者支持：https://open.dingtalk.com/support
- Google Cloud 支持：https://cloud.google.com/support
- OpenAI 支持：https://help.openai.com/
- Mem0 文档：https://docs.mem0.ai/
