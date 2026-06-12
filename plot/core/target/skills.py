"""
Skills registry for Plot.

Responsibility: discover core (bundled), dependency (declared in config.yml
skills.dependencies), and user-registered (declared in config.local.yml
skills.user) skills, and expose them via get_all_skills(plot_dir).

Config layers:
  skills.core         list of bundled skill names (documentation only;
                      actual discovery is filesystem-based)
  skills.dependencies dict of {name: {install: str, description: str}}
  skills.user         dict of {name: {path: str, description: str}}
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


class SkillSource(StrEnum):
    CORE = "core"
    DEPENDENCY = "dependency"
    USER = "user"


@dataclass
class SkillRecord:
    name: str
    description: str
    path: str
    source: SkillSource
    installed: bool


def get_all_skills(plot_dir: Path) -> list[SkillRecord]:
    """Return merged list of all known skills.

    Discovers core skills from the filesystem, then adds dependency and user
    skills from merged configuration.
    """
    config = _load_config(plot_dir)
    skills_raw = config.get("skills")
    skills_cfg: dict[str, Any] = skills_raw if isinstance(skills_raw, dict) else {}

    result: list[SkillRecord] = []
    result.extend(get_core_skills(plot_dir))
    result.extend(get_dependency_skills(skills_cfg))
    result.extend(get_user_skills(skills_cfg))
    return result


def get_core_skills(plot_dir: Path) -> list[SkillRecord]:
    """Discover bundled skills from {plot_dir}/skills/*/SKILL.md."""
    skills_dir = plot_dir / "skills"
    records: list[SkillRecord] = []

    if not skills_dir.is_dir():
        return records

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        frontmatter = _parse_skill_frontmatter(skill_md)
        name = str(frontmatter.get("name") or skill_dir.name)
        description = str(frontmatter.get("description") or "")
        records.append(
            SkillRecord(
                name=name,
                description=description,
                path=str(skill_md),
                source=SkillSource.CORE,
                installed=True,
            )
        )

    return records


def get_dependency_skills(skills_cfg: dict[str, Any]) -> list[SkillRecord]:
    """Return skills declared in config skills.dependencies."""
    deps = skills_cfg.get("dependencies")
    if not isinstance(deps, dict):
        return []

    records: list[SkillRecord] = []
    for name, meta in deps.items():
        if not isinstance(meta, dict):
            continue
        description = str(meta.get("description") or "")
        installed_path = _find_installed_skill(str(name))
        records.append(
            SkillRecord(
                name=str(name),
                description=description,
                path=installed_path if installed_path else _expected_install_path(str(name)),
                source=SkillSource.DEPENDENCY,
                installed=bool(installed_path),
            )
        )

    return records


def get_user_skills(skills_cfg: dict[str, Any]) -> list[SkillRecord]:
    """Return user-registered skills from config skills.user."""
    user = skills_cfg.get("user")
    if not isinstance(user, dict):
        return []

    records: list[SkillRecord] = []
    for name, meta in user.items():
        if not isinstance(meta, dict):
            continue
        description = str(meta.get("description") or "")
        path = str(meta.get("path") or "")
        installed = Path(path).exists() if path else False
        records.append(
            SkillRecord(
                name=str(name),
                description=description,
                path=path,
                source=SkillSource.USER,
                installed=installed,
            )
        )

    return records


def _parse_skill_frontmatter(path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a SKILL.md file.

    Frontmatter is delimited by ``---`` markers at the start of the file.
    Returns an empty dict if frontmatter is absent, malformed, or unreadable.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    if not text.startswith("---"):
        return {}

    rest = text[3:]
    end = rest.find("---")
    if end == -1:
        return {}

    yaml_text = rest[:end]
    try:
        result = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return {}

    return result if isinstance(result, dict) else {}


def _find_installed_skill(name: str) -> str:
    """Check standard skill directories for an installed skill.

    Checks ``~/.cursor/skills/{name}/SKILL.md`` then
    ``~/.codex/skills/{name}/SKILL.md``.  Returns the path string of the first
    match, or empty string if not found.
    """
    home = Path.home()
    candidates = [
        home / ".cursor" / "skills" / name / "SKILL.md",
        home / ".codex" / "skills" / name / "SKILL.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""


def _expected_install_path(name: str) -> str:
    """Return the conventional install path for a named dependency skill."""
    return str(Path.home() / ".cursor" / "skills" / name / "SKILL.md")


def _load_config(plot_dir: Path) -> dict[str, Any]:
    """Load and merge config.yml and config.local.yml from plot_dir.

    Mirrors the logic in plot.core.config.paths.load_config but accepts an
    explicit directory so the function is testable without relying on the
    module-level _CONFIG_DIR constant.
    """
    config: dict[str, Any] = {}

    base_path = plot_dir / "config.yml"
    if base_path.exists():
        with base_path.open() as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                config = loaded

    local_path = plot_dir / "config.local.yml"
    if local_path.exists():
        with local_path.open() as f:
            local = yaml.safe_load(f)
            if isinstance(local, dict):
                config = _deep_merge(config, local)

    return config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base, returning a new dict."""
    result: dict[str, Any] = dict(base)
    for key, value in override.items():
        base_val = result.get(key)
        if isinstance(base_val, dict) and isinstance(value, dict):
            result[key] = _deep_merge(base_val, value)
        else:
            result[key] = value
    return result
