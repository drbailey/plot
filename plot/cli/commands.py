"""
CLI command registry.

Holds command metadata and the @command decorator. Lives in plot.cli because
command registration is a CLI concern — core functions have no knowledge of it.

The CLI builder (plot.cli.builder) reads COMMAND_REGISTRY at startup to
generate argparse subparsers. Registration happens as a side effect of importing
modules that call command() (stubs.py) or of explicit registration in main.py.

Usage::

    from plot.cli.commands import command, Arg
    from typing import Annotated, Literal

    @command(name="submit", help="Submit a result.", group="verify")
    def submit(
        story: str,
        outcome: Literal["pass", "fail"],
        message: Annotated[str, Arg(help="Findings.", short="-m")],
    ) -> SubmitResult:
        ...
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Arg:
    """Per-parameter CLI overrides — only what cannot be derived from type annotations."""

    help: str = ""
    short: str | None = None  # single-character short alias, e.g. "-m"


@dataclass(slots=True)
class CommandDefinition:
    """Metadata describing one CLI command."""

    name: str
    help: str
    func: Callable[..., Any]
    group: str | None = None


COMMAND_REGISTRY: dict[str, CommandDefinition] = {}


def command(
    *,
    name: str,
    help: str,
    group: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a function as a CLI command.

    The decorated function's signature becomes the CLI contract.
    The function itself is returned unchanged so it can be called directly
    as a library function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        COMMAND_REGISTRY[name] = CommandDefinition(
            name=name,
            help=help,
            func=func,
            group=group,
        )
        return func

    return decorator
