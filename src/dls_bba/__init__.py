"""Beam Based Alignment

This module contains the functions to carry out
fast BBA or slow BBA alongside analysis functions.
"""

import sys

if sys.version_info < (3, 8):
    from importlib_metadata import version  # noqa
else:
    from importlib.metadata import version  # noqa

__version__ = version("dls-bba")
del version

__all__ = ["__version__"]
