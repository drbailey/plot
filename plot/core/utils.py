"""
Static utility functions for Plot.

Responsibility: stateless helpers with no dependency on user configuration or
the environment.  Any function that reads config files, env vars, or resolves
user-supplied paths belongs in plot.core.config instead.
"""

from pathlib import Path


def get_plot_dir() -> Path:
    """Return the plot repo root directory.

    This is the directory that contains config.yml, templates/, and skills/.
    Computed relative to this file: plot/core/utils.py -> core/ -> plot/ -> repo_root/.
    """
    return Path(__file__).parent.parent.parent
