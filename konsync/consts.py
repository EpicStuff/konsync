'''
This module contains all the variables for konsync
'''
import os
from konsync import __version__


HOME = os.path.expandvars('$HOME')
CONFIG_DIR = os.path.join(HOME, '.config')
SHARE_DIR = os.path.join(HOME, '.local/share')
BIN_DIR = os.path.join(HOME, '.local/bin')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.taml')

EXPORT_EXTENSION = '.knsv'

VERSION = __version__
