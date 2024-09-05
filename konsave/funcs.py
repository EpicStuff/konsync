'''
This module contains all the functions for konsync.
'''

import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from rich.traceback import install
from send2trash import send2trash

from konsync.consts import CONFIG_FILE, EXPORT_EXTENSION
from konsync.parse import TOKEN_SYMBOL, parse_functions, parse_keywords, tokens

log = logging.getLogger(__name__)
logging.basicConfig()

try:
	from taml import taml
except ModuleNotFoundError as error:
	raise ModuleNotFoundError(
		'Please install the module taml using pip: \n pip install taml'
	) from error


def exception_handler(verbose) -> None:
	install(width=os.get_terminal_size().columns, show_locals=verbose)


def read_config(config_file=CONFIG_FILE) -> dict:
	'''Reads the config file and parses it.

	Args:
		config_file: path to the config file
	'''
	config = taml.load(config_file)

	parse_keywords(tokens, TOKEN_SYMBOL, config)
	parse_functions(tokens, TOKEN_SYMBOL, config)

	# in some cases config.yaml may contain nothing in "entries". Yaml parses
	# these as NoneType which are not iterable which throws an exception
	# we can convert all None-Entries into empty lists recursively so they
	# are simply skipped in loops later on
	def convert_none_to_empty_list(data):
		if isinstance(data, list):
			data[:] = [convert_none_to_empty_list(i) for i in data]
		elif isinstance(data, dict):
			for k, v in data.items():
				data[k] = convert_none_to_empty_list(v)
		return [] if data is None else data

	return convert_none_to_empty_list(config)


def sync(config_file=None, sync_dir=None, verbose=False, force=False):
	'''Saves necessary config files in ~/.config/konsync/profiles/<name>.

	Args:
		name: name of the profile
		profile_list: the list of all created profiles
		force: force overwrite already created profile, optional
	'''

	exception_handler(verbose)

	# run
	log.info('syncing...')
	# load config
	config = read_config(config_file or CONFIG_FILE)
	sync_dir = sync_dir or config['sync_dir']['placeholder']['location']
	# check if sync location is specified
	assert sync_dir, 'No sync location specified'
	# sync files
	config = config['save']
	for section in config:
		location = config[section]['location']
		folder = os.path.join(sync_dir, section)
		Path(folder).mkdir(parents=True, exist_ok=True)
		# for each entry
		for entry in config[section]['entries']:
			source = os.path.join(location, entry)
			dest = os.path.join(folder, entry)
			# if the file/folder exists in local location
			while True:
				if os.path.exists(source):
					if os.path.islink(source.rstrip('/')):
						log.info('removing symlink %s', source)
						send2trash(source)
						break
					# move the file/folder to the sync location
					log.debug('moving %s to %s', source, dest)
					if os.path.exists(dest):
						if force != 'local':
							log.warning('File %s already exists, skipping. Use --force local to overwrite.', dest)
							break
						else:
							log.warning('File %s already exists, deleting.', dest)
							send2trash(dest)
					shutil.move(source, dest)
					break
			# if the file/folder exist in sync location
			if os.path.exists(dest):
				# symlink the file/folder to the local location
				log.debug('symlinking %s to %s', dest, source)
				if os.path.exists(source):
					if force != 'sync':
						log.warning('File %s already exists, skipping. Use --force sync to overwrite.', source)
						continue
					else:
						log.warning('File %s already exists, deleting.', source)
						send2trash(source)
				subprocess.run(['ln', '-s', dest, source.rstrip('/')], check=True)

	log.info('Profile saved successfully!')


def apply_profile(profile_name, profile_list, profile_count):
	'''Applies profile of the given id.

	Args:
		profile_name: name of the profile to be applied
		profile_list: the list of all created profiles
		profile_count: number of profiles created
	'''

	# assert
	assert profile_count != 0, 'No profile saved yet.'
	assert profile_name in profile_list, 'Profile not found :('

	# run
	profile_dir = os.path.join(PROFILES_DIR, profile_name)

	log('copying files...')

	config_location = os.path.join(profile_dir, 'conf.yaml')
	profile_config = read_konsync_config(config_location)['save']
	for name in profile_config:
		location = os.path.join(profile_dir, name)
		copy(location, profile_config[name]['location'])

	log(
		'Profile applied successfully! Please log-out and log-in to see the changes completely!'
	)


def remove(profile_name, profile_list, profile_count):
	'''Removes the specified profile.

	Args:
		profile_name: name of the profile to be removed
		profile_list: the list of all created profiles
		profile_count: number of profiles created
	'''

	# assert
	assert profile_count != 0, 'No profile saved yet.'
	assert profile_name in profile_list, 'Profile not found.'

	# run
	log('removing profile...')
	shutil.rmtree(os.path.join(PROFILES_DIR, profile_name))
	log('removed profile successfully')


