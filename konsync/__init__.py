'''Top-level Konsync package.'''

from contextlib import suppress

from pkg_resources import DistributionNotFound, get_distribution

with suppress(DistributionNotFound):
	__version__ = get_distribution(__name__).version
