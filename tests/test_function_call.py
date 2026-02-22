"""Integration tests for function calling."""

import asyncio
import json
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from tmagent.agent import Agent
from tmagent.llm import LLMClient, LLMResponse
from tmagent.schema import LLMProvider, Message, ToolCall, FunctionCall
from tmagent.tools import ReadTool, WriteTool, BashTool


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, responses: list[LLMResponse]):
        self.responses = responses
        self.call_count = 0

    async def generate(self, messages: list[Message], tools: list = None) -> LLMResponse:
        """Return mock responses in sequence."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return LLMResponse(content="No more responses", tool_calls=None)


class TestAgentFunctionCall:
    """Tests for Agent function calling."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace."""
        return tmp_path

    def test_agent_initialization(self, temp_workspace):
        """Test agent initializes correctly."""
        mock_client = MagicMock(spec=LLMClient)

        tools = [
            ReadTool(workspace_dir=str(temp_workspace)),
            WriteTool(workspace_dir=str(temp_workspace)),
        ]

        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=tools,
            workspace_dir=str(temp_workspace),
        )

        assert agent.llm is not None
        assert len(agent.tools) == 2
        assert "read_file" in agent.tools
        assert "write_file" in agent.tools

    def test_add_user_message(self, temp_workspace):
        """Test adding user messages."""
        mock_client = MagicMock(spec=LLMClient)
        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=[],
            workspace_dir=str(temp_workspace),
        )

        initial_count = len(agent.messages)
        agent.add_user_message("Hello")

        assert len(agent.messages) == initial_count + 1
        assert agent.messages[-1].role == "user"
        assert agent.messages[-1].content == "Hello"

    def test_run_without_tools_calls(self, temp_workspace):
        """Test agent run when no tool calls are needed."""

        # Create mock client that returns a simple response
        async def mock_generate(messages, tools=None):
            return LLMResponse(content="Hello! How can I help you?", tool_calls=None)

        mock_client = MagicMock(spec=LLMClient)
        mock_client.generate = mock_generate

        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=[],
            workspace_dir=str(temp_workspace),
        )

        agent.add_user_message("Say hello")
        result = asyncio.run(agent.run())

        assert result == "Hello! How can I help you?"

    def test_single_tool_call_execution(self, temp_workspace):
        """Test agent executes a single tool call."""

        # First response: tool call for read_file
        # Second response: final answer
        responses = [
            LLMResponse(
                content="I'll read that file for you.",
                tool_calls=[
                    ToolCall(
                        id="tc_1",
                        function=FunctionCall(
                            name="read_file",
                            arguments={"path": "test.txt"},
                        )
                    )
                ]
            ),
            LLMResponse(
                content="The file contains: Hello World",
                tool_calls=None
            ),
        ]

        # Create test file
        (temp_workspace / "test.txt").write_text("Hello World")

        mock_client = MockLLMClient(responses)
        tools = [ReadTool(workspace_dir=str(temp_workspace))]

        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=tools,
            workspace_dir=str(temp_workspace),
        )

        agent.add_user_message("Read test.txt")
        result = asyncio.run(agent.run())

        assert "Hello World" in result

    def test_multiple_tool_calls(self, temp_workspace):
        """Test agent executes multiple tool calls in sequence."""

        responses = [
            # First LLM call: write_file tool call
            LLMResponse(
                content="I'll create the file.",
                tool_calls=[
                    ToolCall(
                        id="tc_1",
                        function=FunctionCall(
                            name="write_file",
                            arguments={
                                "path": "output.txt",
                                "content": "Test content",
                            },
                        )
                    )
                ]
            ),
            # Second LLM call: read_file tool call
            LLMResponse(
                content="Now I'll read it back.",
                tool_calls=[
                    ToolCall(
                        id="tc_2",
                        function=FunctionCall(
                            name="read_file",
                            arguments={"path": "output.txt"},
                        )
                    )
                ]
            ),
            # Third LLM call: final answer
            LLMResponse(
                content="I've created and read the file. It contains: Test content",
                tool_calls=None
            ),
        ]

        mock_client = MockLLMClient(responses)
        tools = [
            ReadTool(workspace_dir=str(temp_workspace)),
            WriteTool(workspace_dir=str(temp_workspace)),
        ]

        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=tools,
            workspace_dir=str(temp_workspace),
        )

        agent.add_user_message("Create a file and read it back")
        result = asyncio.run(agent.run())

        assert "Test content" in result

    def test_bash_tool_call(self, temp_workspace):
        """Test agent can execute bash commands."""

        responses = [
            LLMResponse(
                content="I'll run that command.",
                tool_calls=[
                    ToolCall(
                        id="tc_1",
                        function=FunctionCall(
                            name="bash",
                            arguments={"command": "echo 'Hello from bash'"},
                        )
                    )
                ]
            ),
            LLMResponse(
                content="The command output: Hello from bash",
                tool_calls=None
            ),
        ]

        mock_client = MockLLMClient(responses)
        tools = [BashTool(workspace_dir=str(temp_workspace))]

        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=tools,
            workspace_dir=str(temp_workspace),
        )

        agent.add_user_message("Run echo command")
        result = asyncio.run(agent.run())

        assert "Hello from bash" in result

    def test_unknown_tool_handling(self, temp_workspace):
        """Test agent handles unknown tool gracefully."""

        # LLM calls a tool that doesn't exist
        responses = [
            LLMResponse(
                content="I'll try that tool.",
                tool_calls=[
                    ToolCall(
                        id="tc_1",
                        function=FunctionCall(
                            name="nonexistent_tool",
                            arguments={},
                        )
                    )
                ]
            ),
            LLMResponse(
                content="I apologize, that tool is not available.",
                tool_calls=None
            ),
        ]

        mock_client = MockLLMClient(responses)
        tools = [ReadTool(workspace_dir=str(temp_workspace))]

        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=tools,
            workspace_dir=str(temp_workspace),
        )

        agent.add_user_message("Use nonexistent tool")
        result = asyncio.run(agent.run())

        # Should handle error gracefully
        assert result is not None

    def test_max_steps_limit(self, temp_workspace):
        """Test agent respects max_steps limit."""

        # Create infinite loop scenario - LLM always calls tools
        responses = [
            LLMResponse(
                content="Tool call 1",
                tool_calls=[
                    ToolCall(
                        id=f"tc_{i}",
                        function=FunctionCall(
                            name="read_file",
                            arguments={"path": "test.txt"},
                        )
                    )
                ]
            )
            for i in range(100)  # Many tool calls
        ]

        mock_client = MockLLMClient(responses)
        tools = [ReadTool(workspace_dir=str(temp_workspace))]

        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=tools,
            workspace_dir=str(temp_workspace),
            max_steps=3,  # Limit to 3 steps
        )

        agent.add_user_message("Do something")
        result = asyncio.run(agent.run())

        # Should stop after max_steps
        assert "couldn't be completed" in result.lower()
        assert agent.llm.call_count == 3

    def test_message_history_accumulation(self, temp_workspace):
        """Test message history grows within a single run."""

        # This test checks that within a single run with tool calls,
        # message history accumulates correctly (system + user + assistant + tool results)
        responses = [
            LLMResponse(
                content="I'll use a tool.",
                tool_calls=[
                    ToolCall(
                        id="tc_1",
                        function=FunctionCall(
                            name="read_file",
                            arguments={"path": "test.txt"},
                        )
                    )
                ]
            ),
            # Create test file for the tool to read
            LLMResponse(
                content="File content: Hello World",
                tool_calls=None
            ),
        ]

        # Create the test file
        (temp_workspace / "test.txt").write_text("Hello World")

        mock_client = MockLLMClient(responses)

        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=[ReadTool(workspace_dir=str(temp_workspace))],
            workspace_dir=str(temp_workspace),
        )

        # Single run with tool call should have:
        # system + user + assistant (with tool call) + tool result
        # (final assistant message is returned but not added to history)
        agent.add_user_message("Read test.txt")
        asyncio.run(agent.run())

        # Should have: system + user + assistant + tool
        assert len(agent.messages) == 4

    def test_get_history(self, temp_workspace):
        """Test getting message history."""
        mock_client = MagicMock(spec=LLMClient)
        agent = Agent(
            llm_client=mock_client,
            system_prompt="You are a helpful assistant.",
            tools=[],
            workspace_dir=str(temp_workspace),
        )

        agent.add_user_message("Hello")
        history = agent.get_history()

        assert len(history) == 2  # system + user
        assert history[-1].content == "Hello"

        # Verify history contains expected content
        assert any(msg.role == "system" for msg in history)
        assert any(msg.content == "Hello" for msg in history)


class TestLLMResponseParsing:
    """Tests for LLM response parsing."""

    def test_response_with_tool_calls(self):
        """Test parsing response with tool calls."""
        response = LLMResponse(
            content="I'll use the tool.",
            tool_calls=[
                ToolCall(
                    id="tc_1",
                    function=FunctionCall(
                        name="bash",
                        arguments={"command": "ls"}
                    )
                )
            ]
        )

        assert response.content == "I'll use the tool."
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].function.name == "bash"

    def test_response_without_tool_calls(self):
        """Test parsing response without tool calls."""
        response = LLMResponse(
            content="Hello world",
            tool_calls=None
        )

        assert response.content == "Hello world"
        assert response.tool_calls is None

    def test_response_finish_reason(self):
        """Test response finish reason."""
        response = LLMResponse(
            content="Done",
            finish_reason="stop"
        )

        assert response.finish_reason == "stop"
