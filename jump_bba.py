from __future__ import division

from pkg_resources import require
require('cothread')
require('fa-archiver')
require('scipy')

import sys
import datetime
import scipy.io
from cothread.catools import caget, caput
import cothread
import fa
# For now, import helper functions from ploco
sys.path.append('/dls_sw/prod/R3.14.12.3/support/ploco/0-4')
import excite
from opi.corrector import Corrector
import pml


##########
# Config
QUAD_STEP = 1.0  # A
QUAD_LAG_S = 1
CORR_PERIOD = 1259  # FA network ticks
CORR_AMP = 0.1  # A
CYCLES = 6
NETWORK_LAG_S = 0.2
SAFETY_NET_S = 0.1
##########

TICKS_PER_SECOND = 10072
QUAD_LAG = QUAD_LAG_S * TICKS_PER_SECOND
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
SAFETY_NET = SAFETY_NET_S * TICKS_PER_SECOND
DECIMATED = False

BPM_IDS = range(174)  # 173 plus 0 for timestamps


def test_caput(pvs, val):
    print('caput: {}  {}'.format(pvs, val))


def test_Sleep(val):
    print('cothread: Sleeping for {:.1f}s'.format(val))
    cothread.oSleep(val)


def save_data(datadict, quad, plane, bba_type):
    quad_pv = pml.prefix_from_element(quad)
    plane_name = pml.AXIS_NAMES[plane]
    now = datetime.datetime.now()
    datestring = now.strftime('%Y-%m-%dT%H-%M-%S')
    filename = 'data/bba-%s-%s-%s-%s' % (bba_type, quad_pv,
                                         plane_name, datestring)
    scipy.io.savemat(filename, datadict, oned_as='row')
    print('Saved to %s' % filename)


def select_data(data, exc_high, exc_low):
    # remove bogus data
    # get relevant timestamps
    # select relevant duration
    print('Selecting data')
    print('Raw data: {}'.format(data.shape))
    times = data[:,0,0]
    i = 0
    while times[i] < exc_high.time:
        i += 1
    length = int(exc_high.count // 10) if DECIMATED else exc_high.count
    high_data = data[i:i+length,:,:]
    while times[i] < exc_low.time:
        i += 1
    low_data = data[i:i+length,:,:]
    return high_data, low_data


def get_excitation(corr, plane):
    f = 10072 / CORR_PERIOD
    exc = excite.Excitation(corr.ioc, corr.corr, plane,
                            CORR_AMP, f, CYCLES)
    return exc


def jump_bba(quad, planes):
    '''
    Do we need undecimated data?
    '''
    # set quad value
    quad_pv = quad.pv(handle='setpoint')[0]
    quad_sp = caget(quad_pv)
    quad_high = quad_sp * 1.01
    quad_low = quad_sp * 0.99

    for plane in planes:
        data = {}
        data['period'] = CORR_PERIOD
        data['amp'] = CORR_AMP
        data['cycles'] = CYCLES
        data['plane'] = pml.AXIS_NAMES[plane]
        data['quad'] = pml.prefix_from_element(quad)
        data['bpm'] = pml.quad_to_bpm(quad)[0]
        data['enabled_bpms'] = pml.enabled_bpms()
        corr_id, ap_corr = pml.effective_corrector(quad, plane)
        corr = Corrector(corr_id)
        caput(quad_pv, quad_high)
        now = excite.get_timestamp_fa()
        exc_high = get_excitation(corr, plane)
        exc_low = get_excitation(corr, plane)
        duration = (NETWORK_LAG + QUAD_LAG + SAFETY_NET
                    + exc_high.count + exc_low.count)
        # This should block until the second excitation has finished.
        if DECIMATED:
            duration = int(duration // 10)
        fa_buffer = fa.Buffer(BPM_IDS, duration, DECIMATED)
        high_start = now + NETWORK_LAG
        print('Time now: {}.'.format(now))
        print('High start time: {}.'.format(high_start))
        excite.excite_storage_ring_(high_start, (exc_high, exc_low), QUAD_LAG)
        # Sleep for first excitation
        cothread.Sleep((NETWORK_LAG + exc_high.count + SAFETY_NET) /
                       TICKS_PER_SECOND)
        # Move the quad
        caput(quad_pv, quad_low)
        # This will block until all data has been retrieved.
        fa_data = fa_buffer.get_data()
        print('FA data size: {}'.format(fa_data.shape))
        print('Final timestamp in data: {}'.format(fa_data[-1,0,0]))
        high_data, low_data = select_data(fa_data, exc_high, exc_low)
        print(high_data.shape, low_data.shape)
        data['high'] = high_data
        data['low'] = low_data
        save_data(data, quad, plane, 'jump')

    # restore setpoint
    caput(quad_pv, quad_sp)


if __name__ == '__main__':
    # debugging
    if '-d' in sys.argv:
        caput = test_caput
        excite.caput = test_caput
        cothread.oSleep = cothread.Sleep
        cothread.Sleep = test_Sleep
    QUAD_PV = 'SR01A-PC-Q1D-01'
    ap_quad = pml.quad_from_pv(QUAD_PV)
    jump_bba(ap_quad, (pml.X, pml.Y))
