import logging as log

import numpy as np
from cothread import Sleep

from dls_bba.algorithm import Algorithm
from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
from dls_bba.excite import (
    NETWORK_LAG,
    QUAD_SLEW_RATE,
    SAFETY_NET,
    Excitation,
    Oscillation,
    excite,
)
from dls_bba.faa import TICKS_PER_SECOND, Buffer, get_timestamp
from dls_bba.isotime import get_isotime
from dls_bba.lattice import Lattice

# To convert from nanometers to millimeters
UNIT_CONVERSION = 1000000


class SimFastBBA(Algorithm):
    def __init__(self, lattice: Lattice):
        super().__init__(lattice)

    def run(self, components_pair: list[Components]) -> RawData:
        rawdata = {}
        metadata = {}
        metadata.update(self._lattice._config)
        metadata["method"] = "SimFastBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._lattice.get_enabled_bpms()
        metadata["bpm_name"] = components_pair[0].bpm_name
        metadata["bpm_index"] = components_pair[0].bpm_index
        decimated = metadata["DECIMATED"]

        for quadrupole, quad_name in zip(
            components_pair[0].quadrupoles, components_pair[0].quadrupoles_names
        ):
            log.debug(f"BPM: {components_pair[0].bpm_name}")
            log.debug(f"Quad: {quad_name} of {components_pair[0].quadrupoles_names}")
            log.debug(
                f"Corrector1: {components_pair[0].corrector_name}, Corrector2: {components_pair[1].corrector_name}"
            )
            (
                quad_start,
                quad_high,
                quad_low,
                quad_sp,
            ) = self._lattice.calculate_quad_setpoints(quadrupole)

            hcorr_kick = self._lattice.corrector_kick(components_pair[0].corrector)
            hcorr_sp = self._lattice.get_corrector_setpoint(components_pair[0])

            vcorr_kick = self._lattice.corrector_kick(components_pair[1].corrector)
            vcorr_sp = self._lattice.get_corrector_setpoint(components_pair[1])

            kick = {"x": hcorr_kick, "y": vcorr_kick}
            setpoint = {"x": hcorr_sp, "y": vcorr_sp}

            key = f"{quad_name}"
            metadata[key] = {
                "components": [
                    components_pair[0].as_dict(),
                    components_pair[1].as_dict(),
                ],
                "quad_start_high_low_sp": [
                    quad_start,
                    quad_high,
                    quad_low,
                    quad_sp,
                ],
                "corrector_sp": setpoint,
                "corrector_kick": kick,
            }

            # Always overshoot the high quad step and work down and keep direction
            # consistent to mitigate unwanted hysteresis effects.
            # FYI correctors are significantly less prone to hysteresis effects.
            self._lattice.set_quad_setpoint(quadrupole, quad_start, True)
            # Give Cell 2 DDBA magnets more time to ramp.
            if "SR02" in quad_name:
                Sleep(1)

            # Setup Oscillations
            oscillations = {}
            for index, axis in enumerate(["x", "y"]):
                frequency_key = f"{components_pair[index].axis.upper()}_FREQUENCY"
                frequency = self._lattice._config[frequency_key]
                cycles_key = f"{components_pair[index].axis.upper()}_CYCLES"
                cycles = self._lattice._config[cycles_key]
                oscillations[axis] = Oscillation.from_values(
                    components_pair[index], kick[axis], frequency, cycles
                )
            # TODO: X and Y oscillations must be same tick length. Must check.

            quad_lag_s = (quad_sp - quad_low) / QUAD_SLEW_RATE
            quad_lag = int(quad_lag_s * TICKS_PER_SECOND)

            self._lattice.set_quad_setpoint(quadrupole, quad_high)
            Sleep(quad_lag_s / 2)

            now = get_timestamp(decimated)
            high_start = now + NETWORK_LAG
            low_start = (
                high_start + (2 * oscillations["x"].count) + SAFETY_NET + quad_lag
            )

            fa_buffer = Buffer(
                self._lattice.faa_bpm_list,
                high_start,
                oscillations["x"].duration,
                decimated,
            )
            excitations = {}
            for index, (osc, axis) in enumerate(zip(oscillations, ["x", "y"])):
                excitations[f"High_{axis}"] = Excitation(
                    self._lattice, components_pair[index], osc, high_start
                )
                excitations[f"Low_{axis}"] = Excitation(
                    self._lattice, components_pair[index], osc, low_start
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
            self._lattice.set_quad_setpoint(quadrupole, quad_low)
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
                selected_data = self.select_data(fa_data, index, exc_data)
                rawdata[f"{quad_name}_{axis}"] = {
                    "High": selected_data[0],
                    "Low": selected_data[1],
                }

            self._lattice.set_quad_setpoint(quadrupole, quad_sp)
            Sleep(quad_lag_s / 2)

        return RawData(rawdata, metadata)

    def select_data(self, data, plane_index, exc_data):
        """Extract FA data that covers the excitations exc_high and exc_low.

        The input data array should cover the full length of both excitations.

        """
        # Note: array data must include the timestamps.
        exc_high, exc_low = exc_data
        decimated = False
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
        high_start = np.searchsorted(times, exc_high.start_time)
        low_start = np.searchsorted(times, exc_low.start_time)
        log.debug("Searched start times: %s, %s", high_start, low_start)
        # Ensure we include the entire oscillation if using decimated data.
        length = np.ceil(exc_high.count / 10) if decimated else exc_high.count
        high_data = data[high_start : high_start + length, :, plane_index]
        low_data = data[low_start : low_start + length, :, plane_index]
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
        data = rawdata.rawdata
        metadata = rawdata.metadata

        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        bpm_number = metadata["bpm_index"]
        bpm_index = bpm_number - np.sum(
            enabled_bpms[:bpm_number] == False  # noqa false positive
        )
        results = {}
        plotting = {}

        quad_names = []
        for key in data.keys():
            quad_name = key.split("_")[0]
            if quad_name not in quad_names:
                quad_names.append(quad_name)

        for quad_name in quad_names:
            for axis in ["x", "y"]:
                key = f"{quad_name}_{axis}"

                frequency_key = f"{axis.upper}_FREQUENCY"
                frequency = metadata[frequency_key]

                # Remove bad BPMs
                q_low = data[key]["Low"][:, enabled_bpms]
                q_high = data[key]["High"][:, enabled_bpms]

                q_high_clean = self.extract_freq_excite(q_high, frequency, bpm_index)
                q_low_clean = self.extract_freq_excite(q_low, frequency, bpm_index)

                # Take the difference between fits
                q_diff = q_high_clean - q_low_clean
                good = np.std(q_diff) > np.std(q_diff).max() / 2
                q_diff_good = q_diff[:, good]

                # Use a single fit operation, then transform with the straight line equation
                fit = np.polynomial.polynomial.polyfit(
                    q_high_clean[:, bpm_index], q_diff_good, 1
                )
                p = np.array([1 / fit[1], -fit[0] / fit[1]]).T

                offset = np.mean(p[:, 1]) / UNIT_CONVERSION
                error = np.std(p[:, 1]) / UNIT_CONVERSION
                results[key] = [offset, error]

                # plotting data
                plotting[key] = {
                    "x": q_high_clean[:, bpm_index] / UNIT_CONVERSION,
                    "y": q_diff_good / UNIT_CONVERSION,
                }

        return Results(results, metadata, plotting)