def export(profile_name, profile_list, profile_count, archive_dir, archive_name, force):
	'''It will export the specified profile as a `.knsv` to the specified directory.
	   If there is no specified directory, the directory is set to the current working directory.

	Args:
		profile_name: name of the profile to be exported
		profile_list: the list of all created profiles
		profile_count: number of profiles created
		directory: output directory for the export
		force: force the overwrite of existing export file
		name: the name of the resulting archive
	'''

	# assert
	assert profile_count != 0, 'No profile saved yet.'
	assert profile_name in profile_list, 'Profile not found.'

	# run
	profile_dir = os.path.join(PROFILES_DIR, profile_name)

	if archive_name:
		profile_name = archive_name

	if archive_dir:
		export_path = os.path.join(archive_dir, profile_name)
	else:
		export_path = os.path.join(os.getcwd(), profile_name)

	# Only continue if export_path, export_path.ksnv and export_path.zip don't exist
	# Appends date and time to create a unique file name
	if not force:
		while True:
			paths = [f'{export_path}', f'{export_path}.knsv', f'{export_path}.zip']
			if any(os.path.exists(path) for path in paths):
				time = 'f{:%d-%m-%Y:%H-%M-%S}'.format(datetime.now())
				export_path = f'{export_path}_{time}'
			else:
				break

	# compressing the files as zip
	log('Exporting profile. It might take a minute or two...')

	profile_config_file = os.path.join(profile_dir, 'conf.yaml')
	konsync_config = read_konsync_config(profile_config_file)

	export_path_save = mkdir(os.path.join(export_path, 'save'))
	for name in konsync_config['save']:
		location = os.path.join(profile_dir, name)
		log(f"Exporting '{name}'...")
		copy(location, os.path.join(export_path_save, name))

	konsync_config_export = konsync_config['export']
	export_path_export = mkdir(os.path.join(export_path, 'export'))
	for name in konsync_config_export:
		location = konsync_config_export[name]['location']
		path = mkdir(os.path.join(export_path_export, name))
		for entry in konsync_config_export[name]['entries']:
			source = os.path.join(location, entry)
			dest = os.path.join(path, entry)
			log(f'Exporting "{entry}"...')
			if os.path.exists(source):
				if os.path.isdir(source):
					copy(source, dest)
				else:
					shutil.copy(source, dest)

	shutil.copy(CONFIG_FILE, export_path)

	log('Creating archive')
	shutil.make_archive(export_path, 'zip', export_path)

	shutil.rmtree(export_path)
	shutil.move(export_path + '.zip', export_path + EXPORT_EXTENSION)

	log(f'Successfully exported to {export_path}{EXPORT_EXTENSION}')


def import_profile(path):
	'''This will import an exported profile.

	Args:
		path: path of the `.knsv` file
	'''

	# assert
	assert (
		is_zipfile(path) and path[-5:] == EXPORT_EXTENSION
	), 'Not a valid konsync file'
	item = os.path.basename(path)[:-5]
	assert not os.path.exists(
		os.path.join(PROFILES_DIR, item)
	), 'A profile with this name already exists'

	# run
	log('Importing profile. It might take a minute or two...')

	item = os.path.basename(path).replace(EXPORT_EXTENSION, '')

	temp_path = os.path.join(KONSYNC_DIR, 'temp', item)

	with ZipFile(path, 'r') as zip_file:
		zip_file.extractall(temp_path)

	config_file_location = os.path.join(temp_path, 'conf.yaml')
	konsync_config = read_konsync_config(config_file_location)

	profile_dir = os.path.join(PROFILES_DIR, item)
	copy(os.path.join(temp_path, 'save'), profile_dir)
	shutil.copy(os.path.join(temp_path, 'conf.yaml'), profile_dir)

	for section in konsync_config['export']:
		location = konsync_config['export'][section]['location']
		path = os.path.join(temp_path, 'export', section)
		mkdir(path)
		for entry in konsync_config['export'][section]['entries']:
			source = os.path.join(path, entry)
			dest = os.path.join(location, entry)
			log(f'Importing "{entry}"...')
			if os.path.exists(source):
				if os.path.isdir(source):
					copy(source, dest)
				else:
					shutil.copy(source, dest)

	shutil.rmtree(temp_path)

	log('Profile successfully imported!')


def wipe():
	'''Wipes all profiles.'''
	confirm = input('This will wipe all your profiles. Enter "WIPE" To continue: ')
	if confirm == 'WIPE':
		shutil.rmtree(PROFILES_DIR)
		log('Removed all profiles!')
	else:
		log('Aborting...')
