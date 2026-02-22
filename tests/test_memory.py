"""Tests for memory management functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from tmagent.agent import Agent, DEFAULT_TOKEN_LIMIT
from tmagent.schema import Message, ToolCall, FunctionCall


class TestTokenCounting:
    """Test token counting functionality."""

    def test_system_message_tokens(self):
        """Test token counting for system message."""
        from tmagent.llm import LLMClient
        
        mock_llm = MagicMock(spec=LLMClient)
        mock_llm.generate = AsyncMock(return_value=MagicMock(
            content="test",
            tool_calls=None
        ))
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="You are a helpful assistant.",
            tools=[],
            token_limit=1000
        )
        
        # System prompt should have some tokens
        tokens = agent.count_tokens()
        assert tokens > 0

    def test_token_limit_default(self):
        """Test default token limit is set correctly."""
        assert DEFAULT_TOKEN_LIMIT == 80_000


class TestMessageSummarization:
    """Test message summarization logic."""

    def test_get_messages_to_summarize_empty(self):
        """Test with minimal messages."""
        from tmagent.llm import LLMClient
        
        mock_llm = MagicMock(spec=LLMClient)
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="Test",
            tools=[]
        )
        
        to_summarize, remaining = agent._get_messages_to_summarize()
        # With only system message, nothing to summarize
        assert len(remaining) == 1  # Only system message

    def test_get_messages_to_summarize_single_user(self):
        """Test with single user message."""
        from tmagent.llm import LLMClient
        
        mock_llm = MagicMock(spec=LLMClient)
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="Test",
            tools=[]
        )
        
        # Add one user message
        agent.messages.append(Message(role="user", content="Hello"))
        
        to_summarize, remaining = agent._get_messages_to_summarize()
        # Single user message, nothing to summarize
        assert len(remaining) == 2  # system + user

    def test_get_messages_to_summarize_multiple_users(self):
        """Test with multiple user messages."""
        from tmagent.llm import LLMClient
        
        mock_llm = MagicMock(spec=LLMClient)
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="Test",
            tools=[]
        )
        
        # Add multiple user messages
        agent.messages.append(Message(role="user", content="Hello"))
        agent.messages.append(Message(role="assistant", content="Hi there"))
        agent.messages.append(Message(role="tool", content="Tool result", name="tool1"))
        agent.messages.append(Message(role="user", content="How are you?"))
        
        to_summarize, remaining = agent._get_messages_to_summarize()
        
        # Should find messages between user queries to summarize
        assert len(to_summarize) == 2  # assistant + tool
        # Should keep: system + user1 + user2
        assert len(remaining) == 3


class TestTokenLimitCheck:
    """Test token limit checking."""

    def test_check_and_summarize_under_limit(self):
        """Test when under token limit."""
        from tmagent.llm import LLMClient
        
        mock_llm = MagicMock(spec=LLMClient)
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="Test",
            tools=[],
            token_limit=100_000  # High limit
        )
        
        # Should not need to summarize
        assert not agent._check_and_summarize()

    def test_token_limit_parameter(self):
        """Test token_limit parameter is stored."""
        from tmagent.llm import LLMClient
        
        mock_llm = MagicMock(spec=LLMClient)
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="Test",
            tools=[],
            token_limit=50_000
        )
        
        assert agent.token_limit == 50_000


class TestMemoryManagementIntegration:
    """Integration tests for memory management."""

    @pytest.mark.asyncio
    async def test_summarize_method_exists(self):
        """Test that summarize method exists."""
        from tmagent.llm import LLMClient
        
        mock_llm = MagicMock(spec=LLMClient)
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="Test",
            tools=[]
        )
        
        # Method should exist
        assert hasattr(agent, '_summarize_messages')
        assert asyncio.iscoroutinefunction(agent._summarize_messages)

    @pytest.mark.asyncio
    async def test_run_completes_without_error(self):
        """Test that run loop completes when no tools needed."""
        from tmagent.llm import LLMClient
        from tmagent.llm import LLMResponse
        
        mock_llm = MagicMock(spec=LLMClient)
        
        # Mock generate to return without tool calls
        mock_llm.generate = AsyncMock(return_value=LLMResponse(
            content="Done",
            tool_calls=None,
        ))
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="Test",
            tools=[],
            token_limit=100_000  # High limit
        )
        
        agent.add_user_message("Hello")
        
        result = await agent.run()
        
        # Should complete without error
        assert result == "Done"

    @pytest.mark.asyncio
    async def test_token_count_increases_with_messages(self):
        """Test that token count increases as messages are added."""
        from tmagent.llm import LLMClient
        
        mock_llm = MagicMock(spec=LLMClient)
        
        agent = Agent(
            llm_client=mock_llm,
            system_prompt="You are a helpful assistant.",
            tools=[],
            token_limit=100_000
        )
        
        initial_tokens = agent.count_tokens()
        
        # Add more messages
        agent.messages.append(Message(role="user", content="Hello, how are you?"))
        agent.messages.append(Message(role="assistant", content="I'm doing well, thank you!"))
        
        new_tokens = agent.count_tokens()
        
        assert new_tokens > initial_tokens
