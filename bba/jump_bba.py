import datetime
import logging as log
import math

import cothread
import numpy
import scipy.io
from cothread.catools import caget, caput

from bba import faa, pml
from bba.pml import excite, utils

NETWORK_LAG_S = 0.5
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 0.5  # A/s
NETWORK_LAG = int(NETWORK_LAG_S * faa.TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * faa.TICKS_PER_SECOND)
DECIMATED = True

BPM_IDS = range(174)  # 173 plus 0 for timestamps


def get_filename_prefix():
    now = datetime.datetime.now()
    datestring = now.strftime("%Y-%m-%dT%H-%M-%S")
    return "bba-{}".format(datestring)


def save_data(high_data, low_data, quad, osc, lattice):
    """Save the provided arrays into a .mat file with additional metadata."""
    quad_prefix = quad.get_device("b1").name
    plane_name = pml.AXIS_NAMES[osc.plane]
    period = faa.TICKS_PER_SECOND // osc.freq
    datadict = {"period": period, "amp": osc.amp, "cycles": osc.cycles}
    datadict["quad"] = quad_prefix
    datadict["plane"] = plane_name
    datadict["bpm"] = utils.quad_to_bpm(quad, lattice)[0]
    datadict["enabled_bpms"] = utils.enabled_bpms().astype(numpy.int)
    datadict["high"] = high_data
    datadict["low"] = low_data
    filename = "data/{}-{}-{}".format(get_filename_prefix(), quad_prefix, plane_name)
    scipy.io.savemat(filename, datadict, oned_as="row")
    log.info("Saved data to {}\n".format(filename))


def select_data(data, plane, exc_high, exc_low):
    """Extract FA data that covers the excitations exc_high and exc_low.

    The input data array should cover the full length of both excitations.

    """
    # Note: array data must include the timestamps.
    log.debug("Raw data shape: {}".format(data.shape))
    log.info(
        "Timestamp range in raw data: {} - {}".format(data[0, 0, 0], data[-1, 0, 0])
    )
    log.debug("Excitation length: {}".format(exc_high.count))
    log.debug(
        "Trailing data to crop: {}.".format(
            data[-1, 0, 0] - (exc_low.start_time + exc_low.count)
        )
    )
    assert exc_high.count == exc_low.count, "Excitations different lengths"
    # Extract timestamps from data
    times = data[:, 0, 0]
    data = data[:, 1:, :]
    high_start = numpy.searchsorted(times, exc_high.start_time)
    low_start = numpy.searchsorted(times, exc_low.start_time)
    log.debug("Searched start times: %s, %s", high_start, low_start)
    # Ensure we include the entire oscillation if using decimated data.
    length = math.ceil(exc_high.count / 10) if DECIMATED else exc_high.count
    high_data = data[high_start: high_start + length, :, plane]
    low_data = data[low_start: low_start + length, :, plane]
    log.info("Selected data shape: {} {}".format(high_data.shape, low_data.shape))
    assert high_data.shape == low_data.shape
    return high_data, low_data


def summarise_bba(quad, quad_step, osc):
    """Log information about one BBA instance."""
    prefix = quad.get_device("b1").name
    plane = pml.AXIS_NAMES[osc.plane]
    log.info("BBA of quad {} in plane {}".format(prefix, plane))
    log.info("Quad step is {}".format(quad_step))
    log.info(
        "Oscillation amplitude {}; frequency {}; cycles {}".format(
            osc.amp, osc.freq, osc.cycles
        )
    )


def jump_bba(quad, quad_step, osc, lattice):
    """Execute 'jump BBA' for one quad and save the data."""
    # Do we need undecimated data?
    summarise_bba(quad, quad_step, osc)
    quad_pv = quad.get_pv_name(field="b1", handle="setpoint")
    quad_sp = caget(quad_pv)
    quad_high = quad_sp + quad_step
    quad_low = quad_sp - quad_step
    quad_lag_s = quad_step / QUAD_SLEW_RATE
    quad_lag = int(quad_lag_s * faa.TICKS_PER_SECOND)

    corr_id, ap_corr = pml.utils.effective_corrector(quad, osc.plane, lattice)
    field = "x_kick" if osc.plane == pml.definitions.X else "y_kick"
    log.info("Using corrector {}: {}".format(corr_id, ap_corr.get_device(field).name))
    # Move quad high
    caput(quad_pv, quad_high)
    cothread.Sleep(quad_lag_s / 2)
    now = faa.get_timestamp()
    osc_length = math.ceil(excite.TICKS_PER_SECOND / osc.freq) * osc.cycles
    # Set off the data collection
    high_start = now + NETWORK_LAG
    duration = NETWORK_LAG + osc_length + SAFETY_NET + quad_lag + osc_length
    fa_buffer = faa.Buffer(BPM_IDS, high_start, duration, DECIMATED)
    low_start = high_start + osc_length + SAFETY_NET + quad_lag
    log.debug("Safety net: {}; quad_lag: {}".format(SAFETY_NET, quad_lag))
    log.info("Time now: {}.".format(now))
    log.info("High start time: {}.".format(high_start - now))
    log.info("Low start time: {}.".format(low_start - now))
    log.debug("The oscillation: {}".format(osc))
    exc_high = excite.Excitation(ap_corr, osc, high_start)
    log.debug(
        "The excitation: dwell {} count {}".format(exc_high.dwell, exc_high.count)
    )
    exc_low = excite.Excitation(ap_corr, osc, low_start)
    excite.excite((exc_high,))
    # Sleep for first excitation. SAFETY_NET ensures that we don't start
    # moving the quad before the excitation has finished.
    cothread.Sleep((NETWORK_LAG + exc_high.count + SAFETY_NET) / faa.TICKS_PER_SECOND)
    # Move quad from high to low
    caput(quad_pv, quad_low)
    # Set up second excitation
    excite.excite((exc_low,))
    # This will block until all data has been retrieved.
    fa_data = fa_buffer.get_data()
    high_data, low_data = select_data(fa_data, osc.plane, exc_high, exc_low)
    save_data(high_data, low_data, quad, osc, lattice)

    # Restore setpoint.  We don't need SAFETY_NET here because we've saved
    # all the data before we request the move.
    caput(quad_pv, quad_sp)
    cothread.Sleep(quad_lag_s / 2)
