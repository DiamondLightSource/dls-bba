"""Beam Based Alignment

This module contains the functions to carry out
fast BBA or slow BBA alongside analysis functions.
"""

from importlib.metadata import version

__version__ = version("dls-bba")
del version

__all__ = ["__version__"]
