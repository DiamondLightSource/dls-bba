"""This file contains functions and classes used in both slow and fast BBA."""
import logging as log
from abc import ABC, abstractmethod
from dataclasses import dataclass
from statistics import mean
from subprocess import run
from time import sleep
from typing import Any, Dict, NamedTuple

import numpy as np
import scipy.io as io
from cothread import Sleep
from cothread.catools import caget, caput

MAXIMUM_CURRENT_DROP = 20  # mA
MINIMUM_CURRENT_DROP = 5  # mA

PlaneValues = NamedTuple(
    "PlaneValues", [("index", int), ("axis", str), ("corrector", str), ("kick", str)]
)
PLANE_VALUES = {
    "HORIZONTAL": PlaneValues(0, "X", "HSTR", "x_kick"),
    "VERTICAL": PlaneValues(1, "Y", "VSTR", "y_kick"),
}

ORIGIN_SUFFIXES = {
    # "BBA": ":CF:BBA_{axis}_S",
    "BCD": ":CF:BCD_{axis}_S",
    "GOLDEN": ":CF:GOLDEN_{axis}_S",
}


@dataclass
class RawData:
    raw_data: Dict[str, Any]
    algorithm: str
    metadata: Dict[str, Any]

    # TODO: asdict, make all shared attributes not in metadata.

    def save(self, time_prefix, filepath):
        metadata = self.metadata
        raw_data = self.raw_data
        algorithm = self.algorithm
        filename = "{}/{}-{}-{}-rawdata.mat".format(
            filepath, time_prefix, metadata["bpm_pv"], metadata["plane"].axis
        )
        metadata["plane"] = metadata[
            "plane"
        ]._asdict()  # NamedTuple not supported in .mat file.
        dct = {
            "raw_data": raw_data,
            "algorithm": algorithm,
            "metadata": metadata,
        }
        io.savemat(filename, dct, oned_as="row")
        log.info(f"Saved raw data as {filename}")

    @classmethod
    def from_file(cls, filename):
        dct = io.loadmat(filename, simplify_cells=True)
        metadata = dct["metadata"]
        metadata["plane"] = PlaneValues(**metadata["plane"])
        return cls(dct["raw_data"], dct["algorithm"], metadata)


@dataclass
class Results:
    results: Dict[str, Any]
    bpm_pv_prefix: str
    metadata: Dict[str, Any]

    def save(self, time_prefix, filepath):
        metadata = self.metadata
        bpm_pv_prefix = self.bpm_pv_prefix
        results = self.results
        metadata["plane"] = metadata[
            "plane"
        ]._asdict()  # NamedTuple not supported in .mat file.
        filename = "{}/{}-{}-{}-results.mat".format(
            filepath,
            time_prefix,
            metadata["bpm_pv"],
            metadata["plane"].axis,
        )
        dct = {
            "results": results,
            "bpm_pv_prefix": bpm_pv_prefix,
            "metadata": metadata,
        }
        io.savemat(filename, dct, oned_as="row")
        log.info(f"Saved results as {filename}")
        return filename

    @classmethod
    def from_file(cls, filename):
        dct = io.loadmat(filename, simplify_cells=True)
        metadata = dct["metadata"]
        metadata["plane"] = PlaneValues(**metadata["plane"])
        return cls(dct["results"], dct["bpm_pv_prefix"], metadata)


class LowCurrentError(Exception):
    pass


