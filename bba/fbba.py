"""This file contains fast BBA specific functions and classes"""

from math import ceil
import logging as log

import cothread
import scipy.io as io

from bba.common import Algorithm
from bba import excite
from bba.faa import TICKS_PER_SECOND, get_timestamp, Buffer

class FBBA(Algorithm):
    def __init__(self):
        pass

    def setup(self, accelerator, quad, plane_dict):
        """This are required arguments."""
        self.accelerator = accelerator
        self.quad = quad
        self.plane_dict = plane_dict

        # These are unlikely to ever change.
        self.NETWORK_LAG_S = 0.5
        self.SAFETY_NET_S = 0.1
        self.QUAD_SLEW_RATE = 0.5  # A/s
        self.NETWORK_LAG = int(self.NETWORK_LAG_S * TICKS_PER_SECOND)
        self.SAFETY_NET = int(self.SAFETY_NET_S * TICKS_PER_SECOND)

    def config(self, QUADRUPOLE_SCALAR = 0.01, CYCLES = 1, FREQUENCY = 8):
        """These are optional arguments, which are used during testing."""
        self.QUADRUPOLE_SCALAR = QUADRUPOLE_SCALAR
        self.CYCLES = CYCLES
        self.FREQUENCY = FREQUENCY

        self.DECIMATED = False
        self.PLOT_GRAPHS = True

    def run_bba(self):
        quad_prefix = self.accelerator.prefix_from_element(self.quad, "b1")
        log.warning("BBA on quad {} in plane {}".format(quad_prefix, self.plane_dict.axis))
        quad_step = self.accelerator.measure_quad(self.quad) * self.QUADRUPOLE_SCALAR
        corrector_index, corr_element = self.accelerator.effective_corrector(self.quad, self.plane_dict)
        corr_pv = self.accelerator.element_to_pv(corr_element, self.plane_dict)
        new_corr_amp = self.accelerator.microrads(corr_pv)
        osc = excite.Oscillation(new_corr_amp, self.plane_dict, self.FREQUENCY, self.CYCLES)
                #jump_bba.jump_bba(self.quad, quad_step, osc, self.accelerator)

        # Jump bba.
        prefix = self.accelerator.quad_to_pv(self.quad)
        log.info("BBA of quad {} in plane {}".format(prefix, osc.plane.axis))
        log.info("Quad step is {}".format(quad_step))
        log.info(
            "Oscillation amplitude {}; frequency {}; cycles {}".format(
                osc.amp, osc.freq, osc.cycles))

        quad_sp = self.accelerator.measure_quad(self.quad)
        quad_high = quad_sp + quad_step
        quad_low = quad_sp - quad_step
        quad_lag_s = quad_step / self.QUAD_SLEW_RATE
        quad_lag = int(quad_lag_s * TICKS_PER_SECOND)

        corr_id, ap_corr = self.accelerator.effective_corrector(self.quad, osc.plane)
        field = osc.plane.kick
        log.info("Using corrector {}: {}".format(corr_id, ap_corr.get_device(field).name))
        # Move quad high
        self.accelerator.set_quad(self.quad, quad_high)
        cothread.Sleep(quad_lag_s / 2)
        now = get_timestamp()
        osc_length = ceil(TICKS_PER_SECOND / osc.freq) * osc.cycles
        # Set off the data collection
        high_start = now + self.NETWORK_LAG
        duration = self.NETWORK_LAG + osc_length + self.SAFETY_NET + quad_lag + osc_length
        # Incompatability between pytaclattice and faa number of bpms.
        bpm_list = [i for i in range(len(self.accelerator.bpms) + 1)]
        fa_buffer = Buffer(bpm_list, high_start, duration, self.DECIMATED)
        low_start = high_start + osc_length + self.SAFETY_NET + quad_lag
        log.debug("Safety net: {}; quad_lag: {}".format(self.SAFETY_NET, quad_lag))
        log.info("Time now: {}.".format(now))
        log.info("High start time: {}.".format(high_start - now))
        log.info("Low start time: {}.".format(low_start - now))
        log.debug("The oscillation: {}".format(osc))
        self.exc_high = excite.Excitation(ap_corr, osc, high_start, self.accelerator)
        log.debug(
            "The excitation: dwell {} count {}".format(self.exc_high.dwell, self.exc_high.count))
        self.exc_low = excite.Excitation(ap_corr, osc, low_start, self.accelerator)
        excite.excite((self.exc_high,))
        # Sleep for first excitation. SAFETY_NET ensures that we don't start
        # moving the quad before the excitation has finished.
        cothread.Sleep((self.NETWORK_LAG + self.exc_high.count + self.SAFETY_NET) / TICKS_PER_SECOND)
        # Move quad from high to low
        self.accelerator.set_quad(self.quad, quad_low)
        # Set up second excitation
        excite.excite((self.exc_low,))
        # This will block until all data has been retrieved.
        fa_data = fa_buffer.get_data()
        high_data, low_data = self.select_data(fa_data)
        self.high_data = high_data
        self.low_data = low_data
        #save_data(self.high_data, self.low_data, self.quad, osc, self.accelerator)

        # Restore setpoint.  We don't need SAFETY_NET here because we've saved
        # all the data before we request the move.
        self.accelerator.set_quad(self.quad, quad_sp)
        cothread.Sleep(quad_lag_s / 2)
        # analyse data and return results


    def select_data(self, data):
        """Extract FA data that covers the excitations exc_high and exc_low.

        The input data array should cover the full length of both excitations.

        """
        # Note: array data must include the timestamps.
        log.debug("Raw data shape: {}".format(data.shape))
        log.info(
            "Timestamp range in raw data: {} - {}".format(data[0, 0, 0], data[-1, 0, 0]))
        log.debug("Excitation length: {}".format(self.exc_high.count))
        log.debug("Trailing data to crop: {}.".format(
                data[-1, 0, 0] - (self.exc_low.start_time + self.exc_low.count)))
        assert self.exc_high.count == self.exc_low.count, "Excitations different lengths"
        # Extract timestamps from data
        times = data[:, 0, 0]
        data = data[:, 1:, :]
        high_start = np.searchsorted(times, self.exc_high.start_time)
        low_start = np.searchsorted(times, self.exc_low.start_time)
        log.debug("Searched start times: %s, %s", high_start, low_start)
        # Ensure we include the entire oscillation if using decimated data.
        length = ceil(self.exc_high.count / 10) if self.DECIMATED else self.exc_high.count
        high_data = data[high_start: high_start + length, :, self.plane_dict.index]
        low_data = data[low_start: low_start + length, :, self.plane_dict.index]
        log.info("Selected data shape: {} {}".format(high_data.shape, low_data.shape))
        assert high_data.shape == low_data.shape
        return high_data, low_data


    def save_data(self, prefix):
        """Save the provided arrays into a .mat file with additional metadata."""
        quad_prefix = self.accelerator.quad_2_pv(self.quad)
        plane_name = self.plane_dict.axis
        period = TICKS_PER_SECOND // self.osc.freq #TODO: Wont work: osc isnt self.
        datadict = {"period": period, "amp": osc.amp, "cycles": osc.cycles} #TODO: Wont work: osc isnt self.
        datadict["quad"] = quad_prefix
        datadict["plane"] = plane_name
        datadict["bpm"] = self.accelerator.quad_to_bpm(self.quad)[0]
        datadict["enabled_bpms"] = self.accelerator.enabled_bpms()
        datadict["high"] = self.high_data
        datadict["low"] = self.low_data
        filename = "data/{}-{}-{}".format(prefix, quad_prefix, plane_name)
        io.savemat(filename, datadict, oned_as="row")
        log.info("Saved data to {}\n".format(filename))

    def analyse_data():
        print("Analyse Data")
        pass

    def apply_results():
        print("Applied Result")
        pass