"""
Plot CLI entry point.

Commands register themselves via @command when their modules are imported.
The imports below are side-effects that populate COMMAND_REGISTRY before
the parser is built.

Usage:
    plot <command> [options]
    plot --help
"""

import sys

import plot.cli.stubs  # noqa: F401
import plot.core.story.knowledge_ops  # noqa: F401
import plot.core.story.ops  # noqa: F401
import plot.core.story.task_ops  # noqa: F401
import plot.core.story.transitions  # noqa: F401
import plot.core.story.workflow  # noqa: F401
from plot.cli.builder import build_parser
from plot.cli.commands import COMMAND_REGISTRY
from plot.core.base import output


def main() -> None:
    parser = build_parser(COMMAND_REGISTRY)
    args = parser.parse_args()
    output.default_verbosity = args.verbosity
    sys.exit(args._func(args))


if __name__ == "__main__":
    main()
