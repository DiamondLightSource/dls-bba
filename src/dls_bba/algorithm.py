import logging as log
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import numpy as np
import pytac
from cothread import Sleep
from cothread.catools import caput

from dls_bba.components import Components
from dls_bba.datatypes import CalculatedOffset, RawData, Results
from dls_bba.machine import ORIGIN_SUFFIXES, Machine


class Algorithm(ABC):
    """The abstract base class for the various Algorithm BBA methods."""

    def __init__(self, machine: Machine):
        """The class is initialised with just the machine object.

        Args:
            machine: The machine object
        """
        self._machine = machine

    @abstractmethod
    def run(self, component_pair: List[Components]) -> RawData:
        """Run a single instance of BBA over both axes of a BPM.

        Args:
            component_pair: A list of x, y components for a single BPM.

        Returns:
            RawData object.
        """
        pass

    @abstractmethod
    def analyse(self, rawdata: RawData) -> Results:
        """Analyse a rawdata object and return the results.

        Args:
            rawdata: A RawData object.

        Returns:
            Results object.
        """
        pass

    def calculate_quad_setpoints(
        self, quadrupole: pytac.element.EpicsElement
    ) -> Tuple[float, float, float, float, float]:
        """This function calculates the quadrupole setpoints.

        Args:
            quadrupole: The EpicsElement object for the quadrupole.

        Returns:
            Initial starting point to establish a known hysteresis curve.
            The 'high' measurement point.
            The 'low' measurement point.
            The starting and ending setpoint.
            The step size.
        """
        quad_step_percent: float = (
            self._machine.config["QUADRUPOLE_STEP_PERCENT"] * 1e-2
        )

        quad_setpoint = self._machine.get_quad_setpoint(quadrupole)
        quad_step: float = quad_setpoint * quad_step_percent
        quad_start_high: float = quad_setpoint + (2 * quad_step)
        quad_high: float = quad_setpoint + quad_step
        quad_low: float = quad_setpoint - quad_step
        return quad_start_high, quad_high, quad_low, quad_setpoint, quad_step

    def get_slow_bba_corrector_steps(self, component: Components) -> List[float]:
        """This function calculates the five discrete corrector steps for SlowBBA.

        Args:
            component: A single component

        Returns:
            A list of the corrector steps.
        """
        setpoint = self._machine.get_corrector_setpoint(component)
        step = self._machine.corrector_kick(component)
        corrector_steps = [
            setpoint + step,
            setpoint + (step / 2),
            setpoint,
            setpoint - (step / 2),
            setpoint - step,
        ]
        return corrector_steps

    def create_offsets_dict(
        self, results: Dict[str, List[float]], metadata: Dict[str, Any]
    ) -> Dict[str, CalculatedOffset]:
        """This function converts a results object into a dictionary
        with key offset values stored.

        Args:
            results: The results dictionary from a Results object.
            metadata: The metadata dictionary from a Results object.

        Returns:
            A dictionary of old and new offsets, with keys as the BPM PVs.
        """
        offsets: Dict[str, CalculatedOffset] = {}
        bpm_name: str = metadata["bpm_name"]
        bpm_index: int = metadata["bpm_index"]

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
        self, results: Dict[str, List[float]], axis: str
    ) -> List[float]:
        """This function calculates the offset values when given the results dictionary.

        Args:
            results: The results dictionary from a Results object
            axis: The axis required.

        Returns:
            A list containing the value and the error.
        """
        keys = [key for key in results.keys() if axis in key]
        values: List[float] = []
        errors: List[float] = []
        for key in keys:
            values.append(results[key][0])
            errors.append(results[key][1])

        sum_error = 0.0
        mean_value = float(np.mean(values))
        for value, error in zip(values, errors):
            sum_error += (error / value) ** 2
        total_error = float(np.sqrt(sum_error) * mean_value)
        return [mean_value, total_error]

    def use_bba_offsets(self, results_list: List[Results], save_location: str) -> None:
        """This function supplies the logic on how to handle the results objects.

        Args:
            results_list: A list of Results objects.
            save_location: The folderpath to save the results to.
        """
        offsets_dict: Dict[str, CalculatedOffset] = {}
        for results in results_list:
            offsets_dict.update(results.offsets.items())

        self._save_bba_offsets(offsets_dict, save_location)
        self._plot_bba_offsets(offsets_dict)
        while True:
            message = "Apply these BBA offsets? (y / n) : "
            response = input(message).lower().strip()
            if response == "n":
                break
            elif response == "y":
                self._apply_bba_offsets(offsets_dict)
                pass

    def _save_bba_offsets(
        self,
        offsets_dict: Dict[str, CalculatedOffset],
        save_location: str,
    ) -> None:
        """This function saves the calculated offsets to a file in a human readable format.

        Args:
            offsets_dict: This holds all of the CalculatedOffset objects.
            save_location: The folder path to save the file in.
        """
        filename = os.path.join(save_location, "results.txt")
        with open(filename, "w") as writer:
            for key, value in offsets_dict.items():
                line = f"{key}  : Absolute change: {value.diff_value} +/- {value.diff_error} [mm]\n"
                log.info(line)
                writer.write(line)
                line = f"{key}  : Old: {value.old_value} [mm], New: {value.new_value} [mm]\n"
                log.info(line)
                writer.write(line)
            writer.close()

    def _plot_bba_offsets(self, offsets_dict: Dict[str, CalculatedOffset]) -> None:
        """This function plots the relative change in the new BBA offsets.

        Args:
            offsets_dict: This holds all of the CalculatedOffset objects.
        """
        change_in_x: List[float] = []
        change_in_dx: List[float] = []
        for bpm_name in self._machine.bba_x_pvs:
            if bpm_name in offsets_dict.keys():
                calc_offsets = offsets_dict[bpm_name]
                change_in_x.append(calc_offsets.diff_value)
                change_in_dx.append(calc_offsets.diff_value)
            else:
                change_in_x.append(0)
                change_in_dx.append(0)

        change_in_y: List[float] = []
        change_in_dy: List[float] = []
        for bpm_name in self._machine.bba_y_pvs:
            if bpm_name in offsets_dict.keys():
                calc_offsets = offsets_dict[bpm_name]
                change_in_x.append(calc_offsets.diff_value)
                change_in_dx.append(calc_offsets.diff_value)
            else:
                change_in_y.append(0)
                change_in_dy.append(0)

        # # Plot
        # fig, (ax1, ax2) = plt.subplots(2, sharex=True, tight_layout=True)
        # fig.suptitle("Change in BBA values")
        # ax1.set_xlim(0, 174)
        # ax1.axhline(y=0, color="k", linestyle="-", alpha=0.5)
        # ax1.plot(change_in_x, color="b")
        # ax1.set_ylabel("Horizontal")
        # ax1.grid(which="both", axis="both")
        # ax2.plot(change_in_y, color="r")
        # ax2.axhline(y=0, color="k", linestyle="-", alpha=0.5)
        # ax2.set_ylabel("Vertical")
        # ax2.grid(which="both", axis="both")
        # fig.supxlabel("BPM Number")
        # fig.supylabel("Change in BBA offset [mm]")
        # plt.show()

    def _apply_bba_offsets(
        self,
        offsets_dict: Dict[str, CalculatedOffset],
    ) -> None:
        """This function applies the BBA offset values.

        Args:
            offsets_dict: This holds all of the CalculatedOffset objects.
        """
        pv_names: List[str] = []
        pv_values: List[float] = []
        for key, value in offsets_dict.items():
            pv_names.append(key)
            pv_values.append(value.new_value)
        caput(pv_names, pv_values, wait=True)
        log.info(f"{len(pv_names)} BBA Offsets Applied.")
        Sleep(0.2)
