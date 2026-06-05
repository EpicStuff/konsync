'''parse module parses config.taml.'''
import re
from pathlib import Path

from .consts import BIN_DIR, CONFIG_DIR, HOME, SHARE_DIR, TOKEN_SYMBOL


sync_dir: None | str = None

def ends_with(grouped_regex: str, path: str) -> str:
	'''Find folder with name ending with the provided string.

	Args:
		grouped_regex: regex of the function
		path: path

	'''
	occurrence = re.search(grouped_regex, path).group()
	dirs = Path(path[: path.find(occurrence)]).iterdir()
	ends_with_text = re.search(grouped_regex, occurrence).group(2)
	for directory in dirs:
		if directory.name.endswith(ends_with_text):
			return path.replace(occurrence, directory.name)
	return occurrence
def begins_with(grouped_regex: str, path: str) -> str:
	'''Find folder with name beginning with the provided string.

	Args:
		grouped_regex: regex of the function
		path: path

	'''
	occurrence = re.search(grouped_regex, path).group()
	dirs = Path(path[: path.find(occurrence)]).iterdir()
	ends_with_text = re.search(grouped_regex, occurrence).group(2)
	for directory in dirs:
		if directory.name.startswith(ends_with_text):
			return path.replace(occurrence, directory.name)
	return occurrence

def parse_path(path: str, sync: bool = False) -> Path:
	'''Replace keywords and functions with values.

	For example, it will replace, $HOME with /home/username/ and ${ENDS_WITH='text'} with a folder whose name ends with 'text'

	Args:
		path: the string to be parsed
		sync: is this being called on the sync key/setting and should sync_dir be updated

	'''
	global sync_dir
	tokens = {
		'HOME': str(HOME),
		'CONFIG_DIR': str(CONFIG_DIR),
		'SHARE_DIR': str(SHARE_DIR),
		'BIN_DIR': str(BIN_DIR),
		'SYNC': sync_dir,
	}
	functions = {'ENDS_WITH': ends_with, 'BEGINS_WITH': begins_with}
	quote = r'(?:"|\')'
	raw_regex = rf'\{TOKEN_SYMBOL}\{{\w+={quote}\S+{quote}\}}'
	grouped_regex = rf'\{TOKEN_SYMBOL}\{{(\w+)={quote}(\S+){quote}\}}'

	# replace $... with real path
	for key, value in tokens.items():
		word = TOKEN_SYMBOL + key
		if word in path:
			assert value is not None, f'{TOKEN_SYMBOL}SYNC can only be used after sync has been defined.'
			path = path.replace(word, value)
	# save sync path to be available to use later
	if sync:
		sync_dir = path

	# replace functions
	occurrences = re.findall(raw_regex, path)
	if occurrences:
		for occurrence in occurrences:
			func = re.search(grouped_regex, occurrence).group(1)
			if func in functions:
				path = functions[func](grouped_regex, path)
	return Path(path)
