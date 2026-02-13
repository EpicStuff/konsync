'''parse module parses config.taml.'''
import re
from pathlib import Path

from epicstuff import Dict

from .consts import BIN_DIR, CONFIG_DIR, HOME, SHARE_DIR


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

def parse_keywords(tokens_: Dict, token_symbol: str, parsed: Dict) -> None:
	'''Replace keywords with values in config.taml.

	For example, it will replace, $HOME with /home/username/

	Args:
		tokens_: the token dictionary
		token_symbol: TOKEN_SYMBOL
		parsed: the parsed conf.yaml file

	'''
	for item in parsed.values():
		for name in item:
			for key, value in tokens_.keywords.dict.items():
				if 'location' not in item[name]:
					continue
				word = token_symbol + key
				location = item[name].location
				if word in location:
					item[name].location = location.replace(word, value)
def parse_functions(tokens_: Dict, token_symbol: str, parsed: Dict) -> None:
	'''Replace functions with values in config.taml.

	For example, it will replace, ${ENDS_WITH='text'} with a folder whose name ends with 'text'

	Args:
		tokens_: the token dictionary
		token_symbol: TOKEN_SYMBOL
		parsed: the parsed conf.yaml file

	'''
	functions = tokens_.functions
	raw_regex = f'\\{token_symbol}{functions.raw_regex}'
	grouped_regex = f'\\{token_symbol}{functions.grouped_regex}'

	for item in parsed.values():
		for name in item:
			if 'location' not in item[name]:
				continue
			location = item[name].location
			occurrences = re.findall(raw_regex, location)
			if not occurrences:
				continue
			for occurrence in occurrences:
				func = re.search(grouped_regex, occurrence).group(1)
				if func in functions.dict:
					item[name].location = functions.dict[func](grouped_regex, location)


TOKEN_SYMBOL = '$'  # noqa: S105
tokens = Dict({
	'keywords': {
		'dict': {
			'HOME': str(HOME),
			'CONFIG_DIR': str(CONFIG_DIR),
			'SHARE_DIR': str(SHARE_DIR),
			'BIN_DIR': str(BIN_DIR),
		},
	},
	'functions': {
		'raw_regex': r"\{\w+\=(?:\"|')\S+(?:\"|')\}",
		'grouped_regex': r"\{(\w+)\=(?:\"|')(\S+)(?:\"|')\}",
		'dict': {'ENDS_WITH': ends_with, 'BEGINS_WITH': begins_with},
	},
})
