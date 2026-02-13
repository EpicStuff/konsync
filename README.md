<!-- markdownlint-disable-next-line MD033 -->
<h1 align=center> Konsync (Sync Linux Customizations) </h1>
<!-- markdownlint-disable-next-line MD033 -->
<p align=center>A CLI program that will let you sync and export your Linux customizations with just one command! It officially supports KDE Plasma but it can be used on any other desktop environment!</p>

## Installation

Install from PyPI using uv
`uv tool install konsync`

Install from PyPI using pip  
`pip install konsync`

Install from PyPI using pipx  
`pipx install konsave`

## Usage

### Get Help

`konsync -h` or `konsync --help`

### Sync based on default config

`konsync -s` or `konsync --sync`.
You may need to log out and log in to see all the changes.

### Specify config file

`konsync -sc config.taml` or `konsync --sync --config config.taml`.
The default config file location is `~/.config/konsync.taml`

### Overwrite already existing files

`konsync -sf <local,sync>` or `konsync --sync --force <local|sync>`

### Remove files specified in the config from either local or sync folder

`konsync -r <local,sync>` or `konsync --remove <local|sync>`

### Export larger files/folders that you may not want stored without compression, see compression format for detailed behaviour

`konsync -e` or `konsync --export`

### Import exported archive from sync dir

`konsync -i` or `konsync --import`.
Note this will move existing files to the trash

### Import without trash

`konsync -if` or `konsync --export --force` will delete existing files instead to moving them to trash

### Open config with editors

`konsync --edit` will open the default config with your default editor

### Show current version

`konsync -v` or `konsync --version`

---

## Editing the configuration file

You can make changes to Konsync's configuration file according to your needs. Konsync will check for `./config.taml` by default unless a config file or sync location is specified.
For KDE Plasma users, the configuration file will be pre-configured.

### Format

The configuration file should be formatted in the following way:

```yaml
sync_dir:
	placeholder:  # this is required due to the way the parsing functions were written
		location:
save:
	name:
		location: "path/to/parent/directory"
		entries:
		# These are files to be backed up.
		# They should be present in the specified location.
			- file1
			- file2
			- folder1/
			- folder2/file3
export:
	# This includes files which will be exported with your profile.
	# They will not be saved but only be exported and imported.
	# These may include files like complete icon packs and themes..
	name:
		location: "path/to/parent/directory"
		entries:
			- file1
			- file2
```

### Adding more files/folders to backup

You can add more files/folders in the configuration file like this:

```yaml
save:
	another_name:
		location: "another/path/to/parent/directory"
		entries:
			- file1
```

### Using placeholders

You can use a few placeholders in the `location` of each entry in the configuration file. These are:
`$HOME`: the home directory
`$CONFIG_DIR`: refers to "$HOME/.config/"
`$SHARE_DIR`: refers to "$HOME/.local/share"
`$BIN_DIR`: refers to "$HOME/.local/bin"
`${ENDS_WITH="text"}`: for folders with different names on different computers whose names end with the same thing.  
The best example for this is the ".default-release" folder of firefox.  
`${BEGINS_WITH="text"}`: for folders with different names on different computers whose names start with the same thing.

```yaml
save:
	firefox:
		location: "$HOME/.mozilla/firefox/${ENDS_WITH='.default-release'}"
		entries:
			- chrome
```

---

## Contributing

Please read [CONTRIBUTION.md](https://github.com/epicstuff/konsync/blob/main/CONTRIBUTION.md) for info about contributing.

## License

This project uses GNU General Public License 3.0
