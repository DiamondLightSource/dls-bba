import logging as log
from typing import Any, Dict, List, Tuple

import numpy as np
from cothread import Sleep

from dls_bba.algorithm import Algorithm
from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
from dls_bba.excite import NETWORK_LAG, SAFETY_NET, Excitation, Oscillation, excite
from dls_bba.faa import TICKS_PER_SECOND, Buffer, get_timestamp
from dls_bba.isotime import get_isotime
from dls_bba.machine import QUAD_SLEW_RATE, Machine

NM_TO_MM_UNIT_CONV = 1000000
"""Conversion factor from nanometers to millimeters."""


class FastBBA(Algorithm):
    """Fast BBA algorithm."""

    def __init__(self, machine: Machine) -> None:
        """Initialise Fast BBA algorithm.

        Args:
            machine: Machine object.
        """
        super().__init__(machine)

    def run(self, components_pair: List[Components]) -> RawData:
        """The Fast BBA Process.

        Args:
            components_pair: The components pair to run the algorithm on.

        Returns:
            The RawData object
        """
        rawdata: Dict[str, Any] = {}
        metadata: Dict[str, Any] = {}
        config = self._machine.config.get_settings()
        metadata.update(config)
        metadata["method"] = "FastBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._machine.get_enabled_bpms()
        metadata["bpm_name"] = components_pair[0].bpm_name
        metadata["bpm_index"] = components_pair[0].bpm_index
        decimated: bool = config["DECIMATED"]

        for components in components_pair:
            log.debug(f"Component: {components}")
            for quadrupole, quad_name in zip(
                components.quadrupoles, components.quadrupoles_names
            ):
                log.debug(f"Quad: {quad_name} of {components.quadrupoles_names}")
                (
                    quad_start,
                    quad_high,
                    quad_low,
                    quad_sp,
                    quad_step,
                ) = self.calculate_quad_setpoints(quadrupole)

                corr_kick = self._machine.corrector_kick(components)
                corr_sp = self._machine.get_corrector_setpoint(components)

                key = f"{quad_name}_{components.axis}"
                metadata[key] = {
                    "components": components.as_dict(),
                    "quad_start_high_low_sp": [
                        quad_start,
                        quad_high,
                        quad_low,
                        quad_sp,
                        quad_step,
                    ],
                    "corrector_sp": corr_sp,
                    "corrector_kick": corr_kick,
                }

                # Always overshoot the high quad step and work down and keep direction
                # consistent to mitigate unwanted hysteresis effects.
                # FYI correctors are significantly less prone to hysteresis effects.
                self._machine.set_quad_setpoint(quadrupole, quad_start, True)
                # Give Cell 2 DDBA magnets more time to ramp.
                if "SR02" in quad_name:
                    Sleep(1)

                # Setup Oscillations
                frequency_key = f"{components.axis.upper()}_FREQUENCY"
                frequency = config[frequency_key]
                cycles_key = f"{components.axis.upper()}_CYCLES"
                cycles = config[cycles_key]
                osc = Oscillation(corr_kick, components, frequency, cycles)

                quad_lag_s = quad_step / QUAD_SLEW_RATE
                quad_lag = int(quad_lag_s * TICKS_PER_SECOND)

                log.info("Quadrupole to High Setpoint")
                self._machine.set_quad_setpoint(quadrupole, quad_high)
                Sleep(quad_lag_s / 2)

                now = get_timestamp(decimated)
                high_start = now + NETWORK_LAG
                duration = (2 * osc.length) + NETWORK_LAG + SAFETY_NET + quad_lag
                fa_buffer = Buffer(
                    self._machine.faa_bpm_list, high_start, duration, decimated
                )
                low_start = SAFETY_NET + osc.length + high_start + quad_lag

                exc_high = Excitation(self._machine, components, osc, high_start)
                exc_low = Excitation(self._machine, components, osc, low_start)
                # Sleep for first excitation. SAFETY_NET ensures that we don't start
                # moving the quad before the excitation has finished.
                excite((exc_high,))
                Sleep((NETWORK_LAG + exc_high.count + SAFETY_NET) / TICKS_PER_SECOND)
                # Move quad from high to low
                log.info("Quadrupole to Low Setpoint")
                self._machine.set_quad_setpoint(quadrupole, quad_low)
                # Set up second excitation
                excite((exc_low,))
                # This will block until all data has been retrieved.
                fa_data = fa_buffer.get_data()
                exc_data = (exc_high, exc_low)
                selected_data = self.select_data(fa_data, components.axis, exc_data)

                key = f"{quad_name}_{components.axis}_High"
                rawdata[key] = selected_data[0]
                key = f"{quad_name}_{components.axis}_Low"
                rawdata[key] = selected_data[1]

                log.info("Reset Quadrupole Setpoint")
                self._machine.set_quad_setpoint(quadrupole, quad_sp)
                Sleep(quad_lag_s / 2)

        return RawData(rawdata, metadata)

    def select_data(
        self,
        data: np.ndarray,
        axis: str,
        exc_data: Tuple[Excitation, Excitation],
    ) -> List[np.ndarray]:
        """Extract FA data that covers the excitations exc_high and exc_low.
        The input data array should cover the full length of both excitations.

        Args:
            data: The full FA data array.
            axis: The axis to extract data for.
            exc_data: The excitations to extract data for.

        Returns:
            A list of two arrays containing the data for exc_high and exc_low.
        """
        if axis == "x":
            plane = 0
        else:
            plane = 1

        exc_high, exc_low = exc_data
        decimated = False
        # Note: array data must include the timestamps.
        log.debug("Raw data shape: {}".format(data.shape))
        log.debug(
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
        high_start = int(np.searchsorted(times, exc_high.start_time))
        low_start = int(np.searchsorted(times, exc_low.start_time))
        log.debug("Searched start times: %s, %s", high_start, low_start)
        # Ensure we include the entire oscillation if using decimated data.
        length = np.ceil(exc_high.count / 10) if decimated else exc_high.count
        high_data = data[high_start : high_start + length, :, plane]
        low_data = data[low_start : low_start + length, :, plane]
        log.debug("Selected data shape: {} {}".format(high_data.shape, low_data.shape))
        assert high_data.shape == low_data.shape
        return [high_data, low_data]

    def extract_freq_excite(
        self, data: np.ndarray, known_freq: int, bpm_index: int
    ) -> np.ndarray:
        # Synchronous Detector Method

        # Incoming data arranged as [Time, Axis]

        # The mixing function creates a clean waveform at the known frequency
        # A dummy axis must be created to preserve shape through numpy operations
        # mix aranged as [Time, 1]
        mix = np.exp(
            2j * np.pi * known_freq / TICKS_PER_SECOND * np.arange(1, len(data) + 1).T
        )
        mix = mix[:, None]

        # Find the DC offset; aranged as [Axis, 1]
        dc_offset = data.mean(0)

        # Run the mixing waveform over the data, aongside a hanning window
        # detector aranged as [Axis, 1]
        window = np.hanning(len(mix))[:, None]
        detector = 4 * ((data - dc_offset) * mix * window).mean(0)

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

        # Reconstruct the clean wave; aranged as [Time, Axis]
        clean_wave = np.real(np.conj(detector_fixed) * mix) + np.real(dc_offset)
        return clean_wave

    def analyse(self, rawdata: RawData) -> Results:
        """Analyse the rawdata and calculate the offsets to apply.

        Args:
            rawdata: The rawdata to analyse.

        Returns:
            The results of the analysis.
        """
        data = rawdata.rawdata
        metadata = rawdata.metadata

        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)

        bpm_number = metadata["bpm_index"]
        bpm_index = bpm_number - np.sum(
            enabled_bpms[:bpm_number] == False  # noqa false positive
        )
        results: Dict[str, List[float]] = {}
        plotting: Dict[str, Dict[str, np.ndarray]] = {}

        quad_names = []
        for key in data.keys():
            quad_name = key.split("_")[0]
            if quad_name not in quad_names:
                quad_names.append(quad_name)

        for quad_name in quad_names:
            for axis in ["x", "y"]:
                frequency_key = f"{axis.upper()}_FREQUENCY"
                frequency = metadata[frequency_key]
                high_key = f"{quad_name}_{axis}_High"
                low_key = f"{quad_name}_{axis}_Low"

                # Remove bad BPMs
                q_low = data[low_key][:, enabled_bpms]
                q_high = data[high_key][:, enabled_bpms]

                # Clean the data using the synchronous detector method
                q_high_clean = self.extract_freq_excite(q_high, frequency, bpm_index)
                q_low_clean = self.extract_freq_excite(q_low, frequency, bpm_index)

                # Take the difference between fits
                q_diff = q_high_clean - q_low_clean
                good = q_diff.std(0) > q_diff.std(0).max() / 2
                q_diff_good = q_diff[:, good]

                # Use a single fit operation, then transform with the straight line equation
                fit = np.polynomial.polynomial.polyfit(
                    q_high_clean[:, bpm_index], q_diff_good, 1
                )
                p = np.array([1 / fit[1], -fit[0] / fit[1]]).T

                key = f"{quad_name}_{axis}"
                offset = np.mean(p[:, 1]) / NM_TO_MM_UNIT_CONV
                error = np.std(p[:, 1]) / NM_TO_MM_UNIT_CONV
                results[key] = [offset, error]

                # plotting data
                plotting[key] = {
                    "x": q_high_clean[:, bpm_index] / NM_TO_MM_UNIT_CONV,
                    "y": q_diff_good / NM_TO_MM_UNIT_CONV,
                }

        offsets = self.create_offsets_dict(results, metadata)

        return Results(results, metadata, plotting, offsets)
