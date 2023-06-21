from dataclasses import dataclass

import numpy as np
from cothread.catools import caput

from dls_bba.components import Components
from dls_bba.faa import TICKS_PER_SECOND

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
    duration: float

    @classmethod
    def from_values(cls, amplitude, plane, frequency, cycles):
        dwell = cycles / frequency
        count = int(np.ceil(dwell * TICKS_PER_SECOND))
        delta = int(np.floor(frequency * 2**32 / TICKS_PER_SECOND))
        duration = (2 * count) + NETWORK_LAG + SAFETY_NET
        return cls(amplitude, plane, frequency, cycles, dwell, count, delta, duration)


def get_corrector_table(lattice):
    correctors_txt = lattice._config["CORRECTORS_TXT_PATH"]
    with open(correctors_txt, "r", encoding="utf8", newline="") as file:
        data = np.genfromtxt(file, names=True, dtype=None, encoding="UTF-8")
    return data


def get_fofb_corrector(lattice, components: Components):
    """Create FofbCorrector tuple from pytac element."""
    table = get_corrector_table(lattice)
    name = components.corrector_name
    # Corrector table indices start from 1
    index = int(table["epics"].tolist().index(name)) + 1
    ioc = table["ioc"][index]
    fofb_index = int(table["farow"][index])
    slow_correctors = lattice._get_slow_correctors()
    slow = 1 if name in slow_correctors else 0
    return FofbCorrector(index, ioc, fofb_index, slow)


class Excitation(object):
    """An excitation performed on a corrector."""

    def __init__(self, lattice, components, oscillation, start_time):
        self.corrector = components.corrector
        self.oscillation = oscillation
        self.start_time = start_time
        self.count = oscillation.count

        fofb_corrector = lattice.get_fofb_corrector(components)
        self.ioc = fofb_corrector.ioc
        self.fofb_index = fofb_corrector.corr
        self.iocs = lattice._config["CORRECTOR_IOCS"]


def excite(excitations):
    """Completes caputs which will start the excitation."""

    # Zero all timestamps
    caput(
        [f"{ioc}:EXCITE:START_TIMES" for ioc in excitations.iocs],
        [[0] * N] * len(excitations.iocs),
    )

    # Create dict of PVs to put
    pvs = {}
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
        pvs[f"{e.ioc}:EXCITE:AMPS"][index] = e.oscillation.amp
        pvs[f"{e.ioc}:EXCITE:DELTAS"][index] = e.delta
        pvs[f"{e.ioc}:EXCITE:TICKS"][index] = e.count

    # caput the values
    caput(*zip(*pvs.items()), wait=True)

    # Ensure all values are put, then reset the reset the IOCs
    # cothread.Yield()
    # TODO: ^Delete once tested.
    caput(
        [f"{ioc}:EXCITE:PRIME" for ioc in excitations.iocs],
        1,
        wait=True,
        repeat_value=True,
    )


def cancel_all_oscillations(config):
    """"""
    # Set all to 0, then prime for all IOCS.
    iocs = config["CORRECTOR_IOCS"]
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
