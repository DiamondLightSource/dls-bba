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

ORIGIN_SUFFIXES = {
    "BBA": ":CF:BBA_{axis}_S",
    "BCD": ":CF:BCD_{axis}_S",
    "GOLDEN": ":CF:GOLDEN_{axis}_S"}


@dataclass
class RawData:
    raw_data: Dict[str, Any]
    algorithm: str
    metadata: Dict[str, Any]

    # TODO: asdict, make all shared attributes not in metadata.

    def save(self, time_prefix, filepath = "data"):
        dct = {'raw_data': self.raw_data, 'algorithm': self.algorithm, 'metadata': self.metadata}
        filename = "{}/{}-{}-{}-rawdata".format(filepath, time_prefix, self.metadata["bpm"][0], self.metadata["plane"].axis)
        io.savemat(filename, dct, oned_as="row")
        print(f"Saved data as {filename}")

    @classmethod
    def from_file(cls, filename):
        dct = io.loadmat(filename, squeeze_me=True)
        return cls(dct['raw_data'], dct['algorithm'], dct['metadata'])


@dataclass
class Results:
    results: Dict[str, Any]
    bpm_pv_prefix: str
    metadata: Dict[str, Any]

    def save(self, time_prefix, filepath = "data"):
        dct = {'results': self.results, 'bpm_pv_prefix': self.bpm_pv_prefix, 'metadata': self.metadata}
        filename = "{}/{}-{}-{}-results".format(filepath, time_prefix, self.metadata["bpm"][0], self.metadata["plane"].axis)
        io.savemat(filename, dct, oned_as="row")
        print(f"Saved data as {filename}")
    
    @classmethod
    def from_file(cls, filename):
        dct = io.loadmat(filename, squeeze_me=True)
        return cls(dct['results'], dct['bpm_pv_prefix'], dct['metadata'])


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