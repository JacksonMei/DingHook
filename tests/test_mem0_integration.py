"""Integration tests for Mem0 memory layer with DingHook."""

import os
import sys
import json
import pytest
import logging
from unittest.mock import Mock, patch, MagicMock

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dingbot.mem0_manager import Mem0Manager, get_mem0_manager, init_mem0
from dingbot.agent import analyze_and_reply
from dingbot.server import app, init_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMem0Manager:
    """Test Mem0 manager functionality."""

    def test_mem0_manager_initialization(self):
        """Test that Mem0Manager can be initialized."""
        with patch('dingbot.mem0_manager.Memory') as MockMemory:
            MockMemory.return_value = MagicMock()
            manager = Mem0Manager()
            assert manager.memory is not None

    def test_add_memory(self):
        """Test adding memory to Mem0."""
        with patch('dingbot.mem0_manager.Memory') as MockMemory:
            mock_memory = MagicMock()
            MockMemory.return_value = mock_memory
            mock_memory.add.return_value = "mem_123"
            
            manager = Mem0Manager()
            messages = [{"role": "user", "content": "我喜欢编程"}]
            result = manager.add_memory(messages, "user_001")
            
            assert result == "mem_123"
            mock_memory.add.assert_called_once()

    def test_search_memories(self):
        """Test searching memories from Mem0."""
        with patch('dingbot.mem0_manager.Memory') as MockMemory:
            mock_memory = MagicMock()
            MockMemory.return_value = mock_memory
            mock_memory.search.return_value = {
                "results": [
                    {"memory": "用户喜欢编程", "score": 0.95},
                    {"memory": "用户用Python", "score": 0.87}
                ]
            }
            
            manager = Mem0Manager()
            memories = manager.search_memories("编程", "user_001", limit=5)
            
            assert len(memories) == 2
            assert memories[0]["memory"] == "用户喜欢编程"

    def test_format_memories_as_context(self):
        """Test formatting memories into context string."""
        with patch('dingbot.mem0_manager.Memory'):
            manager = Mem0Manager()
            memories = [
                {"memory": "用户喜欢编程"},
                {"memory": "用户用Python"}
            ]
            context = manager.format_memories_as_context(memories)
            
            assert "用户喜欢编程" in context
            assert "用户用Python" in context
            assert context.startswith("- ")


class TestAgentWithMem0:
    """Test agent integration with Mem0."""

    def test_analyze_and_reply_with_mem0(self):
        """Test analyze_and_reply function with Mem0 integration."""
        with patch('dingbot.agent.get_mem0_manager') as MockGetMem0, \
             patch('dingbot.agent._call_model') as MockCall, \
             patch('dingbot.agent.get_user_memories') as MockGetMemories:
            
            # Setup mocks
            mock_mem0_mgr = MagicMock()
            MockGetMem0.return_value = mock_mem0_mgr
            
            mock_mem0_mgr.search_memories.return_value = [
                {"memory": "用户喜欢编程", "score": 0.95}
            ]
            mock_mem0_mgr.format_memories_as_context.return_value = "- 用户喜欢编程"
            
            MockGetMemories.return_value = []
            MockCall.return_value = json.dumps({"reply": "我看你喜欢编程！"})
            
            # Call the function
            result = analyze_and_reply("你好，我最近在学编程", "张三", "user_001")
            
            # Verify the flow
            assert result["reply"] == "我看你喜欢编程！"
            mock_mem0_mgr.add_memory.assert_called_once()
            mock_mem0_mgr.search_memories.assert_called_once()

    def test_analyze_and_reply_flow(self):
        """Test the complete flow: add -> search -> prompt -> LLM."""
        with patch('dingbot.agent.get_mem0_manager') as MockGetMem0, \
             patch('dingbot.agent._call_model') as MockCall, \
             patch('dingbot.agent.get_user_memories') as MockGetMemories:
            
            # Create a mock mem0 manager
            mock_mem0_mgr = MagicMock()
            MockGetMem0.return_value = mock_mem0_mgr
            
            # Setup the flow
            mock_mem0_mgr.add_memory.return_value = "mem_456"
            mock_mem0_mgr.search_memories.return_value = [
                {"memory": "用户最近提到工作压力大"}
            ]
            mock_mem0_mgr.format_memories_as_context.return_value = "- 用户最近提到工作压力大"
            
            MockGetMemories.return_value = []
            MockCall.return_value = json.dumps({"reply": "看起来你最近工作压力比较大，要注意休息哦"})
            
            # Execute
            result = analyze_and_reply("感觉今天有点累", "李四", "user_002")
            
            # Verify the complete flow
            # 1. add_memory was called with current message
            assert mock_mem0_mgr.add_memory.called
            # 2. search_memories was called
            assert mock_mem0_mgr.search_memories.called
            # 3. format_memories_as_context was called
            assert mock_mem0_mgr.format_memories_as_context.called
            # 4. _call_model was called with a prompt containing memory context
            assert MockCall.called
            call_args = MockCall.call_args[0][0]
            assert "关于用户的相关信息" in call_args
            # 5. Result is returned correctly
            assert result["reply"] == "看起来你最近工作压力比较大，要注意休息哦"


