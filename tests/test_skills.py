"""Tests for skill system with Progressive Disclosure."""

import pytest
from pathlib import Path
from tmagent.tools.skill_loader import SkillLoader, Skill
from tmagent.tools.skill_tool import GetSkillTool, ListSkillsTool


@pytest.fixture
def skills_dir(tmp_path):
    """Create a temporary skills directory with test skills."""
    skills_path = tmp_path / "skills"
    skills_path.mkdir()

    # Create calculator skill
    calc_dir = skills_path / "calculator"
    calc_dir.mkdir()
    (calc_dir / "SKILL.md").write_text("""
---
name: calculator
description: "Perform mathematical calculations."
---

# Calculator Skill

Use Python eval for basic math.

## Example
```python
result = 2 + 2
```
""")

    # Create weather skill
    weather_dir = skills_path / "weather"
    weather_dir.mkdir()
    (weather_dir / "SKILL.md").write_text("""
---
name: weather
description: "Get weather information for a location."
---

# Weather Skill

Use wttr.in API for weather data.

## Example
```bash
curl wttr.in/NewYork
```
""")

    return skills_path


def test_skill_loader_discovery(skills_dir):
    """Test discovering skills."""
    loader = SkillLoader(str(skills_dir))
    skills = loader.discover_skills()

    assert len(skills) == 2
    assert "calculator" in loader.list_skills()
    assert "weather" in loader.list_skills()


def test_skill_metadata(skills_dir):
    """Test skill metadata (Level 1)."""
    loader = SkillLoader(str(skills_dir))
    loader.discover_skills()

    prompt = loader.get_skills_metadata_prompt()

    assert "calculator" in prompt
    assert "Perform mathematical calculations" in prompt
    assert "weather" in prompt
    assert "Get weather information" in prompt


def test_get_skill(skills_dir):
    """Test loading full skill content (Level 2)."""
    loader = SkillLoader(str(skills_dir))
    loader.discover_skills()

    skill = loader.get_skill("calculator")
    assert skill is not None
    assert skill.name == "calculator"
    assert "Calculator Skill" in skill.to_prompt()


def test_get_skill_not_found(skills_dir):
    """Test getting non-existent skill."""
    loader = SkillLoader(str(skills_dir))
    loader.discover_skills()

    skill = loader.get_skill("nonexistent")
    assert skill is None


@pytest.mark.asyncio
async def test_get_skill_tool(skills_dir):
    """Test GetSkillTool."""
    loader = SkillLoader(str(skills_dir))
    loader.discover_skills()

    tool = GetSkillTool(loader)
    result = await tool.execute(skill_name="calculator")

    assert result.success is True
    assert "Calculator Skill" in result.content


@pytest.mark.asyncio
async def test_get_skill_tool_error(skills_dir):
    """Test GetSkillTool with invalid skill."""
    loader = SkillLoader(str(skills_dir))
    loader.discover_skills()

    tool = GetSkillTool(loader)
    result = await tool.execute(skill_name="invalid")

    assert result.success is False
    assert "not found" in result.error


@pytest.mark.asyncio
async def test_list_skills_tool(skills_dir):
    """Test ListSkillsTool."""
    loader = SkillLoader(str(skills_dir))
    loader.discover_skills()

    tool = ListSkillsTool(loader)
    result = await tool.execute()

    assert result.success is True
    assert "calculator" in result.content
    assert "weather" in result.content


def test_skills_directory_not_exists():
    """Test with non-existent skills directory."""
    loader = SkillLoader("/nonexistent/path")
    skills = loader.discover_skills()

    assert len(skills) == 0
    assert loader.get_skills_metadata_prompt() == ""


def test_skill_with_scripts(skills_dir, tmp_path):
    """Test skill with scripts directory (Level 3 path processing)."""
    # Add a script to calculator skill
    calc_dir = skills_dir / "calculator"
    scripts_dir = calc_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "advanced.py").write_text("# Advanced calculator")

    # Update SKILL.md to reference the script
    (calc_dir / "SKILL.md").write_text("""
---
name: calculator
description: "Perform mathematical calculations."
---

# Calculator Skill

Use [advanced.py](scripts/advanced.py) for advanced operations.
""")

    loader = SkillLoader(str(skills_dir))
    skills = loader.discover_skills()

    skill = loader.get_skill("calculator")
    # Path should be converted to absolute
    assert str(calc_dir / "scripts" / "advanced.py") in skill.content
