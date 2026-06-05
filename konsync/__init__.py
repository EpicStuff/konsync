'''Top-level Konsync package.'''

from importlib.metadata import version
from .parse import parse_path  # export so is accessible in schema

__version__: str = version(__name__)
