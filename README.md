# TM-Agent

<p align="center">
  <img src="images/tmagent_banner.png" alt="TM-Agent Banner" width="100%">
</p>

A minimal AI Agent built as a simplified version of [Mini-Agent](https://github.com/MiniMax-ai/Mini-Agent), so it is named as tny mini agent (tmagent), but I may change it in the future.

## Project Stats

| Metric                  | Value        |
| ----------------------- | ------------ |
| **Total Lines**   | ~4,800       |
| **Source Code**   | 1,188 lines  |
| **Tests**         | 1,236 lines  |
| **Documentation** | ~1,400 lines |
| **Test Coverage** | 65 tests     |

## Features

- **Function Calling** - LLM-driven tool execution with automatic tool selection
- **Built-in Tools**:
  - `read_file` - Read file contents with line numbers
  - `write_file` - Write content to files
  - `edit_file` - Edit files by replacing text
  - `bash` - Execute shell commands
- **Progressive Disclosure** - Token-efficient skill system with 3 levels of disclosure
- **Memory Management** - Token-based auto-summarization for long conversations
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
from tmagent import Agent
from tmagent.llm import LLMClient
from tmagent.schema import LLMProvider
from tmagent.tools import ReadTool, WriteTool, BashTool

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

### Using Skills (Progressive Disclosure)

```python
from tmagent import Agent
from tmagent.tools import ReadTool, WriteTool, BashTool

# Create agent with skills directory
agent = Agent(
    llm_client=llm,
    system_prompt="You are a helpful AI assistant.",
    tools=[ReadTool(), WriteTool(), BashTool()],
    skills_dir="./skills",  # Enable skills
)
```

## Progressive Disclosure

TM-Agent implements a token-efficient skill system with 3 levels:

| Level             | What Happens                                                 | Token Cost    |
| ----------------- | ------------------------------------------------------------ | ------------- |
| **Level 1** | Skill names + descriptions in system prompt                  | ~200 tokens   |
| **Level 2** | Agent calls `get_skill(skill_name="xlsx")` → full content | ~2,000 tokens |
| **Level 3** | Relative paths converted to absolute paths                   | Included      |

### How It Works

1. **Startup**: Agent discovers all skills in `skills_dir` and adds only metadata to system prompt
2. **Runtime**: When agent needs a skill, it calls `get_skill(skill_name="...")`
3. **Resources**: Path references in skills are converted to absolute paths

See [skills/README.md](skills/README.md) for detailed documentation.

## Memory Management

TM-Agent automatically manages conversation memory using token-based summarization:

```python
# Create agent with custom token limit
agent = Agent(
    llm_client=llm,
    system_prompt="You are a helpful AI assistant.",
    tools=[ReadTool(), WriteTool(), BashTool()],
    token_limit=80_000,  # Default: 80K tokens
)
```

### How It Works

1. **Token Counting**: Uses `tiktoken` with `cl100k_base` encoding (GPT-4/Claude compatible)
2. **Auto-Trigger**: Before each LLM call, checks if token count exceeds limit
3. **Smart Compression**:
   - Keeps: System prompt + User messages (intent is precious)
   - Summarizes: Assistant reasoning + Tool execution details

### Why This Matters

| Conversation   | Without Memory          | With Memory |
| -------------- | ----------------------- | ----------- |
| 10 tool calls  | 20K tokens              | 20K tokens  |
| 50 tool calls  | 100K tokens (overflow!) | 75K tokens  |
| 100 tool calls | 200K tokens (crash!)    | 80K tokens  |

See [Tutorial/memory_manange.md](Tutorial/memory_manange.md) for detailed explanation.

## Configuration

| Option          | Description                                   | Default          |
| --------------- | --------------------------------------------- | ---------------- |
| `--api-key`   | API key for LLM                               | Required         |
| `--model`     | Model name                                    | `MiniMax-M2.5` |
| `--provider`  | LLM provider (`anthropic` or `openai`)    | `anthropic`    |
| `--workspace` | Working directory                             | `./workspace`  |
| `--task`      | Single task to execute (non-interactive mode) | None             |

## Testing

```bash
# Run all tests with the test runner script
./run_tests.sh

# Or run pytest directly with detailed output
pytest -v --tb=short

# Run specific test file
pytest tests/test_function_call.py -v

# Run with coverage
pytest --cov=src/tmagent --cov-report=html
```

Expected output when all tests pass:

```
✅ All tests passed! (65 tests)
```

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
│       ├── bash_tool.py  # Bash command tool
│       ├── skill_loader.py   # Skill discovery & loading
│       └── skill_tool.py    # get_skill, list_skills tools
├── skills/
│   ├── README.md          # Skills documentation
│   ├── calculator/        # Example skill
│   └── weather/           # Example skill
├── images/
│   ├── tmagent_banner.png    # Social media banner
│   └── tmagent_badge.png     # Square badge/icon
├── tests/
│   ├── test_schema.py        # Schema tests
│   ├── test_tools.py         # Tools tests
│   ├── test_function_call.py # Integration tests
│   ├── test_skills.py        # Skill system tests
│   └── test_memory.py        # Memory management tests
└── pyproject.toml
```

### How Function Calling Works

1. **User Input** → Agent receives task
2. **LLM Call** → Agent calls LLM with available tools
3. **Tool Selection** → LLM decides which tool to use and provides arguments
4. **Tool Execution** → Agent executes the tool and gets result
5. **Result Feedback** → Tool result is sent back to LLM
6. **Repeat** → Steps 2-5 repeat until task is complete

## Comparison with Mini-Agent

TM-Agent is a simplified version of Mini-Agent. Here's what's included vs missing:

### ✅ Implemented

| Feature                         | TM-Agent        | Mini-Agent               |
| ------------------------------- | --------------- | ------------------------ |
| Core Agent loop                 | ✅              | ✅                       |
| Function calling                | ✅              | ✅                       |
| Built-in tools                  | 4 tools         | 10+ tools                |
| Progressive Disclosure          | ✅ (simplified) | ✅ (full)                |
| Memory Management (token limit) | ✅              | ✅                       |
| CLI                             | Basic           | Rich (colors, shortcuts) |
| Tests                           | 65 tests        | Many tests               |

### ❌ Not Implemented (Yet)

| Feature     | Description                         |
| ----------- | ----------------------------------- |
| Streaming   | Real-time response output           |
| MCP support | External tool protocol              |
| Config file | YAML configuration                  |
| Retry logic | Exponential backoff                 |
| Logger      | Detailed request logging            |
| More tools  | SearchTool, HttpTool, ListFilesTool |
| More skills | 13 skills vs 2 skills               |

See [skills/README.md](skills/README.md) for detailed skill comparison.

## Requirements

- Python 3.10+
- anthropic >= 0.39.0
- openai >= 1.57.4
- pydantic >= 2.0.0
- tiktoken >= 0.7.0

## License

MIT
