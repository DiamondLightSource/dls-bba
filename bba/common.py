"""This file contains functions and classes used in both slow and fast BBA."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from statistics import mean
from subprocess import run
from time import sleep
from typing import Any, Dict, NamedTuple

import pytac
import scipy.io as io
import numpy as np
from cothread.catools import caget, caput

MAXIMUM_CURRENT_DROP = 20  # mA
MINIMUM_CURRENT_DROP = 5  # mA

PlaneValues = NamedTuple("PlaneValues", [("index", int), ("axis", str), ("corrector", str), ("kick", str)])
PLANE_VALUES = {
    "HORIZONTAL": PlaneValues(0, "X", "HSTR", "x_kick"),
    "VERTICAL": PlaneValues(1, "Y", "VSTR", "y_kick")}

ORIGIN_SUFFIXES = {
    "BBA": ":CF:BBA_{axis}_S",
    "BCD": ":CF:BCD_{axis}_S",
    "GOLDEN": ":CF:GOLDEN_{axis}_S"}


@dataclass
class RawData:
    raw_data: Dict[str, Any]
    algorithm: str
    metadata: Dict[str, Any]

    # TODO: asdict, make all shared attributes not in metadata.

    def save(self, time_prefix, filepath="data"):
        filename = "{}/{}-{}-{}-rawdata.mat".format(filepath, time_prefix, self.metadata["bpm_pv"], self.metadata["plane"].axis)
        self.metadata["plane"] = self.metadata["plane"]._asdict()  # NamedTuple not supported in .mat file.
        dct = {'raw_data': self.raw_data, 'algorithm': self.algorithm, 'metadata': self.metadata}
        io.savemat(filename, dct, oned_as="row")
        print(f"Saved data as {filename}")

    @classmethod
    def from_file(cls, filename):
        dct = io.loadmat(filename, simplify_cells=True)
        metadata = dct["metadata"]
        metadata["plane"] = PlaneValues(**metadata["plane"])
        return cls(dct['raw_data'], dct['algorithm'], metadata)


@dataclass
class Results:
    results: Dict[str, Any]
    bpm_pv_prefix: str
    metadata: Dict[str, Any]

    def save(self, time_prefix, filepath="data"):
        filename = "{}/{}-{}-{}-results.mat".format(filepath, time_prefix, self.metadata["bpm_pv"], self.metadata["plane"].axis)
        self.metadata["plane"] = self.metadata["plane"]._asdict()  # NamedTuple not supported in .mat file.
        dct = {'results': self.results, 'bpm_pv_prefix': self.bpm_pv_prefix, 'metadata': self.metadata}
        io.savemat(filename, dct, oned_as="row")
        print(f"Saved data as {filename}")

    @classmethod
    def from_file(cls, filename):
        dct = io.loadmat(filename, simplify_cells=True)
        metadata = dct["metadata"]
        metadata["plane"] = PlaneValues(**metadata["plane"])
        return cls(dct['results'], dct['bpm_pv_prefix'], metadata)


class LowBeamCurrent(Exception):
    pass


class Algorithm(ABC):
    def __init__(self, accelerator):
        self._accelerator = accelerator

    @abstractmethod
    def configure(self, *args, **kwargs):
        pass

    def check_beam_current(self, initial_current) -> bool:
        """Checks that the beam current hasn't dropped substantially
        and gives an opportunity to top up. Will return True if beam is okay, 
        will return False if beam is okay but was topped up.
        If beam has dropped too much, will cancel BBA."""
        current_drop = initial_current - self._accelerator.get_beam_current()
        if current_drop > MAXIMUM_CURRENT_DROP:
            log.critical(f"Beam current dropped by >20mA. Cancelling BBA.")
            raise LowBeamCurrent(f"Beam current dropped by >20mA. Cancelling BBA.")

        if current_drop > MINIMUM_CURRENT_DROP:
            log.error(f"Beam current dropped by 5-20mA. Top-up or cancel.")
            response = ""
            while True:
                response = input("Input y to continue, or n to cancel: ").lower()

                if response == "n":
                    log.critical("User cancelled BBA.")
                    raise LowBeamCurrent(f"Beam current dropped by 5-20mA. User cancelled BBA.")
                elif response == "y":
                    current_drop = initial_current - self._accelerator.get_beam_current()
                    if current_drop < MINIMUM_CURRENT_DROP:
                        break
                    print(f"Current not high enough yet. Must be within 5 mA of {initial_current}")

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
            quad = [self._accelerator.pv_prefix_to_element(quad_pv) for quad_pv in quad_pv_prefix]
        else:
            ValueError("Unexpected element: Only quadrupoles and bpms are allowed.")
        return bpm, quad, corrector

    def toggle_feedbacks(self, max_orbit):
        """Confirms that all feedbacks are off, and toggles FOFB to realign if needed."""
        feedbacks = {
            "Fast Orbit Feedback" : ['SR01A-CS-FOFB-01:RUN', 0],
            "Slow Orbit Feedback" : ['SR-CS-SOFB-01:ONOFF', 0],
            "Tune Feedback" : ['SR-CS-TFB-01:ONOFF', 0],
            "Vertical Emittance Feedback" : ['SR-CS-VEFB-01:LOOP', 0]}

        for key, pv_name in feedbacks.items():
            if caget(pv_name[0]) != pv_name[1]:
                raise ValueError(f"{key} running. Stop feedbacks before running BBA.")

        bpm_h_values = self._accelerator.accelerator.get_element_values("BPM", "x", pytac.RB)
        bpm_v_values = self._accelerator.accelerator.get_element_values("BPM", "y", pytac.RB)
        bpm_values = []
        for index in range(len(bpm_h_values)):
            if self._accelerator.bpm_h_fofb_enabled[index] == 0 and self._accelerator.bpm_disabled[index] == 1:
                bpm_values.append(bpm_h_values[index])
        for index in range(len(bpm_v_values)):
            if self._accelerator.bpm_v_fofb_enabled[index] == 0 and self._accelerator.bpm_disabled[index] == 1:
                bpm_values.append(bpm_v_values[index])

        max_value = abs(max(bpm_values, key=abs))
        # value in mm, max_orbit in um.
        if float(max_value * 1000) >= float(max_orbit):
            print("Correcting orbit with FOFB.")
            run("/dls_sw/prod/R3.14.12.3/support/fastfeedback/12-3/fofbApp/opi/fofbnogui.py start", check=True, shell=True)
            sleep(1)
            run("/dls_sw/prod/R3.14.12.3/support/fastfeedback/12-3/fofbApp/opi/fofbnogui.py stop", check=True, shell=True)
            sleep(1)

    def zero_origins(self, bpm, plane_info) -> Dict[str, Any]:
        """Zeros BCD and Golden offsets. Also stores current Golden offset value for restoring later."""
        # return None  # For testing -> PV's dont exist in virtac.
        bpm_pv_root = self._accelerator.element_to_pv_prefix(bpm)
        bcd_pv = bpm_pv_root + ORIGIN_SUFFIXES["BCD"].format(axis=plane_info.axis)
        golden_pv = bpm_pv_root + ORIGIN_SUFFIXES["GOLDEN"].format(axis=plane_info.axis)

        offsets = {}
        offsets[golden_pv]: caget(golden_pv)

        caput(bcd_pv, 0)
        caput(golden_pv, 0)
        return offsets

    def restore_origins(self, offsets):
        """Restores offset values from offsets dictionary."""
        # return None  # For testing -> PV's dont exist in virtac.
        for key, value in offsets.items():
            caput(key, value)

    def set_bpm_offset(self, bpm, value, plane_info):
        """Applies new offset value to the BBA offset."""
        # TODO: Should this be in Algorithm?

        bpm_pv_root = self._accelerator.element_to_pv_prefix(bpm)
        bba_pv = bpm_pv_root + ORIGIN_SUFFIXES["BBA"].format(axis=plane_info.axis)

        current_offset = caget(bba_pv)
        new_offset = current_offset + value
        caput(bba_pv, new_offset)

    @abstractmethod
    def run(self, element, plane_info, max_orbit) -> RawData:
        # This fbba/sbba specifc -> save into a Data object
        raw_data = {}
        return RawData(raw_data)

    @abstractmethod
    def analyse_data(self, data, plot_output, *args, **kwargs):
        pass

    def apply_results(self, results):
        plane_info = results.metadata["plane"]
        bpm_pv_prefix = results.bpm_pv_prefix
        offsets = []
        errors = []
        for key, value in results.results.items():
            offsets.append(value[0])
            errors.append(value[1])
        offset = mean(offsets)
        sum_error = 0
        for error in errors:
            sum_error += error ** 2
        error = np.sqrt(sum_error)

        if plane_info["axis"] == "Y":
            suffix = ":CF:BBA_Y_S"
        elif plane_info["axis"] == "X":
            suffix = ":CF:BBA_X_S"
        setting_pv = bpm_pv_prefix + suffix

        current_offset = caget(setting_pv)
        new_offset = current_offset + offset
        print(f"BPM: {bpm_pv_prefix}, Old offset: {current_offset}, Delta: {offset} +- {error}, New offset: {new_offset}.")
        caput(setting_pv, new_offset)
