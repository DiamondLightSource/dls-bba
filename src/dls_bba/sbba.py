import logging as log

import numpy as np
from cothread import Sleep

from dls_bba.algorithm import Algorithm
from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
from dls_bba.isotime import get_isotime
from dls_bba.machine import Machine


class SlowBBA(Algorithm):
    def __init__(self, machine: Machine):
        super().__init__(machine)

    def run(self, components_pair: list[Components]) -> RawData:
        rawdata = {}
        metadata = {}
        config = self._machine.config.get_settings()
        metadata.update(config)
        metadata["method"] = "SlowBBA"
        metadata["isotime"] = get_isotime()
        metadata["enabled_bpms"] = self._machine.get_enabled_bpms()
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
                    quad_step,
                ) = self.calculate_quad_setpoints(quadrupole)
                corrector_step_list = self.get_slow_bba_corrector_steps(components)

                # Always overshoot the high quad step and work down and keep direction
                # consistent to mitigate unwanted hysteresis effects.
                # FYI correctors are significantly less prone to hysteresis effects.
                self._machine.set_quad_setpoint(quadrupole, quad_start, True)
                # Give Cell 2 DDBA magnets more time to ramp.
                if "SR02" in quad_name:
                    Sleep(1)

                for movement, quad_movement in [
                    ("High", quad_high),
                    ("Low", quad_low),
                ]:
                    log.debug(f"Corrector Movement: {movement}")
                    self._machine.set_quad_setpoint(quadrupole, quad_movement, True)

                    for index, step in enumerate(corrector_step_list, start=1):
                        self._machine.set_corrector_setpoint(components, step)
                        Sleep(0.5)  # Fixed time for orbit to stabilise.
                        measured_bpms = self._machine.measure_bpms(components.axis)

                        key = f"{quad_name}_{components.axis}_{movement}_{index}"
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
                # Reset Quad and Corrector once finished.
                self._machine.set_corrector_setpoint(components, corrector_step_list[2])
                self._machine.set_quad_setpoint(quadrupole, quad_sp, True)
            # run feedbacks after each axis.
            self._machine.check_feedbacks()

        # Saving x and y in one file, as you cannot do just one axis.
        return RawData(rawdata, metadata)

    def analyse(self, rawdata: RawData) -> Results:
        data = rawdata.rawdata
        metadata = rawdata.metadata

        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        min_slope_fraction = metadata["MIN_SLOPE_FRACTION"]
        center_outlier_factor = metadata["CENTER_OUTLIER_FACTOR"]
        bpm_index = metadata["bpm_index"]

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
                for index in range(5):
                    key = f"{quad_name}_{axis}_High_{index + 1}"
                    high = data[key]
                    key = f"{quad_name}_{axis}_Low_{index + 1}"
                    low = data[key]
                    matrix[index, :] = np.subtract(high, low)

                # Get rid of disabled bpms.
                disabled_bpms = np.logical_not(enabled_bpms)
                log.debug(f"Disabled BPMs: {np.flatnonzero(disabled_bpms)}")

                # Get rid of bad bpms.
                fofb_disabled_bpms = np.array(self._machine.fofb_disabled[axis] == 1)
                log.debug(f"Bad BPMs: {np.flatnonzero(fofb_disabled_bpms)}")

                disabled = disabled_bpms | fofb_disabled_bpms
                matrix = np.delete(matrix, disabled, axis=1)
                # To keep the index inline with the original BPM.
                bpm_index -= np.sum(disabled[:bpm_index])

                fit = np.polynomial.polynomial.polyfit(matrix[:, bpm_index], matrix, 1)
                p = np.array([1 / fit[1], -fit[0] / fit[1]]).T
                gradients = list(p[:, 1])

                sorted_gradients = np.sort(gradients)
                # Note: This misses once element if len(sorted_gradients) is odd.
                second_half = np.array_split(sorted_gradients, 2)[1]

                if len(second_half) > 5:
                    min_gradient = second_half[-5]
                else:
                    min_gradient = second_half[-1]
                min_gradient = min_gradient * min_slope_fraction

                bad_gradients = np.abs(gradients) < min_gradient
                log.debug(
                    f"Indices with too shallow gradients: {np.flatnonzero(bad_gradients)}"
                )
                p = np.delete(p, bad_gradients, axis=0)
                log.debug(f"Size of p: {np.shape(p)}")

                # Remove all values that are more than 1 stdev from the mean.
                offset_mean = np.mean(p[:, 1])
                offset_stdev = np.std(p[:, 1])

                max_value = offset_mean + (offset_stdev * center_outlier_factor)
                min_value = offset_mean - (offset_stdev * center_outlier_factor)

                stdev_out_of_range = (p[:, 1] <= min_value) | (p[:, 1] >= max_value)
                p = np.delete(p, stdev_out_of_range, axis=0)

                offset_mean = np.mean(p[:, 1])
                offset_stdev = np.std(p[:, 1])
                log.info(f"Final size of p: {np.shape(p)}")

                key = f"{quad_name}_{axis}"
                results[key] = [offset_mean, offset_stdev]

                # First value is x, second is y
                matrix = np.delete(matrix, bad_gradients, axis=1)
                bpm_index -= np.sum(bad_gradients[:bpm_index])

                matrix = np.delete(matrix, stdev_out_of_range, axis=1)
                bpm_index -= np.sum(stdev_out_of_range[:bpm_index])

                plotting[key] = {"x": (matrix[:, bpm_index]).tolist(), "y": matrix}

        offsets = self.create_offsets_dict(results, metadata)

        return Results(results, metadata, plotting, offsets)
