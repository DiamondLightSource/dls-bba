import logging as log
import os
from collections import defaultdict
from functools import wraps
from subprocess import run
from typing import Any, Optional, Tuple, Union

import cothread

# import matplotlib
# import matplotlib.pyplot as plt
import numpy as np
import pytac
from cothread import Sleep
from cothread.catools import ca_nothing, caget, caput
from pytac import load_csv
from pytac.cothread_cs import ControlSystemException, CothreadControlSystem
from pytac.element import EpicsElement
from scipy.io import loadmat

from dls_bba.components import Components
from dls_bba.configuration import Configuration
from dls_bba.exceptions import (
    BeamPositionMonitorCAException,
    CheckBeamCurrentException,
    FeedbacksActiveException,
    InvalidNameError,
    InvalidRingmodeException,
    LowCurrentError,
)
from dls_bba.excite import QUAD_SLEW_RATE

# matplotlib.use("Qt5Agg")


# Cannot exist inside config files.
BPM_RETRIES = os.getenv("BBA_BPM_RETRIES", 5)

ORIGIN_SUFFIXES = {
    "BBA": ":CF:BBA_{axis}_S",
    "BCD": ":CF:BCD_{axis}_S",
    "GOLDEN": ":CF:GOLDEN_{axis}_S",
}


def _retry_command(num_tries, excp_type):
    def retry_outer(fn):
        @wraps(fn)
        def retry_inner(*args, **kwargs):
            for attempt in range(1, num_tries + 1):
                try:
                    return fn(*args, **kwargs)
                except (ca_nothing, ControlSystemException) as e:
                    message = f"Failure no: {attempt} to run CA command:\n{e}"
                    log.error(message)
                    if attempt == num_tries:
                        message = f"Failed to run CA command {num_tries} times:\n{e}"
                        log.critical(message)
                        raise excp_type(message)
                    cothread.Sleep(1)

        return retry_inner

    return retry_outer


