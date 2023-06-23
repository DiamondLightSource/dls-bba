from abc import ABC, abstractmethod

from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
from dls_bba.machine import Lattice


class Algorithm(ABC):
    def __init__(self, lattice: Lattice):
        self._lattice = lattice

    @abstractmethod
    def run(self, component_pair: list[Components]) -> RawData:
        pass

    @abstractmethod
    def analyse(self, rawdata: RawData) -> Results:
        pass
