import logging as log
import os
from abc import ABC, abstractmethod

from pytac.element import EpicsElement

from dls_bba.components import Components
from dls_bba.datatypes import CalculatedOffset, RawData, Results
from dls_bba.lattice import ORIGIN_SUFFIXES, Lattice


class Algorithm(ABC):
    def __init__(self, lattice: Lattice):
        self._lattice = lattice

    @abstractmethod
    def run(self, component_pair: list[Components]) -> RawData:
        pass

    @abstractmethod
    def analyse(self, rawdata: RawData) -> Results:
        pass


def calculate_quad_setpoints(lattice: Lattice, quadrupole: EpicsElement):
    """"""
    quad_step_percent = lattice.config["QUADRUPOLE_STEP_PERCENT"]

    quad_setpoint = lattice.get_quad_setpoint(quadrupole)
    quad_step = quad_setpoint * quad_step_percent
    quad_start_high = quad_setpoint + (2 * quad_step)
    quad_high = quad_setpoint + quad_step
    quad_low = quad_setpoint - quad_step
    return quad_start_high, quad_high, quad_low, quad_setpoint


def get_slow_bba_corrector_steps(lattice: Lattice, components: Components):
    """"""
    setpoint = lattice.get_corrector_setpoint(components)
    step = lattice.corrector_kick(components)
    corrector_steps = [
        setpoint + step,
        setpoint + (step / 2),
        setpoint,
        setpoint - (step / 2),
        setpoint - step,
    ]
    return corrector_steps
