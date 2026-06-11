"""
Repository scanner for Plot.

Responsibility: detect testing infrastructure, documentation, and agent
configuration files in a repository path. Results power the enhanced
``plot begin`` command.
"""

from dataclasses import dataclass, field
from pathlib import Path

from plot.core.repo_config import ExecutionConfig, get_config_for_repo


@dataclass
class ScanResult:
    repo_exists: bool = False
    is_git_repo: bool = False
    testing_available: bool = False
    test_framework: str | None = None
    readme_exists: bool = False
    changelog_exists: bool = False
    agent_config: list[dict[str, str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def scan_repo(path: str) -> ScanResult:
    """Scan a repository for testing, documentation, and agent configuration.

    Returns a populated ScanResult. If the path does not exist or is not a
    directory, ``repo_exists`` is False and ``errors`` contains a message.
    """
    repo = Path(path)

    if not repo.exists() or not repo.is_dir():
        return ScanResult(
            repo_exists=False,
            errors=[f"Repository not found: {path}"],
        )

    execution = get_config_for_repo(path)

    is_git_repo = (repo / ".git").exists()
    testing_available, test_framework = _detect_testing(repo, execution)
    readme_exists = _detect_file(repo, ["README.md", "README.rst", "README", "readme.md"])
    changelog_exists = _detect_file(
        repo, ["CHANGELOG.md", "HISTORY.md", "CHANGES.md", "changelog.md"]
    )
    agent_config = _detect_agent_config(repo)

    return ScanResult(
        repo_exists=True,
        is_git_repo=is_git_repo,
        testing_available=testing_available,
        test_framework=test_framework,
        readme_exists=readme_exists,
        changelog_exists=changelog_exists,
        agent_config=agent_config,
    )


def scan_repos(paths: list[str]) -> ScanResult:
    """Scan multiple repositories and merge results.

    Boolean capability flags (``is_git_repo``, ``testing_available``,
    ``readme_exists``, ``changelog_exists``) are OR-merged.
    ``test_framework`` takes the first non-None value.
    ``agent_config`` entries are accumulated from all repos.
    ``repo_exists`` is False if any repo is missing.
    """
    if not paths:
        return ScanResult()

    if len(paths) == 1:
        return scan_repo(paths[0])

    merged = ScanResult(repo_exists=True)

    for path in paths:
        result = scan_repo(path)
        if not result.repo_exists:
            merged.repo_exists = False
            merged.errors.extend(result.errors)
        else:
            merged.is_git_repo = merged.is_git_repo or result.is_git_repo
            merged.testing_available = merged.testing_available or result.testing_available
            merged.readme_exists = merged.readme_exists or result.readme_exists
            merged.changelog_exists = merged.changelog_exists or result.changelog_exists
            merged.test_framework = merged.test_framework or result.test_framework
            merged.agent_config.extend(result.agent_config)

    return merged


def _detect_testing(
    repo: Path, execution: ExecutionConfig
) -> tuple[bool, str | None]:
    """Detect testing infrastructure and return (testing_available, test_framework)."""
    testing_available = False
    test_framework: str | None = None

    if (repo / "pytest.ini").exists() or (repo / "conftest.py").exists():
        testing_available = True
        test_framework = "pytest"
    elif (repo / "pyproject.toml").exists():
        pyproject = (repo / "pyproject.toml").read_text()
        if "[tool.pytest" in pyproject or "pytest" in pyproject:
            testing_available = True
            test_framework = "pytest"

    if (repo / "tests").exists() or (repo / "test").exists():
        testing_available = True
        test_framework = test_framework or "pytest"

    for config_file in [
        "jest.config.js",
        "jest.config.ts",
        "vitest.config.js",
        "vitest.config.ts",
    ]:
        if (repo / config_file).exists():
            testing_available = True
            test_framework = "jest" if "jest" in config_file else "vitest"
            break

    if execution.test_cmd:
        testing_available = True

    return testing_available, test_framework


def _detect_file(repo: Path, candidates: list[str]) -> bool:
    """Return True if any candidate filename exists directly in the repo root."""
    return any((repo / name).exists() for name in candidates)


def _detect_agent_config(repo: Path) -> list[dict[str, str]]:
    """Detect agent/AI configuration files present in the repo."""
    found: list[dict[str, str]] = []

    checks = [
        (".cursorrules", "cursorrules", "Cursor rules for AI behavior"),
        (".cursor/rules", "cursor-rules-dir", "Cursor rules directory"),
        ("AGENTS.md", "agents-md", "Agents configuration"),
        ("CLAUDE.md", "claude-md", "Claude Code configuration"),
        ("copilot-instructions.md", "copilot-instructions", "GitHub Copilot instructions"),
        (".clinerules", "cline-rules", "Cline rules"),
        (".windsurfrules", "windsurf-rules", "Windsurf rules"),
    ]

    for path_str, kind, description in checks:
        target = repo / path_str
        if target.exists():
            found.append({"path": str(target), "kind": kind, "description": description})

    return found
