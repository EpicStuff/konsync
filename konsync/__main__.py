'''konsync.

A simple and powerful utility for managing your dotfiles.

Usage:
	konsync <command> [options...]
	konsync -h, --help
	konsync --version

Commands:
	sync, s                Setup sync based on current config
	export, e              Export and compress files specified in config
	import, i              Import files that were exported
	unsync, u              Turn symlinks back into normal files

Options:
	-h, --help             Show this.
	--version              Show version.
	-v, --verbose          Enable verbose output.
	-f, --force <mode>     Force, will delete existing files, specify to whether prioritizes local or sync files. [local | sync]
	-c, --config <file>    Specify config file location, defaults to ./config.taml

Please report bugs at https://www.github.com/epicstuff/konsync/issues
'''

import os, shutil
from importlib.resources import files
from pathlib import Path

from docopt import docopt
from epicstuff import Dict
from loguru import logger as log

from .consts import CONFIG_FILE, VERSION
from .funcs import exception_handler, export, import_, setup_logging, sync, unsync


def main() -> None:
	'''Handle the arguments and options.'''
	# parse command line arguments
	args = docopt(__doc__, version=VERSION)  # pyright: ignore[reportArgumentType]
	args = Dict({'config': args['--config'], 'force': args['--force'], 'verbose': args['--verbose'], 'command': args['<command>']})
	if len(args.config) > 1 or len(args.force) > 1:
		raise Exception('Only pass flag once.')
	if args.config: args.config = args.config[-1]
	if args.force: args.force = args.force[-1]

	# configure logging
	setup_logging(verbose=bool(args.verbose))
	exception_handler(args.verbose)

	# create copy of config file if it doesn't exist
	if not Path(CONFIG_FILE).exists():
		if os.path.expandvars('$XDG_CURRENT_DESKTOP') == 'KDE':
			default_config_path = str(files('konsync') / 'conf_kde.taml')
			shutil.copy(default_config_path, CONFIG_FILE)
		else:
			default_config_path = str(files('konsync') / 'conf_other.taml')
			shutil.copy(default_config_path, CONFIG_FILE)
		log.info('created config file')

	# execute command
	if args.command in {'sync', 's'}:
		sync(args.config, args.force)
	elif args.command in {'export', 'e'}:
		export(args.config, args.verbose)
	elif args.command in {'import', 'i'}:
		import_(args.config, args.verbose, args.force)
	elif args.command in {'unsync', 'u'}:
		unsync(args.config, args.force)
	else:
		# this shouldn't happen, i don't think
		raise Exception('TODO: look into this')


if __name__ == '__main__':
	main()
