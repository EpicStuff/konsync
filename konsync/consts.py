'''consts module contains all the variables for konsync.'''
from pathlib import Path

from . import __version__

HOME = Path('~').expanduser()
CONFIG_DIR = HOME / '.config'
SHARE_DIR = HOME / '.local/share'
BIN_DIR = HOME / '.local/bin'

CONFIG_FILE = Path(__file__).parent / 'config.taml'

VERSION = __version__
