"""Mem0 Memory Manager for personalized chat with long-term memory support.

This module provides:
1. Memory initialization with Mem0
2. Adding conversation messages to memory
3. Searching relevant memories for context
4. Formatting memories into system prompts
"""

import logging
from typing import Dict, List, Any, Optional

try:
    from mem0 import Memory
except ImportError:
    Memory = None

from . import config

logger = logging.getLogger(__name__)


class Mem0Manager:
    """Manages interaction with Mem0 for personalized conversations."""

    def __init__(self):
        """Initialize Mem0 memory instance."""
        if Memory is None:
            raise ImportError("mem0ai is not installed. Please install it via 'pip install mem0ai'")

        try:
            # Initialize Mem0 with default configuration
            # It will use GPT-4o by default for memory operations
            self.memory = Memory()
            logger.info("Mem0 Memory instance initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            raise

    def add_memory(self, messages: List[Dict[str, str]], user_id: str) -> Optional[str]:
        """Add conversation messages to Mem0 memory.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            user_id: Unique identifier for the user
            
        Returns:
            Memory ID if successful, None otherwise
        """
        if not messages or not user_id:
            logger.warning(f"Invalid input: messages={bool(messages)}, user_id={user_id}")
            return None

        try:
            # Format messages for Mem0
            # Mem0 can accept raw messages or formatted text
            result = self.memory.add(
                data=messages,
                user_id=user_id,
                metadata={"source": "dinghook_chat"}
            )
            logger.info(f"Added memory for user {user_id}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error adding memory for user {user_id}: {e}")
            return None

    def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories based on query.
        
        Args:
            query: Search query text
            user_id: Unique identifier for the user
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant memory dicts with 'memory' and 'score' fields
        """
        if not query or not user_id:
            logger.warning(f"Invalid input: query={query}, user_id={user_id}")
            return []

        try:
            result = self.memory.search(query=query, user_id=user_id, limit=limit)
            # Extract results from the response
            memories = result.get("results", []) if isinstance(result, dict) else []
            logger.debug(f"Found {len(memories)} memories for user {user_id} with query '{query}'")
            return memories
        except Exception as e:
            logger.error(f"Error searching memories for user {user_id}: {e}")
            return []

    def format_memories_as_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories into a string for use in system prompt.
        
        Args:
            memories: List of memory dicts returned from search
            
        Returns:
            Formatted string of memories for inclusion in prompt
        """
        if not memories:
            return ""

        formatted = []
        for i, mem in enumerate(memories, 1):
            # Extract memory content - different responses may have different structure
            memory_text = mem.get("memory") or mem.get("content") or str(mem)
            if memory_text:
                formatted.append(f"- {memory_text}")

        return "\n".join(formatted) if formatted else ""

    def get_user_profile(self, user_id: str, limit: int = 10) -> str:
        """Get a brief profile of the user based on their memories.
        
        Args:
            user_id: Unique identifier for the user
            limit: Maximum number of memories to retrieve
            
        Returns:
            Formatted string describing the user profile
        """
        try:
            # Search for general info about the user
            memories = self.memory.search(
                query="user profile preferences interests habits",
                user_id=user_id,
                limit=limit
            )
            
            if not memories or not memories.get("results"):
                return "No user profile information available."
            
            profile_items = []
            for mem in memories.get("results", []):
                memory_text = mem.get("memory") or mem.get("content")
                if memory_text:
                    profile_items.append(memory_text)
            
            if profile_items:
                return "User Profile:\n" + "\n".join(f"- {item}" for item in profile_items)
            return "No user profile information available."
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return "Could not retrieve user profile."

    def build_system_prompt(
        self,
        base_prompt: str,
        user_id: str,
        query: str,
        include_profile: bool = True
    ) -> str:
        """Build a comprehensive system prompt with user context.
        
        Args:
            base_prompt: Base system prompt
            user_id: User identifier
            query: Current user query/message
            include_profile: Whether to include user profile summary
            
        Returns:
            Enhanced system prompt with memory context
        """
        prompt_parts = [base_prompt]

        # Add user profile if requested
        if include_profile:
            profile = self.get_user_profile(user_id, limit=5)
            if profile and profile != "No user profile information available.":
                prompt_parts.append(f"\n{profile}")

        # Search for relevant memories
        memories = self.search_memories(query, user_id, limit=5)
        if memories:
            memories_text = self.format_memories_as_context(memories)
            if memories_text:
                prompt_parts.append(f"\nRelevant Information:\n{memories_text}")

        return "\n".join(prompt_parts)


# Global instance
_mem0_manager: Optional[Mem0Manager] = None


def get_mem0_manager() -> Optional[Mem0Manager]:
    """Get or create the Mem0 manager instance."""
    global _mem0_manager
    if _mem0_manager is None:
        try:
            _mem0_manager = Mem0Manager()
        except Exception as e:
            logger.error(f"Failed to initialize Mem0Manager: {e}")
            return None
    return _mem0_manager


def init_mem0():
    """Initialize Mem0 manager."""
    try:
        get_mem0_manager()
        logger.info("Mem0 initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Mem0: {e}")
        return False
