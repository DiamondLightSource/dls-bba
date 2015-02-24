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
import sys

# Default value from quadcenterinit
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


def filter_bpms(data):
    good_bpms = pml.enabled_bpms()
    # Prepend a one to allow timestamp data through.
    good_bpms = numpy.concatenate((numpy.ones(1, dtype=numpy.bool), good_bpms))
    clean_data = data[:,good_bpms,:]
    return clean_data


def save_data(datadict, quad_pv, bba_type):
    now = datetime.datetime.now()
    datestring = now.strftime('%Y-%m-%dT%H-%M-%S')
    filename = 'data/bba-%s-%s-%s' % (module.__name__, quad_pv, datestring)
    scipy.io.savemat(filename, datadict, oned_as='row')
    print('Saved to %s' % filename)


def quad_bba(quad_pv, method):
    start_oscillation(quad_pv)
    datadict = {}
    for axis in (pml.X, pml.Y):
        corr_id, corr = pml.effective_corrector(quad_pv, axis)
        # start the subscription
        sub = falib.subscription(range(173), decimated=True)
        print 'Using corrector %s for quad %s in %s.' %\
            (corr_id, quad_pv, AXIS_NAMES[axis])
        # I don't understand this interface.
        seti_pv = sorted(corr.pv())[1]
        start_time, ticks_taken = method.move_corrector(corr_id, seti_pv, CORR_AMP)
        data = sub.read((int(ticks_taken + 2000)) / 10)
        sub.close()
        clean_data = filter_bpms(data)
        cropped_data = method.crop_data(start_time, clean_data)
        datadict[AXIS_NAMES[axis]] = cropped_data
    stop_oscillation(quad_pv)
    save_data(datadict, quad_pv, method.__name__)


if __name__ == '__main__':
    QUAD_PV = 'SR01A-PC-Q1D-01'
    try:
        method_name = sys.argv[1]
        if method_name == 'ramp':
            module = ramp
        elif method_name == 'step':
            module = step
        else:
            print 'Method %s not understood' % method_name
            sys.exit()
    except IndexError:
        print 'Usage: %s [ramp|step]' % sys.argv[0]
        sys.exit()

    quad_bba(QUAD_PV, module)
