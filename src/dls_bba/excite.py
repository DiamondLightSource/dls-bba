from dataclasses import dataclass

import numpy as np
from cothread.catools import caput

from dls_bba.components import Components
from dls_bba.faa import TICKS_PER_SECOND

NETWORK_LAG_S = 0.5
"""Additional time to account for Network Lag in seconds."""
SAFETY_NET_S = 0.1
"""Additional time for a safety net in seconds."""
QUAD_SLEW_RATE = 0.5
"""The slew rate of a quadrupole in amps per second."""
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
"""Additional time to account for Network Lag in FAA ticks."""
SAFETY_NET = int(SAFETY_NET_S * TICKS_PER_SECOND)
"""Additional time for a safety net in FAA ticks."""

PLANES = 2
"""Number of planes. eg. 'x' and 'y'."""
MAX_CORRECTORS = 9
"""The maximum number of correctors in a plane per IOC or cell."""
N = MAX_CORRECTORS * PLANES
"""The maximum number of correctors per IOC or cell."""


@dataclass
class FofbCorrector:
    """This dataclass provides information regarding the IOC and the corrector chosen."""

    index: int
    ioc: str
    fofb_index: int
    slow: int


@dataclass
class Oscillation:
    """This dataclass provides information regarding the AC excitation."""

    amplitude: float
    plane: Components
    frequency: int
    cycles: int

    dwell: float  # Length of time of excitation in s.
    count: int  # Length of time of excitation in FOFB ticks.
    delta: int  # Phase advance per tick per revoloution.
    duration: float  # Duration of all oscillations.

    @classmethod
    def from_values(
        cls, amplitude: float, plane: Components, frequency: int, cycles: int
    ):
        """This constructor is the default construction method.

        Args:
            amplitude: The maximum amplitude of the excitation in amps.
            plane: The components including the plane.
            frequency: The frequency of the oscillation in Hz.
            cycles: The number of cycles to excite for.
        """
        dwell = cycles / frequency
        count = int(np.ceil(dwell * TICKS_PER_SECOND))
        delta = int(np.floor(frequency * 2**32 / TICKS_PER_SECOND))
        duration = (2 * count) + NETWORK_LAG + SAFETY_NET
        return cls(amplitude, plane, frequency, cycles, dwell, count, delta, duration)


def get_corrector_table(lattice):
    """This function gets corrector IOC table.

    Args:
        lattice: The lattice object.

    Returns:
        An array with the corrector IOC table.
    """
    correctors_txt = lattice.config["CORRECTORS_TXT_PATH"]
    with open(correctors_txt, "r", encoding="utf8", newline="") as file:
        data = np.genfromtxt(file, names=True, dtype=None, encoding="UTF-8")
    return data


def get_fofb_corrector(lattice, components: Components):
    """Create FofbCorrector tuple from components.

    Args:
        lattice: The lattice object.
        components: The component object for the corrector of interest.

    Returns:
        An FofbCorrector object.
    """
    table = get_corrector_table(lattice)
    name = components.corrector_name
    # Corrector table indices start from 1
    index = int(table["epics"].tolist().index(name)) + 1
    ioc = table["ioc"][index]
    fofb_index = int(table["farow"][index])
    slow = 1 if name in lattice.slow_correctors else 0
    return FofbCorrector(index, ioc, fofb_index, slow)


class Excitation(object):
    """An excitation object contains all the information to perform an AC excitation."""

    def __init__(
        self, lattice, components: Components, oscillation: Oscillation, start_time: int
    ):
        """The default constructor for the excitation object.

        Args:
            lattice: The lattice object.
            components: The component object for the corrector of interest.
            oscillation: The oscillation object for the corrector of interest.
            start_time: The oscillation start time in FAA ticks.
        """
        self.corrector = components.corrector
        self.oscillation = oscillation
        self.start_time = start_time
        self.count = oscillation.count

        fofb_corrector = get_fofb_corrector(lattice, components)
        self.ioc = fofb_corrector.ioc
        self.fofb_index = fofb_corrector.fofb_index
        self.iocs = lattice.config["CORRECTOR_IOCS"]


def excite(excitations):
    """Completes caputs which will start the excitation.

    Args:
        excitations: A tuple of excitation objects.
    """
    iocs = excitations[0].iocs

    # Zero all timestamps
    caput(
        [f"{ioc}:EXCITE:START_TIMES" for ioc in iocs],
        [[0] * N] * len(iocs),
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
        [f"{ioc}:EXCITE:PRIME" for ioc in iocs],
        1,
        wait=True,
        repeat_value=True,
    )


def cancel_all_oscillations(config):
    """This function resets all of the IOCs to stop rogue oscillations.

    Args:
        config: The configuration dictionary of the lattice object.
    """
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
