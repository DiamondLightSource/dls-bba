from __future__ import division

from pkg_resources import require
require('cothread')
require('fa-archiver')
require('scipy')
require('numpy')

import sys
import datetime
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



NETWORK_LAG_S = 1.0
SAFETY_NET_S = 0.1
TICKS_PER_SECOND = 10072
QUAD_SLEW_RATE = 1  # A/s
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * TICKS_PER_SECOND)
DECIMATED = False

BPM_IDS = range(174)  # 173 plus 0 for timestamps


def save_data(high_data, low_data, quad, plane, osc):
    quad_pv = pml.prefix_from_element(quad)
    plane_name = pml.AXIS_NAMES[plane]
    amp, period, cycles = osc
    datadict = {'period': period, 'amp': amp, 'cycles': cycles}
    datadict['quad'] = quad_pv
    datadict['plane'] = plane_name
    datadict['bpm'] = pml.quad_to_bpm(quad)[0]
    datadict['enabled_bpms'] = pml.enabled_bpms().astype(numpy.int)
    datadict['high'] = high_data
    datadict['low'] = low_data
    now = datetime.datetime.now()
    datestring = now.strftime('%Y-%m-%dT%H-%M-%S')
    filename = 'data/bba-%s-%s-%s-%s' % ('jump', quad_pv,
                                         plane_name, datestring)
    scipy.io.savemat(filename, datadict, oned_as='row')
    print('Saved to %s' % filename)


def select_data(data, plane, exc_high, exc_low):
    # get relevant timestamps
    # select relevant duration
    # select correct plane
    print('Final timestamp in data: {}'.format(data[-1,0,0]))
    print('Raw data: {}'.format(data.shape))
    # Extract timestamps from data
    times = data[:,0,0]
    data = data[:,1:,:]
    i = 0
    while times[i] < exc_high.time:
        i += 1
    length = int(exc_high.count // 10) if DECIMATED else exc_high.count
    high_data = numpy.squeeze(data[i:i+length,:,plane])
    while times[i] < exc_low.time:
        i += 1
    low_data = numpy.squeeze(data[i:i+length,:,plane])
    print('Selected data size: {} {}'.format(high_data.shape, low_data.shape))
    return high_data, low_data


def get_excitation(corr, plane):
    amp, period, cycles = osc
    f = 10072 / period
    exc = excite.Excitation(corr.ioc, corr.corr, plane,
                            amp, f, cycles)
    return exc


def jump_bba(quad, plane, quad_step, osc):
    '''
    Do we need undecimated data?
    '''
    amp, period, cycles = osc
    # set quad value
    quad_pv = quad.pv(handle='setpoint')[0]
    quad_sp = caget(quad_pv)
    quad_high = quad_sp + quad_step / 2
    quad_low = quad_sp - quad_step / 2
    quad_lag_s = quad_step * QUAD_SLEW_RATE
    quad_lag = int(quad_lag_s * TICKS_PER_SECOND)

    corr_id, ap_corr = pml.effective_corrector(quad, plane)
    print('Using corrector {}'.format(corr_id))
    corr = Corrector(corr_id)
    # Move quad high
    caput(quad_pv, quad_high)
    cothread.Sleep(quad_lag_s / 2)
    now = excite.get_timestamp_fa()
    exc_high = get_excitation(corr, plane, osc)
    exc_low = get_excitation(corr, plane, osc)
    duration = (NETWORK_LAG + exc_high.count + SAFETY_NET + quad_lag +
                exc_low.count)
    # Set off the data collection
    fa_buffer = fa.Buffer(BPM_IDS, duration, DECIMATED)
    high_start = now + NETWORK_LAG
    print('Time now: {}.'.format(now))
    print('High start time: {}.'.format(high_start))
    low_start = high_start + exc_high.count + SAFETY_NET + quad_lag
    print('Low start time: {}.'.format(low_start))
    excite.excite_storage_ring_(high_start, (exc_high, exc_low),
                                quad_lag + SAFETY_NET)
    # Sleep for first excitation. SAFETY_NET ensures that we don't start
    # moving the quad before the excitation has finished.
    cothread.Sleep((NETWORK_LAG + exc_high.count + SAFETY_NET) /
                   TICKS_PER_SECOND)
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


if __name__ == '__main__':
    ##########
    # Config
    PLANE = pml.X
    QUAD_PV = 'SR01A-PC-Q1D-01'
    QUAD_STEP = 1.0  # A
    CORR_PERIOD = 1259  # FA network ticks
    CORR_AMP = 0.1  # A
    CYCLES = 6
    ##########

    ap_quad = pml.quad_from_pv(QUAD_PV)
    osc = (CORR_AMP, CORR_PERIOD, CYCLES)
    jump_bba(ap_quad, PLANE, QUAD_STEP, osc)
