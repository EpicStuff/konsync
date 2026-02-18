# ruff: noqa: S603
'''funcs module contains all the functions for konsync.'''

import logging, os, shlex, shutil, tempfile
from pathlib import Path
# from os import system as run
from subprocess import PIPE, STDOUT, run
from typing import Literal

from epicstuff import Dict
from rich.traceback import install
from send2trash import TrashPermissionError, send2trash
from taml import taml

from .consts import CONFIG_FILE
from .parse import TOKEN_SYMBOL, parse_functions, parse_keywords, tokens

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def exception_handler(verbose: bool = False) -> None:
	install(width=os.get_terminal_size().columns, show_locals=verbose)
def read_config(config_file: Path = CONFIG_FILE) -> Dict:
	'''Read the config file and parses it.

	Args:
		config_file: path to the config file

	'''
	def convert_none_to_empty_list(data: dict | list) -> dict | list:
		if isinstance(data, list):
			data[:] = [convert_none_to_empty_list(i) for i in data]
		elif isinstance(data, Dict):
			for k, v in data.items():
				data[k] = convert_none_to_empty_list(v)
		return [] if data is None else data

	config: Dict = taml.load(config_file)

	parse_keywords(tokens, TOKEN_SYMBOL, config)
	parse_functions(tokens, TOKEN_SYMBOL, config)

	# in some cases config.taml may contain nothing in "entries". Yaml parses
	# these as NoneType which are not iterable which throws an exception
	# we can convert all None-Entries into empty lists recursively so they
	# are simply skipped in loops later on
	return Dict(convert_none_to_empty_list(config))
def copy(source: Path, dest: Path, overwrite: bool = False) -> None:
	'''Copy file or directory from source to dest.

	- If dest is an existing directory, files/directories are merged.
	- If dest is an existing file, files/directories are skipped or overwritten.
	'''
	if not source.exists():
		raise FileNotFoundError(f'Source not found: {source}')

	if source.is_file():
		# Determine final destination: if dest is a directory, place file inside it
		target = dest / source.name if dest.is_dir() else dest
		if target.exists() and not overwrite:
			log.warning('File %s already exists, skipping. Use --force sync to overwrite.', target)
			return
		target.parent.mkdir(parents=True, exist_ok=True)
		log.debug('%s --> %s', source, target)
		shutil.copy2(source, target)
	elif source.is_dir():
		if dest.exists() and not dest.is_dir():
			if overwrite:
				log.warning('%s already exists as a file, overwriting with directory.', dest)
				dest.unlink()
			else:
				log.warning('%s already exists, skipping. Use --force sync to overwrite.', dest)
				return
		dest.mkdir(parents=True, exist_ok=True)
		for item in source.iterdir():
			copy(item, dest / item.name, overwrite)
	else:
		raise ValueError(f'Unsupported source type: {source}')

def find_executable(name: str) -> Path:
	'''Find the path of an executable.

	Args:
		name: name of the executable

	'''
	if name == 'fpaq':
		possible_names = ['zpaqfranz', 'zpaq']
	else:
		# for the other compression algorithms that might be added in the future
		raise ValueError(f'unsupported executable: {name}')

	# loop through the possible names and check path and ./
	for candidate in possible_names:
		# check path
		resolved = shutil.which(candidate)
		if resolved:
			break
		# check ./
		resolved = shutil.which(str(Path.cwd() / candidate))
		if resolved:
			break

	# if the executable is not found, try to download it
	if not resolved:  # pyright: ignore[reportPossiblyUnboundVariable]
		resolved = download(name)
		# if failed to download, raise error
		if not resolved:
			raise FileNotFoundError(f'{name} not found')

	if name == 'fpaq' and resolved and candidate == 'zpaq':  # pyright: ignore[reportPossiblyUnboundVariable]
		log.debug('I would recommend using zpaqfranz instead of zpaq')
	return Path(resolved)
def download(executable: str) -> Literal[False] | str:
	'Download the specified executable and return its path or False if failed.'
	if executable == 'fpaq':
		log.fatal('download has not yet been implemented, go and manually install fpaq')
		log.info('https://github.com/fcorbelli/zpaqfranz')
		log.fatal('Either zpaqfranz or zpaq needs to be installed or present in working directory')
	else:
		raise NotImplementedError
	return False

