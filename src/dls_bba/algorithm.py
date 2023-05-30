import logging as log
from abc import ABC, abstractmethod

import numpy as np
from cothread import Sleep

from dls_bba.isotime import get_isotime
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
from dls_bba.lattice import Lattice


class Algorithm(ABC):
    def __init__(self, lattice: Lattice):
        self._lattice = lattice

    @abstractmethod
    def run(self, component_pair: list[Components]) -> RawData:
        pass

    @abstractmethod
    def analyse(self, rawdata: RawData) -> Results:
        pass


class SlowBBA(Algorithm):
    def __init__(self, lattice: Lattice):
        super().__init__(lattice)

    def run(self, component_pair: list[Components]) -> RawData:
        rawdata = {}
        metadata = {}
        metadata.update(self._lattice._config)
        metadata["method"] = "SlowBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._lattice.get_enabled_bpms()
        metadata["bpm_prefix"] = component_pair[0].bpm_name

        for component in component_pair:
            for quadrupole, quad_pv_prefix in zip(
                component.quadrupoles, component.quadrupoles_names
            ):
                # TODO: Feedbacks first?
                # self._lattice.check_feedbacks()
                (
                    quad_start,
                    quad_high,
                    quad_low,
                    quad_sp,
                ) = self._lattice.calculate_quad_setpoints(quadrupole)
                corrector_step_list = self._lattice.get_slow_bba_corrector_steps(
                    component.corrector
                )

                # Always overshoot the high quad step and work down and keep direction
                # consistent to mitigate unwanted hysteresis effects.
                # FYI correctors are significantly less prone to hysteresis effects.
                if "SR02" in quad_pv_prefix:
                    # TODO: If Cell 2 (DDBA) complete a full hysteresis cycle.
                    self._lattice.set_quad_setpoint(quadrupole, quad_start, True)
                else:
                    self._lattice.set_quad_setpoint(quadrupole, quad_start, True)

                for movement, quad_movement in [
                    ("High", quad_high),
                    ("Low", quad_low),
                ]:
                    self._lattice.set_quad_setpoint(quadrupole, quad_movement, True)

                    for index, step in enumerate(corrector_step_list, start=1):
                        self._lattice.set_corrector_setpoint(component.corrector, step)
                        Sleep(0.1)  # Fixed time for orbit to stabilise.
                        measured_bpms = self._lattice.measure_bpms(component.axis)

                        key = f"{quad_pv_prefix}_{component.axis}_{movement}_{index}"
                        rawdata[key] = measured_bpms
                        metadata[key] = {
                            "components": component.as_dict(),
                            "quad_start_high_low_sp": [
                                quad_start,
                                quad_high,
                                quad_low,
                                quad_sp,
                            ],
                            "corrector_steps": corrector_step_list,
                        }

                    # Reset the corrector after the steps before moving the quadrupole.
                    self._lattice.set_corrector_setpoint(
                        component.corrector, corrector_step_list[2]
                    )
                # Reset Quad and Corrector once finished.
                self._lattice.set_corrector_setpoint(
                    component.corrector, corrector_step_list[2]
                )
                self._lattice.set_quad_setpoint(quadrupole, quad_sp, True)
            # run feedbacks after each axis.
            self._lattice.check_feedbacks()

        # Saving x and y in one file, as you cannot do just one axis.
        return RawData(rawdata, metadata)

    def analyse(self, rawdata: RawData) -> Results:
        # TODO: Does not reference the bpm???????????
        data = rawdata.rawdata
        metadata = rawdata.metadata

        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        min_slope_fraction = self._lattice._config["MIN_SLOPE_FRACTION"]
        center_outlier_factor = self._lattice._config["CENTER_OUTLIER_FACTOR"]

        results = {}
        # TODO: plotting_data = {}

        quad_names = []
        for key in data.keys():
            quad_name = key.split("_")[0]
            if quad_name not in quad_names:
                quad_names.append(quad_name)

        for quad_name in quad_names:
            for axis in ["x", "y"]:
                matrix = np.zeros(shape=(5, len(enabled_bpms)))
                for index in range(1, 6):
                    key = f"{quad_name}_{axis}_High_{index}"
                    high = data[key]
                    key = f"{quad_name}_{axis}_Low_{index}"
                    low = data[key]
                    matrix[index, :] = np.subtract(high, low)

                bad_indices = []

                # Get rid of disabled bpms.
                for index, value in reversed(list(enumerate(enabled_bpms))):
                    if value == 0:
                        bad_indices.append(index)
                log.debug(f"Disabled BPMs: {bad_indices}")

                # Get rid of bad bpms.
                for index, _ in enumerate(self._lattice.bpms):
                    if self._lattice.fofb_enabled[axis][index] == 1:
                        bad_indices.append(index)
                log.debug(f"Disabled and bad BPMs: {bad_indices}")

                matrix = np.delete(matrix, bad_indices, axis=1)

                # TODO: Should this be setpoint steps or change in step relative to start?
                corrector_steps = metadata[key]["corrector_steps"]
                corrector_steps = [
                    step - corrector_steps[2] for step in corrector_steps
                ]

                fit = np.polynomial.polynomial.polyfit(corrector_steps, matrix, 1)
                p = np.array([1 / fit[1], -fit[0] / fit[1]]).T
                gradients = list(p[:, 1])

                sorted_gradients = sorted(map(abs, gradients))  # type: ignore
                abs_gradients = [abs(value) for value in gradients]
                second_half = sorted_gradients[len(sorted_gradients) // 2 :]
                if len(gradients) > 5:
                    max_gradient = sorted_gradients[-5]
                else:
                    max_gradient = sorted_gradients[-1]
                max_gradient = max_gradient * min_slope_fraction

                bad_gradients = []

                for index, value in enumerate(second_half):
                    if value < max_gradient:
                        bad_gradients.append(abs_gradients.index(value))

                log.debug(f"Bad gradients: {bad_gradients}")
                p = np.delete(p, bad_gradients, axis=0)
                log.debug(f"Size of p: {np.shape(p)}")

                # Remove all values that are more than 1 stdev from the mean.

                offset_mean = np.mean(p[:, 1])
                offset_stdev = np.std(p[:, 1])
                stdev_list = []
                max_value = offset_mean + (offset_stdev * center_outlier_factor)
                min_value = offset_mean - (offset_stdev * center_outlier_factor)
                for index, offset in enumerate(p[:, 1]):
                    if min_value < offset < max_value:
                        pass
                    else:
                        stdev_list.append(index)
                p = np.delete(p, stdev_list, axis=0)

                log.info(f"Final size of p: {np.shape(p)}")

                # TODO: Plotting here? Which data is important to keep at this stage?
                key = f"{quad_name}_{axis}"
                results[key] = [offset_mean, offset_stdev]

        return Results(results, metadata)


class FastBBA(Algorithm):
    def __init__(self, lattice):
        super().__init__(lattice)

    def run(self, component_pair: list[Components]) -> RawData:
        rawdata = {}
        metadata = {}
        metadata.update(self._lattice._config)
        metadata["method"] = "FastBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._lattice.get_enabled_bpms()
        metadata["bpm_prefix"] = component_pair[0].bpm_name
        decimated = self._lattice._config["DECIMATED"]

        for component in component_pair:
            for quadrupole, quad_name in zip(
                component.quadrupoles, component.quadrupoles_names
            ):
                # TODO: Feedbacks first?
                # self._lattice.check_feedbacks()
                (
                    quad_start,
                    quad_high,
                    quad_low,
                    quad_sp,
                ) = self._lattice.calculate_quad_setpoints(quadrupole)

                corr_kick = self._lattice.corrector_kick(component)
                corr_sp = self._lattice.get_corrector_setpoint(component)

                key = f"{quad_name}_{component.axis}"
                metadata[key] = {
                    "components": component.as_dict(),
                    "quad_start_high_low_sp": [
                        quad_start,
                        quad_high,
                        quad_low,
                        quad_sp,
                    ],
                    "corrector_sp": corr_sp,
                    "corrector_kick": corr_kick,
                }

                # Always overshoot the high quad step and work down and keep direction
                # consistent to mitigate unwanted hysteresis effects.
                # FYI correctors are significantly less prone to hysteresis effects.
                if "SR02" in quad_name:
                    # TODO: If Cell 2 (DDBA) complete a full hysteresis cycle.
                    self._lattice.set_quad_setpoint(quadrupole, quad_start, True)
                else:
                    self._lattice.set_quad_setpoint(quadrupole, quad_start, True)

                # Setup Oscillations
                frequency_key = f"{component.axis.upper()}_FREQUENCY"
                frequency = self._lattice._config[frequency_key]
                cycles_key = f"{component.axis.upper()}_CYCLES"
                cycles = self._lattice._config[cycles_key]
                osc = Oscillation.from_values(component, corr_kick, frequency, cycles)

                quad_lag_s = (quad_sp - quad_low) / QUAD_SLEW_RATE
                quad_lag = int(quad_lag_s * TICKS_PER_SECOND)

                self._lattice.set_quad_setpoint(quadrupole, quad_high)
                Sleep(quad_lag_s / 2)

                now = get_timestamp(decimated)
                high_start = now + NETWORK_LAG
                low_start = high_start + (2 * osc.count) + SAFETY_NET + quad_lag

                fa_buffer = Buffer(
                    self._lattice.faa_bpm_list, high_start, osc.duration, decimated
                )

                exc_high = Excitation(self._lattice, component, osc, high_start)
                exc_low = Excitation(self._lattice, component, osc, low_start)
                # Sleep for first excitation. SAFETY_NET ensures that we don't start
                # moving the quad before the excitation has finished.
                excite((exc_high,))
                Sleep((NETWORK_LAG + exc_high.count + SAFETY_NET) / TICKS_PER_SECOND)
                # Move quad from high to low
                self._lattice.set_quad_setpoint(quadrupole, quad_low)
                # Set up second excitation
                excite((exc_low,))
                # This will block until all data has been retrieved.
                fa_data = fa_buffer.get_data()
                selected_data = self.select_data(fa_data, component.axis)

                key = f"{quad_name}_{component.axis}_High"
                rawdata[key] = selected_data[0]
                key = f"{quad_name}_{component.axis}_Low"
                rawdata[key] = selected_data[1]

                self._lattice.set_quad_setpoint(quadrupole, quad_sp)
                Sleep(quad_lag_s / 2)

        return RawData(rawdata, metadata)

    def select_data(self, data, axis):
        """Extract FA data that covers the excitations exc_high and exc_low.

        The input data array should cover the full length of both excitations.

        """
        if axis == "x":
            plane = 0
        else:
            plane = 1

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
            np.ceil(self.exc_high.count / 10) if self.decimated else self.exc_high.count
        )
        high_data = data[high_start : high_start + length, :, plane.index]
        low_data = data[low_start : low_start + length, :, plane.index]
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
        dc_offset = data.mean(0)

        # Reconstruct the clean wave; aranged as [Time, Axis]
        clean_wave = np.real(np.conj(detector_fixed) * mix) + np.real(dc_offset)
        return clean_wave

    def analyse(self, rawdata: RawData) -> Results:
        data = rawdata.rawdata
        metadata = rawdata.metadata

        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        bpm_number = Components.from_dict(self._lattice, metadata[0]["Components"])
        bpm_index = bpm_number - np.sum(
            enabled_bpms[:bpm_number] == False  # noqa false positive
        )
        results = {}

        quad_names = []
        for key in data.keys():
            quad_name = key.split("_")[0]
            if quad_name not in quad_names:
                quad_names.append(quad_name)

        for quad_name in quad_names:
            for axis in ["x", "y"]:
                frequency_key = f"{axis.upper}_FREQUENCY"
                frequency = self._lattice._config[frequency_key]
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
                good = np.std(q_diff) > np.std(q_diff).max() / 2
                q_diff_good = q_diff[:, good]

                # Use a single fit operation, then transform with the straight line equation
                fit = np.polynomial.polynomial.polyfit(
                    q_high_clean[:, bpm_index], q_diff_good, 1
                )
                p = np.array([1 / fit[1], -fit[0] / fit[1]]).T

                # # Produce a large graph
                # if plot_output:
                #     to_plot = [q_high_clean, q_low_clean, q_diff, q_diff_good, p]
                #     plot_labels = [
                #         "quad high clean",
                #         "quad low clean,",
                #         "quad diff,",
                #         "quad diff good,",
                #         "fit coefficients",
                #     ]
                #     # Make a grid three wide and N high
                #     # Fill with 1D plot, image plot, and colourbar
                #     gs = GridSpec(
                #         len(to_plot) + 1,
                #         3,
                #         width_ratios=(20, 20, 1),
                #         height_ratios=([1] * len(to_plot) + [3]),
                #     )
                #     for i, _ in enumerate(to_plot):
                #         plt.subplot(gs[i, 0]).plot(to_plot[i])
                #         plt.ylabel(plot_labels[i])
                #         im = plt.subplot(gs[i, 1]).imshow(
                #             to_plot[i], aspect="auto", interpolation="nearest"
                #         )
                #         plt.colorbar(im, cax=plt.subplot(gs[i, 2]))
                #     # Add a large 1D plot to show end result
                #     plt.subplot(gs[-1, :]).plot(q_high_clean[:, bpm_index], q_diff_good)
                #     plt.ylabel(f"BPM {bpm_number + 1} aginst BPMs")
                #     plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
                #     plt.show()

                key = f"{quad_name}_{axis}"
                offset = np.mean(p[:, 1]) / 1000000
                error = np.std(p[:, 1]) / 1000000
                results[key] = [offset, error]

        return Results(results, metadata)


