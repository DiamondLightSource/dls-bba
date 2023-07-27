import json
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
    ActiveFeedbacksError,
    ChannelAccessError,
    FastOrbitFeedbackError,
    InvalidElementError,
    InvalidRingmodeError,
)

# matplotlib.use("Qt5Agg")


# Cannot exist inside config files.
BPM_RETRIES = os.getenv("BBA_BPM_RETRIES", 5)
FOFB_RETRIES = 10

ORIGIN_SUFFIXES = {
    "BBA": ":CF:BBA_{axis}_S",
    "BCD": ":CF:BCD_{axis}_S",
    "GOLDEN": ":CF:GOLDEN_{axis}_S",
}
UNITS = {
    "ENG": pytac.ENG,
    "PHYS": pytac.PHYS
}
DATASOURCE = {
    "LIVE": pytac.LIVE
}
QUAD_SLEW_RATE = 0.5  # Amps/Second


def _retry_command(num_tries, excp_type):
    def retry_outer(fn):
        @wraps(fn)
        def retry_inner(*args, **kwargs):
            for attempt in range(1, num_tries + 1):
                try:
                    return fn(*args, **kwargs)
                except (ca_nothing, ControlSystemException) as e:
                    msg = f"Failure no: {attempt} to run CA command:\n{e}"
                    log.error(msg)
                    if attempt == num_tries:
                        msg = f"Failed to run CA command {num_tries} times:\n{e}"
                        log.critical(msg)
                        raise excp_type(msg)
                    cothread.Sleep(1)

        return retry_inner

    return retry_outer


