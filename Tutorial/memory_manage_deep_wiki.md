## Persistent Memory in Mini-Agent

Mini-Agent provides persistent memory via the **Session Note Tool** (`SessionNoteTool`), allowing the agent to retain and retrieve key information across sessions. By default, it stores notes as a JSON file in the workspace and can be extended to other backends like PostgreSQL or vector databases [1](#0-0) [2](#0-1) .

### How It Works

- **Storage**: Default implementation writes to `.agent_memory.json` in the workspace directory [3](#0-2) .
- **Operations**: The tool exposes functions to add, search, and manage notes. The agent can proactively save context or user-directed facts during conversations.
- **Persistence**: Since the file resides in the workspace, memory survives CLI restarts and is automatically loaded when the agent starts.

### Configuration

- Enable/disable via `config.yaml` under `tools.enable_note` [4](#0-3) .
- Memory file path defaults to `workspace/.agent_memory.json` but can be customized when initializing `SessionNoteTool` [5](#0-4) .

### Extensibility

You can replace the default JSON storage:

- **PostgreSQL**: Example `PostgresNoteTool` stores notes in a relational DB [6](#0-5) .
- **Vector DB (Milvus)**: Example `MilvusNoteTool` enables semantic search via embeddings [7](#0-6) .

### Usage in Agent

- `SessionNoteTool` is added to the agent’s tool list during initialization if enabled [3](#0-2) .
- The agent can invoke note-related tools (e.g., `add_note`, `search_notes`) as part of its reasoning loop.

## Notes

- The Memory MCP tool (knowledge graph) is a separate, optional long-term memory system; SessionNoteTool is the built-in, file-based persistent memory [8](#0-7) .
- No API keys are required for the default SessionNoteTool [9](#0-8) .

Wiki pages you might want to explore:

- [Troubleshooting and FAQ (MiniMax-AI/Mini-Agent)](/wiki/MiniMax-AI/Mini-Agent#12)

### Citations

**File:** README.md (L9-11)

```markdown
*   ✅ **Full Agent Execution Loop**: A complete and reliable foundation with a basic toolset for file system and shell operations.
*   ✅ **Persistent Memory**: An active **Session Note Tool** ensures the agent retains key information across multiple sessions.
*   ✅ **Intelligent Context Management**: Automatically summarizes conversation history to handle contexts up to a configurable token limit, enabling infinitely long tasks.
```

**File:** docs/DEVELOPMENT_GUIDE_CN.md (L71-82)

```markdown
#### Memory - 知识图谱记忆系统

**功能**：基于图数据库，为 Agent 提供长期记忆的存储与检索能力。

**状态**：默认启用

**配置**：无需 API Key，开箱即用

**能力**：
- 跨会话存储并检索信息
- 根据对话内容构建知识图谱
- 对已存储的记忆进行语义搜索
```

**File:** docs/DEVELOPMENT_GUIDE_CN.md (L241-250)

```markdown
# 扩展示例：使用 PostgreSQL 存储
class PostgresNoteTool(Tool):
    def __init__(self, db_url: str):
        self.db = PostgresDB(db_url)

    async def _save_notes(self, notes: List[Dict]):
        await self.db.execute(
            "INSERT INTO notes (content, category, timestamp) VALUES ($1, $2, $3)",
            notes
        )
```

**File:** docs/DEVELOPMENT_GUIDE_CN.md (L252-266)

```markdown
# 扩展示例：使用向量数据库存储
class MilvusNoteTool(Tool):
    def __init__(self, milvus_host: str):
        self.vector_db = MilvusClient(host=milvus_host)

    async def _save_notes(self, notes: List[Dict]):
        # 生成内容的嵌入向量
        embeddings = await self.get_embeddings([n["content"] for n in notes])

        # 将笔记和向量存入向量数据库
        await self.vector_db.insert(
            collection="agent_notes",
            data=notes,
            embeddings=embeddings
        )
```

**File:** mini_agent/cli.py (L453-456)

```python
    # Session note tool - needs workspace to store memory file
    if config.tools.enable_note:
        tools.append(SessionNoteTool(memory_file=str(workspace_dir / ".agent_memory.json")))
        print(f"{Colors.GREEN}✅ Loaded session note tool{Colors.RESET}")
```

**File:** mini_agent/config/config-example.yaml (L42-47)

```yaml
tools:
  # Basic tool switches
  enable_file_tools: true  # File read/write/edit tools (ReadTool, WriteTool, EditTool)
  enable_bash: true        # Bash command execution tool
  enable_note: true        # Session note tool (SessionNoteTool)

```

**File:** docs/DEVELOPMENT_GUIDE.md (L70-82)

```markdown
#### Memory - Knowledge Graph Memory System

**Function**: Provides long-term memory storage and retrieval based on graph database

**Status**: Enabled by default (`disabled: false`)

**Configuration**: No API Key required, works out of the box

**Capabilities**:
- Store and retrieve information across sessions
- Build knowledge graphs from conversations
- Semantic search through stored memories

```
