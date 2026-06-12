# plot

Story-based planning and execution library (and CLI) for AI-assisted development.

`plot` manages the full lifecycle of an AI-assisted development story: planning, task execution, verification, and finalization. It provides a structured workflow for agents and humans to collaborate on software projects.

## Architecture

`plot` is a **Python library first, CLI second**. The bulk of the implementation lives in `plot/core/`; the CLI is a thin formatting wrapper that exposes core functions to the terminal.

```
plot/
  core/          ← library: all business logic, no CLI coupling
    workflow.py  ← story lifecycle (begin, approve, revise, …)
    router.py    ← action routing
    scanner.py   ← repo detection
    config.py    ← configuration resolution
    output.py    ← emit() helper (also used by CLI layer)
    …
  cli/           ← thin wrapper: @command decoration + output formatting only
    registry.py  ← CommandDefinition, Arg, COMMAND_REGISTRY, @command decorator
    builder.py   ← reflection engine: inspects signatures → generates argparse
    main.py      ← entry point, wires side-effect imports
    cmd_begin.py ← begin command wrapper
    stubs.py     ← @command stubs for unimplemented commands
  db/            ← database layer (StoryDB, StoryLogger, KnowledgeDB)
```

### Two-layer command pattern

Every command has two parts:

**Core function** (`plot/core/<module>.py`) — does the work, returns a result dataclass, raises `WorkflowError` on failure. No `emit()`, no argparse.

```python
# plot/core/workflow.py
def begin(story: str, repo_path: str | None = None, ...) -> BeginResult:
    ...
```

**CLI wrapper** (`plot/cli/cmd_<name>.py`) — applies `@command`, calls the core function, formats output with `emit()`.

```python
# plot/cli/cmd_begin.py
@command(name="begin", help="...", group="story")
def begin(story: str, repo_path: str | None = None, ..., output_json: bool = False) -> int:
    try:
        result = workflow.begin(story=story, repo_path=repo_path, ...)
    except WorkflowError as e:
        output.emit(f"ERROR: {e}", level=-1)
        return 1
    _emit_result(result, output_json=output_json)
    return 0
```

Core functions are importable and usable without the CLI:

```python
from plot.core.workflow import begin, BeginResult, WorkflowError
result = begin(story="my-story", repo_path="api_framework")
```

### Reflection-driven CLI

The CLI requires no duplicate argument definitions. The `@command` decorator registers a function; `builder.py` inspects its signature at runtime to generate the `argparse` subparser automatically.

| Python type | argparse mapping |
|---|---|
| `str` / `int` / `Path` | positional (no default) or `--flag` (has default) |
| `bool` | `--flag / --no-flag` via `store_true` / `store_false` |
| `list[str]` | `--flag VAL ...` (`nargs="+"`) |
| `Literal["a", "b"]` | `choices=["a", "b"]` |
| `Annotated[T, Arg(help="...", short="-x")]` | adds help text and short alias |
| `T \| None` | optional flag, `default=None` |

Adding a command is a single step: write the function with a typed signature and apply `@command`. The parser, `--help`, and dispatch are generated automatically.

### Adding a new command

1. Implement the function in `plot/core/<module>.py`. Apply `@command` from `plot.cli.commands`:

```python
# plot/core/my_ops.py
from plot.cli.commands import command
from plot.core.errors import WorkflowError

@command(name="my-cmd", help="Does something.", group="story")
def my_cmd(story: str, limit: int = 10) -> MyCmdResult:
    ...
```

2. Add a side-effect import to `plot/cli/main.py`:

```python
import plot.core.my_ops  # noqa: F401
```

That's it. The `@command` decorator fires when the module is imported, populating `COMMAND_REGISTRY`. The builder reads the registry and generates the subparser automatically — no argparse code, no wrapper file.

**Why `@command` lives in `plot.cli.commands` but is imported in `plot.core`:** `commands.py` contains only metadata (dataclasses and a dict) — no argparse, no output. The coupling is intentional and bounded: core functions declare their CLI surface via the decorator, and the CLI builder reads it. Core is still fully usable as a library without the CLI layer invoking it.

**Evaluating import direction:** When deciding whether a core module may import from `cli/`, evaluate the *content* of what is being imported, not just the package path. A module in `cli/` that carries no CLI behavior (no argparse, no output formatting, no subprocess calls) is safe to import in core. A module that wires argparse or formats terminal output is not. Apply this test before moving modules or adding indirection to avoid the import.

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

### Core vs CLI boundary

- **Core** (`plot/core/`): pure Python functions, dataclass results, exceptions for errors. Never calls `emit()`. Never imports from `plot.cli`.
- **CLI** (`plot/cli/`): calls core, catches `WorkflowError`, formats results with `emit()`. Never contains business logic.
- **DB** (`plot.db`): always import from the top-level package (`from plot.db import StoryDB, Events`); never import from submodules directly.

### Module-level state

Do not use `global` to rebind module-level variables inside functions. If callers need to change a module setting, expose the variable as a plain attribute and let them set it directly:

```python
# output.py
default_verbosity: int = 0

# caller
from plot.core import output
output.default_verbosity = 1
```

If a setter function is genuinely needed (e.g. for validation), prefer a simple class instance over a `global` declaration.

### emit levels

`emit(message, level=0)` prints when `level <= output.default_verbosity`.

| level | meaning |
|-------|---------|
| `-1`  | error — shown even in quiet mode |
| `0`   | normal output (default) |
| `1+`  | verbose / debug |

Quiet mode sets `default_verbosity = -1`; verbose sets it to `1`.

---

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
