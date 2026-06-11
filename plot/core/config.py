"""
Configuration loading and path resolution for the Plot CLI.

Responsibility: everything that reads user configuration or resolves paths from
it.  This includes loading and merging YAML layers, exposing configured directory
paths, resolving user-supplied repo strings, and returning per-role agent config.
Functions that are stateless and do not touch config or env vars belong in
plot.core.utils instead.

Loads config.yml (repo defaults) and overlays config.local.yml (user overrides).
Config files are located at the repo root -- three levels above this module
(plot/core/config.py -> core/ -> plot/ -> repo_root/).

Priority for all path accessors:
  environment variable > config.local.yml > config.yml > built-in default
"""

import os
from pathlib import Path
from typing import Any

import yaml

# Repo root: plot/core/config.py -> plot/core/ -> plot/ -> repo_root/
_CONFIG_DIR = Path(__file__).parent.parent.parent


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


def load_config() -> dict[str, Any]:
    """
    Load and merge configuration files.

    Reads config.yml (repo defaults) then overlays config.local.yml (user overrides).
    Returns a merged dict with paths, defaults, agents, and skills sections.
    Missing files are silently skipped.
    """
    config: dict[str, Any] = {}

    base_path = _CONFIG_DIR / "config.yml"
    if base_path.exists():
        with base_path.open() as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                config = loaded

    local_path = _CONFIG_DIR / "config.local.yml"
    if local_path.exists():
        with local_path.open() as f:
            local = yaml.safe_load(f)
            if isinstance(local, dict):
                config = _deep_merge(config, local)

    return config


def get_stories_dir() -> Path:
    """
    Return the configured stories directory.

    Priority: PLOT_STORIES_DIR env var > config.local.yml > config.yml > ~/stories.
    """
    env = os.environ.get("PLOT_STORIES_DIR")
    if env:
        return Path(env)
    config = load_config()
    paths: Any = config.get("paths") or {}
    stories_dir: Any = paths.get("stories_dir") if isinstance(paths, dict) else None
    if stories_dir:
        return Path(str(stories_dir)).expanduser()
    return Path("~/stories").expanduser()


def get_workspace_dir() -> Path:
    """
    Return the configured workspace directory.

    Priority: PLOT_WORKSPACE env var > config.local.yml > config.yml > ~.
    """
    env = os.environ.get("PLOT_WORKSPACE")
    if env:
        return Path(env)
    config = load_config()
    paths: Any = config.get("paths") or {}
    workspace: Any = paths.get("workspace") if isinstance(paths, dict) else None
    if workspace:
        return Path(str(workspace)).expanduser()
    return Path("~").expanduser()


def resolve_repo_paths(raw: str) -> list[str]:
    """Resolve comma-separated repo names/paths into absolute path strings.

    Bare names (no path separator, not starting with '~') are joined under
    the configured workspace directory.  Paths starting with '~' are
    home-expanded.  Absolute paths are used as-is.

    Examples:
        "api_framework"           -> ["{workspace}/api_framework"]
        "api_framework, orca"     -> ["{workspace}/api_framework", "{workspace}/orca"]
        "/full/path/to/repo"      -> ["/full/path/to/repo"]
        "~/projects/repo"         -> ["/home/user/projects/repo"]
    """
    workspace = get_workspace_dir()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    resolved: list[str] = []
    for part in parts:
        p = Path(part).expanduser()
        if p.is_absolute():
            resolved.append(str(p))
        elif part.startswith("."):
            resolved.append(str(p.resolve()))
        else:
            resolved.append(str(workspace / part))
    return resolved


def get_agent_config(role: str) -> dict[str, Any]:
    """
    Return the merged agent configuration for a given role.

    Merges agents.roles.{role} overrides onto agents.default.
    Unspecified role fields inherit from the default.
    """
    config = load_config()
    agents: Any = config.get("agents")
    if not isinstance(agents, dict):
        return {}
    default: dict[str, Any] = dict(agents.get("default") or {})
    roles: Any = agents.get("roles")
    if not isinstance(roles, dict):
        return default
    role_cfg: Any = roles.get(role)
    if not isinstance(role_cfg, dict):
        return default
    return _deep_merge(default, role_cfg)
