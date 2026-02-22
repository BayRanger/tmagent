# TM-Agent Tools

This directory contains the tool system that enables TM-Agent to interact with the external world through function calling.

## What is Function Calling?

Function calling (also known as tool calling) allows an LLM to invoke external functions/tools to complete tasks. Instead of just generating text, the LLM can:

1. **Decide** which tool to use based on user input
2. **Extract** the necessary arguments from the conversation
3. **Receive** the tool's output and incorporate it into the response

This enables agents to:
- Read/write files
- Execute commands
- Search the web
- Call APIs
- And much more...

## Architecture

```
tools/
├── __init__.py       # Exports all available tools
├── base.py           # Base Tool class
├── file_tools.py     # File operations (read_file, write_file, edit_file)
└── bash_tool.py      # Shell command execution
```

## Base Tool Class

All tools inherit from the `Tool` base class which provides:

```python
from tm_agent.tools import Tool

class MyTool(Tool):
    @property
    def name(self) -> str:
        """Tool name - used by LLM to identify the tool"""
        return "my_tool"
    
    @property
    def description(self) -> str:
        """Human-readable description of what the tool does"""
        return "Description of what this tool does"
    
    @property
    def parameters(self) -> dict:
        """JSON Schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Description"},
            },
            "required": ["param1"],
        }
    
    async def execute(self, param1: str) -> ToolResult:
        """Execute the tool and return result"""
        return ToolResult(success=True, content="Result here")
```

## Creating Custom Tools

### Step 1: Define the Tool Class

```python
from tm_agent.tools import Tool, ToolResult

class CalculatorTool(Tool):
    def __init__(self):
        pass
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform basic mathematical calculations"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string", 
                    "description": "Mathematical expression (e.g., '2+2', '10*5')"
                }
            },
            "required": ["expression"],
        }
    
    async def execute(self, expression: str) -> ToolResult:
        try:
            result = eval(expression)  # Note: use safer eval in production
            return ToolResult(success=True, content=str(result))
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### Step 2: Register with Agent

```python
from tm_agent import Agent

agent = Agent(
    llm_client=llm,
    tools=[CalculatorTool()],  # Add your custom tool
)
```

## JSON Schema for Parameters

Tools use [JSON Schema](https://json-schema.org/) to define their parameters. This tells the LLM what arguments each tool expects.

### Basic Types

```python
{
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "User's name"},
        "age": {"type": "integer", "description": "User's age"},
        "active": {"type": "boolean", "description": "Is user active"},
    },
    "required": ["name"],
}
```

### With Default Values

```python
{
    "type": "object",
    "properties": {
        "command": {"type": "string", "description": "Command to run"},
        "timeout": {
            "type": "integer", 
            "description": "Timeout in seconds",
            "default": 120,  # Default value
        },
    },
    "required": ["command"],
}
```

### Enum Values

```python
{
    "type": "object",
    "properties": {
        "format": {
            "type": "string",
            "description": "Output format",
            "enum": ["json", "yaml", "xml"],
        },
    },
    "required": ["format"],
}
```

### Nested Objects

```python
{
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["name"],
        },
    },
    "required": ["user"],
}
```

### Arrays

```python
{
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of tags",
        },
    },
}
```

## Tool Schema Conversion

TM-Agent automatically converts tools to the format required by different LLM providers:

### Anthropic Schema

```python
def to_schema(self) -> dict:
    return {
        "name": self.name,
        "description": self.description,
        "input_schema": self.parameters,
    }
```

### OpenAI Schema

```python
def to_openai_schema(self) -> dict:
    return {
        "type": "function",
        "function": {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        },
    }
```

## Built-in Tools

### ReadTool

Read file contents with line numbers.

```python
tool = ReadTool(workspace_dir="/path/to/workspace")
# Parameters: path (string, required)
result = await tool.execute(path="example.py")
```

### WriteTool

Write content to a file (overwrites existing).

```python
tool = WriteTool(workspace_dir="/path/to/workspace")
# Parameters: path (string), content (string), both required
result = await tool.execute(path="example.py", content="print('hello')")
```

### EditTool

Replace exact text in a file.

```python
tool = EditTool(workspace_dir="/path/to/workspace")
# Parameters: path, old_str, new_str, all required
result = await tool.execute(
    path="example.py",
    old_str="hello",
    new_str="world"
)
```

### BashTool

Execute shell commands.

```python
tool = BashTool(workspace_dir="/path/to/workspace")
# Parameters: command (string, required), timeout (integer, optional, default: 120)
result = await tool.execute(command="ls -la", timeout=30)
```

## Best Practices

### 1. Clear Descriptions

Always provide clear, descriptive text for your tool and its parameters:

```python
# ✅ Good
@property
def description(self) -> str:
    return "Search for files matching a pattern in the workspace"

@property
def parameters(self) -> dict:
    return {
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern like *.py"},
        },
    }

# ❌ Bad
@property
def description(self) -> str:
    return "Search files"

@property
def parameters(self) -> dict:
    return {
        "properties": {
            "pattern": {"type": "string"},
        },
    }
```

### 2. Handle Errors Gracefully

Always return a `ToolResult` with `success=False` on errors:

```python
async def execute(self, path: str) -> ToolResult:
    try:
        # Do something
        return ToolResult(success=True, content=result)
    except FileNotFoundError:
        return ToolResult(success=False, error=f"File not found: {path}")
    except PermissionError:
        return ToolResult(success=False, error="Permission denied")
    except Exception as e:
        return ToolResult(success=False, error=str(e))
```

### 3. Use Workspace Boundaries

For file operations, always respect the workspace directory:

```python
def __init__(self, workspace_dir: str = "."):
    self.workspace_dir = Path(workspace_dir).absolute()

async def execute(self, path: str) -> ToolResult:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = self.workspace_dir / file_path  # Resolve relative to workspace
    
    # Security check
    if not str(file_path).startswith(str(self.workspace_dir)):
        return ToolResult(success=False, error="Path outside workspace")
```

### 4. Async Execution

Tools should be async for better performance:

```python
async def execute(self, ...) -> ToolResult:
    # Use async operations
    result = await async_operation()
    return ToolResult(success=True, content=result)
```

## Tool Result Format

Tools return a `ToolResult` with the following structure:

```python
from tm_agent.schema import ToolResult

# Success
result = ToolResult(
    success=True,
    content="The output or result of the tool execution"
)

# Failure
result = ToolResult(
    success=False,
    error="Error message describing what went wrong"
)
```

## Testing Tools

```python
import pytest
from tm_agent.tools import ReadTool, WriteTool, BashTool

@pytest.mark.asyncio
async def test_read_tool():
    tool = ReadTool(workspace_dir="./test_workspace")
    result = await tool.execute(path="test.txt")
    assert result.success is True
    assert "content" in result.content

@pytest.mark.asyncio
async def test_write_tool():
    tool = WriteTool(workspace_dir="./test_workspace")
    result = await tool.execute(path="test.txt", content="Hello")
    assert result.success is True

@pytest.mark.asyncio
async def test_bash_tool():
    tool = BashTool()
    result = await tool.execute(command="echo hello")
    assert result.success is True
    assert "hello" in result.content
```

## Further Reading

- [JSON Schema Documentation](https://json-schema.org/)
- [Anthropic Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
