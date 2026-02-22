"""Core Agent implementation for TinyAgent."""

import asyncio
import json
from pathlib import Path
from typing import Any

from .llm import LLMClient
from .schema import Message, ToolCall, ToolResult
from .tools.base import Tool


class Agent:
    """Minimal AI Agent with function calling capability."""

    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        tools: list[Tool],
        max_steps: int = 50,
        workspace_dir: str = "./workspace",
    ):
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Inject workspace info into system prompt
        if "Current Workspace" not in system_prompt:
            system_prompt = system_prompt + f"\n\n## Current Workspace\n`{self.workspace_dir.absolute()}`"

        self.system_prompt = system_prompt
        self.messages: list[Message] = [Message(role="system", content=system_prompt)]

    def add_user_message(self, content: str):
        """Add a user message to history."""
        self.messages.append(Message(role="user", content=content))

    async def run(self) -> str:
        """Execute agent loop until task is complete or max steps reached."""

        for step in range(self.max_steps):
            print(f"\n=== Step {step + 1}/{self.max_steps} ===\n")

            # Get tool list
            tool_list = list(self.tools.values())

            # Call LLM
            response = await self.llm.generate(messages=self.messages, tools=tool_list)

            # Print assistant response
            if response.content:
                print(f"Assistant: {response.content}\n")

            # Check if task is complete (no tool calls)
            if not response.tool_calls:
                return response.content

            # Execute tool calls and store results
            tool_results = {}
            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                print(f"🔧 Tool Call: {tool_name}")
                print(f"   Arguments: {json.dumps(arguments, indent=2)}\n")

                # Execute tool
                if tool_name not in self.tools:
                    result = ToolResult(success=False, error=f"Unknown tool: {tool_name}")
                else:
                    try:
                        tool = self.tools[tool_name]
                        result = await tool.execute(**arguments)
                    except Exception as e:
                        result = ToolResult(success=False, error=str(e))

                # Print result
                if result.success:
                    print(f"✓ Result: {result.content[:500]}")
                else:
                    print(f"✗ Error: {result.error}")
                
                # Store result keyed by tool_call.id
                tool_results[tool_call.id] = (tool_name, result)

            # Add assistant message with tool calls AFTER executing all tools
            # This is required by Anthropic API - tool results must follow assistant message with tool_use
            if response.tool_calls:
                assistant_msg = Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
                self.messages.append(assistant_msg)

            # Add tool result messages
            for tool_call in response.tool_calls:
                tool_name, result = tool_results[tool_call.id]

                tool_msg = Message(
                    role="tool",
                    content=result.content if result.success else f"Error: {result.error}",
                    tool_call_id=tool_call.id,
                    name=tool_name,
                )
                self.messages.append(tool_msg)

            print()

        return f"Task couldn't be completed after {self.max_steps} steps."

    def get_history(self) -> list[Message]:
        """Get message history."""
        return self.messages.copy()