class TestServerIntegration:
    """Test server integration with Mem0."""

    def test_webhook_endpoint_with_mem0(self):
        """Test webhook endpoint integrates Mem0 correctly."""
        # Initialize app without starting scheduler
        with patch('dingbot.server.init_mem0') as MockInitMem0:
            MockInitMem0.return_value = True
            init_app(start_scheduler=False)
        
        client = app.test_client()
        
        # Mock the agent and Mem0 manager
        with patch('dingbot.server.agent.analyze_and_reply') as MockAnalyze, \
             patch('dingbot.server.sender.send_text_from_env') as MockSend:
            
            MockAnalyze.return_value = {"reply": "你好！"}
            
            # Send a test message
            response = client.post('/webhook', 
                json={
                    "msgtype": "text",
                    "text": {"content": "你好，我是新用户"},
                    "senderNick": "TestUser",
                    "senderId": "test_user_001"
                }
            )
            
            # Verify response
            assert response.status_code == 200
            MockAnalyze.assert_called_once()
            MockSend.assert_called()

    def test_health_check(self):
        """Test health check endpoint."""
        with patch('dingbot.server.init_mem0'):
            init_app(start_scheduler=False)
        
        client = app.test_client()
        response = client.get('/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ok"


class TestMemoryFlow:
    """Test the complete memory flow as specified in requirements."""

    def test_complete_flow_dingtalk_to_mem0_to_llm(self):
        """Test: DingTalk -> Mem0 add -> Mem0 search -> Prompt -> LLM -> DingTalk."""
        with patch('dingbot.agent.get_mem0_manager') as MockGetMem0, \
             patch('dingbot.agent._call_model') as MockCall, \
             patch('dingbot.agent.get_user_memories') as MockGetMemories:
            
            # Setup mock Mem0 manager
            mock_mem0_mgr = MagicMock()
            MockGetMem0.return_value = mock_mem0_mgr
            
            # Simulate the flow
            user_id = "dingtalk_user_123"
            user_message = "我最近在学习深度学习"
            
            # Step 1: Add to Mem0
            mock_mem0_mgr.add_memory.return_value = "mem_id_789"
            
            # Step 2: Search from Mem0
            mock_mem0_mgr.search_memories.return_value = [
                {"memory": "用户之前提到喜欢机器学习", "score": 0.92},
                {"memory": "用户使用Python编程", "score": 0.85}
            ]
            mock_mem0_mgr.format_memories_as_context.return_value = (
                "- 用户之前提到喜欢机器学习\n"
                "- 用户使用Python编程"
            )
            
            # Step 3 & 4: LLM responds with personalized reply
            MockGetMemories.return_value = []
            MockCall.return_value = json.dumps({
                "reply": "深度学习很有趣！看来你在机器学习方向持续深造呢，加油！"
            })
            
            # Execute the complete flow
            result = analyze_and_reply(user_message, "小王", user_id)
            
            # Verify each step
            logger.info(f"Flow test result: {result}")
            
            # Verify Mem0 add was called (Step 1)
            mock_mem0_mgr.add_memory.assert_called_once()
            add_call_args = mock_mem0_mgr.add_memory.call_args
            assert add_call_args[0][1] == user_id
            logger.info(f"Step 1 - Add memory: OK (added for {user_id})")
            
            # Verify Mem0 search was called (Step 2)
            mock_mem0_mgr.search_memories.assert_called_once()
            search_call_args = mock_mem0_mgr.search_memories.call_args
            assert search_call_args[0][1] == user_id
            logger.info(f"Step 2 - Search memory: OK (found {len(mock_mem0_mgr.search_memories.return_value)} results)")
            
            # Verify prompt formatting (Step 3)
            mock_mem0_mgr.format_memories_as_context.assert_called_once()
            logger.info(f"Step 3 - Format context: OK")
            
            # Verify LLM was called (Step 4)
            assert MockCall.called
            call_prompt = MockCall.call_args[0][0]
            assert "关于用户的相关信息" in call_prompt
            assert "深度学习" in call_prompt
            logger.info(f"Step 4 - Call LLM: OK (prompt includes memory context)")
            
            # Verify response (Step 5)
            assert result["reply"] == "深度学习很有趣！看来你在机器学习方向持续深造呢，加油！"
            logger.info(f"Step 5 - Return result: OK")
            
            logger.info("✅ Complete flow test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
