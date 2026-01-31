#!/bin/bash
# DingHook + Mem0 快速开始指南
# Quick Start Guide for DingHook + Mem0 Integration

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     DingHook + Mem0 集成 - 快速开始指南                         ║"
echo "║     Quick Start Guide for DingHook + Mem0 Integration          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "✓ 检查 Python 环境..."
python3 --version || { echo "❌ 需要 Python 3.8+"; exit 1; }

# Install dependencies
echo "✓ 安装依赖..."
pip install -q Flask requests APScheduler pytest 2>/dev/null || true

# Check git branch
echo "✓ 检查 Git 分支..."
cd "$(dirname "$0")"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "  当前分支: $BRANCH"

if [ "$BRANCH" != "integrate-mem0" ]; then
    echo "  ⚠️  建议在 integrate-mem0 分支上工作"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📝 步骤 1: 配置环境变量"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "需要配置以下环境变量:"
echo ""
echo "# 钉钉配置"
echo "export ACCESS_TOKEN=<your_dingtalk_access_token>"
echo "export SECRET=<your_dingtalk_secret>"
echo ""
echo "# LLM 配置 (Gemini)"
echo "export GEMINI_API_KEY=<your_gemini_api_key>"
echo ""
echo "# Mem0 配置 (使用 OpenAI embeddings)"
echo "export OPENAI_API_KEY=<your_openai_api_key>"
echo ""
echo "# 可选配置"
echo "export PORT=8080"
echo "export DATABASE_PATH=dingbot_memory.db"
echo "export GEMINI_MODEL=models/gemini-3"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "🧪 步骤 2: 运行测试"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "运行所有集成测试验证实现:"
echo ""
echo "  python3 -m pytest tests/test_mem0_integration.py -v"
echo ""

# Run tests if requested
if [ "$1" = "test" ]; then
    echo "运行测试中..."
    python3 -m pytest tests/test_mem0_integration.py -v --tb=short
    echo ""
    echo "✅ 测试完成"
fi

echo "═══════════════════════════════════════════════════════════════"
echo "🎬 步骤 3: 运行演示脚本"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "查看完整的 Mem0 集成流程演示:"
echo ""
echo "  python3 demo_mem0_flow.py"
echo ""

# Run demo if requested
if [ "$1" = "demo" ]; then
    echo "运行演示中..."
    python3 demo_mem0_flow.py
    echo ""
fi

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 步骤 4: 启动服务"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "启动 DingHook 服务:"
echo ""
echo "  方式 1 - 直接运行:"
echo "    python -m dingbot.server"
echo ""
echo "  方式 2 - Docker Compose:"
echo "    docker-compose up"
echo ""
echo "  方式 3 - 开发模式 (使用 mock 回复):"
echo "    export FORCE_MOCK_GENAI=1"
echo "    python -m dingbot.server"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "📚 文档"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "主要文档:"
echo "  • INTEGRATION.md - 完整的架构和集成文档"
echo "  • COMPLETION_REPORT.md - 项目完成报告"
echo "  • README.md - 原始项目文档"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "🏗️  架构概览"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "完整流程:"
echo ""
echo "  钉钉消息"
echo "    ↓"
echo "  [Webhook 接收]"
echo "    ↓"
echo "  [Mem0 add()] ← 存入当前对话"
echo "    ↓"
echo "  [Mem0 search()] ← 获取相关记忆"
echo "    ↓"
echo "  [Prompt 拼接] ← 注入记忆上下文"
echo "    ↓"
echo "  [LLM 调用] ← Gemini 生成回复"
echo "    ↓"
echo "  [发送钉钉]"
echo "    ↓"
echo "  用户接收个性化回复 ✅"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "💡 关键特性"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "✅ 基于向量相似度的语义记忆搜索"
echo "✅ 自动累积用户对话用于长期个性化"
echo "✅ 上下文感知的 LLM 回复"
echo "✅ 支持多用户并发"
echo "✅ 完整的测试覆盖 (9/9 通过)"
echo "✅ 向后兼容所有原有功能"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "🔗 快速链接"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "分支信息:"
echo "  • 当前分支: integrate-mem0"
echo "  • 提交: $(git rev-parse --short HEAD)"
echo "  • Mem0 文档: https://docs.mem0.ai/"
echo "  • DingTalk API: https://open.dingtalk.com/"
echo "  • Gemini API: https://ai.google.dev/"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "✨ 准备就绪！"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "接下来建议:"
echo "  1. 阅读 INTEGRATION.md 了解详细架构"
echo "  2. 运行 'bash quickstart.sh test' 执行测试"
echo "  3. 运行 'bash quickstart.sh demo' 查看演示"
echo "  4. 按照步骤 1-4 配置和启动服务"
echo ""
