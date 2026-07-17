import logging as log
from math import ceil
from typing import Any

import numpy as np
from cothread import Sleep

from dls_bba.algorithm import Algorithm
from dls_bba.components import Components
from dls_bba.datatypes import (
    FullResults,
    OscillationPlane,
    QuadResults,
    QuadStrength,
    RawData,
)
from dls_bba.exceptions import OscillationLengthError
from dls_bba.excite import NETWORK_LAG, SAFETY_NET, Excitation, Oscillation, excite
from dls_bba.faa import TICKS_PER_SECOND, Buffer, get_timestamp
from dls_bba.isotime import get_isotime
from dls_bba.machine import QUAD_SLEW_RATE, Machine

NM_TO_MM_UNIT_CONV = 1000000
"""Convert nanometers to millimeters"""


class SimFastBBA(Algorithm):
    """Simultaneous Fast BBA Algorithm."""

    def __init__(self, machine: Machine) -> None:
        """Initialise the Simultaneous Fast BBA Algorithm.

        Args:
            machine: The machine.
        """
        super().__init__(machine)

    def run(self, components_pair: list[Components]) -> RawData | None:
        """The Simultaneous Fast BBA Process.

        Args:
            components_pair: The components pair to use.

        Returns:
            The RawData object.
        """
        rawdata: dict[str, OscillationPlane[QuadStrength]] = {}
        metadata: dict[str, Any] = {}
        config = self._machine.config.get_settings()
        metadata.update(config)
        metadata["method"] = "SimFastBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._machine.get_enabled_bpms()
        metadata["bpm_name"] = components_pair[0].bpm_name
        metadata["bpm_index"] = components_pair[0].bpm_index
        decimated: bool = config["DECIMATED"]

        log.info(f"BPM: {components_pair[0].bpm_name}")
        for quadrupole, quad_name in zip(
            components_pair[0].quadrupoles,
            components_pair[0].quadrupoles_names,
            strict=True,
        ):
            self._check_and_wait_pause_status()
            if self._check_stop_status():
                return None

            log.debug(f"BPM: {components_pair[0].bpm_name}")
            log.debug(f"Quad: {quad_name} of {components_pair[0].quadrupoles_names}")
            log.debug(
                f"Corrector1: {components_pair[0].corrector_name}, "
                f"Corrector2: {components_pair[1].corrector_name}"
            )
            (
                quad_start,
                quad_high,
                quad_low,
                quad_sp,
                quad_step,
            ) = self.calculate_quad_setpoints(quadrupole)

            hcorr_kick = self._machine.corrector_kick(components_pair[0])
            hcorr_sp = self._machine.get_corrector_setpoint(components_pair[0])

            vcorr_kick = self._machine.corrector_kick(components_pair[1])
            vcorr_sp = self._machine.get_corrector_setpoint(components_pair[1])

            kick = {"x": hcorr_kick, "y": vcorr_kick}
            setpoint = {"x": hcorr_sp, "y": vcorr_sp}

            metadata[f"{quad_name}"] = {
                "components": [
                    components_pair[0].as_dict(),
                    components_pair[1].as_dict(),
                ],
                "quad_start_high_low_sp": [
                    quad_start,
                    quad_high,
                    quad_low,
                    quad_sp,
                    quad_step,
                ],
                "corrector_sp": setpoint,
                "corrector_kick": kick,
            }

            # Always overshoot the high quad step and work down and keep direction
            # consistent to mitigate unwanted hysteresis effects.
            # FYI correctors are significantly less prone to hysteresis effects.
            self._machine.set_quad_setpoint(quadrupole, quad_start, True)
            # Give Cell 2 DDBA magnets more time to ramp.
            if "SR02" in quad_name:
                Sleep(1)

            # Setup Oscillations
            oscillations = {}
            for index, axis in enumerate(["x", "y"]):
                frequency = config[f"{components_pair[index].axis.upper()}_FREQUENCY"]
                cycles = config[f"{components_pair[index].axis.upper()}_CYCLES"]
                oscillations[axis] = Oscillation(
                    kick[axis], components_pair[index], frequency, cycles
                )

            if oscillations["x"].length != oscillations["y"].length:
                raise OscillationLengthError(
                    f"X: {oscillations['x'].length} != Y: {oscillations['y'].length}"
                )

            quad_lag_s = quad_step / QUAD_SLEW_RATE
            quad_lag = int(quad_lag_s * TICKS_PER_SECOND)

            log.info("Quadrupole to High Setpoint")
            self._machine.set_quad_setpoint(quadrupole, quad_high)
            Sleep(quad_lag_s / 2)

            now = get_timestamp(decimated)
            high_start = now + NETWORK_LAG
            duration = (
                (2 * oscillations["x"].length) + NETWORK_LAG + SAFETY_NET + quad_lag
            )
            fa_buffer = Buffer(
                self._machine.faa_bpm_list, high_start, duration, decimated
            )
            low_start = SAFETY_NET + oscillations["x"].length + high_start + quad_lag

            excitations = {}
            for index, axis in enumerate(["x", "y"]):
                excitations[f"High_{axis}"] = Excitation(
                    self._machine,
                    components_pair[index],
                    oscillations[axis],
                    high_start,
                )
                excitations[f"Low_{axis}"] = Excitation(
                    self._machine, components_pair[index], oscillations[axis], low_start
                )

            high_keys = [key for key in excitations.keys() if "High_" in key]
            # Sleep for first excitation. SAFETY_NET ensures that we don't start
            # moving the quad before the excitation has finished.
            excite((excitations[high_keys[0]], excitations[high_keys[1]]))
            Sleep(
                (NETWORK_LAG + excitations[high_keys[0]].count + SAFETY_NET)
                / TICKS_PER_SECOND
            )
            # Move quad from high to low
            log.info("Quadrupole to Low Setpoint")
            self._machine.set_quad_setpoint(quadrupole, quad_low)
            low_keys = [key for key in excitations.keys() if "Low_" in key]
            excite((excitations[low_keys[0]], excitations[low_keys[1]]))
            # This will block until all data has been retrieved.

            data_list = [
                [excitations[high_keys[0]], excitations[low_keys[0]]],
                [excitations[high_keys[1]], excitations[low_keys[1]]],
            ]

            fa_data = fa_buffer.get_data()

            for index, axis in enumerate(["x", "y"]):
                exc_data = data_list[index]
                selected_data = self.select_data(fa_data, index, exc_data, decimated)
                if quad_name not in rawdata.keys():
                    rawdata[quad_name] = OscillationPlane()
                rawdata[quad_name][axis] = QuadStrength(*selected_data)

            log.info("Reset Quadrupole Setpoint")
            self._machine.set_quad_setpoint(quadrupole, quad_sp)
            Sleep(quad_lag_s / 2)

        return RawData(rawdata, metadata)

    def select_data(
        self,
        data: np.ndarray,
        plane_index: int,
        exc_data: list[Excitation],
        decimated: bool,
    ) -> list[np.ndarray]:
        """Extract FA data that covers the excitations exc_high and exc_low.

        The input data array should cover the full length of both excitations.

        Args:
            data: Full FA data array.
            plane_index: Index of the plane to extract data for.
            exc_data: List of excitations to extract data for.

        Returns:
            List of arrays containing the data for each excitation.
        """
        # Note: array data must include the timestamps.
        exc_high, exc_low = exc_data
        log.debug(f"Raw data shape: {data.shape}")
        log.debug(f"Timestamp range in raw data: {data[0, 0, 0]} - {data[-1, 0, 0]}")
        log.debug(f"Excitation length: {exc_high.count}")
        log.debug(
            f"Trailing data to crop: "
            f"{data[-1, 0, 0] - (exc_low.start_time + exc_low.count)}."
        )
        assert exc_high.count == exc_low.count, "Excitations different lengths"
        # Extract timestamps from data
        times = data[:, 0, 0]
        data = data[:, 1:, :]
        high_start = int(np.searchsorted(times, exc_high.start_time))
        low_start = int(np.searchsorted(times, exc_low.start_time))
        log.debug("Searched start times: %s, %s", high_start, low_start)
        # Ensure we include the entire oscillation if using decimated data.
        length = ceil(exc_high.count / 10) if decimated else exc_high.count
        high_data = data[high_start : high_start + length, :, plane_index]
        low_data = data[low_start : low_start + length, :, plane_index]
        log.debug(f"Selected data shape: {high_data.shape} {low_data.shape}")
        assert high_data.shape == low_data.shape
        return [high_data, low_data]

    def extract_freq_excite(
        self, data: np.ndarray, known_freq: int, bpm_index: int
    ) -> np.ndarray:
        """Extract and clean the data for a given BPM and known frequency.

        The data is cleaned using the Synchronous Detector Method, where the
        incoming data is arranged as [Time, Axis]. The mixing function creates
        a clean waveform at the known frequency, and a dummy axis must be created
        to preserve shape through numpy operations.

        Args:
            data: The raw data array.
            known_freq: The known frequency of the excitation.
            bpm_index: The index of the BPM to extract data for.

        Returns:
            The cleaned data array.
        """
        # Incoming data arranged as [Time, Axis]
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

    def analyse(self, rawdata: RawData) -> FullResults:
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
        results: dict[str, OscillationPlane[QuadResults]] = {}

        for quad_name in data.keys():
            for axis in ["x", "y"]:
                frequency = metadata[f"{axis.upper()}_FREQUENCY"]

                # Remove bad BPMs
                q_low = data[quad_name][axis]["low"][:, enabled_bpms]
                q_high = data[quad_name][axis]["high"][:, enabled_bpms]

                q_high_clean = self.extract_freq_excite(q_high, frequency, bpm_index)
                q_low_clean = self.extract_freq_excite(q_low, frequency, bpm_index)

                # Take the difference between fits
                q_diff = q_high_clean - q_low_clean
                good = q_diff.std(0) > q_diff.std(0).max() / 2
                q_diff_good = q_diff[:, good]

                # Use a single fit operation, then transform with straight line equation
                oscillation_midpoint = (
                    q_high_clean[:, bpm_index] + q_low_clean[:, bpm_index]
                ) / 2
                oscillation_size = q_diff_good
                fit = np.polynomial.polynomial.polyfit(
                    oscillation_midpoint, oscillation_size, 1
                )
                p = np.array([1 / fit[1], -fit[0] / fit[1]]).T

                offset = np.mean(p[:, 1]) / NM_TO_MM_UNIT_CONV
                error = np.std(p[:, 1]) / NM_TO_MM_UNIT_CONV
                if quad_name not in results.keys():
                    results[quad_name] = OscillationPlane()
                results[quad_name][axis] = QuadResults(offset, error)

                # plotting data
                metadata[f"plotting__{quad_name}__{axis}"] = {
                    "x": oscillation_midpoint / NM_TO_MM_UNIT_CONV,
                    "y": oscillation_size / NM_TO_MM_UNIT_CONV,
                }

        offsets = self.create_offsets_dict(results, metadata)

        return FullResults(results, metadata, offsets)
