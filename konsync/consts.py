'''consts module contains all the variables for konsync.'''
from pathlib import Path


HOME = Path('~').expanduser()
CONFIG_DIR = HOME / '.config'
SHARE_DIR = HOME / '.local/share'
BIN_DIR = HOME / '.local/bin'

CONFIG_FILE = Path(__file__).parent / 'config.taml'
SCHEMA_FILE = Path(__file__).parent / 'schema.taml'

TOKEN_SYMBOL = '$'  # noqa: S105
