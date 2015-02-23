
import cothread
from cothread.catools import caput, caget
import sys
sys.path.append('/dls_sw/prod/R3.14.12.3/support/ploco/0-4')

from excite import TICKS_PER_SECOND, get_fa_data, get_timestamp_fa, get_timestamp_epics

CORR_STEPS = 5
CORR_PERIOD = 0.5 # s

# for testing purposes
def caget(pv):
    print 'caget %s' % pv
    return 10

def caput(pv, value):
    print 'caput %s:%s' % (pv, value)


def move_corrector(corr_id, corr_pv, corr_amp):

    start = caget(corr_pv)
    setpoint = 0
    step = (2.0 * corr_amp) / (CORR_STEPS - 1)
    setpoint = start - corr_amp - step
    start_tick = get_timestamp_fa
    caput(corr_pv, setpoint)
    for i in range(CORR_STEPS):
        setpoint += step
        caput(corr_pv, setpoint)
        cothread.Sleep(CORR_PERIOD)

    caput(corr_pv, start)

    return start_tick, CORR_STEPS * CORR_PERIOD * 10072

def crop_data(data):
    # We want data definitely within each timestep.
    length = data.shape[0]
    samples_per_step = CORR_PERIOD * 1000
    edge = samples_per_step * 0.2
    samples = samples_per_step * 0.6
    # 0.1 + n * CORR_PERIOD + 0.1
    sample_start = 0.1 * 1000 + edge
    data_slices = []
    for i in range(CORR_STEPS):
        data_slices.append(data[sample_start:sample_start+samples,:,:])
        sample_start += samples_per_step

    return data_slices

