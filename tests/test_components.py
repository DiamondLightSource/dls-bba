import pytest

from dls_bba.components import (
    Components,
    check_component,
    construct_component_pair,
    get_component_pairs,
    verify_component_pairing,
)
from dls_bba.exceptions import ComponentConstructionError, ElementDisabledError


def test_components_from_name_for_horizontal_plane_is_valid(machine_setup):
    machine = machine_setup
    bpm_name = machine.bpms_names[0]
    quad_name = [machine.quads_names[0]]
    corrector_name = machine.hstrs_names[0]
    component = Components.from_name(
        machine, bpm_name, quad_name, corrector_name, "x", "x_kick"
    )
    assert component.bpm.get_device("x").name == bpm_name
    assert component.quadrupoles[0].get_device("b1").name == quad_name[0]
    assert component.corrector.get_device("x_kick").name == corrector_name


def test_name_to_element_for_horizontal_plane_is_valid(machine_setup):
    machine = machine_setup
    bpm_name = machine.bpms_names[0]
    quad_name = [machine.quads_names[0]]
    corrector_name = machine.hstrs_names[0]
    bpm, quad, corr = Components.name_to_element(
        machine, bpm_name, quad_name, corrector_name
    )

    assert bpm.get_device("x").name == bpm_name
    assert quad[0].get_device("b1").name == quad_name[0]
    assert corr.get_device("x_kick").name == corrector_name


def test_components_from_name_for_vertical_plane_is_valid(machine_setup):
    machine = machine_setup
    bpm_name = machine.bpms_names[0]
    quad_name = [machine.quads_names[0]]
    corrector_name = machine.vstrs_names[0]
    component = Components.from_name(
        machine, bpm_name, quad_name, corrector_name, "y", "y_kick"
    )
    assert component.bpm.get_device("y").name == bpm_name
    assert component.quadrupoles[0].get_device("b1").name == quad_name[0]
    assert component.corrector.get_device("y_kick").name == corrector_name


def test_name_to_element_for_vertical_plane_is_valid(machine_setup):
    machine = machine_setup
    bpm_name = machine.bpms_names[0]
    quad_name = [machine.quads_names[0]]
    corrector_name = machine.vstrs_names[0]
    bpm, quad, corr = Components.name_to_element(
        machine, bpm_name, quad_name, corrector_name
    )

    assert bpm.get_device("y").name == bpm_name
    assert quad[0].get_device("b1").name == quad_name[0]
    assert corr.get_device("y_kick").name == corrector_name


def test_components_convert_to_dict_is_valid(machine_setup):
    machine = machine_setup
    bpm_name = machine.bpms_names[0]
    quad_name = [machine.quads_names[0]]
    corrector_name = machine.hstrs_names[0]
    component = Components.from_name(
        machine, bpm_name, quad_name, corrector_name, "x", "x_kick"
    )
    c_d = component.as_dict()
    assert isinstance(c_d, dict)
    for key, value in c_d.items():
        assert isinstance(key, str)
        assert isinstance(value, str) or (
            isinstance(value, list) and isinstance(value[0], str)
        )


def test_components_convert_from_dict_is_valid(machine_setup):
    machine = machine_setup
    bpm_name = machine.bpms_names[0]
    quad_name = [machine.quads_names[0]]
    corrector_name = machine.hstrs_names[0]
    component = Components.from_name(
        machine, bpm_name, quad_name, corrector_name, "x", "x_kick"
    )
    c_d = component.as_dict()
    component2 = Components.from_dict(machine, c_d)
    assert component.axis == component2.axis
    assert component.bpm_name == component2.bpm_name
    assert component.bpm_index == component2.bpm_index
    assert component.corrector_name == component2.corrector_name
    assert component.quadrupoles_names == component2.quadrupoles_names
    assert component.kick == component2.kick


