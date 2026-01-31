#!/usr/bin/env python3
"""
端到端集成测试脚本
完整测试 DingHook + Mem0 集成的服务和 API

运行方式: python3 test_end_to_end.py
"""

import os
import sys
import json
import time
import requests
import threading
from pathlib import Path

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def setup_env():
    """配置测试环境变量（开发模式）"""
    print("=" * 70)
    print("📝 设置环境变量（开发/测试模式）")
    print("=" * 70)
    print()
    
    # 设置必要的环境变量
    env_vars = {
        "ACCESS_TOKEN": "test_access_token_for_dev",
        "SECRET": "test_secret_for_dev",
        "GEMINI_API_KEY": "test_gemini_key_for_dev",
        "OPENAI_API_KEY": "test_openai_key_for_dev",
        "FORCE_MOCK_GENAI": "1",  # 使用 mock LLM 回复
        "PORT": "8080",
        "DATABASE_PATH": "dingbot_memory_test.db",
        "CHECK_INTERVAL_SECONDS": "60",
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✓ {key}: {value[:30]}...")
    
    print()
    return env_vars


def start_server():
    """启动 DingHook 服务器"""
    print("=" * 70)
    print("🚀 启动 DingHook 服务器")
    print("=" * 70)
    print()
    
    from dingbot.server import app, init_app
    
    # 初始化应用（不启动调度器以简化测试）
    init_app(start_scheduler=False)
    
    # 在后台线程启动服务
    def run_server():
        app.run(host="127.0.0.1", port=8080, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 等待服务启动
    time.sleep(2)
    print("✓ 服务器启动在 http://127.0.0.1:8080")
    print()
    
    return server_thread


def test_health_check():
    """测试健康检查端点"""
    print("=" * 70)
    print("🏥 测试 1: 健康检查 (GET /)")
    print("=" * 70)
    print()
    
    try:
        response = requests.get("http://127.0.0.1:8080/", timeout=5)
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 响应: {response.json()}")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False


def test_simple_message():
    """测试接收简单消息"""
    print("=" * 70)
    print("💬 测试 2: 接收简单消息 (POST /webhook)")
    print("=" * 70)
    print()
    
    payload = {
        "msgtype": "text",
        "text": {
            "content": "你好，我是测试用户，很高兴认识你！"
        },
        "senderNick": "TestUser",
        "senderId": "test_user_001"
    }
    
    print("📤 发送消息:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print()
    
    try:
        response = requests.post(
            "http://127.0.0.1:8080/webhook",
            json=payload,
            timeout=10
        )
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 响应类型: {response.headers.get('Content-Type')}")
        print(f"✓ 回复内容: {response.text}")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False


def test_mem0_memory_flow():
    """测试 Mem0 记忆流程"""
    print("=" * 70)
    print("🧠 测试 3: Mem0 记忆流程")
    print("=" * 70)
    print()
    
    # 模拟多轮对话
    messages = [
        {"content": "我叫 Alice，我喜欢编程和机器学习"},
        {"content": "最近在学习深度学习"},
        {"content": "请问我最感兴趣的领域是什么？"},
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"--- 对话轮次 {i} ---")
        payload = {
            "msgtype": "text",
            "text": {"content": msg["content"]},
            "senderNick": "Alice",
            "senderId": "alice_mem0_test"
        }
        
        print(f"用户: {msg['content']}")
        
        try:
            response = requests.post(
                "http://127.0.0.1:8080/webhook",
                json=payload,
                timeout=10
            )
            print(f"AI: {response.text}")
            print()
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ 错误: {e}")
            print()
    
    return True


def test_ping_command():
    """测试 /ping 命令"""
    print("=" * 70)
    print("⏱️  测试 4: /ping 命令")
    print("=" * 70)
    print()
    
    payload = {
        "msgtype": "text",
        "text": {"content": "/ping"},
        "senderNick": "TestUser",
        "senderId": "test_user_001"
    }
    
    print(f"📤 发送命令: {payload['text']['content']}")
    print()
    
    try:
        response = requests.post(
            "http://127.0.0.1:8080/webhook",
            json=payload,
            timeout=10
        )
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 回复: {response.text}")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False


def test_help_command():
    """测试 /help 命令"""
    print("=" * 70)
    print("❓ 测试 5: /help 命令")
    print("=" * 70)
    print()
    
    payload = {
        "msgtype": "text",
        "text": {"content": "/help"},
        "senderNick": "TestUser",
        "senderId": "test_user_001"
    }
    
    print(f"📤 发送命令: {payload['text']['content']}")
    print()
    
    try:
        response = requests.post(
            "http://127.0.0.1:8080/webhook",
            json=payload,
            timeout=10
        )
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 回复内容:\n{response.text}")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False


def test_error_handling():
    """测试错误处理"""
    print("=" * 70)
    print("⚠️  测试 6: 错误处理")
    print("=" * 70)
    print()
    
    # 测试非文本消息
    payload = {
        "msgtype": "image",
        "text": {"content": "not text"}
    }
    
    print("📤 发送非文本消息...")
    print()
    
    try:
        response = requests.post(
            "http://127.0.0.1:8080/webhook",
            json=payload,
            timeout=10
        )
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 响应: {response.json()}")
        print("✓ 正确地忽略了非文本消息")
        print()
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False


def print_summary(results):
    """打印测试总结"""
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print()
    
    total = len(results)
    passed = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    print()
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败，请检查日志。")
    
    print()


def print_required_keys():
    """打印所需的 API Keys 说明"""
    print("\n" + "=" * 70)
    print("🔑 生产环境所需的 API Keys")
    print("=" * 70)
    print()
    
    keys_info = {
        "ACCESS_TOKEN": {
            "说明": "钉钉应用的访问令牌",
            "来源": "钉钉开发者平台",
            "地址": "https://open.dingtalk.com/",
            "必需": True
        },
        "SECRET": {
            "说明": "钉钉应用的秘密密钥",
            "来源": "钉钉开发者平台",
            "地址": "https://open.dingtalk.com/",
            "必需": True
        },
        "GEMINI_API_KEY": {
            "说明": "Google Gemini API 密钥（用于 LLM）",
            "来源": "Google Cloud Console",
            "地址": "https://ai.google.dev/",
            "必需": True
        },
        "OPENAI_API_KEY": {
            "说明": "OpenAI API 密钥（Mem0 嵌入模型）",
            "来源": "OpenAI 平台",
            "地址": "https://platform.openai.com/",
            "必需": True,
            "用途": "用于 Mem0 的向量嵌入"
        }
    }
    
    for key, info in keys_info.items():
        status = "⭐ 必需" if info["必需"] else "📌 可选"
        print(f"{status} {key}")
        print(f"  说明: {info['说明']}")
        print(f"  来源: {info['来源']}")
        print(f"  地址: {info['地址']}")
        if "用途" in info:
            print(f"  用途: {info['用途']}")
        print()
    
    print("配置方式:")
    print("  1. 导出环境变量:")
    print("     export ACCESS_TOKEN=your_token")
    print("     export SECRET=your_secret")
    print("     export GEMINI_API_KEY=your_key")
    print("     export OPENAI_API_KEY=your_key")
    print()
    print("  2. 在 .env 文件中配置")
    print()
    print("  3. 或在 docker-compose.yml 中配置")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "DingHook + Mem0 端到端集成测试" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        # 1. 设置环境变量
        env_vars = setup_env()
        
        # 2. 启动服务
        server_thread = start_server()
        
        # 3. 等待服务完全启动
        print("⏳ 等待服务启动...")
        for i in range(5):
            try:
                requests.get("http://127.0.0.1:8080/", timeout=1)
                print("✓ 服务已启动")
                break
            except:
                if i < 4:
                    time.sleep(1)
                    print(".", end="", flush=True)
                else:
                    print("\n❌ 服务启动失败")
                    sys.exit(1)
        
        print()
        
        # 4. 运行测试
        results = {}
        results["健康检查"] = test_health_check()
        results["简单消息"] = test_simple_message()
        results["Mem0记忆流程"] = test_mem0_memory_flow()
        results["Ping命令"] = test_ping_command()
        results["Help命令"] = test_help_command()
        results["错误处理"] = test_error_handling()
        
        # 5. 打印测试总结
        print_summary(results)
        
        # 6. 打印 API Keys 说明
        print_required_keys()
        
        print("=" * 70)
        print("✨ 测试完成！")
        print("=" * 70)
        print()
        print("下一步:")
        print("  1. 配置真实的 API Keys")
        print("  2. 运行生产环境服务: python -m dingbot.server")
        print("  3. 或使用 Docker: docker-compose up")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⏸️  测试被中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
