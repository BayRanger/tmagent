"""Bash command execution tool."""

import asyncio
import os
from typing import Any

from .base import Tool, ToolResult


class BashTool(Tool):
    """Execute shell commands."""

    def __init__(self, workspace_dir: str | None = None):
        self.workspace_dir = workspace_dir

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return """Execute bash commands in terminal.

For terminal operations like git, npm, docker, etc. DO NOT use for file operations.

Parameters:
  - command (required): Bash command to execute
  - timeout (optional): Timeout in seconds (default: 120)"""

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 120)",
                    "default": 120,
                },
            },
            "required": ["command"],
        }

    async def execute(self, command: str, timeout: int = 120) -> ToolResult:
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(success=False, error=f"Command timed out after {timeout} seconds")

            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            if process.returncode != 0:
                error_msg = f"Command failed with exit code {process.returncode}"
                if stderr_text:
                    error_msg += f"\n{stderr_text}"
                return ToolResult(success=False, error=error_msg)

            return ToolResult(success=True, content=stdout_text or "(no output)")

        except Exception as e:
            return ToolResult(success=False, error=str(e))
