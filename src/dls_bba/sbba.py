import logging as log
from typing import Any, Dict, List

import numpy as np
from cothread import Sleep

from dls_bba.algorithm import Algorithm
from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
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

    def run(self, components_pair: List[Components]) -> RawData:
        """The Slow BBA Process.

        Args:
            components_pair: The components pair to use.

        Returns:
            The RawData object.
        """
        rawdata: Dict[str, Any] = {}
        metadata: Dict[str, Any] = {}
        config = self._machine.config.get_settings()
        metadata.update(config)
        metadata["method"] = "SlowBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._machine.get_enabled_bpms()
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
                corrector_step_list = self.get_slow_bba_corrector_steps(components)

                # Always overshoot the high quad step and work down and keep direction
                # consistent to mitigate unwanted hysteresis effects.
                # FYI correctors are significantly less prone to hysteresis effects.
                self._machine.set_quad_setpoint(quadrupole, quad_start, True)
                # Give Cell 2 DDBA magnets more time to ramp.
                #if "SR02" in quad_name:
                #    Sleep(1)
                for movement, quad_movement in [
                    ("High", quad_high),
                    ("Low", quad_low),
                ]:
                    log.info(f"Quadrupole to {movement} Setpoint")
                    self._machine.set_quad_setpoint(quadrupole, quad_movement, True)
                    for index, step in enumerate(corrector_step_list, start=1):
                        self._machine.set_corrector_setpoint(components, step)
                        Sleep(0.5)  # Fixed time for orbit to stabilise.
                        measured_bpms = self._machine.measure_bpms(components.axis)
                        key = f"{quad_name.replace('-', '_')}__{components.axis}_{movement}_{index}"
                        rawdata[key] = measured_bpms
                        metadata[key] = {
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
                    # Reset the corrector after the steps before moving the quadrupole.
                    self._machine.set_corrector_setpoint(
                        components, corrector_step_list[2]
                    )
                # Reset Quad once finished.
                log.info("Reset Quadrupole Setpoint")
                self._machine.set_quad_setpoint(quadrupole, quad_sp, True)
            # run feedbacks after each axis.
            self._machine.check_feedbacks()

        # Saving x and y in one file, as you cannot do just one axis.
        return RawData(rawdata, metadata)

    def get_slow_bba_corrector_steps(self, components: Components) -> List[float]:
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

    def analyse(self, rawdata: RawData) -> Results:
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

        results: Dict[str, List[float]] = {}
        plotting: Dict[str, Dict[str, np.ndarray]] = {}

        quad_names = []
        for key in data.keys():
            quad_name = key.split("__")[0]
            if quad_name not in quad_names:
                quad_names.append(quad_name)

        for quad_name in quad_names:
            for axis in ["x", "y"]:
                # Define variables that get changed for each plane.
                sigma_bpm = metadata["sigma_bpm"]
                bpm_indices = np.array(range(len(enabled_bpms)))
                high = np.zeros(shape=(len(enabled_bpms), 5))
                low = np.zeros(shape=(len(enabled_bpms), 5))
                oscillation_size = np.zeros(shape=(len(enabled_bpms), 5))
                # Extract data into our variables.
                for i in range(5):
                    high[:, i] = data[f"{quad_name}__{axis}_High_{i + 1}"]
                    low[:, i] = data[f"{quad_name}__{axis}_Low_{i + 1}"]
                    oscillation_size[:, i] = np.subtract(low[:, i], high[:, i])

                # Get rid of disabled bpms.
                disabled_bpms = np.logical_not(enabled_bpms)
                log.debug(f"Indices of disabled BPMs: {np.flatnonzero(disabled_bpms)}")
                # NOTE: This is currently disabled in order to give identical results to
                # quadplot.m, though removing them is probably the right thing to do.
                # NOTE: If we do choose to re-enable this then it should probably be
                # done during data collection like enabled_bpms rather than here.
                #fofb_disabled_bpms = np.array(self._machine.fofb_disabled[axis], dtype=bool)
                #log.debug(f"Indices of fofb disabled BPMs: {np.flatnonzero(fofb_disabled_bpms)}")
                disabled = disabled_bpms #| fofb_disabled_bpms
                high = np.delete(high, disabled, axis=0)
                low = np.delete(low, disabled, axis=0)
                oscillation_size = np.delete(oscillation_size, disabled, axis=0)
                sigma_bpm = np.delete(sigma_bpm, disabled)
                bpm_indices = np.delete(bpm_indices, disabled)
                if optimal_bpm not in bpm_indices:
                    raise IndexError(
                        "Please specify a different optimal BPM, currently specified "
                        f"BPM ({optimal_bpm}) is disabled."
                    )
                log.debug(f"Data points remaining after cleaning: {len(sigma_bpm)}")

                # 5 point linear least squares fit.
                bpm_number = list(bpm_indices).index(metadata["bpm_index"])
                oscillation_midpoint = (high[bpm_number, :] + low[bpm_number, :]) / 2
                # NOTE: The code immediately below is taken from quadplot.m with minimal
                # modification, other than porting it to Python.
                X = np.stack((np.ones(5), oscillation_midpoint)).T
                invXX = np.linalg.inv(X.T.dot(X))
                invXX_X = X.dot(invXX).T
                b = invXX_X.dot(oscillation_size.T).T

                # Get absolute gradients and x intercepts of the lines.
                gradients = abs(b[:, 1])
                offsets = -b[:, 0] / b[:, 1]

                # Remove all values with large difference between the fit value and that
                # BPM's standard deviation (currently hardcoded to 1e-4).
                y = np.zeros(shape=(b.shape[0], 5))
                large_fit_diff = np.zeros(b.shape[0], dtype=bool)
                # NOTE: The code immediately below is taken from quadplot.m with minimal
                # modification, other than porting it to Python.
                for i in range(b.shape[0]):
                    y[i, :] = (b[i, 1] * oscillation_midpoint) + b[i, 0]  # y = mx + c
                    if (
                        max(abs(y[i, :] - oscillation_size[i, :]))
                        > outlier_factor * sigma_bpm[i]
                    ):
                        large_fit_diff[i] = True
                log.debug(
                    "Indices with large error between fit and data: "
                    f"{np.flatnonzero(large_fit_diff)}"
                )
                gradients = np.delete(gradients, large_fit_diff)
                offsets = np.delete(offsets, large_fit_diff)
                oscillation_size = np.delete(oscillation_size, large_fit_diff, axis=0)
                bpm_indices = np.delete(bpm_indices, large_fit_diff)
                log.debug(f"Data points remaining after cleaning: {len(offsets)}")

                # Remove all values with overly shallow gradients.
                # NOTE: This misses once element if len(np.sort(gradients)) is odd.
                second_half = np.array_split(np.sort(gradients), 2)[1]
                if len(second_half) > 5:
                    min_gradient = second_half[-5]
                else:
                    min_gradient = second_half[-1]
                bad_gradients = np.abs(gradients) < min_gradient * min_slope_fraction
                log.debug(
                    "Indices with too shallow gradients: "
                    f"{np.flatnonzero(bad_gradients)}"
                )
                gradients = np.delete(gradients, bad_gradients)
                offsets = np.delete(offsets, bad_gradients)
                oscillation_size = np.delete(oscillation_size, bad_gradients, axis=0)
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
                    oscillation_size, stdev_outside_range, axis=0
                )
                bpm_indices = np.delete(bpm_indices, stdev_outside_range)
                log.debug(f"Data points remaining after cleaning: {len(offsets)}")

                key = f"{quad_name}__{axis}"
                results[key] = [np.mean(offsets), np.std(offsets, ddof=1)]
                log.debug(
                    f"Results for {key}: "
                    f"mean: {results[key][0]}, standard deviation: {results[key][1]}"
                )

                # Plot good data only.
                plotting[key] = {"x": oscillation_midpoint, "y": oscillation_size.T}

        offsets = self.create_offsets_dict(results, metadata)

        return Results(results, metadata, plotting, offsets)
