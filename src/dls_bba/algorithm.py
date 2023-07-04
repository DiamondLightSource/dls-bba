from abc import ABC, abstractmethod
from typing import List

from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
from dls_bba.lattice import Lattice


class Algorithm(ABC):
    def __init__(self, lattice: Lattice):
        self._lattice = lattice

    @abstractmethod
    def run(self, component_pair: List[Components]) -> RawData:
        pass

    @abstractmethod
    def analyse(self, rawdata: RawData) -> Results:
        pass
