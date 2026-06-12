"""
Tests for the reflection-driven CLI registry and builder.

Covers:
  - command registration
  - signature discovery
  - argument generation (positional, flag, bool, list, Annotated, Literal)
  - dispatch (end-to-end parse → function call)
"""

import inspect
from typing import Annotated, Literal

import pytest

from plot.cli.builder import build_parser
from plot.cli.commands import COMMAND_REGISTRY, Arg, CommandDefinition, command

# ── Helpers ────────────────────────────────────────────────────────────────────

def _isolated_registry() -> dict[str, CommandDefinition]:
    """Return a fresh empty registry for isolated tests."""
    return {}


def _register(registry: dict[str, CommandDefinition], func, name: str, help: str = "test") -> None:
    """Register func into an isolated registry without touching COMMAND_REGISTRY."""
    from plot.cli.commands import CommandDefinition
    registry[name] = CommandDefinition(name=name, help=help, func=func)


def _parse(registry: dict[str, CommandDefinition], argv: list[str]):
    """Build a parser from the registry and parse argv."""
    parser = build_parser(registry)
    return parser.parse_args(argv)


# ── Registration ───────────────────────────────────────────────────────────────


def test_command_registration() -> None:
    @command(name="_test_reg_cmd", help="Registration test.", group="test")
    def _test_reg_cmd(story: str) -> int:
        return 0

    assert "_test_reg_cmd" in COMMAND_REGISTRY
    defn = COMMAND_REGISTRY["_test_reg_cmd"]
    assert defn.name == "_test_reg_cmd"
    assert defn.help == "Registration test."
    assert defn.group == "test"
    assert defn.func is _test_reg_cmd

    COMMAND_REGISTRY.pop("_test_reg_cmd", None)


def test_command_definition_fields() -> None:
    defn = CommandDefinition(
        name="foo",
        help="Foo command.",
        func=lambda: None,
        group="bar",
    )
    assert defn.name == "foo"
    assert defn.group == "bar"
    assert defn.help == "Foo command."


# ── Signature discovery ────────────────────────────────────────────────────────


def test_signature_discovery() -> None:
    def my_func(story: str, count: int = 5, flag: bool = False) -> int:
        return 0

    sig = inspect.signature(my_func)
    params = list(sig.parameters.values())

    assert params[0].name == "story"
    assert params[0].annotation is str
    assert params[0].default is inspect.Parameter.empty

    assert params[1].name == "count"
    assert params[1].annotation is int
    assert params[1].default == 5

    assert params[2].name == "flag"
    assert params[2].annotation is bool
    assert params[2].default is False


# ── Argument generation: positional ───────────────────────────────────────────


def test_builder_positional_required() -> None:
    """Required str param with no default → positional arg."""

    def cmd(story: str) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    args = _parse(registry, ["cmd", "my-story"])
    assert args.story == "my-story"


def test_builder_two_positionals() -> None:
    """Multiple required params → multiple positional args."""

    def cmd(story: str, task_id: int) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    args = _parse(registry, ["cmd", "my-story", "7"])
    assert args.story == "my-story"
    assert args.task_id == 7


# ── Argument generation: flags ────────────────────────────────────────────────


def test_builder_optional_flag() -> None:
    """str | None = None param → --flag optional arg."""

    def cmd(story: str, message: str | None = None) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    args = _parse(registry, ["cmd", "my-story"])
    assert args.message is None

    args = _parse(registry, ["cmd", "my-story", "--message", "hello"])
    assert args.message == "hello"


def test_builder_bool_flag() -> None:
    """bool = False → store_true action."""

    def cmd(story: str, dry_run: bool = False) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    args = _parse(registry, ["cmd", "my-story"])
    assert args.dry_run is False

    args = _parse(registry, ["cmd", "my-story", "--dry-run"])
    assert args.dry_run is True


def test_builder_int_flag() -> None:
    """int with default → --flag with type=int."""

    def cmd(story: str, limit: int = 20) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    args = _parse(registry, ["cmd", "my-story"])
    assert args.limit == 20

    args = _parse(registry, ["cmd", "my-story", "--limit", "50"])
    assert args.limit == 50


# ── Argument generation: list ─────────────────────────────────────────────────


def test_builder_list_param() -> None:
    """list[str] with no default → positional nargs='+'."""

    def cmd(story: str, updates: list[str]) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    args = _parse(registry, ["cmd", "my-story", "k=v", "x=y"])
    assert args.updates == ["k=v", "x=y"]


# ── Argument generation: Annotated[T, Arg(...)] ───────────────────────────────


def test_builder_arg_annotation_short() -> None:
    """Annotated with Arg(short='-m') creates short alias."""

    def cmd(
        story: str,
        message: Annotated[str | None, Arg(help="A message.", short="-m")] = None,
    ) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    # Long form
    args = _parse(registry, ["cmd", "my-story", "--message", "hi"])
    assert args.message == "hi"

    # Short form
    args = _parse(registry, ["cmd", "my-story", "-m", "hi"])
    assert args.message == "hi"


def test_builder_arg_annotation_required_flag() -> None:
    """Annotated[str, Arg(short='-m')] with no default → required --flag."""

    def cmd(
        story: str,
        message: Annotated[str, Arg(help="Required.", short="-m")],
    ) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    # Short form works
    args = _parse(registry, ["cmd", "my-story", "-m", "findings"])
    assert args.message == "findings"

    # Omitting it raises SystemExit (argparse required error)
    with pytest.raises(SystemExit):
        _parse(registry, ["cmd", "my-story"])


# ── Argument generation: Literal ──────────────────────────────────────────────


def test_builder_literal_choices() -> None:
    """Literal['pass', 'fail'] → positional with choices."""

    def cmd(story: str, outcome: Literal["pass", "fail"]) -> int:
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    args = _parse(registry, ["cmd", "my-story", "pass"])
    assert args.outcome == "pass"

    with pytest.raises(SystemExit):
        _parse(registry, ["cmd", "my-story", "invalid"])


# ── Dispatch ───────────────────────────────────────────────────────────────────


def test_dispatch_calls_function() -> None:
    """End-to-end: parse argv → dispatcher → function called with correct kwargs."""
    calls: list[dict] = []

    def cmd(story: str, count: int = 1, verbose: bool = False) -> int:
        calls.append({"story": story, "count": count, "verbose": verbose})
        return 0

    registry: dict[str, CommandDefinition] = {}
    _register(registry, cmd, "cmd")

    args = _parse(registry, ["cmd", "my-story", "--count", "3", "--verbose"])
    result = args._func(args)

    assert result == 0
    assert calls == [{"story": "my-story", "count": 3, "verbose": True}]
