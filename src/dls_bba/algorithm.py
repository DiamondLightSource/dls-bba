import logging as log
from abc import ABC, abstractmethod

from cothread import Sleep

from dls_bba.datatypes import RawData, Results
from dls_bba.excite import TICKS_PER_SECOND
from dls_bba.lattice import ElementTuple

NETWORK_LAG_S = 0.5
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 0.5  # per amp
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * TICKS_PER_SECOND)


class Algorithm(ABC):
    def __init__(self, lattice):
        self._lattice = lattice

    @abstractmethod
    def run(self, elementtuple_pair):
        pass

    @abstractmethod
    def analyse(self):
        pass


class SlowBBA(Algorithm):
    def __init__(self, lattice):
        super().__init__(lattice)

    def run(self, elementtuple_pair: list[ElementTuple]):
        rawdata = {}
        metadata = {}
        metadata.update(self._lattice.config)

        for elementtuple in elementtuple_pair:
            for quad in elementtuple.quadrupoles:
                (
                    quad_start,
                    quad_high,
                    quad_low,
                    quad_sp,
                ) = self._lattice.calculate_quad_setpoints(
                    quad, self.quadrupole_step_percent
                )
                corrector_step_list = self._lattice.get_slow_bba_corrector_steps(
                    elementtuple.corrector
                )

                # Always overshoot the high quad step and work down and keep direction
                # consistent to mitigate unwanted hysteresis effects.
                # FYI correctors are significantly less prone to hysteresis effects.
                self._lattice.set_quad_setpoint(quad, quad_start)
                # TODO: If Cell 2 (DDBA) complete a full hysteresis cycle.
                pass

                for movement, quad_movement in [
                    ("High", quad_high),
                    ("Low", quad_low),
                ]:
                    self._lattice.set_quad_setpoint(quad, quad_movement)

                    for index, step in enumerate(corrector_step_list, start=1):
                        self._lattice.set_corrector_setpoint(
                            elementtuple.corrector, step
                        )
                        Sleep(0.1)  # Fixed time for orbit to stabilise.
                        measured_bpms = self._lattice.measure_bpms(elementtuple.axis)

                        key = f"{quad}_{movement}_{elementtuple.axis}_{index}"
                        rawdata[key] = measured_bpms

                        metadata[key] = {
                            "element_tuple": elementtuple,
                            "quad_start_high_low_sp": [
                                quad_start,
                                quad_high,
                                quad_low,
                                quad_sp,
                            ],
                            "corrector_steps": corrector_step_list,
                            "enabled_bpms": self._lattice.get_enabled_bpms(),
                        }

                    # Reset the corrector after the steps before moving the quadrupole.
                    self._lattice.set_corrector_setpoint(
                        elementtuple.corrector, corrector_step_list[2]
                    )
                # Reset Quad and Corrector once finished.
                self._lattice.set_corrector_setpoint(
                    elementtuple.corrector, corrector_step_list[2]
                )
                self._lattice.set_quad_setpoint(quad, quad_sp)
            # run feedbacks after that axis done.

        rawdata_object = RawData(rawdata, self.__name__, metadata)
        rawdata_object.save()
        return rawdata_object

    def analyse(self):
        pass


class FastBBA(Algorithm):
    def __init__(self, lattice):
        super().__init__(lattice)

    #     self.configure()

    # def configure(self):
    #     pass

    def run(self):
        pass

    def analyse(self):
        pass


class SimFastBBA(Algorithm):
    def __init__(self, lattice):
        super().__init__(lattice)

    #     self.configure()

    # def configure(self):
    #     pass

    def run(self):
        pass

    def analyse(self):
        pass
