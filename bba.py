"""
Simple version of BBA in Python.

At first it will do a similar thing to the existing Matlab BBA,
except that it will nominally use quadrupole oscillation
rather than manual EPICS settings.

Assume that the waveform is loaded into the quadrupole before starting.

You can find some of the configuration for matlab BBA by 
running quadcenterinit(family, element, plane).
"""

from pkg_resources import require
require('cothread')
require('fa-archiver')
require('scipy')
require('numpy')

import scipy.io
import numpy
import datetime
from cothread.catools import caget, caput
import cothread
import falib
import pml
import ramp
import step


# For now, import helper functions from ploco
import sys
sys.path.append('/dls_sw/prod/R3.14.12.3/support/ploco/0-4')

from excite import get_fa_data
from opi.corrector import Corrector, IOCS

# From quadcenterinit
CORR_AMP = 1.5e-5 # A
EXTRA_DELAY = 0.1 # s
# By default, the first bank.
WF_BANK = 14

AXIS_NAMES = {pml.X: 'X', pml.Y: 'Y'}


# for testing purposes
def caput(pv, value):
    print 'caput %s  %s' % (pv, value)


def start_oscillation(quad_pv):
    selected_bank = caget(quad_pv + ':SETWFSEL')
    assert selected_bank == WF_BANK
    step_size = caget(quad_pv + ':SETWFSTEP')
    print 'step size:', step_size
    amplitude = caget(quad_pv + ':SETWFSCA')
    print 'scale factor:', amplitude
    caput(quad_pv + ':SETWFTRIG', 1)
    caput(quad_pv + ':SETWFENA', 1)


def stop_oscillation(quad_pv):
    caput(quad_pv + ':SETWFENA', 0)
    caput(quad_pv + ':SETWFTRIG', 0)


def quad_bba(quad_pv, ramp_quad=True):
    if ramp_quad:
        module = ramp
    else:
        module = step
    start_oscillation(quad_pv)
    s = {}
    for axis in (pml.X, pml.Y):
        corr_id, corr = pml.effective_corrector(quad_pv, axis)
        cothread.Sleep(EXTRA_DELAY)
        print 'Using corrector %s for quad %s in %s.' % (corr_id, quad_pv, AXIS_NAMES[axis])
        start_time, ticks_taken = module.move_corrector(corr_id, sorted(corr.pv())[1], CORR_AMP)
        cothread.Sleep(EXTRA_DELAY)
        # Note that DECIMATED is True in this call
        data = get_fa_data((int(ticks_taken + 200)))
        print data.shape
        good_bpms = pml.enabled_bpms()
        good_bpms = numpy.concatenate((numpy.ones(1, dtype=numpy.bool), good_bpms))
        clean_data = data[:,good_bpms,:]
        print clean_data.shape
        clean_data = module.crop_data(clean_data)
        s[AXIS_NAMES[axis]] = clean_data
    stop_oscillation(quad_pv)
    now = datetime.datetime.now()
    datestring = now.strftime('%Y-%m-%dT%H-%M-%S')
    filename = 'data/bba-%s-%s-%s' % (module.__name__, quad_pv, datestring)
    scipy.io.savemat(filename, s, oned_as='row')
    print('Saved to %s' % filename)


if __name__ == '__main__':
    fa_server = falib.Server()
    QUAD_PV = 'SR01A-PC-Q1D-01'
    try:
        method = sys.argv[1]
        if method == 'ramp':
            ramp_quad = True
        elif method == 'step':
            ramp_quad = False
        else:
            print 'Method %s not understood' % method
            sys.exit()
    except IndexError:
        print 'Usage: %s [ramp|step]' % sys.argv[0]
        sys.exit()

    quad_bba(QUAD_PV, ramp_quad)