class SimFastBBA(Algorithm):
    def __init__(self, lattice):
        super().__init__(lattice)

    def run(self, component_pair: list[Components]) -> RawData:
        rawdata = {}
        metadata = {}
        metadata.update(self._lattice._config)
        metadata["method"] = "SimFastBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._lattice.get_enabled_bpms()
        metadata["bpm_prefix"] = component_pair[0].bpm_name
        decimated = self._lattice._config["DECIMATED"]

        for quadrupole, quad_name in zip(
            component_pair[0].quadrupoles, component_pair[0].quadrupoles_names
        ):
            (
                quad_start,
                quad_high,
                quad_low,
                quad_sp,
            ) = self._lattice.calculate_quad_setpoints(quadrupole)

            hcorr_kick = self._lattice.corrector_kick(component_pair[0].corrector)
            hcorr_sp = self._lattice.get_corrector_setpoint(component_pair[0].corrector)

            vcorr_kick = self._lattice.corrector_kick(component_pair[1].corrector)
            vcorr_sp = self._lattice.get_corrector_setpoint(component_pair[1].corrector)

            kick = {"x": hcorr_kick, "y": vcorr_kick}
            setpoint = {"x": hcorr_sp, "y": vcorr_sp}

            key = f"{quad_name}"
            metadata[key] = {
                "components": [
                    component_pair[0].as_dict(),
                    component_pair[1].as_dict(),
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
            if "SR02" in quad_name:
                # TODO: If Cell 2 (DDBA) complete a full hysteresis cycle.
                self._lattice.set_quad_setpoint(quadrupole, quad_start, True)
            else:
                self._lattice.set_quad_setpoint(quadrupole, quad_start, True)

            # Setup Oscillations
            oscillations = {}
            for index, axis in enumerate(["x", "y"]):
                frequency_key = f"{component_pair[index].axis.upper()}_FREQUENCY"
                frequency = self._lattice._config[frequency_key]
                cycles_key = f"{component_pair[index].axis.upper()}_CYCLES"
                cycles = self._lattice._config[cycles_key]
                oscillations[axis] = Oscillation.from_values(
                    component_pair[index], kick[axis], frequency, cycles
                )
            # TODO: X and Y oscillations must be same tick length.

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
                    self._lattice, component_pair[index], osc, high_start
                )
                excitations[f"Low_{axis}"] = Excitation(
                    self._lattice, component_pair[index], osc, low_start
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
        dc_offset = data.mean(0)

        # Reconstruct the clean wave; aranged as [Time, Axis]
        clean_wave = np.real(np.conj(detector_fixed) * mix) + np.real(dc_offset)
        return clean_wave

    def analyse(self, rawdata: RawData) -> Results:
        data = rawdata.rawdata
        metadata = rawdata.metadata

        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        bpm_number = Components.from_dict(self._lattice, metadata[0]["Components"])
        bpm_index = bpm_number - np.sum(
            enabled_bpms[:bpm_number] == False  # noqa false positive
        )
        results = {}

        quad_names = []
        for key in data.keys():
            quad_name = key.split("_")[0]
            if quad_name not in quad_names:
                quad_names.append(quad_name)

        for quad_name in quad_names:
            for axis in ["x", "y"]:
                key = f"{quad_name}_{axis}"

                frequency_key = f"{axis.upper}_FREQUENCY"
                frequency = self._lattice._config[frequency_key]

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

                # TODO: Plotting Stuff

                offset = np.mean(p[:, 1]) / 1000000
                error = np.std(p[:, 1]) / 1000000
                results[key] = [offset, error]

        return Results(results, metadata)
