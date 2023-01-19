from importlib.metadata import version

__version__ = version("dls-bba")
del version

__all__ = ["__version__"]
