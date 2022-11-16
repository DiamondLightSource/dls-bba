"""This file contains functions and classes used in both slow and fast BBA."""
from abc import ABC, abstractmethod
from typing import NamedTuple

PlaneValues = NamedTuple("PlaneValues", [("index", int), ("axis", str), ("corrector", str), ("kick", str)])
PLANE_VALUES = {
    "HORIZONTAL": PlaneValues(0, "X", "HSTR", "x_kick"),
    "VERTICAL": PlaneValues(1, "Y", "VSTR", "y_kick")}


class Algorithm(ABC):

    @abstractmethod
    def configure(self, **kwargs):
        pass

    @abstractmethod
    def run(self, quad, plane_dict):
        pass

    @abstractmethod
    def save_data(self):
        pass
    
    @abstractmethod
    def analyse_data(self):
        pass

    @abstractmethod
    def apply_results(self):
        pass