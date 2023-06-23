import os
import sys
from pathlib import Path
from unittest import mock

import pytest

from dls_bba.components import generate_component_pairings
from dls_bba.configuration import DEFAULT_CONFIGS
from dls_bba.exceptions import (
    CheckBeamCurrentError,
    InvalidElementError,
    InvalidRingmodeError,
    LowCurrentError,
)
from dls_bba.lattice import Lattice

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
def lattice_setup():
    lattice = Lattice()
    return lattice


def test_lattice_construction_is_valid():
    lattice = Lattice()
    assert isinstance(lattice, Lattice)


def test_lattice_construction_is_valid_with_additional_files():
    lattice = Lattice(extra_config_files=default_config_resources)
    assert isinstance(lattice, Lattice)


def test_lattice_can_be_updated_with_additional_files():
    lattice = Lattice()
    lattice._update_config(extra_config_files=default_config_resources)
    assert isinstance(lattice, Lattice)


def test_lattice_construction_is_valid_with_new_additional_args():
    lattice = Lattice(overrides=extra_dict_new_key)
    key = list(extra_dict_new_key.keys())[0]
    value = extra_dict_new_key[key]
    assert lattice._config.config[key] == value


def test_lattice_construction_is_valid_with_additional_args():
    lattice = Lattice(overrides=extra_dict_no_reload)
    key = list(extra_dict_no_reload.keys())[0]
    value = extra_dict_no_reload[key]
    assert lattice._config.config[key] == value


def test_lattice_construction_is_valid_with_additional_args_that_require_reload():
    lattice = Lattice(overrides=extra_dict_with_reload)
    key = list(extra_dict_with_reload.keys())[0]
    value = extra_dict_with_reload[key]
    assert lattice._config.config[key] == value
    assert lattice._lattice.get_default_units()[:4] in value.lower()


def test_lattice_can_be_updated_with_additional_args():
    lattice = Lattice()
    lattice._update_config(dct=extra_dict_no_reload)
    key = list(extra_dict_no_reload.keys())[0]
    value = extra_dict_no_reload[key]
    assert lattice._config.config[key] == value


def test_lattice_can_be_updated_with_additional_args_that_require_reload():
    lattice = Lattice()
    lattice._update_config(dct=extra_dict_with_reload)
    key = list(extra_dict_with_reload.keys())[0]
    value = extra_dict_with_reload[key]
    assert lattice._config.config[key] == value
    assert lattice._lattice.get_default_units()[:4] in value.lower()


def test_pytac_lattice_loaded_config_items_correctly(lattice_setup):
    lattice = lattice_setup
    config = lattice._config.config
    pytac_lattice = lattice._lattice
    assert pytac_lattice.name == config["RINGMODE"]
    assert pytac_lattice.get_default_data_source() == config["DATASOURCE"]
    assert pytac_lattice.get_default_units()[:3] in config["UNITS"].lower()


def test_pytac_lattice_loading_fails_with_invalid_ringmode():
    with pytest.raises(InvalidRingmodeError):
        Lattice(overrides=extra_dict_invalid_ringmode)


def test_element_and_name_lists_equal_length(lattice_setup):
    lattice = lattice_setup
    assert len(lattice.bpms) == len(lattice.bpms_names)
    assert len(lattice.quads) == len(lattice.quads_names)
    assert len(lattice.hstrs) == len(lattice.hstrs_names)
    assert len(lattice.vstrs) == len(lattice.vstrs_names)


def test_bpm2quad_is_valid(lattice_setup):
    lattice = lattice_setup
    exceptions = lattice._config.config["BPM2QUAD_EXCEPTIONS"]
    for bpm_name_1 in lattice.bpms_names:
        quad_name = lattice.bpm2quad(bpm_name_1)
        if len(quad_name) == 2:
            bpm_name_2a = lattice.quad2bpm(quad_name[0])
            bpm_name_2b = lattice.quad2bpm(quad_name[1])
            bpm_name_2 = [bpm_name_2a, bpm_name_2b]
        else:
            bpm_name_2 = [lattice.quad2bpm(quad_name[0])]
        if bpm_name_1 not in bpm_name_2:
            if bpm_name_1 in exceptions:
                if bpm_name_2 is exceptions[bpm_name_1]:
                    continue
                else:
                    assert False
            else:
                assert False


def test_bpm2quad_fails_with_invalid_bpm(lattice_setup):
    lattice = lattice_setup
    with pytest.raises(InvalidElementError):
        lattice.bpm2quad("INVALID_BPM")


def test_quad2bpm_is_valid(lattice_setup):
    lattice = lattice_setup
    exceptions = lattice._config.config["QUAD2BPM_EXCEPTIONS"]

    for quad_name_1 in lattice.quads_names:
        bpm_name = lattice.quad2bpm(quad_name_1)
        quad_name_2 = lattice.bpm2quad(bpm_name)
        if quad_name_1 not in quad_name_2:
            if quad_name_1 in exceptions:
                if quad_name_2[0] == exceptions[quad_name_1]:
                    continue
                else:
                    assert False
            else:
                assert False


