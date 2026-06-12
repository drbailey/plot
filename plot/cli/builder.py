"""
Reflection-driven argparse builder.

Reads COMMAND_REGISTRY, inspects each function's signature, and generates
argparse subparsers automatically. Orchestration functions have zero awareness
of argparse; the builder is the only place argparse is touched.

Type → argparse mapping
-----------------------
str                   positional (required) or --flag (optional)
int                   positional (required) or --flag (optional)
bool                  --flag with action="store_true", never positional
Path                  same positional/flag rules as str/int
str | None            --flag, default=None
int | None            --flag, default=None
list[str]             --flag, nargs="+"
Literal["a", "b"]    --flag or positional, choices=["a","b"]
Annotated[T, Arg()]   base type from T, help/short from Arg

Positional vs --flag rule
-------------------------
A parameter is rendered as a positional arg when ALL of the following hold:
  - it has no default value (inspect.Parameter.empty)
  - its type is not X | None
  - its type is not bool
  - its type is not list[...]
"""

from __future__ import annotations

import argparse
import inspect
import typing
from pathlib import Path
from typing import Annotated, Any, Literal, get_args, get_origin

from plot.cli.commands import COMMAND_REGISTRY, Arg, CommandDefinition
from plot.core.base import output
from plot.core.base.errors import PlotError


def build_parser(
    registry: dict[str, CommandDefinition] | None = None,
) -> argparse.ArgumentParser:
    """Build and return a top-level ArgumentParser from the command registry."""
    if registry is None:
        registry = COMMAND_REGISTRY

    parser = argparse.ArgumentParser(
        prog="plot",
        description="Plot story management CLI",
    )
    parser.add_argument(
        "-v", "--verbosity", type=int, default=0, metavar="N",
        help="Output verbosity level (default: 0; -1 = errors only, 1+ = verbose)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    for cmd in registry.values():
        sub = subparsers.add_parser(cmd.name, help=cmd.help)
        _add_arguments(sub, cmd.func)
        sub.add_argument("--json", dest="output_json", action="store_true", help="Output as JSON")
        sub.set_defaults(_func=_make_dispatcher(cmd.func))

    return parser


# ── Argument generation ────────────────────────────────────────────────────────


def _add_arguments(parser: argparse.ArgumentParser, func: Any) -> None:
    """Inspect func's signature and add argparse arguments to parser."""
    sig = inspect.signature(func)
    # Resolve string annotations (handles `from __future__ import annotations`).
    # include_extras=True preserves Annotated[...] wrappers.
    try:
        hints = typing.get_type_hints(func, include_extras=True)
    except Exception:
        hints = {}

    for param in sig.parameters.values():
        annotation = hints.get(param.name, param.annotation)
        _add_one_argument(parser, param, annotation)


def _add_one_argument(
    parser: argparse.ArgumentParser,
    param: inspect.Parameter,
    annotation: Any,
) -> None:
    has_default = param.default is not inspect.Parameter.empty

    # Unwrap Annotated[T, Arg(...)] → extract inner type and Arg metadata
    arg_meta: Arg | None = None
    if get_origin(annotation) is Annotated:
        inner_args = get_args(annotation)
        annotation = inner_args[0]
        for meta in inner_args[1:]:
            if isinstance(meta, Arg):
                arg_meta = meta
                break

    help_text = arg_meta.help if arg_meta else ""
    short = arg_meta.short if arg_meta else None

    # A short alias forces flag rendering (never positional)
    has_short = short is not None

    # Resolve the effective Python type and argparse kwargs
    kwargs = _annotation_to_kwargs(annotation, has_default)

    is_positional = _is_positional(annotation, has_default, has_short)

    if is_positional:
        kwargs.pop("default", None)
        kwargs.pop("required", None)
        if help_text:
            kwargs["help"] = help_text
        parser.add_argument(param.name, **kwargs)
    else:
        # --param-name flag (snake → kebab)
        flag = f"--{param.name.replace('_', '-')}"
        names = [short, flag] if short else [flag]
        # Set default from the parameter value when present
        if has_default and "default" not in kwargs:
            kwargs["default"] = param.default
        # Required flag: no default, not optional type, not bool, not list
        if (
            not has_default
            and not _is_optional(annotation)
            and annotation is not bool
            and get_origin(annotation) is not list
            and kwargs.get("action") != "store_true"
        ):
            kwargs["required"] = True
        if help_text:
            kwargs["help"] = help_text
        parser.add_argument(*names, **kwargs)


def _is_positional(annotation: Any, has_default: bool, has_short: bool) -> bool:
    """Return True when this parameter should be a positional CLI arg."""
    if has_default:
        return False
    # Short alias forces flag rendering
    if has_short:
        return False
    if annotation is bool:
        return False
    # list[...] without a default → positional nargs="+" (e.g. KEY=VALUE pairs)
    # X | None → optional, always a flag
    return not _is_optional(annotation)


def _is_optional(annotation: Any) -> bool:
    """Return True for X | None / Optional[X] union types."""
    origin = get_origin(annotation)
    if origin is None:
        return False
    # Handles both `X | None` (types.UnionType) and `Optional[X]` (typing.Union)
    return type(None) in get_args(annotation)


def _annotation_to_kwargs(annotation: Any, has_default: bool) -> dict[str, Any]:
    """Translate a type annotation into argparse add_argument kwargs."""
    origin = get_origin(annotation)

    # bool → store_true flag
    if annotation is bool:
        return {"action": "store_true", "default": False}

    # list[T] → nargs="+"
    if origin is list:
        inner = get_args(annotation)
        item_type = inner[0] if inner else str
        return {"type": item_type, "nargs": "+"}

    # Literal["a", "b"] → choices
    if origin is Literal:
        choices = list(get_args(annotation))
        py_type = type(choices[0]) if choices else str
        base: dict[str, Any] = {"type": py_type, "choices": choices}
        if has_default:
            base["default"] = None
        else:
            base["required"] = True
        return base

    # X | None → optional flag
    if _is_optional(annotation):
        inner_args = get_args(annotation)
        inner = next(a for a in inner_args if a is not type(None))
        return {"type": _py_type(inner), "default": None}

    # Plain types
    py_type = _py_type(annotation)
    return {"type": py_type}


def _py_type(annotation: Any) -> type:
    """Map an annotation to a callable argparse type converter."""
    if annotation is Path:
        return Path
    if annotation is int:
        return int
    if annotation is float:
        return float
    return str


# ── Dispatch ───────────────────────────────────────────────────────────────────


def _make_dispatcher(func: Any) -> Any:
    """Return a dispatcher that extracts kwargs from the Namespace and calls func.

    Handles the core-to-CLI contract automatically:
    - Catches PlotError and emits it as an error message (exit 1).
    - If the function returns an int, passes it through as the exit code.
    - Otherwise calls output.emit_result() and returns 0.
    """
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())

    def dispatch(args: argparse.Namespace) -> int:
        kwargs: dict[str, Any] = {name: getattr(args, name) for name in param_names}
        try:
            result = func(**kwargs)
        except PlotError as e:
            output.emit(f"ERROR: {e}", level=-1)
            return 1
        if isinstance(result, int):
            return result
        output.emit_result(result, output_json=getattr(args, "output_json", False))
        return 0

    return dispatch
