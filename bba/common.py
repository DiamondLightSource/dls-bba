"""This file contains functions and classes used in both slow and fast BBA."""
from abc import ABC, abstractmethod
from typing import NamedTuple, Dict, Any, Tuple
from dataclasses import dataclass
from cothread.catools import caget, caput
import scipy.io as io
from time import sleep
from subprocess import run
import pytac
from statistics import mean


PlaneValues = NamedTuple("PlaneValues", [("index", int), ("axis", str), ("corrector", str), ("kick", str)])
PLANE_VALUES = {
    "HORIZONTAL": PlaneValues(0, "X", "HSTR", "x_kick"),
    "VERTICAL": PlaneValues(1, "Y", "VSTR", "y_kick")}


class Algorithm(ABC):
    def __init__(self, accelerator):
        self._accelerator = accelerator

    @abstractmethod
    def configure(self, *args, **kwargs):
        pass

    @abstractmethod
    def run(self, quad, plane_dict):
        pass

    @abstractmethod
    def run(self, element, plane_info, max_orbit) -> RawData:
        # This fbba/sbba specifc -> save into a Data object
        raw_data = {}
        return RawData(raw_data)

    @abstractmethod
    def analyse_data(self, data, plot_output = False, *args, **kwargs):
        pass

    @abstractmethod
    def apply_results(self):
        pass