def test_component_pair_is_constructed_from_bpm_as_expected(machine_setup):
    machine = machine_setup
    element = machine.bpms_names[0]
    h_component, v_component = construct_component_pair(machine, element)
    assert isinstance(h_component, Components)
    assert isinstance(v_component, Components)
    assert h_component.bpm_name == v_component.bpm_name == element
    assert h_component.quadrupoles_names == v_component.quadrupoles_names


def test_component_pair_is_constructed_from_quad_as_expected(machine_setup):
    machine = machine_setup
    element = machine.quads_names[0]
    h_component, v_component = construct_component_pair(machine, element)
    assert isinstance(h_component, Components)
    assert isinstance(v_component, Components)
    assert element in h_component.quadrupoles_names
    assert element in v_component.quadrupoles_names
    assert h_component.bpm_name == v_component.bpm_name


def test_component_pair_raises_error_if_constructed_from_invalid_element(machine_setup):
    machine = machine_setup
    element = machine.hstrs_names[0]
    with pytest.raises(ComponentConstructionError):
        construct_component_pair(machine, element)


def test_check_component_return_none_if_components_are_valid(machine_setup):
    machine = machine_setup
    element = machine.bpms_names[0]
    component_pair = construct_component_pair(machine, element)
    check_component(machine, component_pair)


def test_check_component_return_none_if_components_are_fofb_disabled(machine_setup):
    machine = machine_setup
    x_dis = machine.fofb_disabled_indices["x"]
    machine.fofb_disabled_indices["x"] = [0]
    element = machine.bpms_names[0]
    component_pair = construct_component_pair(machine, element)
    check_component(machine, component_pair)
    # Undo settings change.
    machine.fofb_disabled_indices["x"] = x_dis


def test_check_component_raises_ElementDisabledError_if_components_are_disabled(
    machine_setup,
):
    machine = machine_setup
    dis = machine.disabled_bpm_indices
    machine.disabled_bpm_indices = [0]
    element = machine.bpms_names[0]
    component_pair = construct_component_pair(machine, element)
    with pytest.raises(ElementDisabledError):
        check_component(machine, component_pair)
    # Undo settings change.
    machine.disabled_bpm_indices = dis


def test_verify_pairings_does_not_remove_any_valid_components(machine_setup):
    machine = machine_setup
    elements = machine.bpms_names[0:2]
    pairs = []
    for element in elements:
        pairs.append(construct_component_pair(machine, element))
    v_pairs = verify_component_pairing(machine, pairs)
    assert len(v_pairs) == len(pairs)


def test_verify_pairings_does_not_remove_any_fofb_disabled_components(machine_setup):
    machine = machine_setup
    elements = machine.bpms_names[0:2]
    dis_x = machine.fofb_disabled_indices["x"]
    dis_y = machine.fofb_disabled_indices["y"]
    machine.fofb_disabled_indices["x"] = [0, 1, 2]
    machine.fofb_disabled_indices["y"] = [0, 1, 2]
    pairs = []
    for element in elements:
        pairs.append(construct_component_pair(machine, element))
    v_pairs = verify_component_pairing(machine, pairs)
    assert len(v_pairs) == len(pairs)
    # Undo settings change.
    machine.fofb_disabled_indices["x"] = dis_x
    machine.fofb_disabled_indices["y"] = dis_y


def test_verify_pairings_does_remove_any_disabled_components(machine_setup):
    machine = machine_setup
    dis = machine.disabled_bpm_indices
    machine.disabled_bpm_indices = [0, 1, 2]
    elements = machine.bpms_names[0:2]
    pairs = []
    for element in elements:
        pairs.append(construct_component_pair(machine, element))
    v_pairs = verify_component_pairing(machine, pairs)
    assert len(v_pairs) == 0
    # Undo settings change.
    machine.disabled_bpm_indices = dis


def test_get_pairs_correctly_creates_and_verifies_valid_components(machine_setup):
    machine = machine_setup
    elements = machine.bpms_names[0:2]
    pairs = get_component_pairs(machine, elements, True)
    for element, pair in zip(elements, pairs):
        assert pair[0].bpm_name == element
        assert pair[1].bpm_name == element
