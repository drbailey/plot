# plot

Story-based planning and execution CLI for AI-assisted development.

`plot` manages the full lifecycle of an AI-assisted development story: planning, task execution, verification, and finalization. It provides a structured workflow for agents and humans to collaborate on software projects.

## Setup

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for environment management

### Install

```bash
cd plot
uv sync
```

This creates a `.venv/` in the repo root and installs the `plot` command.

```bash
uv run plot --help
```

### Entry point note

If `plot_v1` is installed in your global Python environment, the `plot` command there will conflict with this package. Use `uv run plot` from within this directory to invoke the new version, or update your `config.local.yml` to point `plot` at the `.venv/Scripts/plot.exe` path once ready.

### Configuration

Copy `config.example.yml` to `config.local.yml` and edit paths for your environment. The local file is gitignored and never committed.

## Development

```bash
uv run ruff check plot/
uv run mypy plot/
uv run pytest
```