def test_quad2bpm_fails_with_invalid_quad(lattice_setup):
    lattice = lattice_setup
    with pytest.raises(InvalidElementError):
        lattice.quad2bpm("INVALID_QUADRUPOLE")


def test_element_to_name_for_all_elements(lattice_setup):
    lattice = lattice_setup
    for bpm_name in lattice.bpms_names:
        element = lattice.get_element_from_name(bpm_name)
        assert "bpm" in element.families
    for quad_name in lattice.quads_names:
        element = lattice.get_element_from_name(quad_name)
        assert "quadrupole" in element.families
    for hstr_name in lattice.hstrs_names:
        element = lattice.get_element_from_name(hstr_name)
        assert "hstr" in element.families
    for vstr_name in lattice.vstrs_names:
        element = lattice.get_element_from_name(vstr_name)
        assert "vstr" in element.families


@mock.patch("dls_bba.lattice.Lattice.get_enabled_bpms", return_value=1)
@mock.patch("dls_bba.lattice.Lattice.measure_bpms", return_value=1)
def test_bpm_interactions_are_valid(mock_get_enabled_bpms, mock_measure_bpms):
    lattice = Lattice()
    assert lattice.get_enabled_bpms() == 1
    assert lattice.measure_bpms("axis") == 1


def test_get_element_from_name_fails_with_invalid_name(lattice_setup):
    lattice = lattice_setup
    with pytest.raises(NotImplementedError):
        lattice.get_element_from_name("INVALID_NAME")


def test_update_config_fails_with_invalid_orm_file_path():
    lattice = Lattice()
    with pytest.raises(FileNotFoundError):
        lattice._update_config(dct=extra_dict_invalid_orm_path)


def test_corrector_kick_valid_with_eng_units(lattice_setup):
    lattice = lattice_setup
    bpm_name = lattice.bpms_names[0]
    components_pair = generate_component_pairings(lattice, bpm_name)
    assert isinstance(lattice.corrector_kick(components_pair[0]), float)
    assert lattice._lattice.get_default_units()[:3] == "eng"


def test_corrector_kick_valid_with_phys_units():
    lattice = Lattice(overrides=extra_dict_with_reload)
    bpm_name = lattice.bpms_names[0]
    components_pair = generate_component_pairings(lattice, bpm_name)
    assert isinstance(lattice.corrector_kick(components_pair[0]), float)
    assert lattice._lattice.get_default_units()[:3] == "phy"


@mock.patch("pytac.lattice.Lattice.get_value", return_value=1.0)
def test_get_beam_current_valid(mock_get_value):
    lattice = Lattice()
    assert lattice.get_beam_current() == 1.0


@mock.patch("pytac.lattice.Lattice.get_value", return_value=1.0)
def test_store_starting_beam_current_is_stored_correctly(mock_get_value):
    lattice = Lattice()
    lattice.store_starting_beam_current()
    assert lattice._starting_beam_current == 1.0


def test_check_beam_current_fails_when_starting_current_not_stored():
    lattice = Lattice()
    with pytest.raises(CheckBeamCurrentError):
        lattice.check_beam_current()


@mock.patch("pytac.lattice.Lattice.get_value", return_value=8.0)
def test_check_beam_current_raises_error_when_beam_dumped(mock_get_value):
    lattice = Lattice(overrides=extra_dict_critical_drop)
    lattice._starting_beam_current = 10.0
    with pytest.raises(LowCurrentError):
        lattice.check_beam_current()


@mock.patch("pytac.lattice.Lattice.get_value", return_value=8.0)
@mock.patch("dls_bba.lattice.Lattice._ask_user", return_value="n")
def test_check_beam_current_raises_error_when_topup_prompt_response_is_no(
    mock_get_value, mock_ask_user
):
    lattice = Lattice(overrides=extra_dict_warning_drop)
    lattice._starting_beam_current = 10.0
    with pytest.raises(LowCurrentError):
        lattice.check_beam_current()


@mock.patch("dls_bba.lattice.Lattice.get_beam_current", side_effect=[8.0, 9.1])
@mock.patch("dls_bba.lattice.Lattice._ask_user", return_value="y")
def test_check_beam_current_returns_false_when_topup_prompt_response_is_yes(
    mock_get_beam_current, mock_ask_user
):
    lattice = Lattice(overrides=extra_dict_warning_drop)
    lattice._starting_beam_current = 10.0
    assert not lattice.check_beam_current()
    assert lattice._starting_beam_current is None


@mock.patch("pytac.lattice.Lattice.get_value", return_value=1.0)
def test_check_beam_current_returns_true_when_valid(mock_get_value):
    lattice = Lattice()
    lattice.store_starting_beam_current()
    assert lattice.check_beam_current()
    assert lattice._starting_beam_current is None
