# Mini-Agent Memory Management

> Understanding how Mini-Agent handles long conversations with token-based memory management

---

## The Problem

When an AI agent has long conversations, it faces two critical challenges:

1. **Token Limits**: Most LLM APIs have context windows (8K, 32K, 128K tokens)
2. **Cost**: More tokens = more money per API call

For a coding agent that:
- Reads files
- Runs commands
- Iterates on solutions
- Makes multiple tool calls

The conversation can quickly exceed limits!

---

## Mini-Agent's Solution: Token-Based Summarization

Mini-Agent uses **automatic conversation summarization** to manage memory.

### Core Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                    Token Budget: 80,000                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   System Prompt (2K tokens)  ← Fixed overhead                   │
│   ─────────────────────────                                   │
│   User Message 1 (500)       ← Always kept                      │
│   ─────────────────────────                                   │
│   Assistant + Tools (50K)    ← Can be compressed               │
│   ─────────────────────────                                   │
│   User Message 2 (500)       ← Always kept                      │
│   ─────────────────────────                                   │
│   Assistant + Tools (30K)    ← Can be compressed               │
│   ─────────────────────────                                   │
│   ...                                                         │
│                                                                 │
│   When total > 80K: COMPRESS old assistant messages!           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Insight

> **Keep user intent, compress agent execution**

The user's questions are precious - we never want to lose what they want. But the agent's reasoning and tool executions can be summarized.

---

## Implementation Details

### 1. Token Counting

```python
import tiktoken

class Agent:
    def __init__(self, ...):
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, messages: list[Message]) -> int:
        """Count total tokens in conversation."""
        total = 0
        for msg in messages:
            # Each message has role + content
            total += 4  # Overhead per message
            total += len(self.encoder.encode(msg.content))
        return total
```

### 2. Triggering Summarization

```python
class Agent:
    async def run(self, user_input: str):
        # Before each LLM call, check token count
        if self.count_tokens(self.messages) > self.token_limit:
            await self.summarize_messages()
```

### 3. Summarization Strategy

```python
async def summarize_messages(self):
    """
    Compress conversation while preserving:
    - System prompt (never summarize)
    - User messages (user intent is precious)
    - Most recent context
    """
    
    # Step 1: Separate messages by type
    system_msg = self.messages[0]
    user_messages = [m for m in self.messages if m.role == "user"]
    assistant_messages = [m for m in self.messages if m.role != "user"]
    
    # Step 2: Keep system + user messages
    # Compress all assistant messages between them
    
    summary_prompt = [
        Message(role="user", content=
            "Summarize this conversation concisely, keeping:\n"
            "1. Key decisions made\n"
            "2. Important information discovered\n"
            "3. Current state of work\n\n"
            "Remove verbose details and tool output."
        ),
        *assistant_messages  # All the stuff to compress
    ]
    
    # Step 3: Ask LLM to summarize
    response = await self.llm.generate(summary_prompt)
    
    # Step 4: Replace with compressed version
    self.messages = [
        system_msg,
        *user_messages,
        Message(role="assistant", content=f"[Summary]: {response.content}")
    ]
```

### 4. Result: Conversation Structure

Before summarization:
```
System → User1 → Assistant1 → Tool1 → Tool2 → Assistant2 → User2 → Assistant3 → ...
```

After summarization:
```
System → User1 → [Summary of Assistant1-Tool1-Tool2-Assistant2] → User2 → Assistant3 → ...
```

---

## Why This Works

### Comparison Table

| Approach | Pros | Cons |
|----------|------|------|
| **Fixed window** (sliding) | Simple | Loses early context |
| **Summarization** (Mini-Agent) | Preserves intent | Summary may miss details |
| **External memory** | Unlimited context | Complex, slow retrieval |

### Token Savings

| Conversation Length | Before | After | Savings |
|---------------------|--------|-------|---------|
| 5 tool calls | 15K tokens | 15K | 0% |
| 50 tool calls | 120K | 75K | **37%** |
| 100 tool calls | 240K | 80K | **67%** |

---

## Integration with Function Calling

The memory management works seamlessly with function calling:

```python
agent = Agent(
    llm_client=llm,
    tools=[read_file, write_file, bash],
    token_limit=80_000  # Start summarizing at 80K tokens
)

# Long conversation handled automatically:
await agent.run("Build a web app")      # → execution + memory
await agent.run("Add authentication")    # → execution + memory  
await agent.run("Add tests")            # → execution + memory
# ... 50 requests later ...
# Agent still works! Old context summarized automatically
```

---

## Comparison: TM-Agent vs Mini-Agent

| Feature | TM-Agent | Mini-Agent |
|---------|----------|------------|
| Message history | ✅ | ✅ |
| Token counting | ❌ | ✅ |
| Auto-summarization | ❌ | ✅ |
| Configurable limit | ❌ | ✅ |

---

## Want to Implement in TM-Agent?

See: [Adding Memory Management to TM-Agent](./implementation-guide.md)

---

## Further Reading

- [ tiktoken Documentation](https://github.com/openai/tiktoken)
- [Anthropic Context Window Management](https://docs.anthropic.com)
- [LLM Memory Patterns](https://python.langchain.com/docs/memory/)
