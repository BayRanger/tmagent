# TM-Agent

<p align="center">
  <img src="images/tmagent_banner.png" alt="TM-Agent Banner" width="100%">
</p>

A minimal AI Agent with function calling capability, built as a simplified version of [Mini-Agent](https://github.com/MiniMax-ai/Mini-Agent).

## Features

- **Function Calling** - LLM-driven tool execution with automatic tool selection
- **Built-in Tools**:
  - `read_file` - Read file contents with line numbers
  - `write_file` - Write content to files
  - `edit_file` - Edit files by replacing text
  - `bash` - Execute shell commands
- **Multi-Provider Support** - Works with Anthropic and OpenAI compatible APIs (including MiniMax)
- **Simple CLI** - Interactive and non-interactive modes

## Installation

```bash
# Clone or navigate to the project directory
cd tmagent

# Install in development mode
pip install -e .
```

## Usage

### Command Line

```bash
# Interactive mode
tmagent --api-key "your-api-key"

# Execute a single task
tmagent --api-key "your-api-key" --task "Create a hello.py file"

# Specify model and provider
tmagent --api-key "your-api-key" --model "MiniMax-M2.5" --provider "anthropic"

# Use a custom workspace
tmagent --api-key "your-api-key" --workspace ./myproject
```

### Python API

```python
import asyncio
from tm_agent import Agent
from tm_agent.llm import LLMClient
from tm_agent.schema import LLMProvider
from tm_agent.tools import ReadTool, WriteTool, BashTool

async def main():
    # Create LLM client
    llm = LLMClient(
        api_key="your-api-key",
        provider=LLMProvider.ANTHROPIC,
        model="MiniMax-M2.5",
    )

    # Create tools
    tools = [
        ReadTool(workspace_dir="./workspace"),
        WriteTool(workspace_dir="./workspace"),
        BashTool(workspace_dir="./workspace"),
    ]

    # Create agent
    agent = Agent(
        llm_client=llm,
        system_prompt="You are a helpful AI assistant.",
        tools=tools,
    )

    # Run task
    agent.add_user_message("Create a file called hello.py that prints 'Hello World'")
    result = await agent.run()
    print(result)

asyncio.run(main())
```

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `--api-key` | API key for LLM | Required |
| `--model` | Model name | `MiniMax-M2.5` |
| `--provider` | LLM provider (`anthropic` or `openai`) | `anthropic` |
| `--workspace` | Working directory | `./workspace` |
| `--task` | Single task to execute (non-interactive mode) | None |

## Architecture

```
tmagent/
├── src/tmagent/
│   ├── __init__.py
│   ├── agent.py           # Core Agent implementation
│   ├── llm.py             # LLM client (Anthropic/OpenAI)
│   ├── cli.py             # Command-line interface
│   ├── schema.py          # Data models (Message, ToolCall, etc.)
│   └── tools/
│       ├── __init__.py
│       ├── base.py        # Tool base class
│       ├── file_tools.py  # File operation tools
│       └── bash_tool.py   # Bash command tool
├── images/
│   ├── tmagent_banner.png    # Social media banner
│   └── tmagent_badge.png     # Square badge/icon
├── tests/
│   ├── test_schema.py        # Schema tests
│   ├── test_tools.py         # Tools tests
│   └── test_function_call.py # Integration tests
└── pyproject.toml
```

### How Function Calling Works

1. **User Input** → Agent receives task
2. **LLM Call** → Agent calls LLM with available tools
3. **Tool Selection** → LLM decides which tool to use and provides arguments
4. **Tool Execution** → Agent executes the tool and gets result
5. **Result Feedback** → Tool result is sent back to LLM
6. **Repeat** → Steps 2-5 repeat until task is complete

## Requirements

- Python 3.10+
- anthropic >= 0.39.0
- openai >= 1.57.4
- pydantic >= 2.0.0

## License

MIT
