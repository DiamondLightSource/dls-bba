from __future__ import division

from pkg_resources import require
require('cothread')
require('fa-archiver')
require('scipy')
require('numpy')

import sys
import collections
import datetime
import logging as log
import numpy
import scipy.io
from cothread.catools import caget, caput
import cothread
import fa
# For now, import helper functions from ploco
sys.path.append('/dls_sw/prod/R3.14.12.3/support/ploco/0-4')
import excite
from opi.corrector import Corrector
import pml


# Struct representing one oscillation
Oscillation = collections.namedtuple('Oscillation', ['amp', 'period', 'cycles'])


NETWORK_LAG_S = 1.0
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 1  # A/s
NETWORK_LAG = int(NETWORK_LAG_S * fa.TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * fa.TICKS_PER_SECOND)
DECIMATED = True

BPM_IDS = range(174)  # 173 plus 0 for timestamps


def get_filename_prefix():
    now = datetime.datetime.now()
    datestring = now.strftime('%Y-%m-%dT%H-%M-%S')
    return 'bba-{}'.format(datestring)


def save_data(high_data, low_data, quad, plane, osc):
    quad_pv = pml.prefix_from_element(quad)
    plane_name = pml.AXIS_NAMES[plane]
    datadict = {'period': osc.period, 'amp': osc.amp, 'cycles': osc.cycles}
    datadict['quad'] = quad_pv
    datadict['plane'] = plane_name
    datadict['bpm'] = pml.quad_to_bpm(quad)[0]
    datadict['enabled_bpms'] = pml.enabled_bpms().astype(numpy.int)
    datadict['high'] = high_data
    datadict['low'] = low_data
    filename = 'data/{}-{}-{}'.format(get_filename_prefix(), quad_pv, plane_name)
    scipy.io.savemat(filename, datadict, oned_as='row')
    log.info('Saved data to %s' % filename)


def select_data(data, plane, exc_high, exc_low):
    '''
    Array data must include the timestamps.
    '''
    log.debug('Raw data shape: {}'.format(data.shape))
    log.info('Timestamp range in raw data: {}-{}'.format(data[0,0,0],
                                                         data[-1,0,0]))
    log.debug('Excitation length: {}'.format(exc_high.count))
    log.debug('Trailing data to crop: {}.'.format(data[-1,0,0] -
                                               (exc_low.time + exc_low.count)))
    assert exc_high.count == exc_low.count, 'Excitations different lengths'
    # Extract timestamps from data
    times = data[:,0,0]
    data = data[:,1:,:]
    high_start = numpy.searchsorted(times, exc_high.time)
    low_start = numpy.searchsorted(times, exc_low.time)
    length = int(exc_high.count // 10) if DECIMATED else exc_high.count
    high_data = data[high_start:high_start+length,:,plane]
    low_data = data[low_start:low_start+length,:,plane]
    log.info('Selected data shape: {} {}'.format(high_data.shape,
                                                 low_data.shape))
    assert high_data.shape == low_data.shape
    return high_data, low_data


def get_excitation(corr, plane, osc):
    f = 10072 / osc.period
    exc = excite.Excitation(corr.ioc, corr.corr, plane,
                            osc.amp, f, osc.cycles)
    return exc


def jump_bba(quad, plane, quad_step, osc):
    '''
    Do we need undecimated data?
    '''
    log.info('Quad step is {}'.format(quad_step))
    quad_pv = quad.pv(handle='setpoint')[0]
    quad_sp = caget(quad_pv)
    quad_high = quad_sp + quad_step / 2
    quad_low = quad_sp - quad_step / 2
    quad_lag_s = quad_step * QUAD_SLEW_RATE
    quad_lag = int(quad_lag_s * fa.TICKS_PER_SECOND)

    corr_id, ap_corr = pml.effective_corrector(quad, plane)
    log.info('Using corrector {}'.format(corr_id))
    corr = Corrector(corr_id)
    # Move quad high
    caput(quad_pv, quad_high)
    cothread.Sleep(quad_lag_s / 2)
    now = fa.get_timestamp()
    exc_high = get_excitation(corr, plane, osc)
    exc_low = get_excitation(corr, plane, osc)
    # Set off the data collection
    high_start = now + NETWORK_LAG
    duration = exc_high.count + SAFETY_NET + quad_lag + exc_low.count
    fa_buffer = fa.Buffer(BPM_IDS, high_start, duration, DECIMATED)
    low_start = high_start + exc_high.count + SAFETY_NET + quad_lag
    log.debug('Safety net: {}; quad_lag: {}'.format(SAFETY_NET, quad_lag))
    log.info('Time now: {}.'.format(now))
    log.info('High start time: {}.'.format(high_start - now))
    log.info('Low start time: {}.'.format(low_start - now))
    excite.excite_storage_ring_(high_start, (exc_high, exc_low),
                                quad_lag + SAFETY_NET)
    # Sleep for first excitation. SAFETY_NET ensures that we don't start
    # moving the quad before the excitation has finished.
    cothread.Sleep((NETWORK_LAG + exc_high.count + SAFETY_NET) /
                   fa.TICKS_PER_SECOND)
    # Move quad from high to low
    caput(quad_pv, quad_low)
    # This will block until all data has been retrieved.
    fa_data = fa_buffer.get_data()
    high_data, low_data = select_data(fa_data, plane, exc_high, exc_low)
    save_data(high_data, low_data, quad, plane, osc)

    # Restore setpoint.  We don't need SAFETY_NET here because we've saved
    # all the data before we request the move.
    caput(quad_pv, quad_sp)
    cothread.Sleep(quad_lag_s / 2)
