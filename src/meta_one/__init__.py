"""Package initialization with dynamic version and public API exports."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from pathlib import Path

# Get package name dynamically from directory structure
PACKAGE_NAME = Path(__file__).parent.name

try:
    __version__ = get_version("meta.one")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__", "PACKAGE_NAME"]