class Lattice:
    """"""

    def __init__(
        self,
        extra_config_files: Optional[list[Any]] = None,
        overrides: Optional[dict[str, Any]] = None,
    ):
        """"""
        self._load_config(extra_config_files, overrides)
        self._load_lattice_and_ringmode_elements()

    def _load_config(
        self,
        extra_config_files: Optional[list[Any]] = None,
        overrides: Optional[dict[str, Any]] = None,
    ):
        """"""
        self._config = Configuration.from_configuration_files(extra_config_files)
        if overrides is not None:
            self._config.update_config(overrides)

    def _update_config(
        self, extra_config_files: Optional[list[Any]] = None, dct: Optional[dict] = None
    ):
        flag_files = False
        flag_dict = False

        if extra_config_files is not None:
            flag_files = self._config.apply_config_files(extra_config_files)

        if dct is not None:
            flag_dict = self._config.update_config(dct)

        if flag_files or flag_dict:
            log.debug("Major Config Change: Reloading Lattice")
            self._load_lattice_and_ringmode_elements()

    def _load_lattice_and_ringmode_elements(self):
        self._setup_pytac_lattice()
        self._load_element_and_name_lists()
        self._load_cell_dictionary_and_psps()
        self._load_b2q_q2b()
        self.slow_correctors = self._get_slow_correctors()
        self._get_effective_corrector()
        log.debug("Lattice Loaded")

    def _setup_pytac_lattice(self):
        """"""
        ringmode = self._config.config["RINGMODE"]
        units = self._config.config["UNITS"]
        datasource = self._config.config["DATASOURCE"]
        ccs_timeout = self._config.config["COTHREAD_CONTROL_SYSTEM_TIMEOUT"]
        ccs_wait = self._config.config["COTHREAD_CONTROL_SYSTEM_WAIT_FLAG"]

        _cs = CothreadControlSystem(timeout=ccs_timeout, wait=ccs_wait)
        try:
            self._lattice = load_csv.load(ringmode, _cs)
        except FileNotFoundError as e:
            message = f"Ringmode: {ringmode} does not exist in pytac."
            log.critical(message)
            raise InvalidRingmodeException(message, e)

        self._lattice.set_default_units(eval(units))
        log.info(f"pytac units: {self._lattice.get_default_units()}")

        self._lattice.set_default_data_source(datasource)
        log.info(f"pytac datasource: {self._lattice.get_default_data_source()}")

    def _load_element_and_name_lists(self):
        """"""

        self.bpms = self._lattice.get_elements("BPM")
        self.bpms_names = [bpm.get_device("x").name for bpm in self.bpms]

        self.hstrs = self._lattice.get_elements("HSTR")
        self.hstrs_names = [hstr.get_device("x_kick").name for hstr in self.hstrs]

        self.vstrs = self._lattice.get_elements("VSTR")
        self.vstrs_names = [vstr.get_device("y_kick").name for vstr in self.vstrs]

        self.quads = self._lattice.get_elements("quadrupole")
        self.quads_names = [quad.get_device("b1").name for quad in self.quads]

        self.fofb_disabled = {}
        self.fofb_disabled["x"] = [
            int(v)
            for v in self._lattice.get_element_values(
                "BPM", "x_fofb_disabled", pytac.RB
            )
        ]
        self.fofb_disabled["y"] = [
            int(v)
            for v in self._lattice.get_element_values(
                "BPM", "y_fofb_disabled", pytac.RB
            )
        ]
        # Incompatability between pytaclattice and faa number of bpms.
        self.faa_bpm_list = [0] + [i for i, _ in enumerate(self.bpms, start=1)]

        # The PVs do not exist natively in pytac or as part of the element.
        self.bba_x_pvs = [
            name + ORIGIN_SUFFIXES["BBA"].format(axis="X") for name in self.bpms_names
        ]
        self.bba_y_pvs = [
            name + ORIGIN_SUFFIXES["BBA"].format(axis="Y") for name in self.bpms_names
        ]

    def _load_cell_dictionary_and_psps(self):
        """"""
        PSPdict = self._config.config["PSPS"]

        # Cell Dictionary defined by PV names.
        cell_dictionary = defaultdict(list)
        for _, bpm_name in zip(self.bpms, self.bpms_names):
            key = str(bpm_name[2:4])
            cell_dictionary[key].append(bpm_name)
        self.cell_dictionary = cell_dictionary
        # Primaries and Source Points.
        psps = []
        for cell, indices in PSPdict.items():
            for index in indices:
                psps.append(self.cell_dictionary[cell][int(index)])
        self.psps = psps

    def _load_b2q_q2b(self):
        """"""
        _Q2B_special_cases = self._config.config["QUAD2BPM_SPECIAL_CASES"]
        _B2Q_special_cases = self._config.config["BPM2QUAD_SPECIAL_CASES"]

        self._bpms_s = self._lattice.get_family_s("BPM")
        self._quads_s = self._lattice.get_family_s("quadrupole")
        self._quads_l = [quad.length for quad in self.quads]
        self._quads_mid = [
            quad_s + quad_l / 2 for quad_s, quad_l in zip(self._quads_s, self._quads_l)
        ]

        self._get_quad2bpm(_Q2B_special_cases)
        self._get_bpm2quad(_B2Q_special_cases)

    def _get_quad2bpm(self, Q2B_special_cases):
        """"""
        # should only have a 1 to 1 pairing, and not every bpm is used. Every Quad must be used.
        q2b_names = {}

        for quad, quad_name, quad_mid in zip(
            self.quads, self.quads_names, self._quads_mid
        ):
            if quad_name not in Q2B_special_cases:
                closest_bpm_index, _ = min(
                    enumerate(self._bpms_s), key=lambda x: abs(x[1] - quad_mid)
                )
                q2b_names[quad_name] = self.bpms_names[closest_bpm_index]
            else:
                chosen_bpm_name = Q2B_special_cases[quad_name]
                q2b_names[quad_name] = chosen_bpm_name

        self._quad2bpm_names = q2b_names

    def quad2bpm(self, quad: str) -> str:
        """"""
        try:
            return self._quad2bpm_names[quad]
        except KeyError:
            msg = f"Invalid quadrupole name provided: {quad}"
            log.critical(msg)
            raise InvalidNameError(msg)

    def _get_bpm2quad(self, _B2Q_special_cases):
        """"""
        # every bpm must be used, not every quad will be. 1 to many.
        b2q_names = defaultdict(list)

        for bpm_name in self.bpms_names:
            if bpm_name not in _B2Q_special_cases:
                chosen_quads_names = [
                    k for k, v in self._quad2bpm_names.items() if bpm_name is v
                ]
                b2q_names[bpm_name] = chosen_quads_names
            else:
                chosen_quads_names = _B2Q_special_cases[bpm_name]
                b2q_names[bpm_name] = chosen_quads_names

        self._bpm2quad_names = b2q_names

    def bpm2quad(self, bpm: str) -> list[str]:
        """"""
        # bpm can be either PV or element, default element.
        # Will return 1 to many.
        if bpm in self._bpm2quad_names:
            return self._bpm2quad_names[bpm]
        else:
            msg = f"Invalid BPM name provided: {bpm}"
            log.critical(msg)
            raise InvalidNameError(msg)

    @_retry_command(BPM_RETRIES, BeamPositionMonitorCAException)  # BPM issues (OFL-256)
    def get_enabled_bpms(self):
        """"""
        return self._lattice.get_element_values("BPM", "enabled")

    @_retry_command(BPM_RETRIES, BeamPositionMonitorCAException)  # BPM issues (OFL-256)
    def measure_bpms(self, axis: str):
        """"""
        return self._lattice.get_element_values("BPM", f"{axis}", pytac.RB)

    def get_element_from_name(self, name):
        """"""
        if "-DI-EBPM-" in name:
            element = self.bpms[self.bpms_names.index(name)]
        elif "-PC-Q" in name:
            element = self.quads[self.quads_names.index(name)]
        elif "-PC-H" in name:
            element = self.hstrs[self.hstrs_names.index(name)]
        elif "-PC-V" in name:
            element = self.vstrs[self.vstrs_names.index(name)]
        else:
            message = f"Method not created for element name: {name}"
            log.critical(message)
            raise NotImplementedError(message)
        return element

    def _get_slow_correctors(self) -> list[str]:
        """"""
        # SRxxS or xSCOR correctors are slow
        slow_correctors = []
        for corrector_name in self.hstrs_names + self.vstrs_names:
            split_name = corrector_name.split("-")
            if split_name[0][-1] == "S" or len(split_name[2]) == 5:
                slow_correctors.append(corrector_name)
        return slow_correctors

    def _get_best_corrector_for_bpm(self, index: int, bpm_name: str):
        """"""
        h_row = self._horizontal_orm[index, :]
        v_row = self._vertical_orm[index, :]

        h_corr_index = np.argmax(abs(h_row))
        v_corr_index = np.argmax(abs(v_row))

        hstr_name = self.hstrs_names[h_corr_index]
        vstr_name = self.vstrs_names[v_corr_index]

        self._effective_corrector[bpm_name] = [hstr_name, vstr_name]

    def _get_effective_corrector(self):
        """"""
        orm_filepath = self._config.config["ORBIT_RESPONSE_MATRIX_PATH"]

        if not os.path.exists(orm_filepath):
            message = f"Response Matrix does not exist at: {orm_filepath}"
            log.critical(message)
            raise FileNotFoundError(message)

        self._effective_corrector = defaultdict(list)
        data = loadmat(orm_filepath, appendmat=False, struct_as_record=False)
        self._horizontal_orm, self._vertical_orm = (
            data["Rmat"][0][0].Data,
            data["Rmat"][1][1].Data,
        )

        for index, bpm_name in enumerate(self.bpms_names):
            self._get_best_corrector_for_bpm(index, bpm_name)

    def effective_correctors(self, bpm: str) -> list[str]:
        return self._effective_corrector[bpm]

    def corrector_kick(self, component: Components) -> float:
        """PV ONLY"""
        radian_kick = self._config.config["CORRECTOR_KICK_RADIANS"]

        if str(self._config.config["UNITS"]) == "ENG":
            value = component.corrector.get_unitconv(component.kick).convert(
                radian_kick, pytac.PHYS, pytac.ENG
            )
        else:
            value = radian_kick
        return float(value)

    def get_beam_current(self) -> float:
        """"""
        return float(self._lattice.get_value("beam_current"))

    def store_starting_beam_current(self):
        self._starting_beam_current = self.get_beam_current()
        log.debug(f"Stored Starting Beam Current: {self._starting_beam_current}")

    def check_beam_current(self):
        warning_current_drop = self._config.config["WARNING_CURRENT_DROP"]
        critical_current_drop = self._config.config["CRITICAL_CURRENT_DROP"]

        if self._starting_beam_current is None:
            message = "Starting beam current has not been stored."
            log.critical(message)
            raise CheckBeamCurrentException(message)

        change_in_current = self._starting_beam_current - self.get_beam_current()
        log.debug(f"Change in beam current: {change_in_current}")

        if change_in_current > critical_current_drop:
            message = f"Beam current drop by >{critical_current_drop} mA"
            log.critical(message)
            raise LowCurrentError(message)

        if change_in_current > warning_current_drop:
            message = (
                f"Beam current drop by >{warning_current_drop} mA. Top-up or cancel.",
            )
            log.error(message)
            while True:
                resp_message = "Input y to continue after top-up, or n to cancel: "
                response = input(resp_message).lower().strip()
                if response == "n":
                    message = "User cancelled BBA: Due to beam current drop."
                    log.critical(message)
                    raise LowCurrentError(message)
                elif response == "y":
                    change_in_current = (
                        self._starting_beam_current - self.get_beam_current()
                    )
                    if change_in_current < warning_current_drop:
                        break
                    minimum_current = self._starting_beam_current - warning_current_drop
                    message = f"Current must be greater than {minimum_current} mA"
                    log.warning(message)
            self._starting_beam_current = None
            return False
        self._starting_beam_current = None
        return True

    def get_diagnostics(self):
        """"""
        diagnostics = self._config.config["DIAGNOSTICS"]

        for key, pv in diagnostics.items():
            value = caget(pv)
            log.debug(key, value)

        log.debug("BEAM_CURRENT", self.get_beam_current())

    def apply_feedbacks(self):
        """"""
        feedbacks_bool = self._config.config["FEEDBACKS"]
        log.debug("Applying feedbacks")

        if feedbacks_bool:
            fofb_trigger = self._config.config["FOFB_NOGUI_PATH"]
            tune_trigger = self._config.config["FEEDBACK_PVS"]["Tune_Feedback"]
            waittime = self._config.config["FEEDBACK_WAITTIME"]
            runtime = self._config.config["FEEDBACK_RUNTIME"]

            log.warn("Correcting orbit with FOFB and Tune Feedbacks")

            run(f"{fofb_trigger} start", check=True, shell=True)
            caput(tune_trigger, 1, wait=True)
            Sleep(runtime)
            caput(tune_trigger, 0, wait=True)
            run(f"{fofb_trigger} stop", check=True, shell=True)
            Sleep(waittime)

    def check_feedbacks(self):
        """"""
        max_orbit = self._config.config["MAX_ORBIT_CORRECTION_MICRONS"]
        feedback_pvs = self._config.config["FEEDBACK_PVS"]

        for name, pv in feedback_pvs.items():
            if caget(pv) != 0:
                message = f"{name} unexpectly running."
                log.critical(message)
                raise FeedbacksActiveException(message)

        bpm_values = self.measure_bpms("x") + self.measure_bpms("y")
        enabled_bpms = self.get_enabled_bpms() + self.get_enabled_bpms()
        fofb_disabled_bpms = self.fofb_disabled["x"] + self.fofb_disabled["y"]
        fofb_enabled_bpms = np.logical_not(fofb_disabled_bpms).astype(int)
        acceptable_values = [
            v * e * f for v, e, f in zip(bpm_values, enabled_bpms, fofb_enabled_bpms)
        ]

        max_value = abs(max(acceptable_values, key=abs))

        if max_value * 1000 >= max_orbit:
            self.apply_feedbacks()

    def get_quad_setpoint(self, quadrupole: EpicsElement) -> float:
        """"""
        value = float(quadrupole.get_value("b1"))
        log.debug(f"Quadrupole get value: {value}")
        return value

    def set_quad_setpoint(
        self, quadrupole: EpicsElement, value: Union[float, int], sleep: bool = False
    ) -> None:
        """"""
        start_current = self.get_quad_setpoint(quadrupole)
        quadrupole.set_value("b1", value)
        if sleep:
            # The 2 is a magic number from the old BBA setup.
            Sleep(abs(start_current - value) / QUAD_SLEW_RATE / 2)
        log.debug(f"Quadrupole set value: {value}")

    def get_corrector_setpoint(self, components: Components):
        """"""
        value = float(components.corrector.get_value(components.kick))
        log.debug(f"Corrector {components.corrector_name} get value: {value}")
        return value

    def get_slow_bba_corrector_steps(self, components: Components):
        """"""
        setpoint = self.get_corrector_setpoint(components)
        step = self.corrector_kick(components)
        corrector_steps = [
            setpoint + step,
            setpoint + (step / 2),
            setpoint,
            setpoint - (step / 2),
            setpoint - step,
        ]
        return corrector_steps

    def set_corrector_setpoint(
        self, components: Components, value: Union[float, int]
    ) -> None:
        """"""
        components.corrector.set_value(components.kick, value)
        log.debug(f"Corrector {components.corrector_name} set value: {value}")

    def zero_origins(self):
        """"""
        # zeroes bcd and golden offsets. Golden must be restored later.
        log.debug("Zeroing BCD and Golden Offsets")
        self._golden_offsets = {}

        for bpm, bpm_name in zip(self.bpms, self.bpms_names):
            for axis in ["x", "y"]:
                bcd_pv = bpm_name + ORIGIN_SUFFIXES["BCD"].format(axis=axis.upper())
                golden_pv = bpm_name + ORIGIN_SUFFIXES["GOLDEN"].format(
                    axis=axis.upper()
                )

                self._golden_offsets[golden_pv] = caget(golden_pv)

                caput(bcd_pv, 0, wait=True)
                caput(golden_pv, 0, wait=True)
        Sleep(0.2)
        log.debug(self._golden_offsets)
        log.debug("Origins Zeroed")

    def restore_origins(self):
        """"""
        # restore golden orbits.
        log.debug("Restoring Golden Offsets")
        for key, value in self._golden_offsets.items():
            caput(key, value, wait=True)
        Sleep(0.2)
        log.debug("Origins Restored")

    def calculate_quad_setpoints(self, quadrupole: EpicsElement):
        """"""
        quad_step_percent = self._config.config["QUADRUPOLE_STEP_PERCENT"]

        quad_setpoint = self.get_quad_setpoint(quadrupole)
        quad_step = quad_setpoint * quad_step_percent
        quad_start_high = quad_setpoint + (2 * quad_step)
        quad_high = quad_setpoint + quad_step
        quad_low = quad_setpoint - quad_step
        return quad_start_high, quad_high, quad_low, quad_setpoint

    @_retry_command(BPM_RETRIES, BeamPositionMonitorCAException)  # BPM issues (OFL-256)
    def get_bba_offsets(self) -> Tuple[list[float], list[float]]:
        """"""
        current_bba_x = [float(v) for v in caget(self.bba_x_pvs)]
        current_bba_y = [float(v) for v in caget(self.bba_y_pvs)]

        return (current_bba_x, current_bba_y)

    def draw_bba_plot_and_apply(self, results_list, save_location):
        """"""
        current_bba_x, current_bba_y = self.get_bba_offsets()

        all_results = {}
        for results in results_list:
            all_results.update(results.offsets)

        self.save_calculated_offsets(all_results, save_location)

        new_bba_x = []
        for index, bpm_pv in enumerate(self.bba_x_pvs):
            old_value = current_bba_x[index]
            if bpm_pv in all_results:
                new_value = all_results[bpm_pv][0]
                new_bba_x.append(old_value + new_value)
            else:
                new_bba_x.append(old_value)

        new_bba_y = []
        for index, bpm_pv in enumerate(self.bba_y_pvs):
            old_value = current_bba_y[index]
            if bpm_pv in all_results:
                new_value = all_results[bpm_pv][0]
                new_bba_y.append(old_value + new_value)
            else:
                new_bba_y.append(old_value)

        # change_in_x = np.subtract(current_bba_x, new_bba_x)
        # change_in_y = np.subtract(current_bba_y, new_bba_y)

        # # Plot
        # fig, (ax1, ax2) = plt.subplots(2, sharex=True)
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
        # plt.show()

        log.info("The change in BBA offsets calculated")
        for key, value in all_results.items():
            log.info(f"{key}: {value}")

        while True:
            message = "Apply these BBA offsets? (y / n) : "
            response = input(message).lower().strip()
            if response == "n":
                break
            elif response == "y":
                self.apply_bba_offsets(all_results)
                pass

    def save_calculated_offsets(
        self, results_dictionary: dict[str, list[float]], save_location: str
    ):
        filename = os.path.join(save_location, "results.txt")
        with open(filename, "w") as writer:
            for key, (value, error) in results_dictionary.items():
                old_value = caget(key)
                line = f"{key}, Old: {old_value}, New: {value} +- {error}"
                writer.write(line)
            writer.close()

    def apply_bba_offsets(self, all_results: dict[str, list[float]]):
        """"""
        for key, (value, error) in all_results.items():
            caput(key, value, wait=True)
            message = f"Caput value {value} +- {error} on {key}"
            log.debug(message)
        Sleep(0.2)
