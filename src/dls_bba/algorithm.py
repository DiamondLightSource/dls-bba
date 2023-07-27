import logging as log
import os
from abc import ABC, abstractmethod
from typing import List

import numpy as np
from cothread import Sleep
from cothread.catools import caput
from pytac.element import EpicsElement

from dls_bba.components import Components
from dls_bba.datatypes import CalculatedOffset, RawData, Results
from dls_bba.machine import ORIGIN_SUFFIXES, Machine
from dls_bba.plotting import bba_offsets_plot


class Algorithm(ABC):
    def __init__(self, machine: Machine):
        self._machine = machine

    @abstractmethod
    def run(self, component_pair: list[Components]) -> RawData:
        pass

    @abstractmethod
    def analyse(self, rawdata: RawData) -> Results:
        pass

    def calculate_quad_setpoints(self, quadrupole: EpicsElement):
        """"""
        quad_step_percent = self._machine.config["QUADRUPOLE_STEP_PERCENT"] * 1e-2

        quad_setpoint = self._machine.get_quad_setpoint(quadrupole)
        quad_step = quad_setpoint * quad_step_percent
        quad_start_high = quad_setpoint + (2 * quad_step)
        quad_high = quad_setpoint + quad_step
        quad_low = quad_setpoint - quad_step
        return quad_start_high, quad_high, quad_low, quad_setpoint, quad_step

    def create_offsets_dict(self, results, metadata) -> dict[str, CalculatedOffset]:
        offsets: dict[str, CalculatedOffset] = {}
        bpm_name = metadata["bpm_name"]
        bpm_index = metadata["bpm_index"]

        for index, axis in enumerate(["x", "y"]):
            bpm_key = str(bpm_name + ORIGIN_SUFFIXES["BBA"].format(axis=axis.upper()))
            # Get current BBA offset.
            old_bba = float(self._machine.get_bba_offsets()[index][bpm_index])
            # Calculate the change needed.
            difference = self.calculate_new_offsets(results, axis)
            # Calculate the new BBA offset.
            new_bba = float("%0.4f" % (old_bba + difference[0]))
            # Set all values to 4d.p.
            diff_value, diff_error = [float("%0.4f" % v) for v in difference]

            offsets[bpm_key] = CalculatedOffset(
                old_bba, new_bba, diff_value, diff_error
            )

        return offsets

    def calculate_new_offsets(
        self, results: dict[str, List[float]], axis: str
    ) -> List[float]:
        keys = [key for key in results.keys() if axis in key]
        values = []
        errors = []
        for key in keys:
            values.append(results[key][0])
            errors.append(results[key][1])

        sum_error = 0.0
        mean_value = float(np.mean(values))
        for value, error in zip(values, errors):
            sum_error += (error / value) ** 2
        total_error = np.sqrt(sum_error) * mean_value
        return [mean_value, total_error]

    def use_bba_offsets(self, results_list: List[Results], save_location: str):
        """"""
        offsets_dict: dict[str, CalculatedOffset] = {}
        for results in results_list:
            offsets_dict.update(results.offsets.items())

        self._save_bba_offsets(offsets_dict, save_location)
        # TODO: This is needed for CLI but not for GUI
        bba_offsets_plot(self._machine, offsets_dict, save_location)
        while True:
            msg = "Apply these BBA offsets? (y / n) : "
            response = input(msg).lower().strip()
            if response == "n":
                break
            elif response == "y":
                self.apply_bba_offsets(offsets_dict)
                self._machine.apply_feedbacks()
                break

    def _save_bba_offsets(
        self,
        offsets_dict: dict[str, CalculatedOffset],
        save_location: str,
    ):
        filename = os.path.join(save_location, "results.txt")
        with open(filename, "w") as writer:
            for key, value in offsets_dict.items():
                line = f"{key}  : Absolute change: {value.diff_value} +/- {value.diff_error} [mm]"
                log.info(line)
                writer.write(line)
                line = f"{key}  : Old: {value.old_value} [mm], New: {value.new_value} [mm]\n"
                log.info(line)
                writer.write(line)
            writer.close()

    def apply_bba_offsets(
        self,
        offsets_dict: dict[str, CalculatedOffset],
    ):
        pv_names = []
        pv_values = []
        for key, value in offsets_dict.items():
            pv_names.append(key)
            pv_values.append(value.new_value)
        caput(pv_names, pv_values, wait=True)
        log.info(f"{len(pv_names)} BBA Offsets Applied.")
        Sleep(0.2)
