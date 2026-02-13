'''funcs module contains all the functions for konsync.'''

import logging
import os
import shutil
from os import system as run
from pathlib import Path

from epicstuff import Dict
from rich.traceback import install
from send2trash import send2trash, TrashPermissionError
from taml import taml

from konsync.consts import CONFIG_FILE
from konsync.parse import TOKEN_SYMBOL, parse_functions, parse_keywords, tokens

log = logging.getLogger(__name__)
logging.basicConfig()


def exception_handler(verbose: bool = False) -> None:
	install(width=os.get_terminal_size().columns, show_locals=verbose)


def read_config(config_file: Path = CONFIG_FILE) -> dict:
	'''Reads the config file and parses it.

	Args:
		config_file: path to the config file

	'''
	def convert_none_to_empty_list(data):
		if isinstance(data, list):
			data[:] = [convert_none_to_empty_list(i) for i in data]
		elif isinstance(data, dict):
			for k, v in data.items():
				data[k] = convert_none_to_empty_list(v)
		return [] if data is None else data

	config = taml.load(config_file)

	parse_keywords(tokens, TOKEN_SYMBOL, config)
	parse_functions(tokens, TOKEN_SYMBOL, config)

	# in some cases config.yaml may contain nothing in "entries". Yaml parses
	# these as NoneType which are not iterable which throws an exception
	# we can convert all None-Entries into empty lists recursively so they
	# are simply skipped in loops later on
	return Dict(convert_none_to_empty_list(config))


def sync(config_file: Path | None = None, verbose: bool = False, force: bool | str = False) -> None:
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
		sync_dir = Path(config.settings.target.root)
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
								run(f'rm -r "{source}"')
							break
						else:
							log.warning(f'{source} is a symlink that (probably) doesn\'t point to sync location, might want to look into that')
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
						run(f'rm -r "{source}"')
				else:
					source.parent.mkdir(parents=True, exist_ok=True)
				if run(f'ln -s "{dest}" "{source}"') != 0:
					log.error('something seems to have gone wrong')
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
	def download(zpaq=False) -> bool:
		log.fatal('download has not yet been implemented, go and manualy install fpaq')
		log.info('https://github.com/fcorbelli/zpaqfranz')
		log.fatal('Either zpaqfranz or zpaq needs to be installed or present in working directory')
		return False
	# load config
	config: Dict = read_config(config_file or CONFIG_FILE)
	try:
		export_dir: Path = Path(config.settings.target.root)
		export_name = Path(config.settings.target.export_name)
	except TypeError:
		log.fatal('A sync dir (or export name) must be specified')
		return
	settings = config.settings.compression
	config = config.export
	# compressing the files
	if compression == 'fpaq':
		# try to find fpaq executable
		if run('zpaqfranz > /dev/null') == 0:  # trunk-ignore(bandit/B605,ruff/S605,ruff/S607)
			compression = 'zpaqfranz'
		elif run('./zpaqfranz > /dev/null') == 0:  # trunk-ignore(bandit/B605,ruff/S605,ruff/S607)
			compression = './zpaqfranz'
		elif run('zpaq > /dev/null') == 256:  # trunk-ignore(bandit/B605,ruff/S605,ruff/S607)
			compression = 'zpaq'
		elif run('./zpaq > /dev/null') == 256:  # trunk-ignore(bandit/B605,ruff/S605,ruff/S607)
			compression = './zpaq'
		# if fpaq is not installed
		if compression == 'fpaq':
			# prompt to install fpaq/zpaq, if no download, return  # trunk-ignore(ruff/ERA001)
			if not download(True):
				return
			# if zpaq is installed but fpaq is not
		elif compression in ('zpaq', './zpaq'):
			log.debug('I would recomend using zpaqfranz instead of zpaq')
		# fpaq or zpaq installed
		# get list of all files to compress
		files = []
		for section in config:
			location: Path = Path(config[section].location)
			# for each entry
			for entry in config[section].entries:
				source: Path = location / entry
				# if the file/folder exists in local location
				if source.exists():
					files.append(source)
		# compress files
		log.info('Archiving files. This might take a while')
		command = f'{compression} a \
			"{export_dir / f"{export_name}-????.zpaq"}" \
			{" ".join([f"\"{file}\"" for file in files])} \
			-m{settings.level} \
			{settings.args or "-backupxxh3"}'.replace('\t', '')
		log.debug(f'running: {command}')  # trunk-ignore(ruff/G004,pylint/W1203)
		# print('\033[90m')
		if run(command) == 0:
			log.info(f'Successfully exported to {export_dir / "knsn.zpaq"}')
		else:
			log.warning('Something seems to have gone wrong')
	else:
		log.fatal('No supported compression method specified')
		return


# def remove(profile_name, profile_list, profile_count):
# 	'''Removes the specified profile.

# 	Args:
# 		profile_name: name of the profile to be removed
# 		profile_list: the list of all created profiles
# 		profile_count: number of profiles created

# 	'''

# 	# assert
# 	assert profile_count != 0, 'No profile saved yet.'
# 	assert profile_name in profile_list, 'Profile not found.'

# 	# run
# 	log('removing profile...')
# 	shutil.rmtree(os.path.join(PROFILES_DIR, profile_name))
# 	log('removed profile successfully')


# def import_profile(path):
# 	'''This will import an exported profile.

# 	Args:
# 		path: path of the `.knsv` file
# 	'''

# 	# assert
# 	assert (
# 		is_zipfile(path) and path[-5:] == EXPORT_EXTENSION
# 	), 'Not a valid konsync file'
# 	item = os.path.basename(path)[:-5]
# 	assert not os.path.exists(
# 		os.path.join(PROFILES_DIR, item)
# 	), 'A profile with this name already exists'

# 	# run
# 	log('Importing profile. It might take a minute or two...')

# 	item = os.path.basename(path).replace(EXPORT_EXTENSION, '')

# 	temp_path = os.path.join(KONSYNC_DIR, 'temp', item)

# 	with ZipFile(path, 'r') as zip_file:
# 		zip_file.extractall(temp_path)

# 	config_file_location = os.path.join(temp_path, 'conf.yaml')
# 	konsync_config = read_konsync_config(config_file_location)

# 	profile_dir = os.path.join(PROFILES_DIR, item)
# 	copy(os.path.join(temp_path, 'save'), profile_dir)
# 	shutil.copy(os.path.join(temp_path, 'conf.yaml'), profile_dir)

# 	for section in konsync_config['export']:
# 		location = konsync_config['export'][section]['location']
# 		path = os.path.join(temp_path, 'export', section)
# 		mkdir(path)
# 		for entry in konsync_config['export'][section]['entries']:
# 			source = os.path.join(path, entry)
# 			dest = os.path.join(location, entry)
# 			log(f'Importing "{entry}"...')
# 			if os.path.exists(source):
# 				if os.path.isdir(source):
# 					copy(source, dest)
# 				else:
# 					shutil.copy(source, dest)

# 	shutil.rmtree(temp_path)

# 	log('Profile successfully imported!')


# def wipe():
# 	'''Wipes all profiles.'''
# 	confirm = input('This will wipe all your profiles. Enter "WIPE" To continue: ')
# 	if confirm == 'WIPE':
# 		shutil.rmtree(PROFILES_DIR)
# 		log('Removed all profiles!')
# 	else:
# 		log('Aborting...')
