"""This file contains slow BBA specific functions and classes"""

import logging as log
from statistics import mean, stdev

import cothread
import numpy as np

from dls_bba.common import Algorithm, RawData, Results
from dls_bba.faa import TICKS_PER_SECOND

NETWORK_LAG_S = 0.5
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 0.5
NETWORK_LAG = int(NETWORK_LAG_S * TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * TICKS_PER_SECOND)
SBBA_UNIT_CONVERSION = (
    1000  # TODO: Remember to times result offset by this? SBBA matlab needs it.
)


class SBBA(Algorithm):
    def __init__(self, accelerator):
        super().__init__(accelerator)
        self.configure()

    def configure(
        self,
        quadrupole_scalar=0.02,
        corrector_scalar=2,
        decimated=False,
        *args,
        **kwargs,
    ):
        """These are optional arguments, which are used during testing."""
        self.quadrupole_scalar = quadrupole_scalar
        self.corrector_scalar = float(corrector_scalar)
        self.decimated = decimated
        log.debug(
            f"Configuration: Quadrupole Scalar: {self.quadrupole_scalar}, Corrector Scalar: {self.corrector_scalar}, Decimated: {self.decimated}"
        )

    def run(self, element, plane_info, max_orbit) -> RawData:
        method = "SBBA"
        log.info(f"{method} process started in plane {plane_info.axis}.")

        bpm, quad_list, corrector = self.select_elements(element, plane_info)
        quad_pv_list = [
            self._accelerator.element_to_pv_prefix(quad_element)
            for quad_element in quad_list
        ]
        bpm_pv_prefix = self._accelerator.element_to_pv_prefix(bpm)
        corrector_pv_prefix = self._accelerator.element_to_pv_prefix(
            corrector, plane_info
        )
        log.info(
            f"Quads: {quad_pv_list}, BPM: {bpm_pv_prefix}, Corrector: {corrector_pv_prefix}."
        )
        raw_data = {}
        metadata = {
            "method": method,
            "plane": plane_info,
            "quad": quad_pv_list,
            "bpm_pv": bpm_pv_prefix,
            "bpm_index": self._accelerator.bpms.index(bpm),
            "corrector": corrector_pv_prefix,
            "decimated": self.decimated,
            "enabled_bpms": self._accelerator.enabled_bpms,
            "quadrupole_scalar": self.quadrupole_scalar,
            "corrector_scalar": self.corrector_scalar,
        }
        for quad in quad_list:
            self.toggle_feedbacks(max_orbit)
            original_offsets = self.zero_origins(bpm, plane_info)

            quad_step = self._accelerator.measure_quad(quad) * self.quadrupole_scalar
            corr_step = (
                self._accelerator.microrads(corrector, plane_info)
                * self.corrector_scalar
            )
            log.info(f"Quad step: {quad_step}, Corrector amp: {corr_step}.")
            metadata["quad_step"] = quad_step
            metadata["corr_step"] = corr_step

            quad_sp = self._accelerator.measure_quad(quad)
            quad_high = quad_sp + quad_step
            quad_low = quad_sp - quad_step
            quad_lag_s = quad_step / QUAD_SLEW_RATE

            corrector_sp = self._accelerator.measure_corrector(corrector, plane_info)
            corrector_step_list = [
                corr_step,
                corr_step / 2,
                0,
                -corr_step / 2,
                -corr_step,
            ]

            quad_pv_root = self._accelerator.element_to_pv_prefix(quad).replace(
                "-", "_"
            )

            for index, step in enumerate(corrector_step_list):
                log.info(f"Index: {index}, Step: {step}")
                # Step the corrector to the value.
                self._accelerator.set_corrector(
                    corrector, plane_info, corrector_sp + step
                )
                # cothread.Sleep(NETWORK_LAG + ((Cycle/freq) * ticks) + SAFETY_NET) / TICKS_PER_SECOND)
                cothread.Sleep(0.1)
                # High quad step
                self._accelerator.set_quad(quad, quad_high)
                cothread.Sleep(quad_lag_s / 2)
                log.info(f"Quad High Measurement for corrector step {index}.")
                high_bpms = self._accelerator.measure_bpms(plane_info)
                # Low quad step
                self._accelerator.set_quad(quad, quad_low)
                cothread.Sleep(quad_lag_s)
                log.info(f"Quad Low Measurement for corrector step {index}.")
                low_bpms = self._accelerator.measure_bpms(plane_info)
                cothread.Sleep(quad_lag_s / 2)
                # Change in step.
                raw_data[f"{quad_pv_root}_{index}_High"] = high_bpms
                raw_data[f"{quad_pv_root}_{index}_Low"] = low_bpms

            # Reset magnets
            self._accelerator.set_corrector(corrector, plane_info, corrector_sp)
            self._accelerator.set_quad(quad, quad_sp)
            self.restore_origins(original_offsets)

        return RawData(raw_data, method, metadata)

    def analyse_data(self, raw_data, plot_output, *args, **kwargs):
        data = raw_data.raw_data
        metadata = raw_data.metadata

        enabled_bpms = np.equal(metadata["enabled_bpms"], 1)
        offsets = []
        errors = []

        quad_prefixs = []
        for key in data:
            quad_prefix = "_".join(key.split("_")[0:4])
            if quad_prefix not in quad_prefixs:
                quad_prefixs.append(quad_prefix)

        for quad in quad_prefixs:
            matrix = np.zeros(shape=(5, len(enabled_bpms)))
            for index in range(5):
                high = data[f"{quad}_{index}_High"]
                low = data[f"{quad}_{index}_Low"]
                matrix[index, :] = np.subtract(high, low)

            bad_indices = []
            # Get rid of disabled bpms.
            for index, value in reversed(list(enumerate(enabled_bpms))):
                if value == 0:
                    bad_indices.append(index)

            # Get rid of bad bpms.
            if metadata["plane"]["axis"] == "X":
                for index, _ in enumerate(self._accelerator.bpms):
                    if self._accelerator.bpm_h_fofb_enabled[index] == 1:
                        bad_indices.append(index)
            if metadata["plane"]["axis"] == "Y":
                for index, _ in enumerate(self._accelerator.bpms):
                    if self._accelerator.bpm_v_fofb_enabled[index] == 1:
                        bad_indices.append(index)

            matrix = np.delete(matrix, bad_indices, axis=1)

            corr_step = metadata["corr_step"]
            corrector_step_list = [
                corr_step,
                corr_step / 2,
                0,
                -corr_step / 2,
                -corr_step,
            ]
            fit = np.polynomial.polynomial.polyfit(corrector_step_list, matrix, 1)
            p = np.array([1 / fit[1], -fit[0] / fit[1]]).T

            gradients = list(p[:, 1])
            max_gradient = abs(max(gradients, key=abs))

            # Get rid of bad gradients
            bad_gradients = []
            for gradient in gradients:
                if abs(gradient) < max_gradient * 0.25:
                    bad_gradients.append(gradients.index(gradient))

            p = np.delete(p, bad_gradients, axis=0)
            # gradient > 20 * BPMnoise?

            # Remove all values that are more than 1 stdev from the mean.
            while True:
                log.info(f"Size of p: {np.shape(p)}")
                counter = 0
                offset_mean = mean(p[:, 1])
                offset_stdev = stdev(p[:, 1])
                std_list = []
                for index, (offset, gradient) in enumerate(p):
                    if (offset > offset_mean + offset_stdev) or (
                        offset < offset_mean - offset_stdev
                    ):
                        counter += 1
                        std_list.append(index)
                p = np.delete(p, std_list, axis=0)
                if counter == 0:
                    break

            log.info(f"Final size of p: {np.shape(p)}")
            if plot_output:
                log.error("Plotting - Not implimented yet.")
            offset_mean = mean(p[:, 1])
            offset_stdev = stdev(p[:, 1])
            log.info(offset_mean, offset_stdev)
            # Change results to mm.
            offsets.append(offset_mean / SBBA_UNIT_CONVERSION)
            errors.append(offset_stdev / SBBA_UNIT_CONVERSION)

        results = {}
        for index, _ in enumerate(offsets):
            quadrupole = quad_prefixs[index]
            offset = offsets[index]
            error = errors[index]
            quad_name = quadrupole.replace("_", "-")
            log.debug(f"Quad: {quad_name} offset calculated: {offset} +- {error}.")
            results[quadrupole] = [offset, error]

        offset = mean(offsets)
        sum_error = 0
        for error in errors:
            sum_error += error**2
        error = np.sqrt(sum_error)

        bpm_pv_prefix = metadata["bpm_pv"]
        log.info(f"BPM: {bpm_pv_prefix} offset calculated: {offset} +- {error}.")
        return Results(results, bpm_pv_prefix, metadata)