def sync(config_file: Path | None = None, verbose: bool = False, force: bool | str = False) -> None:  # noqa: C901, PLR0912, PLR0915
	'''Sync specified files with sync_dir.

	Args:
		config_file: location of config file
		sync_dir: directory to sync files to
		verbose: should errors be verbose
		force: force overwrite existing files

	'''
	exception_handler(verbose)

	# load config
	config: Dict = read_config(config_file or CONFIG_FILE)
	errored = False
	# run
	log.info('syncing...')
	try:
		sync_dir = Path(config.settings.target.location)
	except TypeError:
		log.fatal('A sync dir must be specified')
		return
	# sync files
	config = config.sync
	log.info('removing existing symlinks')
	for section in config:
		location: Path = Path(config[section].location)
		folder: Path = sync_dir / section
		folder.mkdir(parents=True, exist_ok=True)
		# for each entry
		for entry in config[section].entries:
			source: Path = location / entry
			dest: Path = folder / entry
			# if the file/folder exists in local location
			while True:
				if source.exists() or source.is_symlink():
					if source.is_symlink():
						# if is a symlink and exists in sync location
						if dest.exists():
							log.debug('removing symlink %s', source)
							try:
								send2trash(source)
							except TrashPermissionError:
								if force:
									source.unlink()
								else:
									log.exception('Failed to trash %s, skipping.', source)
									errored = True
							break
						log.warning("%s is a symlink that (probably) doesn't point to sync location, might want to look into that", source)
					# move the file/folder to the sync location
					log.debug('moving %s to %s', source, dest)
					if dest.exists():
						if force != 'local':
							log.warning('File %s already exists, skipping. Use --force local to overwrite.', dest)
							break
						log.warning('File %s already exists, deleting.', dest)
						send2trash(dest)
					else:
						dest.parent.mkdir(parents=True, exist_ok=True)
					shutil.move(source, dest)
				break
			# if the file/folder exist in sync location
			if dest.exists():
				# symlink the file/folder to the local location
				log.info('%s >>> %s', dest, source)
				if source.exists():
					if force != 'sync':
						log.warning('File %s already exists, skipping. Use --force sync to overwrite.', source)
						continue
					log.warning('File %s already exists, deleting.', source)
					try:
						send2trash(source)
					except TrashPermissionError:
						if force:
							try:
								source.unlink()
							except IsADirectoryError:
								shutil.rmtree(source)
						else:
							log.exception('Failed to trash %s, skipping.', source)
							errored = True
				else:
					source.parent.mkdir(parents=True, exist_ok=True)

				try:
					source.symlink_to(dest)
				except Exception:
					log.exception('something seems to have gone wrong')
					errored = True

	if not errored:
		log.info('Files synced successfully')
	log.info('Log-out and log-in to see the changes completely')
def export(config_file: Path | None = None, verbose: bool = False) -> None:
	'''Will export files as `.knsv` to the sync directory.

	Args:
		config_file: location of config file
		sync_dir: directory to sync files to
		compression: compression algorithm used, currently only fpaq supported
		verbose: should errors be verbose

	'''  # TODO: implement export when sync.export = True
	exception_handler(verbose)  # setup exception handler

	# load config
	config: Dict = read_config(config_file or CONFIG_FILE)
	try:
		export_path = Path(config.settings.target.location) / Path(config.settings.target.export_name)
	except TypeError:
		log.fatal('A sync dir and export name must be specified')
		return
	c_s = config.settings.compression  # compression settings
	config = config.export
	# compressing the files
	if c_s.algorithm == 'fpaq':
		# try to find fpaq executable
		binary = find_executable('fpaq')
		# get list of all files to compress
		files: list[str] = []
		for section in config:
			location: Path = Path(config[section].location)
			# for each entry
			for entry in config[section].entries:
				source: Path = location / entry
				# if the file/folder exists in local location
				if source.exists():
					files.append(str(source))
		# compress files
		log.info('Archiving files. This might take a while')
		command = [
			str(binary), 'a', str(export_path),
			*files,
			f'-m{c_s.level}', (c_s.args or '-backupxxh3'),
		]
		log.debug('running: %s', shlex.join(command))
		if run(command).returncode == 0:
			log.info('Successfully exported to %s', export_path)
		else:
			log.warning('Something seems to have gone wrong')
	else:
		log.fatal('No supported compression method specified')
		return
def import_(config_file: Path | None = None, verbose: bool = False, force: bool = False) -> None:
	'''Import an exported profile.

	Args:
		config_file: location of config file
		force: should existing files be overwritten
		verbose: should errors be verbose

	'''
	exception_handler(verbose)  # setup exception handler

	# load config
	config: Dict = read_config(config_file or CONFIG_FILE)
	# check if location, export_name have been specified and exists
	try:
		if Path(config.settings.target.export_name).is_absolute():
			import_name = Path(config.settings.target.export_name)
		else:
			import_name = Path(config.settings.target.location) / config.settings.target.export_name
	except TypeError:
		log.fatal('A sync dir and import name must be specified')
		return

	# rest of settings
	c_s = config.settings.compression  # compression settings
	config = config.export

	if c_s.algorithm == 'fpaq':
		# get binary
		binary = find_executable('fpaq')
		# check if is valid archive
		out = run([binary, 't', import_name], stdout=PIPE, stderr=STDOUT, input='\n', text=True)
		if out.returncode != 0:
			log.fatal('Invalid archive or something seems to have gone wrong')
			log.info('fpaq output:\n%s', out.stdout)
			return
		# run
		log.info('Importing profile. It might take a minute or two...')

		temp_dir = Path(tempfile.mkdtemp(prefix='konsync-'))
		run([binary, 'x', import_name, '-to', temp_dir], text=True, check=True)

		# for each section in the export part of the config
		for section in config.values():
			location = Path(section.location)  # where the files should go
			assert location.is_absolute(), 'location must be an absolute path'
			path = temp_dir / location.relative_to(location.anchor)  # where the files are
			for entry in section.entries:
				source = path / entry
				dest = location / entry
				if source.exists():
					log.info('Importing "%s"...', dest)
					copy(source, dest, force)
	else:
		log.fatal('No supported compression method specified')
		return
	shutil.rmtree(temp_dir)
	log.info('Profile successfully imported!')
def unsync(config_file: Path | None, verbose: bool = False) -> None:
	'''Turn symlinks back into normal files.

	Args:
		config_file: location of config file
		verbose: should errors be verbose

	'''
	exception_handler(verbose)

	# load config
	config = read_config(config_file or CONFIG_FILE)
	log.info('unsyncing...')
	# for each section
	for section in config:
		location = Path(config[section].location)
		# for each entry
		for entry in config[section].entries:
			path: Path = location / entry
			# if the file/folder in the local location is symlink
			if path.is_symlink():
				target = path.resolve()
				if target.exists():
					log.debug('Unsyncing %s...', path)
					path.unlink()
					shutil.copy2(target, path)
	log.info('Files unsynced successfully')
