"""LLM client for TinyAgent."""

import json
from typing import Any

import anthropic
import httpx
import openai

from .schema import FunctionCall, LLMProvider, Message, ToolCall, ToolResult


class LLMResponse:
    """LLM response."""

    def __init__(
        self,
        content: str,
        tool_calls: list[ToolCall] | None = None,
        finish_reason: str = "stop",
    ):
        self.content = content
        self.tool_calls = tool_calls
        self.finish_reason = finish_reason


class LLMClient:
    """Unified LLM client supporting Anthropic and OpenAI protocols."""

    def __init__(
        self,
        api_key: str,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        api_base: str = "https://api.minimaxi.com",
        model: str = "MiniMax-M2.5",
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model

        # Normalize api_base
        api_base = api_base.rstrip("/")

        # Handle MiniMax API endpoints
        if "minimax" in api_base:
            if provider == LLMProvider.ANTHROPIC:
                api_base = f"{api_base}/anthropic"
            elif provider == LLMProvider.OPENAI:
                api_base = f"{api_base}/v1"

        self.api_base = api_base

        # Initialize clients
        if provider == LLMProvider.ANTHROPIC:
            self.client = anthropic.AsyncAnthropic(base_url=api_base, api_key=api_key)
        elif provider == LLMProvider.OPENAI:
            self.client = openai.AsyncOpenAI(api_key=api_key, base_url=api_base)

    async def generate(
        self,
        messages: list[Message],
        tools: list | None = None,
    ) -> LLMResponse:
        """Generate response from LLM."""

        if self.provider == LLMProvider.ANTHROPIC:
            return await self._generate_anthropic(messages, tools)
        else:
            return await self._generate_openai(messages, tools)

    async def _generate_anthropic(self, messages: list[Message], tools: list | None = None) -> LLMResponse:
        """Generate using Anthropic protocol."""

        system_message = None
        api_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
                continue

            if msg.role == "user":
                api_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                if msg.tool_calls:
                    content = []
                    for tc in msg.tool_calls:
                        content.append(
                            {
                                "type": "tool_use",
                                "id": tc.id,
                                "name": tc.function.name,
                                "input": tc.function.arguments,
                            }
                        )
                    api_messages.append({"role": "assistant", "content": content})
                else:
                    api_messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == "tool":
                api_messages.append(
                    {
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": msg.tool_call_id, "content": msg.content}],
                    }
                )

        params = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": api_messages,
        }

        if system_message:
            params["system"] = system_message

        if tools:
            tool_schemas = []
            for tool in tools:
                if hasattr(tool, "to_schema"):
                    tool_schemas.append(tool.to_schema())
                else:
                    tool_schemas.append(tool)
            params["tools"] = tool_schemas

        response = await self.client.messages.create(**params)

        # Parse response
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        type="function",
                        function=FunctionCall(name=block.name, arguments=block.input),
                    )
                )

        return LLMResponse(content=content, tool_calls=tool_calls if tool_calls else None)

    async def _generate_openai(self, messages: list[Message], tools: list | None = None) -> LLMResponse:
        """Generate using OpenAI protocol."""

        api_messages = []

        for msg in messages:
            if msg.role == "system":
                api_messages.append({"role": "system", "content": msg.content})
            elif msg.role == "user":
                api_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                if msg.tool_calls:
                    content = []
                    for tc in msg.tool_calls:
                        content.append(
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": json.dumps(tc.function.arguments)},
                            }
                        )
                    api_messages.append({"role": "assistant", "content": None, "tool_calls": content})
                else:
                    api_messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == "tool":
                api_messages.append(
                    {"role": "tool", "tool_call_id": msg.tool_call_id, "content": msg.content, "name": msg.name}
                )

        params = {"model": self.model, "messages": api_messages}

        if tools:
            tool_schemas = []
            for tool in tools:
                if hasattr(tool, "to_openai_schema"):
                    tool_schemas.append(tool.to_openai_schema())
                else:
                    tool_schemas.append(tool)
            params["tools"] = tool_schemas

        response = await self.client.chat.completions.create(**params)
        response_msg = response.choices[0].message

        # Parse response
        content = response_msg.content or ""
        tool_calls = []

        if response_msg.tool_calls:
            for tc in response_msg.tool_calls:
                args = json.loads(tc.function.arguments)
                tool_calls.append(
                    ToolCall(id=tc.id, type="function", function=FunctionCall(name=tc.function.name, arguments=args))
                )

        return LLMResponse(content=content, tool_calls=tool_calls if tool_calls else None)
