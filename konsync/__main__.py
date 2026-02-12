'''Konsync entry point.'''

import argparse, os, shutil
from importlib.resources import files
from pathlib import Path

from konsync.consts import CONFIG_FILE, VERSION
from konsync.funcs import export, log, sync


def _get_parser() -> argparse.ArgumentParser:
	'''Return CLI parser.

	Return:
		argparse.ArgumentParser: Created parser.

	'''
	parser = argparse.ArgumentParser(
		prog='Konsync',
		description='A simple and powerful utility for managing your dotfiles.',
		epilog='Please report bugs at https://www.github.com/epicstuff/konsync/issues',
		usage='%(prog)s [options...] [location]',
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
		'-e',
		'--export',
		required=False,
		action='store_true',
		help='Export and compress files that are not synced',
	)
	parser.add_argument(
		'-i',
		'--import',
		required=False,
		action='store_true',
		help='Import files that are not synced',
	)
	parser.add_argument(
		'-f',
		'--force',
		required=False,
		help='Force, will delete existing files, specify to wether prioritise local or sync files',
		choices=['local', 'sync', ''],
		nargs='?',
		const=True,
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
		help='Specify config file location, defaults to ./config.taml',
	)
	parser.add_argument(
		'-C',
		'--compression',
		required=False,
		type=str,
		default='fpaq',
		help='Specify compression algorithm, overwriting config.taml',
		choices=['fpaq'],
	)
	parser.add_argument(
		'location',
		nargs='?',
		type=Path,
		help='Specify directory to sync files to, overwrites config.taml',
	)

	return parser


def main() -> None:
	'''Handle the arguments and options.'''
	# create copy of config file if it doesn't exist
	if not Path(CONFIG_FILE).exists():
		if os.path.expandvars('$XDG_CURRENT_DESKTOP') == 'KDE':
			default_config_path = str(files('konsync') / 'conf_kde.taml')
			shutil.copy(default_config_path, CONFIG_FILE)
		else:
			default_config_path = str(files('konsync') / 'conf_other.taml')
			shutil.copy(default_config_path, CONFIG_FILE)
		log.info('created config file')

	parser = _get_parser()
	args = parser.parse_args()

	# set log level based on verbose (version)
	if args.version:
		log.setLevel('DEBUG')
	else:
		log.setLevel('INFO')
	if args.sync:
		sync(args.config, args.location, args.version, args.force)
	elif args.export:
		export(args.config, args.location, args.compression, args.version)
	# elif args.remove:
	# 	remove()
	elif args.version:
		print(VERSION)
	else:
		parser.print_help()


if __name__ == '__main__':
	main()
