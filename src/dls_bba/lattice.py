import logging as log
import os
from collections import defaultdict
from functools import wraps
from subprocess import run
from typing import Any, Optional, Union

import cothread
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
    BBAComponentException,
    BeamPositionMonitorCAException,
    CheckBeamCurrentException,
    FeedbacksActiveException,
    InvalidRingmodeException,
    LowCurrentError,
)
from dls_bba.excite import QUAD_SLEW_RATE

# TODO: Cannot exist inside config files.
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
        self._config.update_config(overrides)

    def _update_config(
        self, extra_config_files: Optional[list[Any]] = None, dct: Optional[dict] = None
    ):
        if extra_config_files is not None:
            flag_files = self._config.apply_config_files(extra_config_files)

        if dct is not None:
            flag_dict = self._config.update_config(dct)

        if flag_files or flag_dict:
            self._load_lattice_and_ringmode_elements()

    def _load_lattice_and_ringmode_elements(self):

        self._setup_pytac_lattice()
        self._load_element_and_pv_root_lists()
        self._load_cell_dictionary_and_psps()
        self._load_b2q_q2b()
        self._get_slow_correctors()
        self._get_effective_corrector()

    def _setup_pytac_lattice(self):
        """"""
        # TODO: Warning: Changing the ringmode but not updating the settings.json can cause issues.
        ringmode = self._config["RINGMODE"]
        units = self._config["UNITS"]
        datasource = self._config["DATASOURCE"]
        ccs_timeout = self._config["COTHREAD_CONTROL_SYSTEM_TIMEOUT"]
        ccs_wait = self._config["COTHREAD_CONTROL_SYSTEM_WAIT_FLAG"]

        _cs = CothreadControlSystem(timeout=ccs_timeout, wait=ccs_wait)
        try:
            self._lattice = load_csv.load(ringmode, _cs)
        except FileNotFoundError as e:
            message = f"Ringmode: {ringmode} does not exist in pytac."
            log.critical(message, e)
            raise InvalidRingmodeException(message, e)

        self._lattice.set_default_units(eval(units))
        log.info(f"pytac units: {self._lattice.get_default_units()}")

        self._lattice.set_default_data_source(datasource)
        log.info(f"pytac datasource: {self._lattice.get_default_data_source()}")

    def _load_element_and_pv_root_lists(self):
        """"""

        self.bpms = self._lattice.get_elements("BPM")
        self.bpms_names = [bpm.get_device("x").name for bpm in self.bpms]

        self.hstrs = self._lattice.get_elements("HSTR")
        self.hstrs_names = [hstr.get_device("x_kick").name for hstr in self.hstrs]

        self.vstrs = self._lattice.get_elements("VSTR")
        self.vstrs_names = [vstr.get_device("y_kick").name for vstr in self.vstrs]

        self.quads = self._lattice.get_elements("quadrupole")
        self.quads_names = [quad.get_device("b1").name for quad in self.quads]

        self.fofb_enabled = {}
        self.fofb_enabled["x"] = self._lattice.get_element_values(
            "BPM", "x_fofb_disabled", pytac.RB
        )
        self.fofb_enabled["y"] = self._lattice.get_element_values(
            "BPM", "y_fofb_disabled", pytac.RB
        )
        # Incompatability between pytaclattice and faa number of bpms.
        self.faa_bpm_list = [0] + [i for i, _ in enumerate(self.bpms, start=1)]

    def _load_cell_dictionary_and_psps(self):
        """"""
        PSPdict = self._config["PSPS"]

        # Cell Dictionary defined by PV names.
        cell_dictionary = defaultdict(list)
        for _, bpm_name in zip(self.bpms, self.bpms_names):
            key = str(bpm_name[2:4])
            cell_dictionary[key].append(bpm_name)
        self.cell_dictionary = cell_dictionary
        # Primaries and Source Points.
        psps = []
        for cell, indices in PSPdict:
            for index in indices:
                psps.append(self.cell_dictionary[cell][index])
        self.psps = psps

    def _load_b2q_q2b(self):
        """"""
        _Q2B_special_cases = self._config["QUAD2BPM_SPECIAL_CASES"]
        _B2Q_special_cases = self._config["BPM2QUAD_SPECIAL_CASES"]

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
        q2b_elements = {}
        q2b_names = {}

        for quad, quad_name, quad_mid in zip(
            self.quads, self.quads_names, self._quads_mid
        ):
            if quad_name not in Q2B_special_cases:
                closest_bpm_index, _ = min(
                    enumerate(self._bpms_s), key=lambda x: abs(x[1] - quad_mid)
                )
                q2b_elements[quad] = self.bpms[closest_bpm_index]
                q2b_names[quad_name] = self.bpms_names[closest_bpm_index]
            else:
                chosen_bpm_name = Q2B_special_cases[quad_name]
                chosen_bpm = self.bpms[self.bpms_names.index(chosen_bpm_name)]
                q2b_elements[quad] = chosen_bpm
                q2b_names[quad_name] = chosen_bpm_name

        self._quad2bpm_elements = q2b_elements
        self._quad2bpm_names = q2b_names

    def quad2bpm(
        self, quad: Union[pytac.element.EpicsElement, str]
    ) -> Union[pytac.element.EpicsElement, str]:
        """"""
        # quad can be either PV or element
        # Will only return 1 to 1.
        if isinstance(quad, pytac.element.EpicsElement):
            return [self._quad2bpm_elements[quad]]
        elif isinstance(quad, str):
            return [self._quad2bpm_names[quad]]
        else:
            message = f"Invalid quad: {quad} {type(quad)} is not 'pytac.element.EpicsElement' or 'str'"
            log.critical(message)
            raise ValueError(message)

    def _get_bpm2quad(self, _B2Q_special_cases):
        """"""
        # every bpm must be used, not every quad will be. 1 to many.
        b2q_elements = defaultdict(list)
        b2q_names = defaultdict(list)

        for bpm, bpm_name in zip(self.bpms, self.bpms_names):
            if bpm_name not in _B2Q_special_cases:
                chosen_quads = [
                    k for k, v in self._quad2bpm_elements.items() if bpm is v
                ]
                chosen_quads_names = [
                    k for k, v in self._quad2bpm_names.items() if bpm_name is v
                ]
                b2q_elements[bpm] = chosen_quads
                b2q_names[bpm_name] = chosen_quads_names
            else:
                chosen_quads_names = _B2Q_special_cases[bpm_name]
                chosen_quads = [
                    self.quads[self.quads_names.index(chosen_quad_name)]
                    for chosen_quad_name in chosen_quads_names
                ]
                b2q_elements[bpm] = chosen_quads
                b2q_names[bpm_name] = chosen_quads_names

        self._bpm2quad_elements = b2q_elements
        self._bpm2quad_names = b2q_names

    def bpm2quad(
        self, bpm: Union[pytac.element.EpicsElement, str]
    ) -> list[Union[pytac.element.EpicsElement, str]]:
        """"""
        # bpm can be either PV or element, default element.
        # Will return 1 to many.
        if isinstance(bpm, pytac.element.EpicsElement):
            return self._bpm2quad_elements[bpm]
        elif isinstance(bpm, str):
            return self._bpm2quad_names[bpm]
        else:
            message = f"Invalid bpm: {bpm} {type(bpm)} is not 'pytac.element.EpicsElement' or 'str'"
            log.critical(message)
            raise ValueError(message)

    # TODO: Cant use BPM_RETRIES FROM self._config["BPM_RETRIES"]
    @_retry_command(BPM_RETRIES, BeamPositionMonitorCAException)  # BPM issues (OFL-256)
    def get_enabled_bpms(self):
        """"""
        return self._lattice.get_element_values("BPM", "enabled")

    @_retry_command(BPM_RETRIES, BeamPositionMonitorCAException)  # BPM issues (OFL-256)
    def measure_bpms(self, axis: str):
        """"""
        # TODO: """Where axis is 'x', 'y'."""
        # returns in mm.
        return self._lattice.get_element_values("BPM", f"{axis}", pytac.RB)

    def get_element_from_pv(self, name):
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
            message = f"Method not created for pv name: {name}"
            log.critical(message)
            raise NotImplementedError(message)
        return element

    def _get_slow_correctors(self):
        """"""
        # SRxxS or xSCOR correctors are slow
        # better to do array of 0, 1?
        slow_correctors = []
        for corrector_pv in self.hstrs_names + self.vstrs_names:
            split_pv = corrector_pv.split("-")
            if split_pv[0][-1] == "S" or len(split_pv[2]) == 5:
                slow_correctors.append(corrector_pv)
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
        # TODO: Effective corrector for the cell, check with ALBA?
        orm_filepath = self._config["ORBIT_RESPONSE_MATRIX_PATH"]

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

    def effective_correctors(
        self, bpm: Union[pytac.element.EpicsElement, str]
    ) -> list[Union[pytac.element.EpicsElement, str]]:
        if isinstance(bpm, pytac.element.EpicsElement):
            bpm = self.bpms_names[self.bpms.index(bpm)]
        correctors = self._effective_corrector[bpm]
        if isinstance(bpm, pytac.element.EpicsElement):
            correctors = [
                self.get_element_from_pv(corrector) for corrector in correctors
            ]
        return correctors

    def generate_component_pairings(self, element_name: str) -> list[Components]:
        """Can accept either bpm or quad pv prefix."""
        if element_name in self.bpms_names:
            bpm = element_name
            quads = self.bpm2quad(bpm)
        elif element_name in self.quads_names:
            quad = [element_name]
            bpm = self.quad2bpm(quad)
        else:
            message = "Neither a quadrupole nor BPM pv root was given."
            log.critical(message)
            raise BBAComponentException(message)

        hor_corr, ver_corr = self.effective_correctors(bpm)
        horizontal_elements = Components.from_pv_prefixes(
            self._lattice, bpm, quads, hor_corr, "x", "x_kick"
        )
        vertical_elements = Components.from_pv_prefixes(
            self._lattice, bpm, quads, ver_corr, "y", "y_kick"
        )
        return [horizontal_elements, vertical_elements]

    def corrector_kick(self, components: Components) -> float:
        """PV ONLY"""
        radian_kick = self._config["CORRECTOR_KICK_RADIANS"]

        if str(self._config["UNITS"]) == "ENG":
            value = components.corrector.get_unitconv(components.kick).convert(
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

    def check_beam_current(self):
        warning_current_drop = self._config["WARNING_CURRENT_DROP"]
        critical_current_drop = self._config["CRITICAL_CURRENT_DROP"]

        if self._starting_beam_current is None:
            message = "Starting beam current has not been stored."
            log.critical(message)
            raise CheckBeamCurrentException(message)

        change_in_current = self._starting_beam_current - self.get_beam_current()

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
        emit_value = np.round(caget("SR-DI-EMIT-01:EMITTANCE"), 3)
        x_emit_v = np.round(caget("SR-DI-EMIT-01:HEMIT"), 3)
        x_emit_e = np.round(caget("SR-DI-EMIT-01:HERROR"), 3)
        y_emit_v = np.round(caget("SR-DI-EMIT-01:VEMIT"), 3)
        y_emit_e = np.round(caget("SR-DI-EMIT-01:VERROR"), 3)
        x_tune = np.round(caget("SR23C-DI-TMBF-01:X:TUNE:TUNE"), 4)
        y_tune = np.round(caget("SR23C-DI-TMBF-01:Y:TUNE:TUNE"), 4)
        coupling = np.round(caget("SR-DI-EMIT-01:COUPLING"), 3)
        current = np.round(self.get_beam_current(), 3)
        lifetime = np.round(caget("SR-DI-DCCT-01:LIFETIME"), 3)
        diagnostics_dict = {
            "emittance": f"{emit_value} nm rad",
            "x_emittance": f"{x_emit_v} +/- {x_emit_e} um",
            "y_emittance": f"{y_emit_v} +/- {y_emit_e} pm",
            "tune": f"X: {x_tune}, Y: {y_tune}",
            "coupling": f"{coupling} %",
            "current": f"{current} mA",
            "lifetime": f"{lifetime} h",
        }
        for key, value in diagnostics_dict.items():
            log.debug(key, value)

    def apply_feedbacks(self):
        """"""
        fofb_trigger = self.settings["FOFB_NOGUI_PATH"]
        tune_trigger = "SR-CS-TFB-01:ONOFF"
        waittime = self.config["FEEDBACK_WAITTIME"]
        runtime = self.config["FEEDBACK_RUNTIME"]

        log.warn("Correcting orbit with FOFB and Tune Feedbacks")

        run(f"{fofb_trigger} start", check=True, shell=True)
        caput(tune_trigger, 1, wait=True)
        Sleep(runtime)
        caput(tune_trigger, 0, wait=True)
        run(f"{fofb_trigger} stop", check=True, shell=True)
        Sleep(waittime)

    def check_feedbacks(self, max_orbit=None):
        """"""
        max_orbit = self.config["MAX_ORBIT_CORRECTION_MICRONS"]

        # TODO: This into config.
        feedbacks = {
            "Fast Orbit Feedback": "SR01A-CS-FOFB-01:RUN",
            "Slow Orbit Feedback": "SR-CS-SOFB-01:ONOFF",
            "Tune Feedback": "SR-CS-TFB-01:ONOFF",
            "Vertical Emittance Feedback": "SR-CS-VEFB-01:LOOP",
        }

        for name, pv in feedbacks.items():
            if caget(pv) != 0:
                message = f"{name} unexpectly running."
                log.critical(message)
                raise FeedbacksActiveException(message)

        bpm_values = self.measure_bpms("x") + self.measure_bpms("y")
        enabled_bpms = self.get_enabled_bpms() + self.get_enabled_bpms()
        acceptable_values = [v * e for v, e in zip(bpm_values, enabled_bpms)]

        max_value = abs(max(acceptable_values, key=abs))

        if max_value * 1000 >= max_orbit:
            self.apply_feedbacks()

    def get_quad_setpoint(self, quadrupole: EpicsElement) -> float:
        """"""
        return float(quadrupole.get_value("b1"))

    def set_quad_setpoint(
        self, quadrupole: EpicsElement, value: Union[float, int], sleep: bool = False
    ) -> None:
        """"""
        start_current = self.get_quad_setpoint(quadrupole)
        quadrupole.set_value("b1", value)
        if sleep:
            # The 2 is a magic number from the old BBA setup.
            Sleep(abs(start_current - value) / QUAD_SLEW_RATE / 2)

    def get_corrector_setpoint(self, component: Components):
        """"""
        return float(component.corrector.get_value(component.kick))

    def get_slow_bba_corrector_steps(self, component: Components):
        """"""
        setpoint = self.get_corrector_setpoint(component)
        step = self.corrector_kick(component)
        corrector_steps = [
            setpoint + step,
            setpoint + (step / 2),
            setpoint,
            setpoint - (step / 2),
            setpoint - step,
        ]
        return corrector_steps

    def set_corrector_setpoint(
        self, component: Components, value: Union[float, int]
    ) -> None:
        """"""
        component.corrector.set_value(component.kick, value)

    def zero_origins(self):
        """"""
        # zeroes bcd and golden offsets. Golden must be restored later.
        self._golden_offsets = {}

        for bpm, bpm_name in zip(self.bpms, self.bpms_names):
            for axis in ["x", "y"]:
                bcd_pv = bpm_name + ORIGIN_SUFFIXES["BCD"].format(axis)
                golden_pv = bpm_name + ORIGIN_SUFFIXES["GOLDEN"].format(axis)

                self._golden_offsets[golden_pv] = caget(golden_pv)

                caput(bcd_pv, 0, wait=True)
                caput(golden_pv, 0, wait=True)
        Sleep(0.2)
        log.debug(self._golden_offsets)
        log.debug("Origins Zeroed")

    def restore_origins(self):
        """"""
        # restore golden orbits.
        for key, value in self._golden_offsets.items():
            caput(key, value, wait=True)
        Sleep(0.2)
        log.debug("Origins Restored")

    def calculate_quad_setpoints(self, quadrupole: EpicsElement):
        """"""
        quad_step_percent = self._config["QUADRUPOLE_STEP_PERCENT"]

        quad_setpoint = self._lattice.get_quad_setpoint(quadrupole)
        quad_step = quad_setpoint * quad_step_percent
        quad_start_high = quad_setpoint + (2 * quad_step)
        quad_high = quad_setpoint + quad_step
        quad_low = quad_setpoint - quad_step
        return quad_start_high, quad_high, quad_low, quad_setpoint

    def apply_bba(self, results):
        """"""
        # TODO
        # TODO should be where the human readable .txt is created too.
        # lists before/after values.
        # TODO should pop up with a plot asking y or n for each thing to apply.
        pass

    def hysteresis(
        self,
    ):
        # TODO
        # overshoot in one direction.
        # only for ddba cell2?
        pass

    def cancel_oscillations(self):
        # TODO
        # Set all to 0, then prime for all IOCS.
        pass
