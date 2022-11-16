"""This file contains functions and classes used in both slow and fast BBA."""

from typing import NamedTuple

PlaneValues = NamedTuple("PlaneValues", [("index", int), ("axis", str), ("corrector", str), ("kick", str)])
PLANE_VALUES = {
    "HORIZONTAL": PlaneValues(0, "X", "HSTR", "x_kick"),
    "VERTICAL": PlaneValues(1, "Y", "VSTR", "y_kick")}

class Algorithm:
    def setup():
        raise NotImplementedError()

    def config():
        raise NotImplementedError()

    def run_bba():
        raise NotImplementedError()   

