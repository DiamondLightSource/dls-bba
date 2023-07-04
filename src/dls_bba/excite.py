from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List, Union

import numpy as np
from cothread.catools import caput

from dls_bba.components import Components
from dls_bba.faa import TICKS_PER_SECOND

if TYPE_CHECKING:
    from dls_bba.lattice import Lattice

NETWORK_LAG_S = 0.5
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 0.5  # Amps/Second
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * TICKS_PER_SECOND)

PLANES = 2
MAX_CORRECTORS = 9
N = MAX_CORRECTORS * PLANES


@dataclass
class FofbCorrector:
    index: int
    ioc: str
    fofb_index: int
    slow: int


@dataclass
class Oscillation:
    amplitude: float
    plane: Components
    frequency: int
    cycles: int

    # Length of time of excitation in s
    dwell: float
    # Length of time of excitation in FOFB ticks
    count: int
    # Phase advance per tick per revoloution
    delta: int
    # Duration of all oscillations.
    duration: int

    @classmethod
    def from_values(
        cls, amplitude: float, plane: Components, frequency: int, cycles: int
    ) -> Oscillation:
        dwell = cycles / frequency
        count = int(np.ceil(dwell * TICKS_PER_SECOND))
        delta = int(np.floor(frequency * 2**32 / TICKS_PER_SECOND))
        duration = int((2 * count) + NETWORK_LAG + SAFETY_NET)
        return cls(amplitude, plane, frequency, cycles, dwell, count, delta, duration)


def get_corrector_table(lattice: Lattice) -> np.ndarray[Any, Any]:
    correctors_txt: str = lattice.config["CORRECTORS_TXT_PATH"]
    with open(correctors_txt, "r", encoding="utf8", newline="") as file:
        data = np.genfromtxt(file, names=True, dtype=None, encoding="UTF-8")
    return data


def get_fofb_corrector(lattice: Lattice, components: Components) -> FofbCorrector:
    """Create FofbCorrector tuple from pytac element."""
    table = get_corrector_table(lattice)
    name = components.corrector_name
    # Corrector table indices start from 1
    index = int(table["epics"].tolist().index(name)) + 1
    ioc = table["ioc"][index]
    fofb_index = int(table["farow"][index])
    slow = 1 if name in lattice.slow_correctors else 0
    return FofbCorrector(index, ioc, fofb_index, slow)


class Excitation(object):
    """An excitation performed on a corrector."""

    def __init__(
        self,
        lattice: Lattice,
        components: Components,
        oscillation: Oscillation,
        start_time: int,
    ):
        self.corrector = components.corrector
        self.oscillation: Oscillation = oscillation
        self.start_time: int = start_time
        self.count: int = oscillation.count

        fofb_corrector = get_fofb_corrector(lattice, components)
        self.ioc = fofb_corrector.ioc
        self.fofb_index = fofb_corrector.fofb_index
        self.iocs = lattice.config["CORRECTOR_IOCS"]


def excite(excitations: tuple[Excitation, ...]):
    """Completes caputs which will start the excitation."""

    iocs = excitations[0].iocs

    # Zero all timestamps
    caput(
        [f"{ioc}:EXCITE:START_TIMES" for ioc in iocs],
        [[0] * N] * len(iocs),
    )

    # Create dict of PVs to put
    pvs: dict[str, List[Union[float, int]]] = {}
    for e in excitations:
        pvs.update(
            {
                f"{e.ioc}:EXCITE:START_TIMES": [0] * N,
                f"{e.ioc}:EXCITE:AMPS": [0] * N,
                f"{e.ioc}:EXCITE:DELTAS": [0] * N,
                f"{e.ioc}:EXCITE:TICKS": [0] * N,
            }
        )

        index = e.fofb_index

        # If start times has already been filled in this corrector is
        # specified twice. The IOC can't deal with this so raise an exception
        if pvs[f"{e.ioc}:EXCITE:START_TIMES"][index] != 0:
            raise ValueError(
                f"Corrector {e.ioc}:{e.fofb_index:02d} cannot be "
                "specified twice in the same plane"
            )
        pvs[f"{e.ioc}:EXCITE:START_TIMES"][index] = e.start_time
        pvs[f"{e.ioc}:EXCITE:AMPS"][index] = e.oscillation.amplitude
        pvs[f"{e.ioc}:EXCITE:DELTAS"][index] = e.oscillation.delta
        pvs[f"{e.ioc}:EXCITE:TICKS"][index] = e.count

    # caput the values
    caput(*zip(*pvs.items()), wait=True)

    # Ensure all values are put, then reset the reset the IOCs
    # cothread.Yield()
    # TODO: ^Delete once tested.
    caput(
        [f"{ioc}:EXCITE:PRIME" for ioc in iocs],
        1,
        wait=True,
        repeat_value=True,
    )


def cancel_all_oscillations(lattice: Lattice):
    """"""
    # Set all to 0, then prime for all IOCS.
    iocs = lattice.config["CORRECTOR_IOCS"]
    pvs = {}

    for ioc in iocs:
        pvs.update(
            {
                f"{ioc}:EXCITE:START_TIMES": [0] * N,
                f"{ioc}:EXCITE:AMPS": [0] * N,
                f"{ioc}:EXCITE:DELTAS": [0] * N,
                f"{ioc}:EXCITE:TICKS": [0] * N,
            }
        )

    caput(*zip(*pvs.items()), wait=True)

    # Ensure all values are put, then reset the reset the IOCs
    # cothread.Yield()
    caput(
        [f"{ioc}:EXCITE:PRIME" for ioc in iocs],
        1,
        wait=True,
        repeat_value=True,
    )