class Algorithm(ABC):
    def __init__(self, accelerator):
        self._accelerator = accelerator

    @abstractmethod
    def configure(self):
        pass

    def check_beam_current(self, initial_current) -> bool:
        """Checks that the beam current hasn't dropped substantially
        and gives an opportunity to top up. Will return True if beam is okay,
        will return False if beam is okay but was topped up.
        If beam has dropped too much, will cancel BBA."""
        current_drop = initial_current - self._accelerator.get_beam_current()
        if current_drop > MAXIMUM_CURRENT_DROP:
            log.critical(
                f"Beam current dropped by >{MAXIMUM_CURRENT_DROP}mA. Cancelling BBA."
            )
            raise LowCurrentError(
                f"Beam current dropped by >{MAXIMUM_CURRENT_DROP}mA. Cancelling BBA."
            )

        if current_drop > MINIMUM_CURRENT_DROP:
            log.error(
                f"Beam current dropped by {MINIMUM_CURRENT_DROP}-{MAXIMUM_CURRENT_DROP}mA. Top-up or cancel."
            )
            response = ""
            while True:
                response = input("Input y to continue, or n to cancel: ").lower()

                if response == "n":
                    log.critical("User cancelled BBA.")
                    raise LowCurrentError(
                        f"Beam current dropped by {MINIMUM_CURRENT_DROP}-{MAXIMUM_CURRENT_DROP}mA. User cancelled BBA."
                    )
                elif response == "y":
                    current_drop = (
                        initial_current - self._accelerator.get_beam_current()
                    )
                    if current_drop < MINIMUM_CURRENT_DROP:
                        break
                    print(
                        f"Current not high enough yet. Must be within {MINIMUM_CURRENT_DROP} mA of {initial_current}"
                    )

            return False

        return True

    def select_elements(self, element, plane_info):
        """Input quad/bpm element, calculate relevent elements.

        Note: This returns quads in a list.
        """
        if "quadrupole" in element.families:
            quad_pv_prefix = self._accelerator.element_to_pv_prefix(element)
            quad = [element]
            bpm_pv_prefix = self._accelerator.quad_to_bpm_dict[quad_pv_prefix]
            bpm = self._accelerator.pv_prefix_to_element(bpm_pv_prefix)
            corrector = self._accelerator.effective_corrector(bpm_pv_prefix, plane_info)
        elif "bpm" in element.families:
            bpm = element
            bpm_pv_prefix = self._accelerator.element_to_pv_prefix(bpm)
            corrector = self._accelerator.effective_corrector(bpm_pv_prefix, plane_info)
            bpm_pv_prefix = self._accelerator.element_to_pv_prefix(bpm)
            quad_pv_prefix = self._accelerator.bpm_to_quad_dict[bpm_pv_prefix]
            quad = [
                self._accelerator.pv_prefix_to_element(quad_pv)
                for quad_pv in quad_pv_prefix
            ]
        else:
            ValueError("Unexpected element: Only quadrupoles and bpms are allowed.")
        return bpm, quad, corrector

    def toggle_tune(self, tolerance=0.0005):
        tune_approved = False
        target_x = caget("SR-CS-TFB-01:TUNE:H")
        target_y = caget("SR-CS-TFB-01:TUNE:V")
        log.debug(f"Target tunes: X {target_x}, Y {target_y}")

        while not tune_approved:
            tune_x = caget("SR23C-DI-TMBF-01:TUNE:TUNE")
            tune_y = caget("SR23C-DI-TMBF-02:TUNE:TUNE")
            log.debug(f"Measured tunes: X {tune_x}, Y {tune_y}")
            if (target_x - tolerance < tune_x < target_x + tolerance) and (
                target_y - tolerance < tune_y < target_y + tolerance
            ):
                tune_approved = True
            else:
                log.debug("Correcting tune.")
                caput("SR-CS-TFB-01:ONOFF", 1, wait=True)
                Sleep(5)
                caput("SR-CS-TFB-01:ONOFF", 0, wait=True)

    def toggle_fofb(self):
        log.warn("Correcting orbit with FOFB.")
        run(
            "/dls_sw/prod/R3.14.12.3/support/fastfeedback/12-3/fofbApp/opi/fofbnogui.py start",
            check=True,
            shell=True,
        )
        sleep(3)
        run(
            "/dls_sw/prod/R3.14.12.3/support/fastfeedback/12-3/fofbApp/opi/fofbnogui.py stop",
            check=True,
            shell=True,
        )
        sleep(3)

    def toggle_feedbacks(self, max_orbit):
        """Confirms that all feedbacks are off, and toggles FOFB to realign if needed."""
        feedbacks = {
            "Fast Orbit Feedback": ["SR01A-CS-FOFB-01:RUN", 0],
            "Slow Orbit Feedback": ["SR-CS-SOFB-01:ONOFF", 0],
            "Tune Feedback": ["SR-CS-TFB-01:ONOFF", 0],
            "Vertical Emittance Feedback": ["SR-CS-VEFB-01:LOOP", 0],
        }

        for key, pv_name in feedbacks.items():
            if caget(pv_name[0]) != pv_name[1]:
                log.critical(f"{key} running. Stop feedbacks before running BBA.")
                raise ValueError(f"{key} running. Stop feedbacks before running BBA.")

        bpm_h_values = self._accelerator.measure_bpms(PLANE_VALUES["HORIZONTAL"])
        bpm_v_values = self._accelerator.measure_bpms(PLANE_VALUES["VERTICAL"])

        bpm_values = []
        for index, _ in enumerate(bpm_h_values):
            if (
                self._accelerator.bpm_h_fofb_enabled[index] == 0
                and self._accelerator.enabled_bpms[index] == 1
            ):
                bpm_values.append(bpm_h_values[index])
        for index, _ in enumerate(bpm_v_values):
            if (
                self._accelerator.bpm_v_fofb_enabled[index] == 0
                and self._accelerator.enabled_bpms[index] == 1
            ):
                bpm_values.append(bpm_v_values[index])

        max_value = abs(max(bpm_values, key=abs))
        # value in mm, max_orbit in um.
        if float(max_value * 1000) >= float(max_orbit):
            self.toggle_fofb()
            self.toggle_tune()

    def zero_origins(self) -> Dict[str, Any]:
        """Zeros BCD and Golden offsets. Also stores current Golden offset value for restoring later."""
        log.info("Origins Zeroed")
        offsets = {}
        for bpm in self._accelerator.bpms:
            for direction in ["HORIZONTAL", "VERTICAL"]:
                bpm_pv_root = self._accelerator.element_to_pv_prefix(bpm)
                bcd_pv = bpm_pv_root + ORIGIN_SUFFIXES["BCD"].format(
                    axis=PLANE_VALUES[direction].axis
                )
                golden_pv = bpm_pv_root + ORIGIN_SUFFIXES["GOLDEN"].format(
                    axis=PLANE_VALUES[direction].axis
                )

                offsets[golden_pv] = caget(golden_pv)

                caput(bcd_pv, 0, wait=True)
                caput(golden_pv, 0, wait=True)
        Sleep(0.2)
        log.debug(offsets)
        return offsets

    def restore_origins(self, offsets):
        """Restores offset values from offsets dictionary."""
        # for key, value in offsets.items():
        #     caput(key, value, wait=True)
        Sleep(0.2)
        log.info("Origins Restored")

    @abstractmethod
    def run(self, element, plane_info, max_orbit):
        # This is fbba/sbba specifc -> save into a RawData object
        return RawData

    @abstractmethod
    def analyse_data(self, data, plot_output, *args, **kwargs):
        # This is fbba/sbba specifc -> save into a Results object
        return Results

    def apply_results(self, results):
        plane_info = results.metadata["plane"]
        bpm_pv_prefix = results.bpm_pv_prefix
        offsets = []
        errors = []
        for key, value in results.results.items():
            offsets.append(value[0])
            errors.append(value[1])

        mean_offset = mean(offsets)
        sum_error = 0
        for offset, error in zip(offsets, errors):
            sum_error += (error / offset) ** 2
        error = np.sqrt(sum_error) * mean_offset

        if plane_info.axis == "Y":
            suffix = ":CF:BBA_Y_S"
            log.info("Applying to the Y axis.")
        elif plane_info.axis == "X":
            suffix = ":CF:BBA_X_S"
            log.info("Applying to the X axis.")
        else:
            raise ValueError("Plane info incorrect.")
        setting_pv = bpm_pv_prefix + suffix

        current_offset = caget(setting_pv)
        new_offset = current_offset + mean_offset
        log.info(
            f"BPM: {bpm_pv_prefix}, Old offset: {current_offset}, Delta: {mean_offset} +- {error}, New offset: {new_offset}."
        )
        caput(setting_pv, new_offset, wait=True)
        Sleep(0.2)
