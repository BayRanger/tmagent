# Function Calling in Mini-Agent

> How Mini-Agent enables LLMs to use tools through structured function calling

---

## What is Function Calling?

Function calling (also called tool calling) allows an LLM to:

1. **Generate structured output** (not just text)
2. **Call external functions** with specific arguments
3. **Act on the results** before responding

### Traditional LLM Flow

```
User → LLM → Text Response (end)
```

### Function Calling Flow

```
User → LLM → Function Call → Execute Tool → Results → LLM → Response
```

---

## The Mechanism

### 1. Tool Definition

```python
from tmagent.tools import Tool, ToolResult

class ReadFileTool(Tool):
    name = "read_file"
    description = "Read contents of a file from the filesystem"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["path"]
    }
    
    async def execute(self, path: str) -> ToolResult:
        try:
            content = Path(path).read_text()
            return ToolResult(success=True, content=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### 2. Schema Conversion

LLMs need tools in their native format. Mini-Agent converts to both:

#### Anthropic Format (JSON Schema)

```python
def to_schema(self) -> list[dict]:
    """Convert to Anthropic tool format."""
    return [{
        "name": self.name,
        "description": self.description,
        "input_schema": {
            "type": "object",
            "properties": self.parameters.get("properties", {}),
            "required": self.parameters.get("required", [])
        }
    }]
```

#### OpenAI Format

```python
def to_openai_schema(self) -> list[dict]:
    """Convert to OpenAI function format."""
    return [{
        "type": "function",
        "function": {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    }]
```

### 3. The Agent Loop

```python
class Agent:
    async def run(self, user_input: str):
        # Add user message
        self.messages.append(Message(role="user", content=user_input))
        
        # Main loop
        for step in range(self.max_steps):
            # Step 1: Call LLM with tools
            response = await self.llm.generate(
                messages=self.messages,
                tools=self.tools  # Pass tool definitions
            )
            
            # Step 2: Check for function calls
            if response.tool_calls:
                # Execute each tool
                for tool_call in response.tool_calls:
                    result = await self.execute_tool(tool_call)
                    self.messages.append(Message(
                        role="tool",
                        content=result.content,
                        name=tool_call.name,
                        tool_call_id=tool_call.id
                    ))
                
                # Step 3: Loop back with results
                continue
            
            # Step 4: No tools = return response
            return response.content
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                │
│                     "Read file foo.py"                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ADD TO MESSAGES                             │
│  Message(role="user", content="Read file foo.py")               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CALL LLM                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ System: You are a helpful assistant                     │    │
│  │ User: Read file foo.py                                  │    │
│  │ Tools: [read_file, write_file, bash, ...]               │    │
│  └─────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM RESPONSE                               │
│  ToolCall(name="read_file", args={"path": "foo.py"})           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTE TOOL                                  │
│  read_file(path="foo.py")                                       │
│  → Returns: "def hello(): print('world')"                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ADD TOOL RESULT                               │
│  Message(role="tool", content="def hello(): ..."                │
│                    name="read_file")                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LOOP BACK TO LLM                            │
│  (Repeat until no tool calls)                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FINAL RESPONSE                              │
│  "The file foo.py contains: def hello(): print('world')"        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Built-in Tools

### File Tools

```python
from tmagent.tools import ReadTool, WriteTool, EditTool

# Read file
read_tool = ReadTool(workspace_dir="/project")

# Write file
write_tool = WriteTool(workspace_dir="/project")

# Edit file (exact string replacement)
edit_tool = EditTool(workspace_dir="/project")
```

### Bash Tool

```python
from tmagent.tools import BashTool

bash = BashTool(workspace_dir="/project")

# Usage:
# > bash(command="ls -la")
# Returns: file listing
```

### Custom Tools

```python
class WeatherTool(Tool):
    name = "get_weather"
    description = "Get current weather for a location"
    parameters = {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    }
    
    async def execute(self, location: str) -> ToolResult:
        # Call weather API
        weather = await fetch_weather(location)
        return ToolResult(success=True, content=f"Weather: {weather}")
```

---

## JSON Schema for Parameters

Define clear parameters for your tools:

### Simple Types

```python
parameters = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "active": {"type": "boolean"}
    }
}
```

### Enums

```python
parameters = {
    "type": "object",
    "properties": {
        "format": {
            "type": "string",
            "enum": ["json", "xml", "yaml"]
        }
    }
}
```

### Nested Objects

```python
parameters = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            }
        }
    }
}
```

### Arrays

```python
parameters = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}
```

---

## Best Practices

### 1. Clear Descriptions

```python
# ❌ Bad
parameters = {"path": {"type": "string"}}

# ✅ Good
parameters = {
    "path": {
        "type": "string",
        "description": "Absolute or relative path to the file"
    }
}
```

### 2. Required Fields

```python
# Always specify what's required
parameters = {
    "required": ["path", "content"]  # Both needed
}
```

### 3. Error Handling

```python
async def execute(self, **kwargs) -> ToolResult:
    try:
        result = do_something(kwargs)
        return ToolResult(success=True, content=result)
    except FileNotFoundError:
        return ToolResult(success=False, error="File not found")
    except PermissionError:
        return ToolResult(success=False, error="Permission denied")
    except Exception as e:
        return ToolResult(success=False, error=str(e))
```

### 4. Workspace Isolation

```python
class SafeTool(Tool):
    def __init__(self, workspace_dir: str):
        self.workspace = Path(workspace_dir).resolve()
    
    def execute(self, path: str) -> ToolResult:
        # Prevent directory traversal
        full_path = (self.workspace / path).resolve()
        
        if not str(full_path).startswith(str(self.workspace)):
            return ToolResult(success=False, error="Path outside workspace")
        
        # Safe to proceed
        return ToolResult(success=True, content=full_path.read_text())
```

---

## Comparison: TM-Agent vs Mini-Agent

| Feature | TM-Agent | Mini-Agent |
|---------|----------|------------|
| Tool base class | ✅ | ✅ |
| Schema conversion | ✅ | ✅ |
| Built-in tools | ✅ (4) | ✅ (10+) |
| Custom tools | ✅ | ✅ |
| Async execution | ✅ | ✅ |
| Tool error handling | ✅ | ✅ |
| Workspace isolation | ✅ | ✅ |
| Streaming | ❌ | ✅ |
| Tool retry | ❌ | ✅ |

---

## Further Reading

- [Tool Implementation Guide](../tools/README.md)
- [Anthropic Tool Use](https://docs.anthropic.com/en/docs/tool-use)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [JSON Schema Reference](https://json-schema.org/)
