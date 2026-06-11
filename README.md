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

## Code Conventions

### When to use `StrEnum`

Use `StrEnum` only when the set of values is **closed by architecture** — meaning adding a new member requires an intentional design change, not just a label addition.

Good candidates:
- State-machine outputs where every possible value has distinct handling by callers (`RouteAction`)
- Protocol-level event names persisted to a database and queried by type (`Events`)
- Values that map one-to-one with architectural concepts, where a new value = a new concept (`SkillSource`)

Not worth the cost:
- User-supplied config strings that are passed through opaquely (`env_type: "venv"`)
- Detection labels that could grow freely as new tools are supported (`test_framework: "pytest"`)
- Any field typed as `str` where the enum is never actually enforced

When in doubt: if callers would write `if x == "some_value"` rather than `if x == MyEnum.SOME_VALUE`, the enum is adding friction without adding safety — use a plain string.

## Development

```bash
uv run ruff check plot/
uv run mypy plot/
uv run pytest
```
