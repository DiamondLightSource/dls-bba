from abc import ABC, abstractmethod

from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
from dls_bba.machine import Machine


class Algorithm(ABC):
    def __init__(self, machine: Machine):
        self._machine = machine

    @abstractmethod
    def run(self, component_pair: list[Components]) -> RawData:
        pass

    @abstractmethod
    def analyse(self, rawdata: RawData) -> Results:
        pass
