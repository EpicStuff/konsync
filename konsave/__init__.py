'''Top-level Konsync package.'''

from pkg_resources import DistributionNotFound, get_distribution


try:
	__version__ = get_distribution(__name__).version
except DistributionNotFound:
	# Package is not installed
	pass
