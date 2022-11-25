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

        bpm, quad_list, corrector = self.select_elements(element, plane_info)
        quad_pv_list = [self._accelerator.element_to_pv_prefix(quad_element) for quad_element in quad_list]
        bpm_pv_prefix = self._accelerator.element_to_pv_prefix(bpm)
        corrector_pv_prefix = self._accelerator.element_to_pv_prefix(corrector, plane_info)
        log.info(f"Quads: {quad_pv_list}, BPM: {bpm_pv_prefix}, Corrector: {corrector_pv_prefix}.")
        raw_data = {}
        metadata = {
            "plane" : plane_info,
            "quad" : quad_pv_list,
            "bpm" : [bpm_pv_prefix, self._accelerator.bpms.index(bpm)],
            "corrector" : corrector_pv_prefix,
            "decimated" : self.decimated,
            "enabled_bpms" : self._accelerator.enabled_bpms}

        for quad in quad_list:
            self.toggle_feedbacks(max_orbit)
            original_offsets = self.zero_origins(bpm, plane_info)
            quad_step = self._accelerator.measure_quad(quad) * self.quadrupole_scalar
            # Changed for testing. 
            if temp_corr_amp == None:
                corr_amp = self._accelerator.microrads(corrector, plane_info)
            else:
                corr_amp = temp_corr_amp
            log.info(f"Quad step: {quad_step}, Corrector step: {corr_amp}.")

            osc = Oscillation(corr_amp, plane_info, self.frequency, self.cycles)
            self.osc = osc

            log.info(
                "Oscillation amplitude {}; frequency {}; cycles {}".format(
                    osc.amp, osc.freq, osc.cycles))
            metadata["period"] = TICKS_PER_SECOND // self.osc.freq
            metadata["amp"] = self.osc.amp
            metadata["cycles"] = self.osc.cycles

            quad_sp = self._accelerator.measure_quad(quad)
            quad_high = quad_sp + quad_step
            quad_low = quad_sp - quad_step
            quad_lag_s = quad_step / QUAD_SLEW_RATE
            quad_lag = int(quad_lag_s * TICKS_PER_SECOND)

            # Move quad high
            self._accelerator.set_quad(quad, quad_high)
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
            self.exc_high = Excitation(corrector, osc, high_start, self._accelerator)
            log.debug(
                "The excitation: dwell {} count {}".format(self.exc_high.dwell, self.exc_high.count))
            self.exc_low = Excitation(corrector, osc, low_start, self._accelerator)

            excite((self.exc_high,))
            # Sleep for first excitation. SAFETY_NET ensures that we don't start
            # moving the quad before the excitation has finished.
            cothread.Sleep((NETWORK_LAG + self.exc_high.count + SAFETY_NET) / TICKS_PER_SECOND)
            # Move quad from high to low
            self._accelerator.set_quad(quad, quad_low)
            # Set up second excitation
            excite((self.exc_low,))
            # This will block until all data has been retrieved.

            fa_data = fa_buffer.get_data()
            selected_data = self.select_data(fa_data, plane_info)
            raw_data[self._accelerator.element_to_pv_prefix(quad)+":High"] = selected_data[0]
            raw_data[self._accelerator.element_to_pv_prefix(quad)+":Low"] = selected_data[1]

            self._accelerator.set_quad(quad, quad_sp)
            cothread.Sleep(quad_lag_s / 2)
            self.restore_origins(original_offsets)

        return RawData(raw_data, method, metadata)

    def select_data(self, data, plane_info):
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
        high_data = data[high_start: high_start + length, :, plane_info.index]
        low_data = data[low_start: low_start + length, :, plane_info.index]
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
