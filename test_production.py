#!/usr/bin/env python3
"""
生产环境测试脚本
用于测试真实的 API 密钥和完整的流程

使用方式: python3 test_production.py

注意：需要配置真实的 API 密钥
"""

import os
import json
import requests
import time
from pathlib import Path

def check_env_vars():
    """检查必需的环境变量"""
    print("=" * 70)
    print("🔍 检查环境变量配置")
    print("=" * 70)
    print()
    
    required_vars = [
        "ACCESS_TOKEN",
        "SECRET",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 只显示前后各 10 个字符
            if len(value) > 20:
                display = f"{value[:10]}...{value[-10:]}"
            else:
                display = "***"
            print(f"✓ {var}: {display}")
        else:
            print(f"❌ {var}: 未设置")
            missing.append(var)
    
    print()
    
    if missing:
        print(f"❌ 缺少以下环境变量: {', '.join(missing)}")
        print()
        print("配置方式:")
        print("  export ACCESS_TOKEN=your_token")
        print("  export SECRET=your_secret")
        print("  export GEMINI_API_KEY=your_key")
        print("  export OPENAI_API_KEY=your_key")
        print()
        return False
    
    print("✅ 所有环境变量已配置")
    print()
    return True


def test_gemini_api():
    """测试 Gemini API"""
    print("=" * 70)
    print("🤖 测试 Gemini API")
    print("=" * 70)
    print()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    print("📤 发送测试请求到 Gemini...")
    print()
    
    try:
        from google import genai
        
        client = genai.Client()
        print("✓ Gemini 客户端已初始化")
        
        response = client.models.generate_content(
            model="models/gemini-3-pro-preview",
            contents="你好，请用一句话介绍自己。"
        )
        
        print(f"✓ API 响应状态: 成功")
        print(f"✓ 回复内容: {response.text}")
        print()
        return True
    
    except ImportError:
        print("❌ google-genai 未安装")
        print("   运行: pip install google-genai")
        print()
        return False
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False


def test_openai_api():
    """测试 OpenAI API（用于 Mem0）"""
    print("=" * 70)
    print("🧠 测试 OpenAI API (Mem0 所需)")
    print("=" * 70)
    print()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    print("📤 发送测试请求到 OpenAI...")
    print()
    
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        print("✓ OpenAI 客户端已初始化")
        
        # 测试嵌入
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="测试文本"
        )
        
        print(f"✓ Embedding API 响应状态: 成功")
        print(f"✓ 向量维度: {len(response.data[0].embedding)}")
        print()
        return True
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        print()
        return False


def test_mem0_integration():
    """测试 Mem0 集成"""
    print("=" * 70)
    print("💾 测试 Mem0 集成")
    print("=" * 70)
    print()
    
    try:
        from mem0 import Memory
        
        print("✓ Mem0 SDK 已导入")
        
        # 初始化 Mem0
        memory = Memory()
        print("✓ Mem0 Memory 实例已初始化")
        
        user_id = "test_user_prod"
        
        # 测试添加记忆
        print()
        print("测试: 添加记忆...")
        messages = [
            {"role": "user", "content": "我叫小王，我喜欢编程"}
        ]
        result = memory.add(messages, user_id=user_id)
        print(f"✓ 记忆已添加: {result}")
        
        # 测试搜索记忆
        print()
        print("测试: 搜索记忆...")
        time.sleep(1)  # 等待索引更新
        results = memory.search("编程", user_id=user_id, limit=3)
        print(f"✓ 搜索结果数量: {len(results.get('results', []))}")
        if results.get("results"):
            for i, mem in enumerate(results["results"], 1):
                print(f"  {i}. {mem.get('memory', mem)}")
        
        print()
        return True
    
    except ImportError:
        print("❌ mem0ai 未安装")
        print("   运行: pip install mem0ai")
        print()
        return False
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_dingtalk_connection():
    """测试钉钉连接"""
    print("=" * 70)
    print("📱 测试钉钉连接")
    print("=" * 70)
    print()
    
    access_token = os.getenv("ACCESS_TOKEN")
    
    if not access_token or access_token.startswith("test_"):
        print("⚠️  使用的是测试 Token（开发模式）")
        print("   生产环境需要真实的钉钉 AccessToken")
        print()
        return True
    
    try:
        print("📤 测试钉钉 API 连接...")
        
        # 获取钉钉 API 信息
        response = requests.get(
            "https://oapi.dingtalk.com/snapshot/record",
            params={"access_token": access_token},
            timeout=5
        )
        
        print(f"✓ 连接状态码: {response.status_code}")
        data = response.json()
        
        if data.get("errcode") == 0:
            print("✓ 钉钉 AccessToken 有效")
            print()
            return True
        else:
            print(f"❌ 错误码: {data.get('errcode')}")
            print(f"   错误信息: {data.get('errmsg')}")
            print()
            return False
    
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print()
        return False


def print_summary(results):
    """打印测试总结"""
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print()
    
    test_names = {
        "env": "✓ 环境变量配置",
        "gemini": "✓ Gemini API",
        "openai": "✓ OpenAI API",
        "mem0": "✓ Mem0 集成",
        "dingtalk": "✓ 钉钉连接"
    }
    
    for test_key, test_name in test_names.items():
        if test_key in results:
            status = "✅ PASS" if results[test_key] else "❌ FAIL"
            print(f"{status}: {test_name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    print()
    
    if passed == total:
        print("🎉 所有测试通过！系统准备就绪。")
        print()
        print("后续步骤:")
        print("  1. 启动服务: python -m dingbot.server")
        print("  2. 配置钉钉 Webhook")
        print("  3. 发送测试消息验证集成")
    else:
        print("⚠️  部分测试失败，请检查上面的错误信息。")
        print()
        print("故障排查:")
        print("  1. 确保所有 API 密钥正确")
        print("  2. 检查网络连接")
        print("  3. 验证 API 配额和付款方式")
        print("  4. 查看详细日志了解错误原因")
    
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 12 + "DingHook + Mem0 生产环境配置验证" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        results = {}
        
        # 检查环境变量
        results["env"] = check_env_vars()
        
        if not results["env"]:
            print("❌ 环境变量配置不完整，无法继续测试。")
            print()
            import sys
            sys.exit(1)
        
        # 测试各个 API
        results["gemini"] = test_gemini_api()
        results["openai"] = test_openai_api()
        results["mem0"] = test_mem0_integration()
        results["dingtalk"] = test_dingtalk_connection()
        
        # 打印总结
        print_summary(results)
        
    except KeyboardInterrupt:
        print("\n\n⏸️  测试被中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
