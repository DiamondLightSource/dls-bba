
import cothread
from cothread.catools import caput
import numpy
# For now, import helper functions from ploco
import sys
sys.path.append('/dls_sw/prod/R3.14.12.3/support/ploco/0-4')

from excite import TICKS_PER_SECOND, get_fa_data, get_timestamp_fa, get_timestamp_epics
from opi.corrector import Corrector


# for testing purposes
def caget(pv):
    print 'caget %s' % pv
    return 10

def caput(pv, value):
    print 'caput %s:%s' % (pv, value)


def get_ramp_waveform(length):
    # To do:
    # Half sine wave intro
    # Ramp
    # Half sine wave exit
    intro_length = length / 10
    ramp_length = length - 2 * intro_length
    intro_scale = numpy.arange(100) * numpy.pi / 100
    intro = (1.0/2) * (numpy.cos(intro_scale) - 1)
    exit = (1.0/2) * (numpy.cos(intro_scale) + 1)
    ramp = numpy.arange(-1.0, 1.0, 2.0/ramp_length)

    waveform = numpy.concatenate((intro, ramp, exit))

    """
    import matplotlib.pyplot as pp
    pp.plot(waveform)
    pp.show()
    """
    return waveform


def move_corrector(corr_id, corr_pv, corr_amp):

    STEPS = 10
    c = Corrector(corr_id)
    length = 1000
    waveform = get_ramp_waveform(length)
    caput('%s:WAVEFORM:WAVEFORM' % c.ioc, waveform)
    caput('%s:WAVEFORM:LENGTH' % c.ioc, len(waveform))
    caput('%s:WAVEFORM:TICKS' % c.ioc, len(waveform))
    caput('%s:WAVEFORM:STEP_SIZES' % c.ioc, STEPS)
    caput('%s:WAVEFORM:SCALES' % c.ioc, corr_amp)
    # Caput the start times, in the future.
    network_lag = TICKS_PER_SECOND * 0.5
    now = get_timestamp_fa()
    start_tick = now + network_lag
    start_times = numpy.zeros(18)
    start_times[c.corr-1] = start_tick
    caput('%s:WAVEFORM:START_TIMES' % c.ioc, start_times)
    total_ticks = len(waveform) * STEPS
    print('Length of waveform is %ss' % total_ticks)
    caput('%s:WAVEFORM:PRIME' % c.ioc, 1)
    return start_tick, total_ticks


def crop_data(data):
    # We want data that is definitely within the ramp.
    length = data.shape[0]
    print 'length of data is', length
    chop = numpy.floor(length * 0.15)
    left = length - 2 * chop
    mask = numpy.concatenate((numpy.zeros(chop), numpy.ones(left), numpy.ones(chop)))
    mask = numpy.array(mask, dtype=bool)
    print mask.shape
    data = data[mask,:,:]
    return data
