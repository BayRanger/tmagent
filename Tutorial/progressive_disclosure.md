# Progressive Disclosure in Mini-Agent

> How Mini-Agent efficiently handles hundreds of skills without overwhelming the LLM

---

## The Problem

Imagine you have **100 skills** in your agent:

| Skill | Description | Tokens |
|-------|-------------|--------|
| xlsx | Create Excel spreadsheets with formulas | 2K |
| pdf | Extract text from PDF files | 3K |
| pptx | Create PowerPoint presentations | 2.5K |
| docx | Edit Word documents | 2K |
| ... | ... | ... |
| **Total (100 skills)** | | **200K+** |

**Issues:**
- ❌ Exceeds context window (128K limit!)
- ❌ Slow inference (more tokens = slower)
- ❌ Higher API costs
- ❌ LLM gets confused by too many options
- ❌ Poor tool selection accuracy

---

## Mini-Agent's Solution: Progressive Disclosure

Show the LLM **only what it needs**, **when it needs it**.

### Three Levels of Disclosure

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Level 1: Skill Metadata (Always in system prompt)             │
│  ─────────────────────────────────────────────                  │
│  • Skill name + one-line description                            │
│  • ~200 tokens for 100 skills                                  │
│  • Used for: "Which skill should I use?"                       │
│                                                                 │
│  Level 2: Full Skill Content (On-demand)                        │
│  ─────────────────────────────────────────────                  │
│  • Loaded when agent calls get_skill()                          │
│  • ~2,000 tokens per skill                                      │
│  • Used for: "How do I use this skill?"                         │
│                                                                 │
│  Level 3: Resources (Absolute paths)                           │
│  ─────────────────────────────────────────────                  │
│  • Scripts, templates, assets                                  │
│  • Referenced in skill content                                  │
│  • Used for: "Execute the code"                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Token Savings

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| 100 skills loaded | 200K tokens | 200 tokens | **99.9%** |
| Using 1 skill | 200K tokens | 2.2K tokens | **98.9%** |
| Using 5 skills | 200K tokens | 10K tokens | **95%** |

---

## Implementation Details

### 1. Skill Discovery

```python
from pathlib import Path

class SkillLoader:
    def discover_skills(self, skills_dir: Path) -> list[Skill]:
        """Find all SKILL.md files."""
        skills = []
        for md in skills_dir.rglob("SKILL.md"):
            skill = self.load_skill(md)
            skills.append(skill)
        return skills
```

### 2. SKILL.md Format

```yaml
---
name: xlsx
description: Create and edit Excel spreadsheets with formulas and formatting
requirements: openpyxl>=3.0.0
---

# Excel Spreadsheet Skill

Use openpyxl to create Excel files.

## Creating a Workbook

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws['A1'] = 'Hello'
wb.save('output.xlsx')
```

## Formulas

Use cell references: `=A1+B1`
```

### 3. Level 1: Metadata Prompt

```python
def get_skills_metadata_prompt(self) -> str:
    """Generate Level 1: Skill names + descriptions."""
    lines = ["## Available Skills\n"]
    for skill in self.skills:
        lines.append(f"- **{skill.name}**: {skill.description}")
    return "\n".join(lines)
```

Output:
```
## Available Skills
- xlsx: Create and edit Excel spreadsheets with formulas
- pdf: Extract text and tables from PDF files
- pptx: Create PowerPoint presentations
...
```

### 4. Level 2: On-Demand Loading

```python
class GetSkillTool(Tool):
    """Tool for loading full skill content on demand."""
    
    def execute(self, skill_name: str) -> ToolResult:
        """Load and return full skill content."""
        skill = self.loader.get_skill(skill_name)
        if not skill:
            return ToolResult(success=False, error=f"Skill not found: {skill_name}")
        
        return ToolResult(
            success=True,
            content=f"# {skill.name}\n\n{skill.content}"
        )
