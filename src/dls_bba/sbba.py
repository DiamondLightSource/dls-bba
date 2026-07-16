import logging as log
from math import floor
from typing import Any

import cothread
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
from dls_bba.isotime import get_isotime
from dls_bba.machine import Machine


class SlowBBA(Algorithm):
    """Slow BBA Algorithm."""

    def __init__(self, machine: Machine) -> None:
        """Initialise the Slow BBA Algorithm.

        Args:
            machine: The machine.
        """
        super().__init__(machine)

    def run(
        self,
        components_pair: list[Components],
        stop_event: cothread.Event | None = None,
    ) -> RawData | None:
        """The Slow BBA Process.

        Args:
            components_pair: The components pair to use.
            stop_event: Cothread event which is triggered when the GUI stop button
                        is pressed.

        Returns:
            The RawData object.
        """
        rawdata: dict[str, OscillationPlane[QuadStrength]] = {}
        metadata: dict[str, Any] = {}
        config = self._machine.config.get_settings()
        metadata.update(config)
        metadata["method"] = "SlowBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._machine.get_enabled_bpms()
        number_of_bpms = len(metadata["enabled_bpms"])
        # NOTE: This should probably be calculated properly, but even in getsigma.m it
        # just sets them all to 1e-4 when it fails to find the file that it's supposed
        # to read them from.
        metadata["sigma_bpm"] = np.ones(len(metadata["enabled_bpms"])) * 1e-4
        metadata["bpm_name"] = components_pair[0].bpm_name
        metadata["bpm_index"] = components_pair[0].bpm_index

        log.info(f"BPM: {components_pair[0].bpm_name}")
        for components in components_pair:
            log.debug(f"Component: {components}")
            for quadrupole, quad_name in zip(
                components.quadrupoles, components.quadrupoles_names, strict=True
            ):
                log.debug(f"Quad: {quad_name} of {components.quadrupoles_names}")
                (
                    quad_start,
                    quad_high,
                    quad_low,
                    quad_sp,
                    quad_step,
                ) = self.calculate_quad_setpoints(quadrupole)
                corrector_step_list = self.get_slow_bba_corrector_steps(components)
                metadata[f"{quad_name.replace('-', '_')}__{components.axis}"] = {
                    "components": components.as_dict(),
                    "quad_start_high_low_sp": [
                        quad_start,
                        quad_high,
                        quad_low,
                        quad_sp,
                        quad_step,
                    ],
                    "corrector_steps": corrector_step_list,
                }
                plane_data = {
                    "High": np.zeros((5, number_of_bpms)),
                    "Low": np.zeros((5, number_of_bpms)),
                }

                for index, corrector_step in enumerate(corrector_step_list):
                    self._machine.set_corrector_setpoint(components, corrector_step)
                    # Always overshoot the high quad step and work down and keep
                    # direction consistent to mitigate unwanted hysteresis effects.
                    # FYI correctors are significantly less prone to hysteresis effects.
                    self._machine.set_quad_setpoint(quadrupole, quad_start, True)

                    for quad_movement, quad_value in [
                        ("High", quad_high),
                        ("Low", quad_low),
                    ]:
                        if bool(stop_event):
                            return None

                        log.info(f"Quadrupole to {quad_movement} Setpoint")
                        self._machine.set_quad_setpoint(quadrupole, quad_value, True)
                        if "SR02" in quad_name:
                            Sleep(1)  # Give Cell 2 DDBA magnets more time to ramp.
                        plane_data[quad_movement][index] = self._machine.measure_bpms(
                            components.axis
                        )
                # Reset quad and corrector once finished.
                log.info("Reset Quadrupole Setpoint")
                self._machine.set_quad_setpoint(quadrupole, quad_sp, True)
                self._machine.set_corrector_setpoint(components, corrector_step_list[2])
                # Save the raw data that we've measured
                if quad_name not in rawdata.keys():
                    rawdata[quad_name] = OscillationPlane()
                rawdata[quad_name][components.axis] = QuadStrength(
                    plane_data["High"], plane_data["Low"]
                )
            # run feedbacks after each axis.
            self._machine.check_feedbacks()

        # Saving x and y in one file, as you cannot do just one axis.
        return RawData(rawdata, metadata)

    def get_slow_bba_corrector_steps(self, components: Components) -> list[float]:
        """Get the corrector steps for the slow BBA.

        Args:
            components: The components to use.

        Returns:
            The corrector steps in a list. Where s is the setpoint and k is the kick.
            [s + k, s + (k / 2), s, s - (k / 2), s - k]
        """
        setpoint = self._machine.get_corrector_setpoint(components)
        step = self._machine.corrector_kick(components)
        corrector_steps = [
            setpoint + step,
            setpoint + (step / 2),
            setpoint,
            setpoint - (step / 2),
            setpoint - step,
        ]
        return corrector_steps

    def analyse(self, rawdata: RawData) -> FullResults:
        """Analyse the rawdata and calculate the offsets to apply.

        Args:
            rawdata: The rawdata to analyse.

        Returns:
            The results of the analysis.
        """
        data = rawdata.rawdata
        metadata = rawdata.metadata

        # Define variables that aren't changed between planes.
        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        outlier_factor = metadata["OUTLIER_FACTOR"]
        min_slope_fraction = metadata["MIN_SLOPE_FRACTION"]
        center_outlier_factor = metadata["CENTER_OUTLIER_FACTOR"]
        optimal_bpm = metadata["bpm_index"]

        results: dict[str, OscillationPlane[QuadResults]] = {}

        for quad_name in data.keys():
            for axis in ["x", "y"]:
                # Define variables that get changed for each plane.
                sigma_bpm = metadata["sigma_bpm"]
                bpm_indices = np.array(range(len(enabled_bpms)))
                high = np.copy(data[quad_name][axis].high)
                low = np.copy(data[quad_name][axis].low)
                oscillation_size = low - high
                # Get rid of disabled bpms.
                disabled_bpms = np.logical_not(enabled_bpms)
                log.debug(f"Indices of disabled BPMs: {np.flatnonzero(disabled_bpms)}")
                # NOTE: This is currently disabled in order to give identical results to
                # quadplot.m, though removing them is probably the right thing to do.
                # NOTE: If we do choose to re-enable this then it should probably be
                # done during data collection like enabled_bpms rather than here.
                # fofb_disabled_bpms = np.array(self._machine.fofb_disabled[axis], dtype=bool)  # noqa: E501
                # log.debug(f"Indices of fofb disabled BPMs: {np.flatnonzero(fofb_disabled_bpms)}")  # noqa: E501
                disabled = disabled_bpms  # | fofb_disabled_bpms
                high = np.delete(high, disabled, axis=1)
                low = np.delete(low, disabled, axis=1)
                oscillation_size = np.delete(oscillation_size, disabled, axis=1)
                sigma_bpm = np.delete(sigma_bpm, disabled)
                bpm_indices = np.delete(bpm_indices, disabled)
                if optimal_bpm not in bpm_indices:
                    raise IndexError(
                        f"Please specify a different optimal BPM, currently specified "
                        f"BPM ({optimal_bpm}) is disabled."
                    )
                log.debug(f"Data points remaining after cleaning: {len(sigma_bpm)}")

                # 5 point linear least squares fit.
                bpm_number = list(bpm_indices).index(metadata["bpm_index"])
                oscillation_midpoint = (high[:, bpm_number] + low[:, bpm_number]) / 2
                X = np.stack((np.ones(5), oscillation_midpoint), axis=1)  # noqa: N806
                # Matrix least squares b = (Xᵀ.X)⁻¹.Xᵀ.OS
                inverse_Xtranspose_X = np.linalg.inv(X.T.dot(X))  # noqa: N806
                b = inverse_Xtranspose_X.dot(X.T).dot(oscillation_size)

                # Get absolute gradients and x intercepts of the lines.
                gradients = abs(b[1, :])
                offsets = -b[0, :] / b[1, :]

                # Remove all values with large difference between the fit value and that
                # BPM's standard deviation (currently hardcoded to 1e-4).
                y = np.zeros(shape=(5, b.shape[1]))
                large_fit_diff = np.zeros(b.shape[1], dtype=bool)
                for i in range(b.shape[1]):
                    y[:, i] = (b[1, i] * oscillation_midpoint) + b[0, i]  # y = mx + c
                    if (
                        max(abs(y[:, i] - oscillation_size[:, i]))
                        > outlier_factor * sigma_bpm[i]
                    ):
                        large_fit_diff[i] = True
                log.debug(
                    f"Indices with large error between fit and data: "
                    f"{np.flatnonzero(large_fit_diff)}"
                )
                gradients = np.delete(gradients, large_fit_diff)
                offsets = np.delete(offsets, large_fit_diff)
                oscillation_size = np.delete(oscillation_size, large_fit_diff, axis=1)
                bpm_indices = np.delete(bpm_indices, large_fit_diff)
                log.debug(f"Data points remaining after cleaning: {len(offsets)}")

                # Remove all values with overly shallow gradients.
                second_half = np.sort(gradients)[floor(len(gradients) / 2) :]
                if len(second_half) > 5:
                    min_gradient = second_half[-5]
                else:
                    min_gradient = second_half[-1]
                bad_gradients = np.abs(gradients) < min_gradient * min_slope_fraction
                log.debug(
                    f"Indices with too shallow gradients: "
                    f"{np.flatnonzero(bad_gradients)}"
                )
                gradients = np.delete(gradients, bad_gradients)
                offsets = np.delete(offsets, bad_gradients)
                oscillation_size = np.delete(oscillation_size, bad_gradients, axis=1)
                bpm_indices = np.delete(bpm_indices, bad_gradients)
                log.debug(f"Data points remaining after cleaning: {len(offsets)}")

                # Remove all values that are more than center_outlier_factor standard
                # deviation(s) away from the mean.
                stdev_outside_range = np.array(
                    abs(offsets - np.mean(offsets))
                    > center_outlier_factor * np.std(offsets, ddof=1)
                )
                log.debug(
                    f"Indices more than {center_outlier_factor} standard deviation(s) "
                    f"away from the mean: {np.flatnonzero(stdev_outside_range)}"
                )
                gradients = np.delete(gradients, stdev_outside_range)
                offsets = np.delete(offsets, stdev_outside_range)
                oscillation_size = np.delete(
                    oscillation_size, stdev_outside_range, axis=1
                )
                bpm_indices = np.delete(bpm_indices, stdev_outside_range)
                log.debug(f"Data points remaining after cleaning: {len(offsets)}")

                if quad_name not in results.keys():
                    results[quad_name] = OscillationPlane()
                results[quad_name][axis] = QuadResults(
                    np.mean(offsets), np.std(offsets, ddof=1)
                )
                log.debug(
                    f"Results for {quad_name} {axis.upper()} plane:\n"
                    f"    mean: {results[quad_name][axis].mean_offset}"
                    f"    standard deviation: {results[quad_name][axis].std_dev_offset}"
                )

                # Plot data after cleaning.
                metadata[f"plotting__{quad_name}__{axis}"] = {
                    "x": oscillation_midpoint,
                    "y": oscillation_size,
                }

        offsets = self.create_offsets_dict(results, metadata)

        return FullResults(results, metadata, offsets)
