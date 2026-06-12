"""
Execution configuration registry for Plot targets.

Responsibility: manage per-target execution settings (env type, virtual env,
container name, working directory, format/lint/test commands). Provides
helpers to look up configs by target name or full path and to load a registry
from a YAML file.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ExecutionConfig:
    env_type: str | None = None
    venv_name: str | None = None
    container_name: str | None = None
    working_dir: str | None = None
    format_cmd: str | None = None
    lint_cmd: str | None = None
    test_cmd: str | None = None


_REPO_CONFIGS: dict[str, ExecutionConfig] = {}


def register_repo_config(name: str, config: ExecutionConfig) -> None:
    """Register an ExecutionConfig under the given target name or path."""
    _REPO_CONFIGS[name] = config


def get_config_for_repo(path: str) -> ExecutionConfig:
    """Look up ExecutionConfig by target name, then full path, then return default.

    Lookup order:
    1. Last path component (target name, e.g. ``api_framework``)
    2. Full path string as registered
    3. Returns an empty ExecutionConfig if no match
    """
    name = Path(path).name
    if name in _REPO_CONFIGS:
        return _REPO_CONFIGS[name]
    if path in _REPO_CONFIGS:
        return _REPO_CONFIGS[path]
    return ExecutionConfig()


def load_repo_configs_from_yaml(path: str) -> dict[str, ExecutionConfig]:
    """Read a ``repos:`` YAML block into the global registry.

    Expects a YAML file with a top-level ``repos`` mapping where each key is a
    target name and each value is a dict of ExecutionConfig fields.  Updates
    ``_REPO_CONFIGS`` in place and returns the newly loaded configs.

    Unknown keys in each target block are silently ignored.
    """
    loaded: dict[str, ExecutionConfig] = {}
    p = Path(path)
    if not p.exists():
        return loaded

    with p.open() as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        return loaded

    repos = data.get("repos")
    if not isinstance(repos, dict):
        return loaded

    for name, cfg in repos.items():
        if not isinstance(cfg, dict):
            continue
        config = ExecutionConfig(
            env_type=cfg.get("env_type"),
            venv_name=cfg.get("venv_name"),
            container_name=cfg.get("container_name"),
            working_dir=cfg.get("working_dir"),
            format_cmd=cfg.get("format_cmd"),
            lint_cmd=cfg.get("lint_cmd"),
            test_cmd=cfg.get("test_cmd"),
        )
        _REPO_CONFIGS[name] = config
        loaded[name] = config

    return loaded
