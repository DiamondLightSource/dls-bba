import collections
import os

import cothread
import numpy
from cothread.catools import caput

from bba import X

RINGMODE_PV = "SR-CS-RING-01:MODE"

IOCS = ["SR%02dA-CS-FOFB-01" % i for i in range(1, 25)]
TICKS_PER_SECOND = 10072

Oscillation = collections.namedtuple("Oscillation", ["amp", "plane", "freq", "cycles"])

FofbCorrector = collections.namedtuple(
    "FofbCorrector", ["num", "ioc", "corr", "is_slow"]
)


def get_corrector_table():
    basepath = os.path.dirname(__file__)
    filepath = os.path.join(basepath, "data", "correctors.txt")
    return numpy.genfromtxt(filepath, names=True, dtype=None, encoding="UTF-8")


def get_fofb_corrector(pytac_element, plane):
    """Create FofbCorrector tuple from pytac element."""
    table = get_corrector_table()
    kick_field = "x_kick" if plane == X else "y_kick"
    name = pytac_element.get_device(kick_field).name
    index = int(table["epics"].tolist().index(name))
    return FofbCorrector(
        pytac_element.index + 1,
        table["ioc"][index],
        int(table["farow"][index]),
        int(table["slow"][index]),
    )


class Excitation(object):
    """An excitation performed on a corrector."""

    def __init__(self, corrector, oscillation, start_time):
        self.corrector = corrector
        self.oscillation = oscillation
        self.start_time = start_time

        # Length of time of excitation in s
        self.dwell = self.oscillation.cycles / self.oscillation.freq
        # Length of time of excitation in FOFB ticks
        self.count = int(numpy.round(self.dwell * TICKS_PER_SECOND))
        # Phase advance per tick per revoloution
        self.delta = int(
            numpy.floor(self.oscillation.freq * 2 ** 32 / TICKS_PER_SECOND)
        )

        fofb_corrector = get_fofb_corrector(self.corrector, oscillation.plane)
        self.ioc = fofb_corrector.ioc
        self.fofb_index = fofb_corrector.corr


def excite(excitations):
    """Completes caputs which will start the excitation."""
    pvs = {}
    PLANES = 2
    MAX_CORRECTORS = 9
    N = MAX_CORRECTORS * PLANES

    # Zero all timestamps
    caput([f"{ioc}:EXCITE:START_TIMES" for ioc in IOCS], [[0] * N] * len(IOCS))

    # Create dict of PVs to put
    for e in excitations:
        index = e.fofb_index + e.oscillation.plane * MAX_CORRECTORS

        # If start times has already been filled in this corrector is
        # specified twice. The IOC can't deal with this so raise an exception
        if pvs.setdefault(f"{e.ioc}:EXCITE:START_TIMES", [0] * N)[index] != 0:
            raise ValueError(
                f"Corrector {e.ioc}:{e.fofb_index:02d} cannot be "
                "specified twice in the same plane"
            )
        pvs.setdefault(f"{e.ioc}:EXCITE:START_TIMES", [0] * N)[index] = e.start_time
        pvs.setdefault(f"{e.ioc}:EXCITE:AMPS", [0] * N)[index] = e.oscillation.amp
        pvs.setdefault(f"{e.ioc}:EXCITE:DELTAS", [0] * N)[index] = e.delta
        pvs.setdefault(f"{e.ioc}:EXCITE:TICKS", [0] * N)[index] = e.count

    # caput the values
    for key, values in pvs.items():
        caput(key, values)
    # Ensure all values are put, then reset the reset the IOCs
    cothread.Yield()
    caput([f"{ioc}:EXCITE:PRIME" for ioc in IOCS], [1] * len(IOCS))
