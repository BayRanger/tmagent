"""Tests for schema models."""

import pytest
from tmagent.schema import (
    FunctionCall,
    LLMProvider,
    Message,
    ToolCall,
    ToolResult,
)


class TestLLMProvider:
    """Tests for LLMProvider enum."""

    def test_anthropic_value(self):
        assert LLMProvider.ANTHROPIC.value == "anthropic"

    def test_openai_value(self):
        assert LLMProvider.OPENAI.value == "openai"


class TestFunctionCall:
    """Tests for FunctionCall model."""

    def test_create_function_call(self):
        fc = FunctionCall(name="test", arguments={"key": "value"})
        assert fc.name == "test"
        assert fc.arguments == {"key": "value"}

    def test_function_call_with_empty_args(self):
        fc = FunctionCall(name="test", arguments={})
        assert fc.name == "test"
        assert fc.arguments == {}


class TestToolCall:
    """Tests for ToolCall model."""

    def test_create_tool_call(self):
        tc = ToolCall(
            id="test_id",
            type="function",
            function=FunctionCall(name="test", arguments={"key": "value"}),
        )
        assert tc.id == "test_id"
        assert tc.type == "function"
        assert tc.function.name == "test"

    def test_tool_call_default_type(self):
        tc = ToolCall(
            id="test_id",
            function=FunctionCall(name="test", arguments={}),
        )
        assert tc.type == "function"


class TestMessage:
    """Tests for Message model."""

    def test_create_user_message(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_create_assistant_message_with_tool_calls(self):
        tool_call = ToolCall(
            id="tc_1",
            function=FunctionCall(name="bash", arguments={"command": "ls"}),
        )
        msg = Message(
            role="assistant",
            content="I'll run that command",
            tool_calls=[tool_call],
        )
        assert msg.role == "assistant"
        assert msg.tool_calls is not None
        assert len(msg.tool_calls) == 1

    def test_create_tool_message(self):
        msg = Message(
            role="tool",
            content="file content",
            tool_call_id="tc_1",
            name="read_file",
        )
        assert msg.role == "tool"
        assert msg.tool_call_id == "tc_1"
        assert msg.name == "read_file"


class TestToolResult:
    """Tests for ToolResult model."""

    def test_create_success_result(self):
        result = ToolResult(success=True, content="result content")
        assert result.success is True
        assert result.content == "result content"
        assert result.error is None

    def test_create_error_result(self):
        result = ToolResult(success=False, error="something went wrong")
        assert result.success is False
        assert result.content == ""
        assert result.error == "something went wrong"

    def test_tool_result_default_content(self):
        result = ToolResult(success=True)
        assert result.content == ""
