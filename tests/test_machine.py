import os
import sys
from pathlib import Path
from unittest import mock

import pytest

from dls_bba.beam_current import BeamCurrentCheck
from dls_bba.components import get_component_pairs
from dls_bba.configuration import DEFAULT_CONFIGS
from dls_bba.exceptions import (
    InvalidElementError,
    InvalidRingmodeError,
    LowCurrentError,
)
from dls_bba.machine import Machine

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files


extra_dict_no_reload = {"MAX_ORBIT_CORRECTION_MICRONS": 16}
extra_dict_new_key = {"TEST_FIELD": 100}
extra_dict_with_reload = {"UNITS": "pytac.PHYS"}
extra_dict_invalid_ringmode = {"RINGMODE": "TEST"}
extra_dict_invalid_orm_path = {
    "ORBIT_RESPONSE_MATRIX_PATH": os.path.join(os.getcwd(), "file.mat")
}
extra_dict_critical_drop = {"CRITICAL_CURRENT_DROP": 1, "WARNING_CURRENT_DROP": 1000}
extra_dict_warning_drop = {"CRITICAL_CURRENT_DROP": 1000, "WARNING_CURRENT_DROP": 1}
default_config_resources = [
    Path(str(files("dls_bba").joinpath(resource))) for resource in DEFAULT_CONFIGS
]


@pytest.fixture(scope="module")
def machine_setup():
    machine = Machine()
    return machine


def test_machine_construction_is_valid():
    machine = Machine()
    assert isinstance(machine, Machine)


def test_machine_construction_is_valid_with_additional_files():
    machine = Machine(extra_config_files=default_config_resources)
    assert isinstance(machine, Machine)


def test_machine_can_be_updated_with_additional_files():
    machine = Machine()
    machine._update_config(extra_config_files=default_config_resources)
    assert isinstance(machine, Machine)


def test_machine_construction_is_valid_with_new_additional_args():
    machine = Machine(overrides=extra_dict_new_key)
    key = list(extra_dict_new_key.keys())[0]
    value = extra_dict_new_key[key]
    assert machine.config[key] == value


def test_machine_construction_is_valid_with_additional_args():
    machine = Machine(overrides=extra_dict_no_reload)
    key = list(extra_dict_no_reload.keys())[0]
    value = extra_dict_no_reload[key]
    assert machine.config[key] == value


def test_machine_construction_is_valid_with_additional_args_that_require_reload():
    machine = Machine(overrides=extra_dict_with_reload)
    key = list(extra_dict_with_reload.keys())[0]
    value = extra_dict_with_reload[key]
    assert machine.config[key] == value
    assert machine._lattice.get_default_units()[:4] in value.lower()


def test_machine_can_be_updated_with_additional_args():
    machine = Machine()
    machine._update_config(dct=extra_dict_no_reload)
    key = list(extra_dict_no_reload.keys())[0]
    value = extra_dict_no_reload[key]
    assert machine.config[key] == value


def test_machine_can_be_updated_with_additional_args_that_require_reload():
    machine = Machine()
    machine._update_config(dct=extra_dict_with_reload)
    key = list(extra_dict_with_reload.keys())[0]
    value = extra_dict_with_reload[key]
    assert machine.config[key] == value
    assert machine._lattice.get_default_units()[:4] in value.lower()


def test_pytac_lattice_loaded_config_items_correctly(machine_setup):
    machine = machine_setup
    config = machine.config
    pytac_lattice = machine._lattice
    assert pytac_lattice.name == config["RINGMODE"]
    assert pytac_lattice.get_default_data_source() == config["DATASOURCE"]
    assert pytac_lattice.get_default_units()[:3] in config["UNITS"].lower()


def test_pytac_lattice_loading_fails_with_invalid_ringmode():
    with pytest.raises(InvalidRingmodeError):
        Machine(overrides=extra_dict_invalid_ringmode)


def test_element_and_name_lists_equal_length(machine_setup):
    machine = machine_setup
    assert len(machine.bpms) == len(machine.bpms_names)
    assert len(machine.quads) == len(machine.quads_names)
    assert len(machine.hstrs) == len(machine.hstrs_names)
    assert len(machine.vstrs) == len(machine.vstrs_names)


def test_bpm2quad_is_valid(machine_setup):
    machine = machine_setup
    exceptions = machine.config["BPM2QUAD_EXCEPTIONS"]
    for bpm_name_1 in machine.bpms_names:
        quad_name = machine.bpm2quad(bpm_name_1)
        if len(quad_name) == 2:
            bpm_name_2a = machine.quad2bpm(quad_name[0])
            bpm_name_2b = machine.quad2bpm(quad_name[1])
            bpm_name_2 = [bpm_name_2a, bpm_name_2b]
        else:
            bpm_name_2 = [machine.quad2bpm(quad_name[0])]
        if bpm_name_1 not in bpm_name_2:
            if bpm_name_1 in exceptions:
                if bpm_name_2 is exceptions[bpm_name_1]:
                    continue
                else:
                    assert False
            else:
                assert False


