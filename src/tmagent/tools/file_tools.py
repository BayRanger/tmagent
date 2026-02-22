"""File operation tools."""

from pathlib import Path
from typing import Any

from .base import Tool, ToolResult


class ReadTool(Tool):
    """Read file content."""

    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read file contents from the filesystem. Output includes line numbers."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative path to the file"},
            },
            "required": ["path"],
        }

    async def execute(self, path: str) -> ToolResult:
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")

            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Format with line numbers
            numbered_lines = [f"{i:6d}|{line.rstrip()}" for i, line in enumerate(lines, 1)]
            content = "\n".join(numbered_lines)

            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteTool(Tool):
    """Write content to a file."""

    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file. Will overwrite existing files completely."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative path to the file"},
                "content": {"type": "string", "description": "Complete content to write"},
            },
            "required": ["path", "content"],
        }

    async def execute(self, path: str, content: str) -> ToolResult:
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            return ToolResult(success=True, content=f"Successfully wrote to {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class EditTool(Tool):
    """Edit file by replacing text."""

    def __init__(self, workspace_dir: str = "."):
        self.workspace_dir = Path(workspace_dir).absolute()

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Perform exact string replacement in a file."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative path to the file"},
                "old_str": {"type": "string", "description": "Exact string to find and replace"},
                "new_str": {"type": "string", "description": "Replacement string"},
            },
            "required": ["path", "old_str", "new_str"],
        }

    async def execute(self, path: str, old_str: str, new_str: str) -> ToolResult:
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.workspace_dir / file_path

            if not file_path.exists():
                return ToolResult(success=False, error=f"File not found: {path}")

            content = file_path.read_text(encoding="utf-8")

            if old_str not in content:
                return ToolResult(success=False, error="Text not found in file")

            new_content = content.replace(old_str, new_str)
            file_path.write_text(new_content, encoding="utf-8")

            return ToolResult(success=True, content=f"Successfully edited {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
