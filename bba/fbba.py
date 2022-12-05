"""This file contains fast BBA specific functions and classes."""

import logging as log
from math import ceil
from statistics import mean

import cothread
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from bba.common import Algorithm, RawData, Results
from bba.excite import Excitation, Oscillation, excite
from bba.faa import TICKS_PER_SECOND, Buffer, get_timestamp

NETWORK_LAG_S = 0.5
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 0.5
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * TICKS_PER_SECOND)


class FBBA(Algorithm):
    def __init__(self, accelerator):
        super().__init__(accelerator)
        self.configure()

    def configure(self, quadrupole_scalar=0.01, cycles=1, frequency=8, decimated=False):
        """These are optional arguments, which are used during testing."""
        self.quadrupole_scalar = quadrupole_scalar
        self.cycles = cycles
        self.frequency = frequency
        self.decimated = decimated
        # self.PLOT_GRAPHS = PLOT_GRAPHS

    def run(self, element, plane_info, max_orbit, temp_corr_amp=None) -> RawData:
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
            "bpm_pv" : bpm_pv_prefix,
            "bpm_index" : self._accelerator.bpms.index(bpm),
            "corrector" : corrector_pv_prefix,
            "decimated" : self.decimated,
            "enabled_bpms" : self._accelerator.enabled_bpms}

        for quad in quad_list:
            self.toggle_feedbacks(max_orbit)
            original_offsets = self.zero_origins(bpm, plane_info)
            quad_step = self._accelerator.measure_quad(quad) * self.quadrupole_scalar
            # Changed for testing.
            if temp_corr_amp is None:
                corr_amp = self._accelerator.microrads(corrector, plane_info)
            else:
                corr_amp = temp_corr_amp
            log.info(f"Quad step: {quad_step}, Corrector step: {corr_amp}.")

            osc = Oscillation(corr_amp, plane_info, self.frequency, self.cycles)
            self.osc = osc

            log.info(
                "Oscillation amplitude {}; frequency {}; cycles {}".format(
                    osc.amp, osc.freq, osc.cycles))
            metadata["frequency"] = self.osc.freq
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
            raw_data[self._accelerator.element_to_pv_prefix(quad) + ":High"] = selected_data[0]
            raw_data[self._accelerator.element_to_pv_prefix(quad) + ":Low"] = selected_data[1]

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

    def extract_freq_fft(self, data, freq):
        index = freq - 2
        data_i = np.fft.rfft(data, axis=0)
        data_i_f = np.zeros(data_i.shape, "complex")
        data_i_f[index] = data_i[index]
        return np.fft.irfft(data_i_f, axis=0)

    def extract_freq_excite(self, data, freq):
        data_length = data.shape[0]
        num_oscs = 1.0 * data_length * freq / TICKS_PER_SECOND
        num_oscs = num_oscs * 10 if self.decimated else num_oscs

        osc = np.exp(np.linspace(0, 2j * np.pi * num_oscs, data_length))
        osc = np.tile(osc, (data.shape[1], 1)).T
        data_es = np.mean(data * osc, 0)

        reverse_osc = np.exp(np.linspace(0, -2j * np.pi * num_oscs, data_length))
        reverse_osc = np.tile(reverse_osc, (data.shape[1], 1)).T
        # Force the phase to zero by using only the imaginary part of the mean
        return 2 * np.real(reverse_osc * 1j * np.imag(data_es))

    def analyse_data(self, raw_data, plot_output, use_fft=False, *args, **kwargs) -> Results:
        data = raw_data.raw_data
        # algorithm = raw_data["algorithm"] -> Not used.
        metadata = raw_data.metadata

        bpm_number = metadata["bpm_index"]
        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        bpm_index = bpm_number - np.sum(enabled_bpms[:bpm_number] == False)  # noqa false positive
        freq = TICKS_PER_SECOND / metadata["period"]

        offsets = []
        errors = []

        quad_prefixs = []
        for key in data:
            quad_prefix = "_".join(key.split("_")[0:4])
            if quad_prefix not in quad_prefixs:
                quad_prefixs.append(quad_prefix)
        for quad in quad_prefixs:
            low_key = quad + "_Low"
            high_key = quad + "_High"

            # Remove bad BPMs and change units to um
            q_low = data[low_key][:, enabled_bpms] * 1e-3
            q_high = data[high_key][:, enabled_bpms] * 1e-3

            # Extract the DC componenet of the orbit, and add it to the excitation
            q_high_dc = q_high.mean(0)
            q_low_dc = q_low.mean(0)
            if use_fft:
                q_high_clean = np.add(self.extract_freq_fft(q_high - q_high_dc, freq), q_high_dc)
                q_low_clean = np.add(self.extract_freq_fft(q_low - q_low_dc, freq), q_low_dc)
            else:
                q_high_clean = np.add(self.extract_freq_excite(q_high - q_high_dc, freq), q_high_dc)
                q_low_clean = np.add(self.extract_freq_excite(q_low - q_low_dc, freq), q_low_dc)

            # Take the difference between fits
            q_diff = q_high_clean - q_low_clean
            good = q_diff.std(0) > q_diff.std(0).max() / 2
            q_diff_good = q_diff[:, good]

            # Use a single fit operation, then transform with the straight line equation
            fit = np.polynomial.polynomial.polyfit(q_high_clean[:, bpm_index], q_diff_good, 1)
            p = np.array([1 / fit[1], -fit[0] / fit[1]]).T
            # Produce a large graph
            if plot_output:
                to_plot = [q_high_clean, q_low_clean, q_diff, q_diff_good, p]
                plot_labels = [
                    "quad high clean",
                    "quad low clean,",
                    "quad diff,",
                    "quad diff good,",
                    "fit coefficients",
                ]
                # Make a grid three wide and N high
                # Fill with 1D plot, image plot, and colourbar
                gs = GridSpec(
                    len(to_plot) + 1,
                    3,
                    width_ratios=(20, 20, 1),
                    height_ratios=([1] * len(to_plot) + [3]),
                )
                for i in range(len(to_plot)):
                    plt.subplot(gs[i, 0]).plot(to_plot[i])
                    plt.ylabel(plot_labels[i])
                    im = plt.subplot(gs[i, 1]).imshow(
                        to_plot[i], aspect="auto", interpolation="nearest"
                    )
                    plt.colorbar(im, cax=plt.subplot(gs[i, 2]))
                # Add a large 1D plot to show end result
                plt.subplot(gs[-1, :]).plot(q_high_clean[:, bpm_index], q_diff_good)
                plt.ylabel(f"BPM {bpm_number + 1} aginst BPMs")
                plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
                plt.show()
            offsets.append(p[:, 1].mean())
            errors.append(p[:, 1].std())

        results = {}
        for index, number in enumerate(offsets):

            quadrupole = quad_prefixs[index]
            offset = offsets[index]
            error = errors[index]
            quad_name = quadrupole.replace("_", "-")
            print(f"Quad: {quad_name} offset calculated: {offset} +- {error}.")
            results[quadrupole] = [offset, error]

        offset = mean(offsets)
        error = mean(errors)
        sum_error = 0
        # TODO: Fix error propagation.
        for place, error in enumerate(error):
            sum_error += (error/offset[place]) ** 2
        sum_error = np.sqrt(sum_error) * offset

        bpm_pv_prefix = metadata['bpm'][0]
        print(f"BPM: {bpm_pv_prefix} offset calculated: {offset} +- {sum_error}.")
        return Results(results, bpm_pv_prefix, metadata)