def test_bpm2quad_fails_with_invalid_bpm(machine_setup):
    machine = machine_setup
    with pytest.raises(InvalidElementError):
        machine.bpm2quad("INVALID_BPM")


def test_quad2bpm_is_valid(machine_setup):
    machine = machine_setup
    exceptions = machine.config["QUAD2BPM_EXCEPTIONS"]

    for quad_name_1 in machine.quads_names:
        bpm_name = machine.quad2bpm(quad_name_1)
        quad_name_2 = machine.bpm2quad(bpm_name)
        if quad_name_1 not in quad_name_2:
            if quad_name_1 in exceptions:
                if quad_name_2[0] == exceptions[quad_name_1]:
                    continue
                else:
                    assert False
            else:
                assert False


def test_quad2bpm_fails_with_invalid_quad(machine_setup):
    machine = machine_setup
    with pytest.raises(InvalidElementError):
        machine.quad2bpm("INVALID_QUADRUPOLE")


def test_element_to_name_for_all_elements(machine_setup):
    machine = machine_setup
    for bpm_name in machine.bpms_names:
        element = machine.get_element_from_name(bpm_name)
        assert "bpm" in element.families
    for quad_name in machine.quads_names:
        element = machine.get_element_from_name(quad_name)
        assert "quadrupole" in element.families
    for hstr_name in machine.hstrs_names:
        element = machine.get_element_from_name(hstr_name)
        assert "hstr" in element.families
    for vstr_name in machine.vstrs_names:
        element = machine.get_element_from_name(vstr_name)
        assert "vstr" in element.families


@mock.patch("dls_bba.machine.Machine.get_enabled_bpms", return_value=1)
@mock.patch("dls_bba.machine.Machine.measure_bpms", return_value=1)
def test_bpm_interactions_are_valid(mock_get_enabled_bpms, mock_measure_bpms):
    machine = Machine()
    assert machine.get_enabled_bpms() == 1
    assert machine.measure_bpms("axis") == 1


def test_get_element_from_name_fails_with_invalid_name(machine_setup):
    machine = machine_setup
    with pytest.raises(NotImplementedError):
        machine.get_element_from_name("INVALID_NAME")


def test_update_config_fails_with_invalid_orm_file_path():
    machine = Machine()
    with pytest.raises(FileNotFoundError):
        machine._update_config(dct=extra_dict_invalid_orm_path)


def test_corrector_kick_valid_with_eng_units(machine_setup):
    machine = machine_setup
    bpm_name = machine.bpms_names[0]
    components_pair = get_component_pairs(machine, bpm_name)[0]
    assert isinstance(machine.corrector_kick(components_pair[0]), float)
    assert machine._lattice.get_default_units()[:3] == "eng"


def test_corrector_kick_valid_with_phys_units():
    machine = Machine(overrides=extra_dict_with_reload)
    bpm_name = machine.bpms_names[0]
    components_pair = get_component_pairs(machine, bpm_name)[0]
    assert isinstance(machine.corrector_kick(components_pair[0]), float)
    assert machine._lattice.get_default_units()[:3] == "phy"


@mock.patch("pytac.lattice.Lattice.get_value", return_value=1.0)
def test_get_beam_current_valid(mock_get_value):
    machine = Machine()
    assert machine.get_beam_current() == 1.0


@mock.patch("dls_bba.machine.Machine.get_beam_current", return_value=1.0)
def test_starting_beam_current_is_stored_correctly(mock_get_value):
    machine = Machine()
    beam_check = BeamCurrentCheck(machine)
    assert beam_check._initial_current == 1.0


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[9.1, 8.0])
def test_check_beam_current_raises_error_when_beam_dumped(mock_get_value):
    machine = Machine(overrides=extra_dict_critical_drop)
    beam_check = BeamCurrentCheck(machine)
    with pytest.raises(LowCurrentError):
        beam_check.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[9.1, 8.0])
@mock.patch("dls_bba.machine.Machine._ask_user", return_value="n")
def test_check_beam_current_raises_error_when_topup_prompt_response_is_no(
    mock_get_value, mock_ask_user
):
    machine = Machine(overrides=extra_dict_warning_drop)
    beam_check = BeamCurrentCheck(machine)
    with pytest.raises(LowCurrentError):
        beam_check.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", side_effect=[9.1, 8.0, 9.2])
@mock.patch("dls_bba.machine.Machine._ask_user", return_value="y")
@mock.patch("dls_bba.machine.Machine.check_feedbacks", return_value=None)
def test_check_beam_current_returns_false_when_topup_prompt_response_is_yes(
    mock_get_beam_current, mock_ask_user, mock_check_feedbacks
):
    machine = Machine(overrides=extra_dict_warning_drop)
    beam_check = BeamCurrentCheck(machine)
    assert not beam_check.check_beam_drop()


@mock.patch("dls_bba.machine.Machine.get_beam_current", return_value=1.0)
def test_check_beam_current_returns_true_when_valid(mock_get_value):
    machine = Machine()
    beam_check = BeamCurrentCheck(machine)
    assert beam_check.check_beam_drop()
