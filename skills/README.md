# TM-Agent Skills

This folder contains skills that extend TM-Agent's capabilities through Progressive Disclosure.

## Accomplished Features

### ✅ Progressive Disclosure (3 Levels)

| Level | Description | Implementation |
|-------|-------------|----------------|
| **Level 1** | Skill metadata (name + description) in system prompt | `SkillLoader.get_skills_metadata_prompt()` |
| **Level 2** | Full skill content on-demand via `get_skill` tool | `GetSkillTool.execute()` |
| **Level 3** | Relative paths converted to absolute paths | `SkillLoader._process_skill_paths()` |

### ✅ Skill File Format (SKILL.md)

Skills are defined in YAML frontmatter + Markdown content:

```yaml
---
name: skill_name
description: "One-line description of what this skill does"
---

# Skill Title

Detailed documentation, examples, and instructions...

## Examples

```python
# Code examples here
```

## Scripts

- [script.py](scripts/script.py) - Executable script
```

### ✅ Skill Discovery

- Automatic discovery via `SkillLoader.discover_skills()`
- Recursive search for `SKILL.md` files
- YAML frontmatter parsing

### ✅ Built-in Skill Tools

| Tool | Description |
|------|-------------|
| `get_skill` | Load full skill content on-demand |
| `list_skills` | List all available skills |

### ✅ Example Skills Included

| Skill | Description |
|-------|-------------|
| `calculator` | Mathematical calculations |
| `weather` | Weather lookup via wttr.in API |

---

## Missing Features vs Mini-Agent

### ❌ Skill Metadata Fields

Mini-Agent supports more YAML frontmatter fields:

```yaml
---
name: xlsx
description: "Comprehensive spreadsheet manipulation..."
license: "Proprietary"           # ❌ Not implemented
allowed-tools: [read_file, write_file]  # ❌ Not implemented
metadata:                       # ❌ Not implemented
  version: "1.0"
  author: "Team"
---
```

### ❌ Skill Categories

Mini-Agent organizes skills into categories:
- `document-skills/` (PDF, PPTX, DOCX, XLSX)
- `algorithmic-art/`
- `canvas-design/`
- `webapp-testing/`
- etc.

TM-Agent has flat structure.

### ❌ Rich Skill Content Processing

Mini-Agent's `_process_skill_paths()` handles more patterns:

| Pattern | Mini-Agent | TM-Agent |
|---------|------------|----------|
| `python scripts/file.py` | ✅ | ✅ |
| `[link](file.md)` | ✅ | ✅ |
| `see reference.md` | ✅ | ❌ |
| `Read file.txt` | ✅ | ❌ |

### ❌ Skill Validation

Mini-Agent validates:
- Required fields
- File existence
- Allowed tools

TM-Agent has minimal validation.

### ❌ Skill Hot Reload

Mini-Agent can reload skills without restart. ❌ Not implemented.

### ❌ Skill Versioning

Mini-Agent doesn't have explicit versioning, but TM-Agent doesn't track at all. ❌ Not implemented.

---

## Mini-Agent Skills (13 Total) - Not in TM-Agent

These skills exist in Mini-Agent but not in TM-Agent:

1. **document-skills/pdf** - PDF manipulation
2. **document-skills/pptx** - PowerPoint creation
3. **document-skills/docx** - Word document handling
4. **document-skills/xlsx** - Excel spreadsheet operations
5. **algorithmic-art** - p5.js generative art
6. **canvas-design** - Visual design creation
7. **artifacts-builder** - React/HTML artifacts
8. **webapp-testing** - Playwright browser automation
9. **internal-comms** - Internal communication templates
10. **theme-factory** - Theming system
11. **mcp-builder** - MCP server creation
12. **skill-creator** - Guide for creating new skills
13. **slack-gif-creator** - Animated GIFs for Slack
14. **brand-guidelines** - Anthropic brand styling

---

## Adding New Skills

### Step 1: Create Skill Directory

```
skills/
└── my_skill/
    ├── SKILL.md          # Required
    └── scripts/          # Optional
        └── helper.py
```

### Step 2: Write SKILL.md

```yaml
---
name: my_skill
description: "What this skill does in one line"
---

# My Skill

Detailed description...

## Usage

```bash
python scripts/helper.py
```
```

### Step 3: Use in Agent

```python
from tmagent import Agent
from tmagent.tools import ReadTool, WriteTool

agent = Agent(
    llm_client=llm,
    system_prompt="You are helpful.",
    tools=[ReadTool(), WriteTool()],
    skills_dir="./skills",  # Auto-discovers all SKILL.md
)
```

---

## Future Improvements

Priority order for adding features:

1. **Medium Priority**
   - More skill content path patterns
   - Skill categories/folders
   - Better YAML parsing (use pyyaml)

2. **Low Priority**
   - Skill validation
   - Hot reload
   - Skill versioning

3. **Long-term**
   - Import skills from Mini-Agent
   - Skill marketplace
   - Skill dependencies
