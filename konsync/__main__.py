'''Konsync entry point.'''

import docopt, os, shutil
from importlib.resources import files
from pathlib import Path

from epicstuff import Dict, s

from konsync.consts import CONFIG_FILE, VERSION
from konsync.funcs import export, log, sync


def _get_parser(argv: list[str] | str | None = None) -> docopt.ParsedOptions:
	'Return CLI parser.'
	doc = s('''
		konsync
		A simple and powerful utility for managing your dotfiles.

		Usage:
			konsync <command> [options...]
			konsync -h, --help
			konsync --version

		Commands:
			sync, s     Setup sync based on current config
			export, e   Export and compress files specified in config
			import, i   Import files that were exported
			remove, r   Remove links and copies files

		Options:
			-h, --help                  Show this.
			--version                   Show version.
			-v, --verbose               Enable verbose output.
			-f, --force <mode>          Force, will delete existing files, specify to wether prioritizes local or sync files. [local | sync]
			-c, --config <file>         Specify config file location, defaults to ./config.taml
			-C, --compression <method>  Specify compression algorithm, overwriting config.taml [fpaq]
			-l, --location <dir>        Specify directory to sync files to, overwrites config.taml

		Please report bugs at https://www.github.com/epicstuff/konsync/issues
	''').replace('\t', '    ')
	return docopt.docopt(doc, argv, version=VERSION)

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

	# parse command line arguments
	args = _get_parser()
	args = Dict({'compression': args['--compression'], 'config': args['--config'], 'force': args['--force'], 'location': args['--location'], 'verbose': args['--verbose'], 'command': args['<command>']})

	# set log level based on verbose (version)
	if args.verbose:
		log.setLevel('DEBUG')
	else:
		log.setLevel('INFO')
	if args.command in {'sync', 's'}:
		sync(args.config, args.location, args.version, args.force)
	elif args.command in {'export', 'e'}:
		export(args.config, args.location, args.compression, args.version)
	elif args.command in {'import', 'i'}:
		...
	elif args.command in {'remove', 'r'}:
		...
	elif args.version:
		print(VERSION)
	else:
		raise Exception('TODO: look into this')


if __name__ == '__main__':
	main()
