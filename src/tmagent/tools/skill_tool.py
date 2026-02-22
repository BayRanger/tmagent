"""Skill Tool - Load skills on-demand (Progressive Disclosure Level 2)."""

from typing import Any, Dict, Optional

from .base import Tool, ToolResult
from .skill_loader import SkillLoader


class GetSkillTool(Tool):
    """Tool to load full skill content on-demand."""

    def __init__(self, skill_loader: SkillLoader):
        self.skill_loader = skill_loader

    @property
    def name(self) -> str:
        return "get_skill"

    @property
    def description(self) -> str:
        return "Get complete content and guidance for a specified skill. Use this when you need detailed information about a specific skill."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Name of the skill to retrieve",
                }
            },
            "required": ["skill_name"],
        }

    async def execute(self, skill_name: str) -> ToolResult:
        """Load and return full skill content."""
        skill = self.skill_loader.get_skill(skill_name)

        if not skill:
            available = ", ".join(self.skill_loader.list_skills())
            return ToolResult(
                success=False,
                content="",
                error=f"Skill '{skill_name}' not found. Available: {available}",
            )

        return ToolResult(success=True, content=skill.to_prompt())


class ListSkillsTool(Tool):
    """Tool to list all available skills."""

    def __init__(self, skill_loader: SkillLoader):
        self.skill_loader = skill_loader

    @property
    def name(self) -> str:
        return "list_skills"

    @property
    def description(self) -> str:
        return "List all available skills with their descriptions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self) -> ToolResult:
        """List all skills."""
        skills = self.skill_loader.list_skills()
        if not skills:
            return ToolResult(success=True, content="No skills available.")

        lines = ["Available Skills:\n"]
        for skill_name in skills:
            skill = self.skill_loader.get_skill(skill_name)
            if skill:
                lines.append(f"- `{skill_name}`: {skill.description}")

        return ToolResult(success=True, content="\n".join(lines))


def create_skill_tools(
    skills_dir: str = "./skills",
) -> tuple[list[Tool], Optional[SkillLoader]]:
    """Create skill tools with Progressive Disclosure.

    Args:
        skills_dir: Directory containing SKILL.md files

    Returns:
        Tuple of (tools list, skill loader)
    """
    loader = SkillLoader(skills_dir)
    skills = loader.discover_skills()

    tools = [
        GetSkillTool(loader),
        ListSkillsTool(loader),
    ]

    return tools, loader
