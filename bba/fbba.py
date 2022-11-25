"""This file contains fast BBA specific functions and classes"""

from math import ceil
import logging as log

import cothread
import scipy.io as io
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
from cothread.catools import caget, caput

from bba.common import Algorithm, RawData, Results
from bba.excite import excite, Oscillation, Excitation
from bba.faa import TICKS_PER_SECOND, get_timestamp, Buffer

NETWORK_LAG_S = 0.5
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 0.5
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * TICKS_PER_SECOND)

class FBBA(Algorithm):
    def __init__(self, accelerator):
        super().__init__(accelerator)
        self.configure()

    def configure(self, quadrupole_scalar = 0.01, cycles = 1, frequency = 8, decimated = False):
        """These are optional arguments, which are used during testing."""
        self.quadrupole_scalar = quadrupole_scalar
        self.cycles = cycles
        self.frequency = frequency
        self.decimated = decimated
        # self.PLOT_GRAPHS = PLOT_GRAPHS

    def run(self, element, plane_info, max_orbit, temp_corr_amp = None) -> RawData:
        """Run the FBBA process."""
        method = "FBBA"
        log.info(f"{method} process started in plane {plane_info.axis}.")

        self.plane_info = plane_info
        log.info(f"FBBA process started in plane {self.plane_info.axis}.")

        self.quad_bpm_corr(element)
        log.info(f"Quad: {self.quad_pv}, BPM: {self.bpm_pv}, Corrector: {self.corrector_pv}.")

        quad_step = self._accelerator.measure_quad(self.quad) * self.quadrupole_scalar
        corr_amp = self._accelerator.microrads(self.corrector, self.plane_info)
        log.info(f"Quad step: {quad_step}, Corrector step: {corr_amp}.")


        

        osc = excite.Oscillation(corr_amp, self.plane_info, self.frequency, self.cycles)
        self.osc = osc
                #jump_bba.jump_bba(self.quad, quad_step, osc, self.accelerator)

        log.info(
            "Oscillation amplitude {}; frequency {}; cycles {}".format(
                osc.amp, osc.freq, osc.cycles))

        quad_sp = self._accelerator.measure_quad(self.quad)
        quad_high = quad_sp + quad_step
        quad_low = quad_sp - quad_step
        quad_lag_s = quad_step / QUAD_SLEW_RATE
        quad_lag = int(quad_lag_s * TICKS_PER_SECOND)



        #corr_id, ap_corr = self._accelerator.effective_corrector(self.bpm, osc.plane)
        field = osc.plane.kick
        log.info("Using corrector: {}".format(self.corrector.get_device(field).name))
        # Move quad high
        self._accelerator.set_quad(self.quad, quad_high)
        cothread.Sleep(quad_lag_s / 2)
        now = get_timestamp(self.decimated)
        osc_length = ceil(TICKS_PER_SECOND / osc.freq) * osc.cycles
        # Set off the data collection
        high_start = now + NETWORK_LAG
        duration = NETWORK_LAG + osc_length + SAFETY_NET + quad_lag + osc_length
        # Incompatability between pytaclattice and faa number of bpms.
        bpm_list = [i for i in range(len(self._accelerator.bpms) + 1)]
        fa_buffer = Buffer(bpm_list, high_start, duration, self.decimated)
        low_start = high_start + osc_length + SAFETY_NET + quad_lag
        log.debug("Safety net: {}; quad_lag: {}".format(SAFETY_NET, quad_lag))
        log.info("Time now: {}.".format(now))
        log.info("High start time: {}.".format(high_start - now))
        log.info("Low start time: {}.".format(low_start - now))
        log.debug("The oscillation: {}".format(osc))
        self.exc_high = excite.Excitation(self.corrector, osc, high_start, self._accelerator)
        log.debug(
            "The excitation: dwell {} count {}".format(self.exc_high.dwell, self.exc_high.count))
        self.exc_low = excite.Excitation(self.corrector, osc, low_start, self._accelerator)
        excite.excite((self.exc_high,))
        # Sleep for first excitation. SAFETY_NET ensures that we don't start
        # moving the quad before the excitation has finished.
        cothread.Sleep((NETWORK_LAG + self.exc_high.count + SAFETY_NET) / TICKS_PER_SECOND)
        # Move quad from high to low
        self._accelerator.set_quad(self.quad, quad_low)
        # Set up second excitation
        excite.excite((self.exc_low,))
        # This will block until all data has been retrieved.
        fa_data = fa_buffer.get_data()
        results = self.select_data(fa_data)
                #save_data(self.high_data, self.low_data, self.quad, osc, self.accelerator)
        # Restore setpoint.  We don't need SAFETY_NET here because we've saved
        # all the data before we request the move.
        self._accelerator.set_quad(self.quad, quad_sp)
        cothread.Sleep(quad_lag_s / 2)        
        return results


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
        length = ceil(self.exc_high.count / 10) if self.decimated else self.exc_high.count
        high_data = data[high_start: high_start + length, :, self.plane_info.index]
        low_data = data[low_start: low_start + length, :, self.plane_info.index]
        log.info("Selected data shape: {} {}".format(high_data.shape, low_data.shape))
        assert high_data.shape == low_data.shape
        return [high_data, low_data]


    def save_data(self, prefix):
        """Save the provided arrays into a .mat file with additional metadata."""
        quad_prefix = self._accelerator.quad_to_pv(self.quad)
        plane_name = self.plane_info.axis
        period = TICKS_PER_SECOND // self.osc.freq
        datadict = {"period": period, "amp": self.osc.amp, "cycles": self.osc.cycles}
        datadict["method"] = "FBBA"
        datadict["decimated"] = self.decimated
        datadict["quad"] = quad_prefix
        datadict["plane"] = plane_name
        datadict["bpm"] = self._accelerator.quad_to_bpm(self.quad)[0]
        datadict["enabled_bpms"] = self._accelerator.enabled_bpms
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
