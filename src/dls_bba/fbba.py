"""This file contains fast BBA specific functions and classes."""

import logging as log
from math import ceil
from statistics import mean, stdev
from typing import Any, Dict

import cothread
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from dls_bba.common import PLANE_VALUES, Algorithm, RawData, Results
from dls_bba.excite import Excitation, Oscillation, excite
from dls_bba.faa import TICKS_PER_SECOND, Buffer, get_timestamp

NETWORK_LAG_S = 0.5
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 0.5
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * TICKS_PER_SECOND)
FBBA_UNIT_CONVERSION = 1000


class FBBA(Algorithm):
    def __init__(self, accelerator):
        super().__init__(accelerator)
        self.configure()

    def configure(
        self,
        quadrupole_scalar=0.02,
        corrector_scalar=2,
        cycles=[22, 26],
        frequency=[11, 13],
        decimated=False,
        *args,
        **kwargs,
    ):
        """These are optional arguments, which are used during testing."""
        self.quadrupole_scalar = quadrupole_scalar  # 0.01 is old default
        self.corrector_scalar = float(corrector_scalar)  # 1 is old default
        self.cycles = cycles
        self.frequency = frequency
        self.decimated = decimated
        log.debug(
            f"Configuration: Cycles: {self.cycles}, Frequency: {self.frequency}, Quadrupole Scalar: {self.quadrupole_scalar}, Corrector Scalar: {self.corrector_scalar}, Decimated: {self.decimated}"
        )

    def run(self, element, plane_info, max_orbit) -> RawData:
        """Run the FBBA process."""
        metadata: Dict[str, Any] = {}
        quad_metadata: Dict[str, Any] = {}
        raw_data: Dict[str, Any] = {}

        metadata["algorithm"] = "FBBA"
        metadata["plane"] = plane_info
        log.info(f"{(metadata['algorithm'])} process started in {metadata['plane']}.")

        bpm, quad_list, corrector_x, corrector_y = self.select_elements(element)
        # Incompatability between pytaclattice and faa number of bpms.
        bpm_list = [0] + [i for i, _ in enumerate(self._accelerator.bpms, start=1)]

        bpm_pv_prefix = self._accelerator.element_to_pv_prefix(bpm)
        quad_pv_prefix_list = [
            self._accelerator.element_to_pv_prefix(quad_element)
            for quad_element in quad_list
        ]
        corrector_pv_prefix_x = self._accelerator.element_to_pv_prefix(
            corrector_x, PLANE_VALUES["HORIZONTAL"]
        )
        corrector_pv_prefix_y = self._accelerator.element_to_pv_prefix(
            corrector_y, PLANE_VALUES["VERTICAL"]
        )

        metadata["quadrupoles"] = quad_pv_prefix_list
        metadata["bpm_pv"] = bpm_pv_prefix
        metadata["bpm_index"] = self._accelerator.bpms.index(bpm)
        metadata["bpm_initial_xy"] = self.get_offsets(bpm_pv_prefix)
        metadata["corrector_X"] = [corrector_x, corrector_pv_prefix_x]
        metadata["corrector_Y"] = [corrector_y, corrector_pv_prefix_y]

        log.debug(f"Quads: {metadata['quadrupoles']}")
        log.debug(f"BPM: {metadata['bpm_pv']}, Index: {metadata['bpm_index']}")
        log.debug(
            f"Correctors: {metadata['corrector_X'][1]}, {metadata['corrector_Y'][1]}."
        )

        metadata["decimated"] = self.decimated
        metadata["enabled_bpms"] = self._accelerator.enabled_bpms
        metadata["quadrupole_scalar"] = self.quadrupole_scalar
        metadata["corrector_scalar"] = self.corrector_scalar

        for quad in quad_list:
            for values in PLANE_VALUES.values():
                quad_pv = self._accelerator.element_to_pv_prefix(quad).replace("-", "_")
                quad_step = (
                    self._accelerator.measure_quad(quad) * self.quadrupole_scalar
                )

                quad_metadata[f"{quad_pv}_{values.axis}"] = {
                    "plane": values,
                    "quadrupole": quad,
                    "quad_step": quad_step,
                    "frequency": self.frequency[values.index],
                    "period": TICKS_PER_SECOND // self.frequency[values.index],
                    "cycles": self.cycles[values.index],
                    "corrector": metadata[f"corrector_{values.axis}"][1],
                    "corr_step": self._accelerator.microrads(
                        metadata[f"corrector_{values.axis}"][0],
                        values,  # must be element not pv.
                    )
                    * self.corrector_scalar,
                }
                quad_metadata[f"{quad_pv}_{values.axis}"]["osc"] = Oscillation(
                    quad_metadata[f"{quad_pv}_{values.axis}"]["corr_step"],
                    quad_metadata[f"{quad_pv}_{values.axis}"]["plane"],
                    quad_metadata[f"{quad_pv}_{values.axis}"]["frequency"],
                    quad_metadata[f"{quad_pv}_{values.axis}"]["cycles"],
                )
        for key, value in quad_metadata.items():
            log.info(f"{key}: {value}")

        for quad in quad_list:
            metadata_key = self._accelerator.element_to_pv_prefix(quad).replace(
                "-", "_"
            )
            key_list = [key for key in quad_metadata.keys() if metadata_key in key]

            self.toggle_feedbacks(max_orbit)
            original_offsets = self.zero_origins(bpm)

            quad_sp = self._accelerator.measure_quad(quad)
            quad_step = quad_metadata[key_list[0]]["quad_step"]
            quad_high = quad_sp + quad_step
            quad_low = quad_sp - quad_step
            quad_lag_s = quad_step / QUAD_SLEW_RATE
            quad_lag = int(quad_lag_s * TICKS_PER_SECOND)

            osc_length = (
                ceil(TICKS_PER_SECOND / quad_metadata[key_list[0]]["frequency"])
                * quad_metadata[key_list[0]]["cycles"]
            )
            duration = NETWORK_LAG + osc_length + SAFETY_NET + quad_lag + osc_length

            # Move quad high
            self._accelerator.set_quad(quad, quad_high)
            cothread.Sleep(quad_lag_s / 2)

            now = get_timestamp(self.decimated)
            # Set off the data collection
            high_start = now + NETWORK_LAG
            fa_buffer = Buffer(bpm_list, high_start, duration, self.decimated)
            low_start = high_start + osc_length + SAFETY_NET + quad_lag
            excitation = {}
            for key in key_list:
                plane_info = quad_metadata[key]["plane"]
                corrector_key_dash = quad_metadata[key]["corrector"].replace("_", "-")
                corrector = self._accelerator.pv_prefix_to_element(
                    corrector_key_dash, plane_info
                )
                log.info(f"In: {quad_metadata[key]['corrector']}, Out: {corrector}")

                axis = quad_metadata[key]["plane"].axis
                excitation[f"High_{axis}"] = Excitation(
                    corrector,
                    quad_metadata[key]["osc"],
                    high_start,
                    self._accelerator,
                )
                excitation[f"Low_{axis}"] = Excitation(
                    corrector,
                    quad_metadata[key]["osc"],
                    low_start,
                    self._accelerator,
                )
            log.info(excitation)
            log.info("High Oscillation")
            high_keys = [key for key in excitation.keys() if "High_" in key]
            log.debug(excitation[high_keys[0]])
            excite((excitation[high_keys[0]], excitation[high_keys[0]]))

            # Sleep for first excitation. SAFETY_NET ensures that we don't start
            # moving the quad before the excitation has finished.
            cothread.Sleep(
                (NETWORK_LAG + excitation[high_keys[0]].count + SAFETY_NET)
                / TICKS_PER_SECOND
            )

            # Move quad from high to low
            self._accelerator.set_quad(quad, quad_low)
            log.info("Low Oscillation")
            low_keys = [key for key in excitation.keys() if "Low_" in key]
            excite((excitation[low_keys[0]], excitation[low_keys[1]]))

            # This will block until all data has been retrieved.

            fa_data = fa_buffer.get_data()
            for values in PLANE_VALUES.values():
                selected_data = self.select_data(fa_data, values)
                raw_data[f"{metadata_key}_{values.axis}"] = {
                    "High": selected_data[0],
                    "Low": selected_data[1],
                }

            self._accelerator.set_quad(quad, quad_sp)

            cothread.Sleep(quad_lag_s / 2)
            self.restore_origins(original_offsets)

        return RawData(raw_data, quad_metadata, metadata)

    def select_data(self, data, plane_info):
        """Extract FA data that covers the excitations exc_high and exc_low.

        The input data array should cover the full length of both excitations.

        """
        # Note: array data must include the timestamps.
        log.debug("Raw data shape: {}".format(data.shape))
        log.debug(
            "Timestamp range in raw data: {} - {}".format(data[0, 0, 0], data[-1, 0, 0])
        )
        log.debug("Excitation length: {}".format(self.exc_high.count))
        log.debug(
            "Trailing data to crop: {}.".format(
                data[-1, 0, 0] - (self.exc_low.start_time + self.exc_low.count)
            )
        )
        assert (
            self.exc_high.count == self.exc_low.count
        ), "Excitations different lengths"
        # Extract timestamps from data
        times = data[:, 0, 0]
        data = data[:, 1:, :]
        high_start = np.searchsorted(times, self.exc_high.start_time)
        low_start = np.searchsorted(times, self.exc_low.start_time)
        log.debug("Searched start times: %s, %s", high_start, low_start)
        # Ensure we include the entire oscillation if using decimated data.
        length = (
            ceil(self.exc_high.count / 10) if self.decimated else self.exc_high.count
        )
        high_data = data[high_start : high_start + length, :, plane_info.index]
        low_data = data[low_start : low_start + length, :, plane_info.index]
        log.debug("Selected data shape: {} {}".format(high_data.shape, low_data.shape))
        assert high_data.shape == low_data.shape
        return [high_data, low_data]

    def extract_freq_excite(self, data, known_freq, bpm_index):
        # Synchronous Detector Method

        # Incoming data arranged as [Time, Axis]

        # The mixing function creates a clean waveform at the known frequency
        # A dummy axis must be created to preserve shape through numpy operations
        # mix aranged as [Time, 1]
        mix = np.exp(
            2j * np.pi * known_freq / TICKS_PER_SECOND * np.arange(0, len(data)).T
        )
        mix = mix[:, None]

        # Run the mixing waveform over the data, aongside a hanning window
        # detector aranged as [Axis, 1]
        detector = 4 * (data * mix * np.hanning(len(mix))[:, None]).mean(0)

        # Find the phase of each axis; aranged as [Axis, 1]
        angle = np.angle(detector)

        # smodpi function to align the phases
        def smodpi(x):
            return np.mod(x + (np.pi / 2), np.pi) - (np.pi / 2)

        # Find the phase of the chosen BPM
        phase_bpm = angle[bpm_index]

        # Fix the angle of all BPMs to the chosen BPM
        # dector_fixed aranged as [Axis, 1]
        angle_fixed = smodpi(angle - phase_bpm)
        detector_fixed = detector * np.exp(-1j * (angle_fixed + phase_bpm))

        # Find the DC offset; aranged as [Axis, 1]
        dc_offset = detector_fixed.mean(0)

        # Reconstruct the clean wave; aranged as [Time, Axis]
        clean_wave = np.real(np.conj(detector_fixed) * mix) + dc_offset
        return clean_wave

    def analyse_data(self, raw_data, plot_output=False, *args, **kwargs):
        data = raw_data.raw_data
        # algorithm = raw_data["algorithm"] -> Not used.
        metadata = raw_data.metadata
        quad_metadata = raw_data.quad_metadata

        bpm_number = metadata["bpm_index"]
        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        bpm_index = bpm_number - np.sum(
            enabled_bpms[:bpm_number] == False  # noqa false positive
        )
        # freq = metadata["frequency"]

        results = {}

        quad_prefixs = []
        for key in data:
            quad_prefix = "_".join(key.split("_")[0:4])
            if quad_prefix not in quad_prefixs:
                quad_prefixs.append(quad_prefix)

        for quad in quad_prefixs:
            for values in PLANE_VALUES.values():
                key = f"{quad}_{values.axis}"

                # Remove bad BPMs and change units to um
                q_low = data[key]["Low"][:, enabled_bpms] * 1e-3
                q_high = data[key]["High"][:, enabled_bpms] * 1e-3

                q_high_clean = self.extract_freq_excite(
                    q_high, quad_metadata[key]["frequency"], bpm_index
                )
                q_low_clean = self.extract_freq_excite(
                    q_low, quad_metadata[key]["frequency"], bpm_index
                )

                # Take the difference between fits
                q_diff = q_high_clean - q_low_clean
                good = q_diff.std(0) > q_diff.std(0).max() / 2
                q_diff_good = q_diff[:, good]

                # Use a single fit operation, then transform with the straight line equation
                fit = np.polynomial.polynomial.polyfit(
                    q_high_clean[:, bpm_index], q_diff_good, 1
                )
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
                    for i, _ in enumerate(to_plot):
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
                # Change results to mm.
                offset_value = mean(p[:, 1]) / FBBA_UNIT_CONVERSION
                error_value = stdev(p[:, 1]) / FBBA_UNIT_CONVERSION
                results[f"{quad}_{values.axis}"] = (offset_value, error_value)
                log.debug(
                    f"Quad: {quad} {values.axis} offset calculated: {offset_value} +- {error_value}."
                )
        bpm_pv_prefix = metadata["bpm_pv"]
        return Results(results, bpm_pv_prefix, metadata)
