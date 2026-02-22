"""Skill Loader - Load Skills with Progressive Disclosure.

Simplified implementation of Progressive Disclosure:
- Level 1: Metadata (name + description) in system prompt
- Level 2: Full skill content on-demand via get_skill tool
- Level 3: Resources with absolute paths
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Skill:
    """Skill data structure."""

    name: str
    description: str
    content: str
    skill_path: Optional[Path] = None

    def to_prompt(self) -> str:
        """Convert skill to prompt format."""
        skill_root = str(self.skill_path.parent) if self.skill_path else "unknown"
        return f"""
# Skill: {self.name}

**Skill Root Directory:** `{skill_root}`

---

{self.content}
"""


class SkillLoader:
    """Skill loader with Progressive Disclosure support."""

    def __init__(self, skills_dir: str = "./skills"):
        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, Skill] = {}

    def load_skill(self, skill_path: Path) -> Optional[Skill]:
        """Load single skill from SKILL.md file."""
        try:
            content = skill_path.read_text(encoding="utf-8")

            # Parse YAML frontmatter - handle leading/trailing whitespace and newlines
            # Format: ---\nname: ...\ndescription: ...\n---\n<content>
            frontmatter_match = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)

            if not frontmatter_match:
                print(f"⚠️  {skill_path} missing YAML frontmatter")
                return None

            frontmatter_text = frontmatter_match.group(1)
            skill_content = frontmatter_match.group(2).strip()

            # Simple YAML parsing (name: and description:)
            name_match = re.search(r"name:\s*(.+)", frontmatter_text)
            desc_match = re.search(r"description:\s*(.+)", frontmatter_text)

            if not name_match or not desc_match:
                print(f"⚠️  {skill_path} missing required fields")
                return None

            skill_name = name_match.group(1).strip().strip('"').strip("'")
            skill_desc = desc_match.group(1).strip().strip('"').strip("'")

            # Process paths (Level 3)
            skill_dir = skill_path.parent
            processed_content = self._process_skill_paths(skill_content, skill_dir)

            return Skill(
                name=skill_name,
                description=skill_desc,
                content=processed_content,
                skill_path=skill_path,
            )

        except Exception as e:
            print(f"❌ Failed to load skill ({skill_path}): {e}")
            return None

    def _process_skill_paths(self, content: str, skill_dir: Path) -> str:
        """Convert relative paths to absolute paths."""

        # Pattern: scripts/file.py, references/doc.md
        def replace_path(match):
            prefix = match.group(1)
            rel_path = match.group(2)
            abs_path = skill_dir / rel_path
            if abs_path.exists():
                return f"{prefix}`{abs_path}`"
            return match.group(0)

        # Match: python scripts/test.py or `scripts/test.py`
        pattern = r"(python\s+|`)((?:scripts|references|assets)/[^\s`\)]+)"
        content = re.sub(pattern, replace_path, content)

        # Markdown links: [script](scripts/test.py)
        def replace_markdown_link(match):
            prefix = match.group(1) or ""
            link_text = match.group(2)
            filepath = match.group(3)
            clean_path = filepath[2:] if filepath.startswith("./") else filepath
            abs_path = skill_dir / clean_path
            if abs_path.exists():
                return f"{prefix}[{link_text}](`{abs_path}`)"
            return match.group(0)

        pattern_md = r"(?:(Read|See|Check)\s+)?\[([^\]]+)\]\(((?:\./)?[^)]+)\)"

        def md_replacer(m):
            return replace_markdown_link(m)

        content = re.sub(pattern_md, md_replacer, content)

        return content

    def discover_skills(self) -> List[Skill]:
        """Discover and load all skills."""
        skills = []

        if not self.skills_dir.exists():
            print(f"⚠️  Skills directory does not exist: {self.skills_dir}")
            return skills

        # Find all SKILL.md files
        for skill_file in self.skills_dir.rglob("SKILL.md"):
            skill = self.load_skill(skill_file)
            if skill:
                skills.append(skill)
                self.loaded_skills[skill.name] = skill
                print(f"✅ Loaded skill: {skill.name}")

        print(f"📦 Total skills loaded: {len(skills)}")
        return skills

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get loaded skill by name."""
        return self.loaded_skills.get(name)

    def list_skills(self) -> List[str]:
        """List all loaded skill names."""
        return list(self.loaded_skills.keys())

    def get_skills_metadata_prompt(self) -> str:
        """Generate Level 1 prompt with metadata only."""
        if not self.loaded_skills:
            return ""

        prompt_parts = ["## Available Skills\n"]
        prompt_parts.append(
            "You have access to specialized skills. Each skill provides expert guidance for specific tasks.\n"
        )
        prompt_parts.append("Load a skill's full content using the get_skill tool when needed.\n")

        for skill in self.loaded_skills.values():
            prompt_parts.append(f"- `{skill.name}`: {skill.description}")

        return "\n".join(prompt_parts)
