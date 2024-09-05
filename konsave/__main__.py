'''Konsync entry point.'''

import argparse
import os
import shutil
from pathlib import Path

from pkg_resources import resource_filename

from konsync.consts import CONFIG_FILE, VERSION
from konsync.funcs import export, log, remove, sync


def _get_parser() -> argparse.ArgumentParser:
	'''Returns CLI parser.

	Returns:
		argparse.ArgumentParser: Created parser.
	'''
	parser = argparse.ArgumentParser(
		prog='Konsync',
		epilog='Please report bugs at https://www.github.com/epicstuff/konsync',
	)

	parser.add_argument(
		'-s',
		'--sync',
		required=False,
		action='store_true',
		help='Setup sync based on current config',
	)
	parser.add_argument(
		'-r',
		'--remove',
		required=False,
		action='store_true',
		help='Remove links and copies files',
	)
	parser.add_argument(
		'-i',
		'--import',
		required=False,
		action='store_true',
		help='Import files that are not synced',
	)
	parser.add_argument(
		'-e',
		'--export',
		required=False,
		action='store_true',
		help='Export and compress files that are not synced',
	)
	parser.add_argument(
		'-f',
		'--force',
		required=False,
		help='Force, will delete existing files, specify prioritise local or sync files with -f local or -f sync',
	)
	parser.add_argument(
		'-v',
		'--version',
		'--verbose',
		required=False,
		action='store_true',
		help='Show version when used without other aguments, acts as verbose switch when used with other aguments',
	)
	parser.add_argument(
		'-c',
		'--config',
		required=False,
		type=Path,
		help='Specify config file location, defaults to ./config.taml'
	)
	parser.add_argument(
		'-C',
		'--compression',
		required=False,
		type=str,
		default='fpaq',
		help='Specify compression algorithm, defaults to fpaq, Options: fpaq'
	)
	parser.add_argument(
		'location',
		nargs='?',
		type=str,
		help='Specify directory to sync files to, overwrites config.taml'
	)

	return parser


def main():
	'''The main function that handles all the arguments and options.'''

	# create copy of config file if it doesn't exist
	if not os.path.exists(CONFIG_FILE):
		if os.path.expandvars('$XDG_CURRENT_DESKTOP') == 'KDE':
			default_config_path = resource_filename('konsync', 'conf_kde.taml')
			shutil.copy(default_config_path, CONFIG_FILE)
		else:
			default_config_path = resource_filename('konsync', 'conf_other.taml')
			shutil.copy(default_config_path, CONFIG_FILE)
		log('created config file')

	parser = _get_parser()
	args = parser.parse_args()

	# set log level based on verbose
	if args.version:
		log.setLevel('DEBUG')
	else:
		log.setLevel('INFO')
	#
	if args.sync:
		sync(args.config, args.location, args.version, args.force)
	elif args.remove:
		remove()
	elif args.export:
		export(args.export_name, args.force)
	elif args.version:
		print(VERSION)
	elif not args.version:
		parser.print_help()


if __name__ == '__main__':
	main()
