"""Skyline - CLI tool for easily creating GitHub Apps."""

import site
from pathlib import Path

__version__ = "0.1.0"

def get_version_string():
    """Get version string"""

    # todo: check if we're in development mode
    version = __version__
    return version
