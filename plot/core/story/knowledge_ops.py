"""
Knowledge query/record operations, skills listing, and repo-config.

All functions are registered as CLI commands via @command. Importing this
module populates COMMAND_REGISTRY with: knowledge-patterns, knowledge-search,
knowledge-record-pattern, knowledge-record-decision, knowledge-query,
skills, repo-config.

Business logic only — no argparse, no output formatting. The CLI dispatcher
in plot.cli.builder calls output.emit_result() after a successful command.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from plot.cli.commands import Arg, command
from plot.core.base.errors import PlotError
from plot.core.base.result import Result
from plot.core.config.execution import get_configs_for_repos, load_repo_configs_from_yaml
from plot.core.config.paths import get_stories_dir
from plot.core.story.workflow import StoryWorkflow
from plot.core.target.skills import SkillRecord, get_all_skills
from plot.db import KnowledgeDB, PatternRow, SearchResult

# Three levels up from core/story/knowledge_ops.py → plot/ repo root
_PLOT_DIR = Path(__file__).parent.parent.parent


# ── Internal helpers ───────────────────────────────────────────────────────────


def _get_knowledge_db() -> KnowledgeDB:
    return KnowledgeDB(get_stories_dir() / "knowledge.db")


# ── Result types ───────────────────────────────────────────────────────────────


@dataclass
class KnowledgePatternListResult(Result):
    """Result of a knowledge-patterns query."""

    patterns: list[PatternRow]
    tag: str | None
    limit: int

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        import dataclasses

        return {
            "tag": self.tag,
            "limit": self.limit,
            "patterns": [dataclasses.asdict(p) for p in self.patterns],
        }

    def __str__(self) -> str:
        if not self.patterns:
            return "No patterns found."
        lines = [f"Patterns ({len(self.patterns)}):"]
        for p in self.patterns:
            desc = (p.description or "")[:60]
            lines.append(f"  [{p.tag}] {p.title} - {desc}")
        return "\n".join(lines)


@dataclass
class KnowledgeSearchOutput(Result):
    """Result of a knowledge-search query."""

    query: str
    results: list[SearchResult]

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        import dataclasses

        return {
            "query": self.query,
            "results": [dataclasses.asdict(r) for r in self.results],
        }

    def __str__(self) -> str:
        if not self.results:
            return f"No results for '{self.query}'."
        lines = [f"Results for '{self.query}' ({len(self.results)}):"]
        for r in self.results:
            title = r.title or ""
            desc = (r.description or "")[:60]
            lines.append(f"  [{r.source}] {title} - {desc}")
        return "\n".join(lines)


@dataclass
class KnowledgeRecordResult(Result):
    """Result of a knowledge record operation."""

    id: int
    action: str  # "pattern" or "decision"

    def __str__(self) -> str:
        return f"Recorded {self.action} id={self.id}"


@dataclass
class KnowledgeQueryResult(Result):
    """Result of a raw knowledge-query execution."""

    sql: str
    rows: list[dict]  # type: ignore[type-arg]

    def __str__(self) -> str:
        lines = [f"Rows: {len(self.rows)}"]
        for row in self.rows:
            lines.append(f"  {row}")
        return "\n".join(lines)


@dataclass
class SkillsResult(Result):
    """Result of a skills listing."""

    skills: list[SkillRecord]

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        return {
            "skills": [
                {
                    "name": s.name,
                    "description": s.description,
                    "source": str(s.source),
                    "installed": s.installed,
                    "path": s.path,
                }
                for s in self.skills
            ]
        }

    def __str__(self) -> str:
        if not self.skills:
            return "No skills found."
        lines = [f"Skills ({len(self.skills)}):"]
        for s in self.skills:
            status = "installed" if s.installed else "not installed"
            lines.append(f"  {s.name} [{s.source}] {status} - {s.description}")
        return "\n".join(lines)


@dataclass
class RepoConfigResult(Result):
    """Result of a repo-config query for one or more repos."""

    repos: list[dict]  # type: ignore[type-arg]

    def __str__(self) -> str:
        if not self.repos:
            return "No repo config found."
        lines = []
        for entry in self.repos:
            lines.append(f"Repo: {entry['repo']}")
            for key in (
                "env_type",
                "venv_name",
                "container_name",
                "working_dir",
                "format_cmd",
                "lint_cmd",
                "test_cmd",
            ):
                val = entry.get(key)
                if val is not None:
                    lines.append(f"  {key}: {val}")
        return "\n".join(lines)


# ── Commands ───────────────────────────────────────────────────────────────────


@command(name="knowledge-patterns", help="List knowledge patterns.", group="knowledge")
def knowledge_patterns(
    tag: str | None = None,
    limit: int = 20,
) -> KnowledgePatternListResult:
    """Query patterns from the knowledge store, optionally filtered by tag."""
    kdb = _get_knowledge_db()
    patterns = kdb.get_patterns(tag=tag, limit=limit)
    return KnowledgePatternListResult(patterns=patterns, tag=tag, limit=limit)


@command(name="knowledge-search", help="Search the knowledge store.", group="knowledge")
def knowledge_search(
    query: str,
    limit: int = 20,
) -> KnowledgeSearchOutput:
    """Search patterns, decisions, and artifacts using keyword matching."""
    kdb = _get_knowledge_db()
    results = kdb.search(query, limit=limit)
    return KnowledgeSearchOutput(query=query, results=results)


@command(
    name="knowledge-record-pattern",
    help="Record a knowledge pattern.",
    group="knowledge",
)
def knowledge_record_pattern(
    tag: str,
    title: str,
    message: Annotated[str | None, Arg(help="Pattern description.", short="-m")] = None,
    context: str | None = None,
    run_id: int | None = None,
) -> KnowledgeRecordResult:
    """Record or update a pattern in the knowledge store."""
    kdb = _get_knowledge_db()
    record_id = kdb.record_pattern(
        run_id=run_id or 0,
        tag=tag,
        title=title,
        description=message or "",
        context=context,
    )
    return KnowledgeRecordResult(id=record_id, action="pattern")


@command(
    name="knowledge-record-decision",
    help="Record a knowledge decision.",
    group="knowledge",
)
def knowledge_record_decision(
    context: Annotated[str, Arg(help="Context in which the decision was made.", short="-c")],
    decision: Annotated[str, Arg(help="Decision made.", short="-d")],
    rationale: Annotated[str, Arg(help="Rationale for the decision.", short="-r")],
    run_id: int | None = None,
) -> KnowledgeRecordResult:
    """Record a decision in the knowledge store. Decisions are story-independent."""
    kdb = _get_knowledge_db()
    record_id = kdb.record_decision(
        run_id=run_id or 0,
        story="",
        context=context,
        decision=decision,
        rationale=rationale,
    )
    return KnowledgeRecordResult(id=record_id, action="decision")


@command(
    name="knowledge-query",
    help="Execute a raw SQL query against the knowledge store (internal/debug use).",
    group="knowledge",
)
def knowledge_query(sql: str) -> KnowledgeQueryResult:
    """Run ad-hoc SQL against knowledge.db. No stability guarantee on output shape."""
    kdb = _get_knowledge_db()
    rows = kdb.execute(sql)
    return KnowledgeQueryResult(sql=sql, rows=rows)


@command(name="skills", help="List all known skills.", group="meta")
def skills() -> SkillsResult:
    """Discover and list core, dependency, and user-registered skills."""
    records = get_all_skills(_PLOT_DIR)
    return SkillsResult(skills=records)


@command(name="repo-config", help="Show repo execution config.", group="meta")
def repo_config(story: str) -> RepoConfigResult:
    """Output execution config for the story's target repo(s)."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' not found.")
    repo_path_str: str = state.get("repo_path") or ""
    paths = [p.strip() for p in repo_path_str.split(",") if p.strip()]

    for cfg_file in ("config.yml", "config.local.yml"):
        cfg_path = _PLOT_DIR / cfg_file
        if cfg_path.exists():
            load_repo_configs_from_yaml(str(cfg_path))

    pairs = get_configs_for_repos(paths)
    repos = [
        {
            "repo": path,
            "env_type": cfg.env_type,
            "venv_name": cfg.venv_name,
            "container_name": cfg.container_name,
            "working_dir": cfg.working_dir,
            "format_cmd": cfg.format_cmd,
            "lint_cmd": cfg.lint_cmd,
            "test_cmd": cfg.test_cmd,
        }
        for path, cfg in pairs
    ]
    return RepoConfigResult(repos=repos)
