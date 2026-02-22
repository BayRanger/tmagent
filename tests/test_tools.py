"""Tests for tool base class and tools."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from tmagent.schema import ToolResult
from tmagent.tools.base import Tool
from tmagent.tools.file_tools import ReadTool, WriteTool, EditTool
from tmagent.tools.bash_tool import BashTool


class TestTool:
    """Tests for base Tool class."""

    def test_tool_name_not_implemented(self):
        """Tool.name should raise NotImplementedError."""
        tool = Tool()
        with pytest.raises(NotImplementedError):
            _ = tool.name

    def test_tool_description_not_implemented(self):
        """Tool.description should raise NotImplementedError."""
        tool = Tool()
        with pytest.raises(NotImplementedError):
            _ = tool.description

    def test_tool_parameters_not_implemented(self):
        """Tool.parameters should raise NotImplementedError."""
        tool = Tool()
        with pytest.raises(NotImplementedError):
            _ = tool.parameters

    def test_tool_execute_not_implemented(self):
        """Tool.execute should raise NotImplementedError."""
        tool = Tool()
        with pytest.raises(NotImplementedError):
            import asyncio

            asyncio.run(tool.execute())


class ConcreteTool(Tool):
    """Concrete tool implementation for testing."""

    @property
    def name(self) -> str:
        return "test_tool"

    @property
    def description(self) -> str:
        return "A test tool"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "arg1": {"type": "string", "description": "First argument"}
            },
            "required": ["arg1"],
        }

    async def execute(self, arg1: str) -> ToolResult:
        return ToolResult(success=True, content=f"Executed with {arg1}")


class TestToolSchema:
    """Tests for tool schema conversion."""

    def test_to_schema(self):
        """Test converting tool to Anthropic schema."""
        tool = ConcreteTool()
        schema = tool.to_schema()

        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool"
        assert schema["input_schema"]["type"] == "object"
        assert "arg1" in schema["input_schema"]["properties"]

    def test_to_openai_schema(self):
        """Test converting tool to OpenAI schema."""
        tool = ConcreteTool()
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "test_tool"
        assert schema["function"]["description"] == "A test tool"
        assert schema["function"]["parameters"]["type"] == "object"


class TestReadTool:
    """Tests for ReadTool."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with test files."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World\nLine 2\nLine 3")
        return tmp_path

    def test_read_existing_file(self, temp_workspace):
        """Test reading an existing file."""
        tool = ReadTool(workspace_dir=str(temp_workspace))

        import asyncio

        result = asyncio.run(tool.execute(path="test.txt"))

        assert result.success is True
        assert "Hello World" in result.content

    def test_read_nonexistent_file(self, tmp_path):
        """Test reading a file that doesn't exist."""
        tool = ReadTool(workspace_dir=str(tmp_path))

        import asyncio

        result = asyncio.run(tool.execute(path="nonexistent.txt"))

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_read_with_absolute_path(self, tmp_path):
        """Test reading with absolute path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        tool = ReadTool(workspace_dir=str(tmp_path))

        import asyncio

        result = asyncio.run(tool.execute(path=str(test_file)))

        assert result.success is True

    def test_read_includes_line_numbers(self, temp_workspace):
        """Test that read includes line numbers."""
        tool = ReadTool(workspace_dir=str(temp_workspace))

        import asyncio

        result = asyncio.run(tool.execute(path="test.txt"))

        assert result.success is True
        # Check for line number format (e.g., "1|Hello World")
        assert "|Hello World" in result.content


class TestWriteTool:
    """Tests for WriteTool."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace."""
        return tmp_path

    def test_write_new_file(self, temp_workspace):
        """Test writing to a new file."""
        tool = WriteTool(workspace_dir=str(temp_workspace))

        import asyncio

        result = asyncio.run(
            tool.execute(path="new_file.txt", content="Hello World")
        )

        assert result.success is True
        assert (temp_workspace / "new_file.txt").read_text() == "Hello World"

    def test_overwrite_existing_file(self, temp_workspace):
        """Test overwriting an existing file."""
        test_file = temp_workspace / "existing.txt"
        test_file.write_text("Old content")

        tool = WriteTool(workspace_dir=str(temp_workspace))

        import asyncio

        result = asyncio.run(
            tool.execute(path="existing.txt", content="New content")
        )

        assert result.success is True
        assert test_file.read_text() == "New content"

    def test_create_nested_directories(self, temp_workspace):
        """Test creating nested directories."""
        tool = WriteTool(workspace_dir=str(temp_workspace))

        import asyncio

        result = asyncio.run(
            tool.execute(path="nested/dir/file.txt", content="Content")
        )

        assert result.success is True
        assert (temp_workspace / "nested" / "dir" / "file.txt").exists()


class TestEditTool:
    """Tests for EditTool."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create a temporary workspace with a test file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World\nFoo Bar\nHello Again")
        return tmp_path

    def test_edit_existing_text(self, temp_workspace):
        """Test editing existing text in a file."""
        tool = EditTool(workspace_dir=str(temp_workspace))

        import asyncio

        result = asyncio.run(
            tool.execute(
                path="test.txt",
                old_str="World",
                new_str="Python",
            )
        )

        assert result.success is True
        content = (temp_workspace / "test.txt").read_text()
        assert "World" not in content
        assert "Python" in content

    def test_edit_nonexistent_text(self, temp_workspace):
        """Test editing text that doesn't exist."""
        tool = EditTool(workspace_dir=str(temp_workspace))

        import asyncio

        result = asyncio.run(
            tool.execute(
                path="test.txt",
                old_str="Nonexistent",
                new_str="Something",
            )
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_edit_nonexistent_file(self, tmp_path):
        """Test editing a file that doesn't exist."""
        tool = EditTool(workspace_dir=str(tmp_path))

        import asyncio

        result = asyncio.run(
            tool.execute(
                path="nonexistent.txt",
                old_str="old",
                new_str="new",
            )
        )

        assert result.success is False
        assert "not found" in result.error.lower()


class TestBashTool:
    """Tests for BashTool."""

    def test_execute_echo_command(self):
        """Test executing a simple echo command."""
        tool = BashTool()

        import asyncio

        result = asyncio.run(tool.execute(command="echo 'Hello World'"))

        assert result.success is True
        assert "Hello World" in result.content

    def test_execute_ls_command(self):
        """Test executing ls command."""
        tool = BashTool(workspace_dir="/tmp")

        import asyncio

        result = asyncio.run(tool.execute(command="ls"))

        assert result.success is True

    def test_execute_invalid_command(self):
        """Test executing an invalid command."""
        tool = BashTool()

        import asyncio

        result = asyncio.run(tool.execute(command="nonexistent_command_xyz"))

        assert result.success is False
        assert result.error is not None

    def test_command_timeout(self):
        """Test command timeout."""
        tool = BashTool()

        import asyncio

        # Sleep command with very short timeout should fail
        result = asyncio.run(
            tool.execute(command="sleep 10", timeout=1)
        )

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_working_directory(self, tmp_path):
        """Test executing command in specified working directory."""
        tool = BashTool(workspace_dir=str(tmp_path))

        import asyncio

        result = asyncio.run(tool.execute(command="pwd"))

        assert result.success is True
        # The command should run in the workspace directory
