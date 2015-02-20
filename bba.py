"""
Simple version of BBA in Python.

At first it will do a similar thing to the existing Matlab BBA,
except that it will nominally use quadrupole oscillation
rather than manual EPICS settings.

Assume that the waveform is loaded into the quadrupole before starting.
"""

from pkg_resources import require
require('cothread')
require('fa-archiver')
require('scipy')
require('numpy')

import scipy.io
from cothread.catools import caget, caput
import cothread
import falib
import pml


CORR_STEPS = 5
CORR_CHANGE = 1 # A
CORR_PERIOD = 0.5 # s
EXTRA_DELAY = 0.1 # s

OSC_STEP = 60
WF_BANK = 10


# for testing purposes
def caget(pv):
    print 'caget %s' % pv
    return 10

def caput(pv, value):
    print 'caput %s:%s' % (pv, value)


def start_oscillation(quad_pv):
    selected_bank = caget(quad_pv + ':SETWFSEL')
    assert selected_bank == WF_BANK
    caput(quad_pv + ':SETWTRIG', 1)
    caput(quad_pv + ':SETWFSTEP', OSC_STEP)
    caput(quad_pv + ':SETWFENA', 1)


def stop_oscillation(quad_pv):
    caput(quad_pv + ':SETWFENA', 0)
    caput(quad_pv + ':SETWTRIG', 0)


def step_corrector(corr_pv, fa_server):

    sub = fa_server.subscription(range(1, 173), decimated=True)
    cothread.Sleep(EXTRA_DELAY)
    start = caget(corr_pv)
    setpoint = 0
    step = (2.0 * CORR_CHANGE) / (CORR_STEPS - 1)
    setpoint = start - CORR_CHANGE - step
    caput(corr_pv, setpoint)
    for i in range(CORR_STEPS):
        setpoint += step
        caput(corr_pv, setpoint)
        cothread.Sleep(CORR_PERIOD)

    caput(corr_pv, start)
    cothread.Sleep(EXTRA_DELAY)

    data = sub.read(int(CORR_PERIOD * CORR_STEPS * 1000 + 200))
    sub.close()
    return data


if __name__ == '__main__':
    fa_server = falib.Server()
    QUAD_PV = 'SR01A-PC-Q1D-01'
    start_oscillation(QUAD_PV)
    s = {}
    for axis in ('X', 'Y'):
        corr_id, corr = pml.effective_corrector(QUAD_PV, getattr(pml, axis))
        print 'Using corrector %s for quad %s in %s.' % (corr_id, QUAD_PV, axis)
        s[axis] = step_corrector(corr.pv()[1], fa_server)
    stop_oscillation(QUAD_PV)
    scipy.io.savemat('quaddata', s)
