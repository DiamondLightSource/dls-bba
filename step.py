
import cothread
from cothread.catools import caput, caget
import sys
sys.path.append('/dls_sw/prod/R3.14.12.3/support/ploco/0-4')

from excite import TICKS_PER_SECOND, get_fa_data, get_timestamp_fa, get_timestamp_epics

CORR_STEPS = 5
CORR_PERIOD = 0.5 # s

# for testing purposes
def caput(pv, value):
    print 'caput %s  %s' % (pv, value)


def move_corrector(corr_id, corr_pv, corr_amp):

    start = caget(corr_pv)
    print('Initial corrector setpoint is %s.' % start)
    try:
        setpoint = 0
        step = (2.0 * corr_amp) / (CORR_STEPS - 1)
        setpoint = start - corr_amp - step
        start_tick = get_timestamp_fa()
        caput(corr_pv, setpoint)
        for i in range(CORR_STEPS):
            setpoint += step
            caput(corr_pv, setpoint)
            cothread.Sleep(CORR_PERIOD)

        end_tick = get_timestamp_fa()
    finally:
        caput(corr_pv, start)

    print 'calc duration:', CORR_STEPS * CORR_PERIOD * 10072
    print 'meas duration:', end_tick - start_tick
    return start_tick, end_tick - start_tick


def crop_data(start_time, data):
    # We want data definitely within each timestep.
    # Assume that the data is decimated.
    print data.shape
    timestamps = data[:,0,0]
    assert timestamps[0] < start_time < timestamps[-1]
    print 'extra data:', start_time - timestamps[0]
    print 'relevant data:', timestamps[-1] - start_time
    length = data.shape[0]
    samples_per_step = CORR_PERIOD * 1000
    edge = samples_per_step * 0.2
    samples = samples_per_step * 0.6
    # 0.1 + n * CORR_PERIOD + 0.1
    for i, item in enumerate(timestamps):
        if item > start_time:
            sample_start = i + edge
            print 'started at sample', i
            break
    data_slices = []
    for i in range(CORR_STEPS):
        print 'selecting %s to %s' % (sample_start, sample_start+samples)
        data_slices.append(data[sample_start:sample_start+samples,:,:])
        sample_start += samples_per_step

    return data_slices

