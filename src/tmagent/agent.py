"""Core Agent implementation for TinyAgent."""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

import tiktoken

from .llm import LLMClient
from .schema import Message, ToolCall, ToolResult
from .tools.base import Tool
from .tools.skill_loader import SkillLoader


# Default token limit (80K tokens, leaving room for response)
DEFAULT_TOKEN_LIMIT = 80_000


class Agent:
    """Minimal AI Agent with function calling capability, Progressive Disclosure, and Memory Management."""

    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        tools: list[Tool],
        max_steps: int = 50,
        workspace_dir: str = "./workspace",
        skills_dir: Optional[str] = None,
        token_limit: int = DEFAULT_TOKEN_LIMIT,
    ):
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory management
        self.token_limit = token_limit
        self.encoder = tiktoken.get_encoding("cl100k_base")

        # Initialize skill loader if skills_dir is provided
        self.skill_loader: Optional[SkillLoader] = None
        if skills_dir:
            from .tools.skill_loader import SkillLoader
            from .tools.skill_tool import GetSkillTool, ListSkillsTool

            self.skill_loader = SkillLoader(skills_dir)
            discovered_skills = self.skill_loader.discover_skills()

            # Add skill tools to agent
            if discovered_skills:
                self.tools["get_skill"] = GetSkillTool(self.skill_loader)
                self.tools["list_skills"] = ListSkillsTool(self.skill_loader)

                # Add skill metadata to system prompt (Level 1)
                skills_prompt = self.skill_loader.get_skills_metadata_prompt()
                if skills_prompt:
                    system_prompt = system_prompt + f"\n\n{skills_prompt}"

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

            # Check token limit and summarize if needed
            if self._check_and_summarize():
                await self._summarize_messages()

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

    # ==================== Memory Management ====================
    
    def count_tokens(self, messages: list[Message] | None = None) -> int:
        """Count total tokens in message history.
        
        Uses tiktoken with cl100k_base encoding (GPT-4/Claude compatible).
        """
        if messages is None:
            messages = self.messages
            
        total = 0
        for msg in messages:
            # Base overhead per message (role + content structure)
            total += 4
            # Content tokens
            total += len(self.encoder.encode(msg.content))
            # Additional tokens for tool calls
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total += len(self.encoder.encode(tc.function.name))
                    total += len(self.encoder.encode(json.dumps(tc.function.arguments)))
        return total

    def _get_messages_to_summarize(self) -> tuple[list[Message], list[Message]]:
        """Get messages between user queries that can be summarized.
        
        Returns:
            - messages_to_summarize: Assistant + tool messages between user queries
            - remaining_messages: System + user messages to keep
        """
        if len(self.messages) <= 2:
            return [], self.messages
            
        # Keep system message
        system_msg = self.messages[0]
        
        # Find all user messages (we never summarize user intent)
        user_indices = []
        for i, msg in enumerate(self.messages):
            if msg.role == "user":
                user_indices.append(i)
        
        if len(user_indices) < 2:
            # Only one user message, no need to summarize
            return [], self.messages
        
        # Get messages between first user and last user
        first_user_idx = user_indices[0]
        last_user_idx = user_indices[-1]
        
        # Messages to summarize (between first and last user, excluding both)
        to_summarize = self.messages[first_user_idx + 1:last_user_idx]
        
        # Keep: system + all user messages + messages after last user
        remaining = [system_msg] + [self.messages[i] for i in user_indices]
        
        # Add messages after last user query
        if last_user_idx + 1 < len(self.messages):
            remaining += self.messages[last_user_idx + 1:]
        
        return to_summarize, remaining

    async def _summarize_messages(self) -> bool:
        """Summarize old messages when token limit is exceeded.
        
        Keeps:
        - System prompt (never summarize)
        - All user messages (user intent is precious)
        - Most recent context
        
        Compresses:
        - Assistant reasoning
        - Tool execution details
        - Intermediate steps
        
        Returns:
            True if summarization was performed, False otherwise
        """
        to_summarize, remaining = self._get_messages_to_summarize()
        
        if not to_summarize:
            return False
        
        # Build summarization prompt
        summary_prompt = [
            Message(role="user", content=
                "Summarize the following conversation concisely, keeping:\n"
                "1. Key decisions made\n"
                "2. Important information discovered\n"
                "3. Current state of work\n"
                "4. Any errors encountered and how they were resolved\n\n"
                "Remove verbose details, tool output, and repetitive information."
            ),
            *to_summarize
        ]
        
        print(f"\n📝 Summarizing {len(to_summarize)} messages...")
        
        # Call LLM to summarize
        response = await self.llm.generate(messages=summary_prompt, tools=[])
        
        # Create summary message
        summary_content = f"[Previous conversation summarized]\n\n{response.content}"
        
        # Replace old messages with summary
        self.messages = remaining + [
            Message(role="assistant", content=summary_content)
        ]
        
        new_count = self.count_tokens()
        print(f"📝 Token count: {new_count:,} (limit: {self.token_limit:,})")
        
        return True

    def _check_and_summarize(self) -> bool:
        """Check if summarization is needed but don't execute it.
        
        Returns:
            True if tokens exceed limit, False otherwise
        """
        return self.count_tokens() > self.token_limit
