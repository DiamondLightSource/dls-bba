import os
from json import dump
from unittest import mock

import pytest
from conftest import _get_effective_corrector, get_element_values

from dls_bba.components import Components
from dls_bba.configuration import LATTICE_SETTINGS
from dls_bba.exceptions import InvalidElementError, InvalidRingmodeError
from dls_bba.machine import Machine

OVERRIDES_WITH_RELOAD = {
    LATTICE_SETTINGS[0]: "I04",  # RINGMODE
    LATTICE_SETTINGS[1]: "PHYS",  # UNITS
    LATTICE_SETTINGS[2]: "LIVE",  # DATASOURCE
}


@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
@mock.patch(
    "dls_bba.machine.Machine._get_effective_corrector",
    side_effect=_get_effective_corrector,
)
def test_machine_init_normal(mock_element_values, mock_effected_corrector):
    machine = Machine()
    assert isinstance(machine, Machine)
    assert machine.config["UNITS"] == "ENG"


@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
@mock.patch(
    "dls_bba.machine.Machine._get_effective_corrector",
    side_effect=_get_effective_corrector,
)
def test_machine_init_additional_files(
    mock_element_values, mock_effected_corrector, tmp_path
):
    paths = []
    for i in range(3):
        filename = f"json_dump_{i}.json"
        filepath = os.path.join(tmp_path, filename)
        with open(filepath, "w") as fp:
            dump(OVERRIDES_WITH_RELOAD, fp)
        paths.append(filepath)
    machine = Machine(extra_config_files=paths)
    assert isinstance(machine, Machine)
    assert machine.config["UNITS"] == "PHYS"


@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
@mock.patch(
    "dls_bba.machine.Machine._get_effective_corrector",
    side_effect=_get_effective_corrector,
)
def test_machine_init_additional_args(mock_element_values, mock_effected_corrector):
    machine = Machine(overrides=OVERRIDES_WITH_RELOAD)
    assert isinstance(machine, Machine)
    assert machine.config["UNITS"] == "PHYS"


@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
@mock.patch(
    "dls_bba.machine.Machine._get_effective_corrector",
    side_effect=_get_effective_corrector,
)
def test_machine_init_additional_files_and_args(
    mock_element_values, mock_effected_corrector, tmp_path
):
    paths = []
    for i in range(3):
        filename = f"json_dump_{i}.json"
        filepath = os.path.join(tmp_path, filename)
        with open(filepath, "w") as fp:
            dump(OVERRIDES_WITH_RELOAD, fp)
        paths.append(filepath)
    machine = Machine(extra_config_files=paths, overrides=OVERRIDES_WITH_RELOAD)
    assert isinstance(machine, Machine)
    assert machine.config["UNITS"] == "PHYS"


@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
@mock.patch(
    "dls_bba.machine.Machine._get_effective_corrector",
    side_effect=_get_effective_corrector,
)
def test_machine_update_config_with_path(
    mock_element_values, mock_effected_corrector, tmp_path
):
    paths = []
    for i in range(3):
        filename = f"json_dump_{i}.json"
        filepath = os.path.join(tmp_path, filename)
        with open(filepath, "w") as fp:
            dump(OVERRIDES_WITH_RELOAD, fp)
        paths.append(filepath)

    machine = Machine()
    assert machine.config["UNITS"] == "ENG"
    machine.update_config(extra_config_files=paths)
    assert machine.config["UNITS"] == "PHYS"


def test_machine_update_config_with_args():
    machine = Machine()
    assert machine.config["UNITS"] == "ENG"
    machine.update_config(dct=OVERRIDES_WITH_RELOAD)
    assert machine.config["UNITS"] == "PHYS"


def test_machine_init_invalid_ringmode():
    with pytest.raises(InvalidRingmodeError):
        Machine(overrides={"RINGMODE": "DOESNT_EXIST"})


def test_machine_lists_generate_correctly(machine_setup):
    machine = machine_setup
    assert len(machine.bpms) == len(machine.bpms_names)
    assert len(machine.quads) == len(machine.quads_names)
    assert len(machine.hstrs) == len(machine.hstrs_names)
    assert len(machine.vstrs) == len(machine.vstrs_names)
    for value in machine.fofb_disabled.values():
        assert len(value) == len(machine.bpms_names)
    assert len(machine.disabled_bpm_indices) == 0
    assert len(machine.faa_bpm_list) == len(machine.bpms_names) + 1
    assert len(machine.bba_x_pvs) == len(machine.bpms_names)
    assert len(machine.bba_y_pvs) == len(machine.bpms_names)


def test_machine_generates_cell_dictionary(machine_setup):
    machine = machine_setup
    for key, value in machine.cell_dictionary.items():
        for v in value:
            assert key in v


def test_machine_generates_psps(machine_setup):
    machine = machine_setup
    assert isinstance(machine.psps, list)


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


# TODO: Test get_enabled_bpms / measure_bpms / get_bba_offsets / retry_command.


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


def test_get_element_from_name_fails_with_invalid_name(machine_setup):
    machine = machine_setup
    with pytest.raises(NotImplementedError):
        machine.get_element_from_name("INVALID_NAME")


@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
def test_orm_does_not_exist(mock_element_values, tmp_path):
    with pytest.raises(FileNotFoundError):
        Machine(overrides={"ORBIT_RESPONSE_MATRIX_PATH": tmp_path})


@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
def test_corrector_kick_ENG(mock_element_values):
    KICK = 2e-5
    machine = Machine(overrides={"CORRECTOR_KICK_RADIANS": KICK, "UNITS": "ENG"})
    bpm_name = machine.bpms_names[0]
    quad_name = [machine.quads_names[0]]
    corrector_name = machine.hstrs_names[0]
    component = Components.from_name(
        machine, bpm_name, quad_name, corrector_name, "x", "x_kick"
    )
    assert machine.corrector_kick(component) == 0.09810708539977947


@mock.patch(
    "pytac.lattice.EpicsLattice.get_element_values",
    side_effect=get_element_values,
)
def test_corrector_kick_PHYS(mock_element_values):
    KICK = 2e-5
    machine = Machine(overrides={"CORRECTOR_KICK_RADIANS": KICK, "UNITS": "PHYS"})
    bpm_name = machine.bpms_names[0]
    quad_name = [machine.quads_names[0]]
    corrector_name = machine.hstrs_names[0]
    component = Components.from_name(
        machine, bpm_name, quad_name, corrector_name, "x", "x_kick"
    )
    assert machine.corrector_kick(component) == KICK


# TODO: Check feedbacks
# If use_feedbacks false, no feedbacks
# if use_fofb false, use sofb
# if max orbit too large, uses sofb then fofb
# normal, use fofb
# use fofb but fofb hasnt turned on (fofb_activation failure)

# TODO: Get/set quad/corrector

# TODO: zero and restore origins
