import logging as log

import numpy as np
from cothread import Sleep

from dls_bba.algorithm import Algorithm
from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
from dls_bba.isotime import get_isotime
from dls_bba.lattice import Lattice


class SlowBBA(Algorithm):
    def __init__(self, lattice: Lattice):
        super().__init__(lattice)

    def run(self, components_pair: list[Components]) -> RawData:
        rawdata = {}
        metadata = {}
        metadata.update(self._lattice.config._config)
        metadata["method"] = "SlowBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._lattice.get_enabled_bpms()
        metadata["bpm_name"] = components_pair[0].bpm_name
        metadata["bpm_index"] = components_pair[0].bpm_index

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
                ) = self._lattice.calculate_quad_setpoints(quadrupole)
                corrector_step_list = self._lattice.get_slow_bba_corrector_steps(
                    components
                )

                # Always overshoot the high quad step and work down and keep direction
                # consistent to mitigate unwanted hysteresis effects.
                # FYI correctors are significantly less prone to hysteresis effects.
                self._lattice.set_quad_setpoint(quadrupole, quad_start, True)
                # Give Cell 2 DDBA magnets more time to ramp.
                if "SR02" in quad_name:
                    Sleep(1)

                for movement, quad_movement in [
                    ("High", quad_high),
                    ("Low", quad_low),
                ]:
                    log.debug(f"Corrector Movement: {movement}")
                    self._lattice.set_quad_setpoint(quadrupole, quad_movement, True)

                    for index, step in enumerate(corrector_step_list, start=1):
                        self._lattice.set_corrector_setpoint(components.corrector, step)
                        Sleep(0.1)  # Fixed time for orbit to stabilise.
                        measured_bpms = self._lattice.measure_bpms(components.axis)

                        key = f"{quad_name}_{components.axis}_{movement}_{index}"
                        rawdata[key] = measured_bpms
                        metadata[key] = {
                            "components": components.as_dict(),
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
                        components.corrector, corrector_step_list[2]
                    )
                # Reset Quad and Corrector once finished.
                self._lattice.set_corrector_setpoint(
                    components.corrector, corrector_step_list[2]
                )
                self._lattice.set_quad_setpoint(quadrupole, quad_sp, True)
            # run feedbacks after each axis.
            self._lattice.check_feedbacks()

        # Saving x and y in one file, as you cannot do just one axis.
        return RawData(rawdata, metadata)

    def analyse(self, rawdata: RawData) -> Results:
        # TODO: Does not reference the bpm?
        data = rawdata.rawdata
        metadata = rawdata.metadata

        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        min_slope_fraction = metadata["MIN_SLOPE_FRACTION"]
        center_outlier_factor = metadata["CENTER_OUTLIER_FACTOR"]

        results = {}
        plotting = {}

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
                    if self._lattice.fofb_disabled[axis][index] == 1:
                        bad_indices.append(index)
                log.debug(f"Disabled and bad BPMs: {bad_indices}")

                matrix = np.delete(matrix, bad_indices, axis=1)

                # Relative corrector step from current setpoint
                corrector_steps = metadata[key]["corrector_steps"]
                corrector_steps = [
                    step - corrector_steps[2] for step in corrector_steps
                ]

                fit = np.polynomial.polynomial.polyfit(corrector_steps, matrix, 1)
                p = np.array([1 / fit[1], -fit[0] / fit[1]]).T
                gradients = list(p[:, 1])

                sorted_gradients = sorted((abs(v), i) for i, v in enumerate(gradients))

                second_half = sorted_gradients[len(sorted_gradients) // 2 :]
                if len(second_half) > 5:
                    min_gradient, _ = second_half[-5]
                else:
                    min_gradient, _ = second_half[-1]
                min_gradient = min_gradient * min_slope_fraction

                bad_gradients = []
                for v, i in sorted_gradients:
                    if v < min_gradient:
                        bad_gradients.append(i)
                bad_gradients = sorted(bad_gradients)[::-1]

                log.debug(f"Indices with too shallow gradients: {bad_gradients}")
                p = np.delete(p, bad_gradients, axis=0)
                log.debug(f"Size of p: {np.shape(p)}")

                # Remove all values that are more than 1 stdev from the mean.
                offset_mean = np.mean(p[:, 1])
                offset_stdev = np.std(p[:, 1])
                stdev_list = []
                max_value = offset_mean + (offset_stdev * center_outlier_factor)
                min_value = offset_mean - (offset_stdev * center_outlier_factor)
                for index, offset in enumerate(p[:, 1]):
                    if not min_value < offset < max_value:
                        stdev_list.append(index)
                p = np.delete(p, stdev_list, axis=0)

                log.info(f"Final size of p: {np.shape(p)}")

                key = f"{quad_name}_{axis}"
                results[key] = [offset_mean, offset_stdev]

                # First value is x, second is y
                matrix_x = np.delete(matrix, bad_gradients, axis=1)
                matrix_xy = np.delete(matrix_x, stdev_list, axis=1)
                plotting[key] = {"x": corrector_steps, "y": matrix_xy}

        return Results(results, metadata, plotting)
