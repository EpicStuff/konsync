'''Setup module'''

from pathlib import Path

from setuptools import find_packages, setup


def _read_desc() -> str:
	'''Reads the README.md.

	Returns:
		str: Contents of README.md file.
	'''
	with open('README.md', 'r', encoding='utf-8') as desc:
		return desc.read()


def _read_reqs(path: Path) -> list[str]:
	'''Reads a pip requirement file.

	Args:
		path (Path): Path to pip requirements file.

	Returns:
		:type: list of str: List of dependency identifiers.
	'''
	with open(path, 'r', encoding='utf-8') as file:
		return file.readlines()


# Package requirements
_REQUIREMENTS: list[str] = _read_reqs(Path('requirements.txt'))
_REQUIREMENTS_DEV: list[str] = _read_reqs(Path('requirements_dev.txt'))

setup(
	name='konsync',
	use_scm_version=True,
	setup_requires=['setuptools_scm'],
	author='EpicStuff',
	author_email='EpicStuff@users.noreply.github.com',
	description='A program that lets you sync your Plasma configuration to a synced folder. (Seafile, Nextcloud, etc.)',
	long_description=_read_desc(),
	long_description_content_type='text/markdown',
	url='https://www.github.com/epicstuff/konsync/',
	packages=find_packages(),
	package_data={'config': ['conf.yaml']},
	include_package_data=True,
	python_requires='>=3.8',
	install_requires=_REQUIREMENTS,
	classifiers=[
		'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
		'Operating System :: POSIX',
		'Environment :: Console',
		'Intended Audience :: End Users/Desktop',
		'Programming Language :: Python',
	],
	entry_points={'console_scripts': ['konsync = konsync.__main__:main']},
)