class Machine:
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
        self.config = Configuration.from_configuration_files(extra_config_files)
        if overrides is not None:
            self.config.update_config(overrides)

    def update_config(
        self, extra_config_files: Optional[list[Any]] = None, dct: Optional[dict] = None
    ):
        flag_files = False
        flag_dict = False

        if extra_config_files is not None:
            flag_files = self.config.apply_config_files(extra_config_files)

        if dct is not None:
            flag_dict = self.config.update_config(dct)

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
        ringmode = self.config["RINGMODE"]
        units = self.config["UNITS"]
        datasource = self.config["DATASOURCE"]
        ccs_timeout = self.config["COTHREAD_CONTROL_SYSTEM_TIMEOUT"]
        ccs_wait = self.config["COTHREAD_CONTROL_SYSTEM_WAIT_FLAG"]

        _cs = CothreadControlSystem(timeout=ccs_timeout, wait=ccs_wait)
        try:
            self._lattice = load_csv.load(ringmode, _cs)
        except FileNotFoundError as e:
            msg = f"Ringmode: {ringmode} does not exist in pytac."
            log.critical(msg)
            raise InvalidRingmodeError(msg, e)

        self._lattice.set_default_units(UNITS[units])
        log.info(f"pytac units: {self._lattice.get_default_units()}")

        self._lattice.set_default_data_source(DATASOURCE[datasource])
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
        self.fofb_disabled_indices = {
            "x": np.nonzero(self.fofb_disabled["x"])[0].tolist(),
            "y": np.nonzero(self.fofb_disabled["y"])[0].tolist(),
        }
        self.disabled_bpm_indices = np.flatnonzero(
            np.logical_not(self.get_enabled_bpms())
        ).tolist()

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
        PSPdict = self.config._config["PSPS"]

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
        _Q2B_special_cases = self.config["QUAD2BPM_SPECIAL_CASES"]
        _B2Q_special_cases = self.config["BPM2QUAD_SPECIAL_CASES"]

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
            raise InvalidElementError(msg)

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
            raise InvalidElementError(msg)

    @_retry_command(BPM_RETRIES, ChannelAccessError)  # BPM issues (OFL-256)
    def get_enabled_bpms(self):
        """"""
        return self._lattice.get_element_values("BPM", "enabled")

    @_retry_command(BPM_RETRIES, ChannelAccessError)  # BPM issues (OFL-256)
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
            msg = f"Method not created for element name: {name}"
            log.critical(msg)
            raise NotImplementedError(msg)
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
        orm_filepath = self.config["ORBIT_RESPONSE_MATRIX_PATH"]

        if not os.path.exists(orm_filepath):
            msg = f"Response Matrix does not exist at: {orm_filepath}"
            log.critical(msg)
            raise FileNotFoundError(msg)

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
        radian_kick = self.config["CORRECTOR_KICK_RADIANS"]

        if str(self.config["UNITS"]) == "pytac.ENG":
            value = component.corrector.get_unitconv(component.kick).convert(
                radian_kick, pytac.PHYS, pytac.ENG
            )
        else:
            value = radian_kick
        return float(value)

    def get_beam_current(self) -> float:
        """"""
        return float(self._lattice.get_value("beam_current"))

    def _ask_user(self, msg):
        response = input(msg).lower().strip()
        log.debug(f"User Response: {response}")
        return response

    def get_diagnostics(self):
        """"""
        diagnostics = self.config["DIAGNOSTICS"]

        for key, pv in diagnostics.items():
            value = caget(pv)
            log.debug(key, value)

        log.debug("BEAM_CURRENT", self.get_beam_current())

    def apply_feedbacks(self):
        """"""
        use_fofb = self.config["FOFB_FEEDBACKS"]
        log.info("Applying feedbacks")

        if use_fofb:
            self.max_orbit_too_big_for_fofb()
            self.run_fofb()

        else:
            self.run_sofb()

    def confirm_fofb_activation(self) -> None:
        fofb_on_off = self.config["FEEDBACK_PVS"]["Fast_Orbit_Feedback"]
        counter = 0
        while True:
            if counter == FOFB_RETRIES:
                msg = "BBA cancelled due to FOFB activation failure."
                log.critical(msg)
                raise FastOrbitFeedbackError(msg)

            if caget(fofb_on_off) == 1:
                break
            Sleep(0.5)
            counter += 1

    def max_orbit_too_big_for_fofb(self):
        fofb_max_orbit = self.config["FOFB_MAX_ORBIT_MICRONS"]
        max_value = self.get_largest_orbit()
        while max_value >= fofb_max_orbit:
            msg = "Orbit is too large for FOFB. Running SOFB."
            log.error(msg)
            self.run_sofb()
            max_value = self.get_largest_orbit()

    def run_sofb(self):
        sofb_trigger = self.config["FEEDBACK_PVS"]["Slow_Orbit_Feedback"]
        tune_trigger = self.config["FEEDBACK_PVS"]["Tune_Feedback"]
        sofb_runtime = self.config["SOFB_RUNTIME"]
        waittime = self.config["FEEDBACK_WAITTIME"]
        caput(sofb_trigger, 1, wait=True)
        caput(tune_trigger, 1, wait=True)
        Sleep(sofb_runtime)
        caput(tune_trigger, 0, wait=True)
        caput(sofb_trigger, 0, wait=True)
        Sleep(waittime)

    def run_fofb(self):
        tune_trigger = self.config["FEEDBACK_PVS"]["Tune_Feedback"]
        fofb_trigger = self.config["FOFB_NOGUI_PATH"]
        waittime = self.config["FEEDBACK_WAITTIME"]
        runtime = self.config["FEEDBACK_RUNTIME"]
        run(f"{fofb_trigger} start", check=True, shell=True)
        caput(tune_trigger, 1, wait=True)

        self.confirm_fofb_activation()
        Sleep(runtime)

        caput(tune_trigger, 0, wait=True)
        run(f"{fofb_trigger} stop", check=True, shell=True)
        Sleep(waittime)

    def check_feedbacks(self):
        """"""
        max_orbit = self.config["MAX_ORBIT_CORRECTION_MICRONS"]
        feedback_pvs = self.config["FEEDBACK_PVS"]

        for name, pv in feedback_pvs.items():
            if caget(pv) != 0:
                msg = f"{name} unexpectly running."
                log.critical(msg)
                raise ActiveFeedbacksError(msg)

        max_value = self.get_largest_orbit()

        if max_value >= max_orbit:
            log.info(f"Orbit larger than {max_value} um. Running Feedbacks")
            self.apply_feedbacks()

    def get_largest_orbit(self) -> float:
        """"""
        bpm_values = self.measure_bpms("x") + self.measure_bpms("y")
        enabled_bpms = self.get_enabled_bpms() + self.get_enabled_bpms()
        fofb_disabled_bpms = self.fofb_disabled["x"] + self.fofb_disabled["y"]
        fofb_enabled_bpms = np.logical_not(fofb_disabled_bpms).astype(int)
        acceptable_values = [
            v * e * f for v, e, f in zip(bpm_values, enabled_bpms, fofb_enabled_bpms)
        ]
        max_value = abs(max(acceptable_values, key=abs))
        # Multiplied by 1000 to convert from mm to microns.
        return max_value * 1000

    @staticmethod
    def get_quad_setpoint(quadrupole: EpicsElement) -> float:
        """"""
        value = float(quadrupole.get_value("b1"))
        log.debug(f"Quadrupole get value: {value}")
        return value

    @staticmethod
    def set_quad_setpoint(
        quadrupole: EpicsElement, value: Union[float, int], sleep: bool = False
    ) -> None:
        """"""
        start_current = Machine.get_quad_setpoint(quadrupole)
        quadrupole.set_value("b1", value)
        if sleep:
            # The 2 is a magic number from the old BBA setup.
            Sleep(abs(start_current - value) / QUAD_SLEW_RATE / 2)
        log.debug(f"Quadrupole set value: {value}")

    @staticmethod
    def get_corrector_setpoint(components: Components):
        """"""
        value = float(components.corrector.get_value(components.kick))
        log.debug(f"Corrector {components.corrector_name} get value: {value}")
        return value

    @staticmethod
    def set_corrector_setpoint(
        components: Components, value: Union[float, int]
    ) -> None:
        """"""
        components.corrector.set_value(components.kick, value)
        log.debug(f"Corrector {components.corrector_name} set value: {value}")

    def zero_origins(self, folder_path: str):
        """"""
        # zeroes bcd and golden offsets. Golden must be restored later.
        log.info("Zeroing BCD and Golden Offsets")
        golden_offsets = {}
        pv_names = []

        for bpm_name in self.bpms_names:
            for axis in ["x", "y"]:
                bcd_pv = bpm_name + ORIGIN_SUFFIXES["BCD"].format(axis=axis.upper())
                golden_pv = bpm_name + ORIGIN_SUFFIXES["GOLDEN"].format(
                    axis=axis.upper()
                )
                golden_offsets[golden_pv] = caget(golden_pv)
                pv_names.append(bcd_pv)
                pv_names.append(golden_pv)

        with open(os.path.join(folder_path, "golden_offsets.json"), "w") as outfile:
            json.dump(golden_offsets, outfile)

        caput(pv_names, 0, wait=True)
        Sleep(0.2)
        log.debug("Origins Zeroed")

    def restore_origins(self, folder_path: str):
        """"""
        # restore golden orbits.
        log.info("Restoring Golden Offsets")

        with open(os.path.join(folder_path, "golden_offsets.json")) as f:
            golden_offsets = json.load(f)

        pv_names = []
        pv_values = []
        for key, value in golden_offsets.items():
            pv_names.append(key)
            pv_values.append(value)
        caput(pv_names, pv_values, wait=True)
        Sleep(0.2)
        log.debug("Origins Restored")

    @_retry_command(BPM_RETRIES, ChannelAccessError)  # BPM issues (OFL-256)
    def get_bba_offsets(self) -> Tuple[list[float], list[float]]:
        """"""
        current_bba_x = [float(v) for v in caget(self.bba_x_pvs)]
        current_bba_y = [float(v) for v in caget(self.bba_y_pvs)]

        return (current_bba_x, current_bba_y)
