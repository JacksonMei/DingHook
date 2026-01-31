#!/usr/bin/env python3
"""
演示脚本：展示 Mem0 集成的完整流程

这个脚本演示了：
1. 钉钉消息接收
2. Mem0 add() - 存入对话
3. Mem0 search() - 获取记忆
4. 拼接 Prompt
5. 调用 LLM
6. 返回回复

运行方式: python3 demo_mem0_flow.py
"""

import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dingbot.mem0_manager import Mem0Manager
from dingbot.agent import analyze_and_reply


def print_step(step_num, title, content=""):
    """Print a formatted step."""
    print(f"\n{'='*70}")
    print(f"步骤 {step_num}: {title}")
    print(f"{'='*70}")
    if content:
        print(content)


def demo_simple_conversation():
    """演示简单的对话流程。"""
    print("\n" + "▓" * 70)
    print("▓  演示：基于 Mem0 的个性化聊天")
    print("▓" * 70)

    # Mock Mem0 Manager
    with patch('dingbot.agent.get_mem0_manager') as MockGetMem0, \
         patch('dingbot.agent._call_model') as MockCall, \
         patch('dingbot.agent.get_user_memories') as MockGetMemories:
        
        # Setup mock Mem0 manager
        mock_mem0_mgr = MagicMock()
        MockGetMem0.return_value = mock_mem0_mgr
        
        # Scenario: User is learning machine learning
        user_id = "user_alice_123"
        sender_name = "Alice"
        
        print_step(1, "钉钉消息接收", 
                  f"用户 ID: {user_id}\n"
                  f"用户名: {sender_name}\n"
                  f"消息: 最近在学深度学习，有点困难")
        
        # Message to process
        user_message = "最近在学深度学习，有点困难"
        
        # Step 1: Mem0 add - Store the conversation
        print_step(2, "Mem0 add() - 存入当前对话",
                  f"将用户消息添加到 Mem0 长期记忆中...\n"
                  f"内容: {user_message}\n"
                  f"用户 ID: {user_id}")
        
        mock_mem0_mgr.add_memory.return_value = "mem_id_xyz789"
        
        # Step 2: Mem0 search - Get relevant memories
        print_step(3, "Mem0 search() - 获取相关记忆",
                  "根据当前消息搜索相关的历史记忆...")
        
        memories_found = [
            {"memory": "Alice 之前提到喜欢编程和数据科学", "score": 0.92},
            {"memory": "Alice 使用 Python 和 PyTorch 编程", "score": 0.88},
            {"memory": "Alice 是一名初级数据工程师", "score": 0.85}
        ]
        mock_mem0_mgr.search_memories.return_value = memories_found
        
        print(f"✓ 找到 {len(memories_found)} 条相关记忆:")
        for i, mem in enumerate(memories_found, 1):
            print(f"  {i}. {mem['memory']} (相关度: {mem['score']})")
        
        # Step 3: Format memories into context
        print_step(4, "格式化记忆为上下文",
                  "将相关记忆转换为提示词中的上下文信息...")
        
        formatted_context = (
            "- Alice 之前提到喜欢编程和数据科学\n"
            "- Alice 使用 Python 和 PyTorch 编程\n"
            "- Alice 是一名初级数据工程师"
        )
        mock_mem0_mgr.format_memories_as_context.return_value = formatted_context
        
        print("格式化后的上下文:\n" + formatted_context)
        
        # Step 4: Build prompt
        print_step(5, "拼接 Prompt",
                  "将记忆、用户消息和系统指令组合成完整的提示词...")
        
        system_prompt = (
            "你是一个贴心且记忆力超群的助手。请简洁、自然地回复用户 'Alice'。"
            "\n\n关于用户的相关信息（基于历史对话）：\n"
            f"{formatted_context}"
            f"\n\n用户消息:\n{user_message}"
            "\n\n请返回 JSON: {\"reply\": <回复文本>}，不要包含其它内容。"
        )
        
        print("生成的完整 Prompt:\n" + system_prompt)
        
        # Step 5: Call LLM
        print_step(6, "调用 LLM (Gemini)",
                  "使用上下文调用语言模型生成个性化回复...")
        
        llm_response = {
            "reply": "我看你在学习深度学习呢！这确实是个挑战，特别是对初级的数据工程师来说。不过根据我的记忆，你已经很擅长 Python 和 PyTorch 了，相信你能掌握的！建议可以从一些经典的深度学习项目开始，比如 MNIST 识别或者 CNN 图像分类。加油！💪"
        }
        mock_mem0_mgr.format_memories_as_context.return_value = formatted_context
        MockGetMemories.return_value = []
        MockCall.return_value = json.dumps(llm_response)
        
        print(f"LLM 回复:\n{llm_response['reply']}")
        
        # Execute the complete flow
        print_step(7, "执行完整流程",
                  "调用 agent.analyze_and_reply() 执行完整的流程...")
        
        result = analyze_and_reply(user_message, sender_name, user_id)
        
        print(f"最终返回结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # Verify the flow
        print_step(8, "流程验证",
                  "验证每个步骤是否正确执行...")
        
        checks = [
            ("Mem0 add() 已调用", mock_mem0_mgr.add_memory.called),
            ("Mem0 search() 已调用", mock_mem0_mgr.search_memories.called),
            ("记忆格式化已执行", mock_mem0_mgr.format_memories_as_context.called),
            ("LLM 已调用", MockCall.called),
            ("回复已返回", bool(result.get("reply")))
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}")
            all_passed = all_passed and check_result
        
        print("\n" + "=" * 70)
        if all_passed:
            print("✅ 完整流程测试 PASSED")
        else:
            print("❌ 完整流程测试 FAILED")
        print("=" * 70)
        
        return all_passed


def demo_multi_turn_conversation():
    """演示多轮对话的记忆累积。"""
    print("\n\n" + "▓" * 70)
    print("▓  演示：多轮对话中的记忆累积")
    print("▓" * 70)
    
    with patch('dingbot.agent.get_mem0_manager') as MockGetMem0, \
         patch('dingbot.agent._call_model') as MockCall, \
         patch('dingbot.agent.get_user_memories') as MockGetMemories:
        
        mock_mem0_mgr = MagicMock()
        MockGetMem0.return_value = mock_mem0_mgr
        
        user_id = "user_bob_456"
        sender_name = "Bob"
        
        # Simulate multi-turn conversation
        conversations = [
            ("你好，我叫 Bob", "很高兴认识你！"),
            ("我喜欢旅游", "旅游很有趣，你最喜欢去哪儿？"),
            ("最近去过日本", "日本很美！你在日本的哪些地方玩过？"),
            ("去过东京和京都", "东京和京都都是很棒的地方，分别有现代和传统的特色。")
        ]
        
        for turn, (user_msg, ai_reply) in enumerate(conversations, 1):
            print(f"\n--- 对话轮次 {turn} ---")
            print(f"用户: {user_msg}")
            
            # Mock the memories accumulation
            memories_count = turn  # Simulating memory grows with each turn
            mock_mem0_mgr.add_memory.return_value = f"mem_id_{turn}"
            mock_mem0_mgr.search_memories.return_value = [
                {"memory": f"Bob 在对话轮次 {i} 提到的信息", "score": 0.9 - i*0.05}
                for i in range(1, min(turn + 1, 4))
            ]
            mock_mem0_mgr.format_memories_as_context.return_value = (
                "\n".join([f"- Bob 在对话轮次 {i} 提到的信息" 
                          for i in range(1, min(turn + 1, 4))])
            )
            MockGetMemories.return_value = []
            MockCall.return_value = json.dumps({"reply": ai_reply})
            
            result = analyze_and_reply(user_msg, sender_name, user_id)
            print(f"AI: {result.get('reply', '无回复')}")
            print(f"✓ 已添加记忆，当前记忆累积 {memories_count} 条")
        
        print("\n" + "=" * 70)
        print("✅ 多轮对话演示完成")
        print("=" * 70)


if __name__ == "__main__":
    try:
        # Run demos
        passed = demo_simple_conversation()
        demo_multi_turn_conversation()
        
        print("\n\n" + "▓" * 70)
        print("▓  演示总结")
        print("▓" * 70)
        print("""
完整的 Mem0 集成流程展示如下:

1. ✅ 钉钉接收消息
   └─ 服务器 webhook 接收用户消息

2. ✅ Mem0 add() - 存入当前对话
   └─ 将消息存入 Mem0 的长期记忆数据库

3. ✅ Mem0 search() - 获取相关记忆
   └─ 根据当前消息进行语义搜索，获取相关的历史记忆

4. ✅ 拼接 Prompt - 注入记忆上下文
   └─ 将相关记忆格式化并注入到系统提示词

5. ✅ 调用 LLM - 生成个性化回复
   └─ 使用 Gemini 模型基于上下文生成回复

6. ✅ 返回给钉钉
   └─ 将 AI 回复发送回钉钉会话

关键特性:
• 基于向量相似度搜索相关记忆
• 自动累积用户记忆用于长期个性化
• 支持多用户并发对话
• 可配置的记忆搜索数量和相关性
• 支持本地和云端存储

如需部署到生产环境:
1. 配置 OpenAI API Key (Mem0 所需)
2. 配置 Gemini API Key (LLM 所需)
3. 配置钉钉 ACCESS_TOKEN 和 SECRET
4. 使用 docker-compose up 启动服务
        """)
        print("▓" * 70)
        
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()