```

### 5. Level 3: Path Processing

```python
def _process_skill_paths(self, skill: Skill, base_path: Path):
    """Convert relative paths to absolute."""
    content = skill.content
    
    # Find patterns like [script.py](script.py)
    # Convert to: /absolute/path/to/skill/script.py
    
    import re
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def replace_path(match):
        filename = match.group(2)
        if not filename.startswith('/'):
            absolute = (base_path / filename).resolve()
            return f"[{match.group(1)}]({absolute})"
        return match.group(0)
    
    skill.content = re.sub(pattern, replace_path, content)
```

---

## How It Works in Practice

### Conversation Flow

```
User: "Create an Excel file with sales data"

Agent (Level 1):
  → Sees: xlsx skill available
  → Calls: get_skill("xlsx")
  → Gets: Full xlsx skill content (Level 2)
  
Agent (Level 2):
  → Reads skill content
  → Sees: uses openpyxl library
  → Calls: get_skill("python")  # if needed
  
Agent executes:
  → Writes Python code
  → Calls: BashTool to run code
  → Result: sales.xlsx created
```

### Real Example

```python
# System prompt includes only metadata:
"""
## Available Skills
- xlsx: Create Excel spreadsheets with formulas
- pdf: Extract text from PDF files
- pptx: Create PowerPoint presentations

You have access to tools: get_skill, read_file, write_file, bash
"""

# When agent needs xlsx skill:
> get_skill("xlsx")

# Returns full skill (Level 2):
"""
# Excel Spreadsheet Skill

Use openpyxl to create Excel files with:
- Cell formatting (bold, colors, borders)
- Formulas (SUM, VLOOKUP, etc.)
- Charts and graphs
- Multiple sheets

## Creating a Workbook
...
"""
```

---

## Why This Works

### Benefits

| Benefit | Description |
|---------|-------------|
| **Token Efficiency** | 99%+ reduction in initial tokens |
| **Cost Reduction** | Much cheaper API calls |
| **Faster Inference** | Smaller context = faster processing |
| **Better Accuracy** | Fewer choices = better tool selection |
| **Scalability** | Can handle 1000+ skills |

### Comparison Table

| Approach | Tokens | Cost | Speed | Scalability |
|----------|--------|------|-------|--------------|
| **All skills** | 200K | $$$$ | Slow | ❌ |
| **Top 10 skills** | 20K | $$$ | Medium | ❌ |
| **Progressive** | 200→2K | $ | Fast | ✅ |

---

## TM-Agent Implementation

TM-Agent already implements Progressive Disclosure:

```python
from tmagent import Agent, LLMClient
from tmagent.tools import GetSkillTool, ListSkillsTool
from tmagent.tools.skill_loader import SkillLoader

# Setup
loader = SkillLoader("skills/")
tools = [GetSkillTool(loader), ListSkillsTool(loader), read_file, write_file, bash]

agent = Agent(llm, tools=tools, skills_dir="skills/")

# Skills loaded progressively:
# Level 1: Names + descriptions in system prompt
# Level 2: Full content via get_skill()
# Level 3: Resources with absolute paths
```

---

## Comparison: TM-Agent vs Mini-Agent

| Feature | TM-Agent | Mini-Agent |
|---------|----------|------------|
| Skill discovery | ✅ | ✅ |
| YAML frontmatter | ✅ | ✅ |
| Level 1 metadata | ✅ | ✅ |
| Level 2 get_skill | ✅ | ✅ |
| Level 3 path processing | ✅ | ✅ |
| Skill categories | ❌ | ✅ |
| Hot reload | ❌ | ✅ |
| Skill validation | ❌ | ✅ |

---

## Further Reading

- [Mini-Agent Skill System](./skills/README.md)
- [Tool Implementation Guide](../tools/README.md)
- [Anthropic Tool Use Best Practices](https://docs.anthropic.com/en/docs/tool-use)
