import pytest

from dls_bba.components import Components, generate_component_pairings
from dls_bba.exceptions import ComponentConstructionError
from dls_bba.machine import Lattice


@pytest.fixture(scope="module")
def lattice_setup():
    lattice = Lattice()
    return lattice


def test_name_to_element_generates_valid_elements_with_single_element(lattice_setup):
    lattice = lattice_setup
    bpm_name = lattice.bpms_names[0]
    quad_name = [lattice.quads_names[0]]
    corrector_name = lattice.hstrs_names[0]
    bpm, quad, corr = Components.name_to_element(
        lattice, bpm_name, quad_name, corrector_name
    )

    assert bpm.get_device("x").name == bpm_name
    assert quad[0].get_device("b1").name == quad_name[0]
    assert corr.get_device("x_kick").name == corrector_name


def test_name_to_element_generates_valid_elements_with_double_elements(lattice_setup):
    lattice = lattice_setup
    bpm_name = lattice.bpms_names[0]
    quad_name = [lattice.quads_names[0], lattice.quads_names[1]]
    corrector_name = lattice.vstrs_names[0]
    bpm, quads, corr = Components.name_to_element(
        lattice, bpm_name, quad_name, corrector_name
    )

    assert bpm.get_device("x").name == bpm_name
    assert quads[0].get_device("b1").name == quad_name[0]
    assert quads[1].get_device("b1").name == quad_name[1]
    assert corr.get_device("y_kick").name == corrector_name


def test_component_construction_from_element_names_is_valid(lattice_setup):
    bpm_number = 0
    axis = "x"
    kick = "x_kick"

    lattice = lattice_setup
    bpm_name = lattice.bpms_names[bpm_number]
    quad_name = [lattice.quads_names[0]]
    corrector_name = lattice.hstrs_names[0]
    component = Components.from_name(
        lattice, bpm_name, quad_name, corrector_name, axis, kick
    )

    assert component.bpm_index == bpm_number
    assert component.bpm.get_device(axis).name == bpm_name
    assert component.corrector.get_device(kick).name == corrector_name


def test_component_conversion_to_dictionary_is_valid(lattice_setup):
    bpm_number = 0
    axis = "x"
    kick = "x_kick"

    lattice = lattice_setup
    bpm_name = lattice.bpms_names[bpm_number]
    quad_name = [lattice.quads_names[0]]
    corrector_name = lattice.hstrs_names[0]
    component = Components.from_name(
        lattice, bpm_name, quad_name, corrector_name, axis, kick
    )
    component_dictionary = component.as_dict()

    assert component_dictionary["bpm_name"] == bpm_name
    assert component_dictionary["quadrupoles_names"] == quad_name
    assert component_dictionary["corrector_name"] == corrector_name
    assert component_dictionary["axis"] == axis
    assert component_dictionary["kick"] == kick


def test_component_construction_from_dictionary_is_valid(lattice_setup):
    bpm_number = 0
    axis = "x"
    kick = "x_kick"

    lattice = lattice_setup
    bpm_name = lattice.bpms_names[bpm_number]
    quad_name = [lattice.quads_names[0]]
    corrector_name = lattice.hstrs_names[0]
    component = Components.from_name(
        lattice, bpm_name, quad_name, corrector_name, axis, kick
    )
    component_dictionary = component.as_dict()
    new_component = Components.from_dict(lattice, component_dictionary)

    assert new_component.bpm_index == component.bpm_index
    assert new_component.bpm_name == component.bpm_name
    assert new_component.quadrupoles_names == component.quadrupoles_names
    assert new_component.corrector_name == component.corrector_name
    assert new_component.axis == component.axis
    assert new_component.kick == component.kick


def test_component_pairing_generation_is_valid_from_single_bpm(lattice_setup):
    lattice = lattice_setup
    bpm_name = lattice.bpms_names[0]
    components_pair = generate_component_pairings(lattice, bpm_name)
    component_x, component_y = components_pair

    assert component_x.bpm_name == component_y.bpm_name
    assert component_x.quadrupoles_names == component_y.quadrupoles_names
    assert component_x.axis == "x"
    assert component_y.axis == "y"
    assert component_x.kick == "x_kick"
    assert component_y.kick == "y_kick"


def test_component_pairing_generation_is_valid_from_double_bpm(lattice_setup):
    lattice = lattice_setup
    bpm_name = lattice.bpms_names[67]
    components_pair = generate_component_pairings(lattice, bpm_name)
    component_x, component_y = components_pair

    assert component_x.bpm_name == component_y.bpm_name
    assert component_x.quadrupoles_names == component_y.quadrupoles_names
    assert component_x.axis == "x"
    assert component_y.axis == "y"
    assert component_x.kick == "x_kick"
    assert component_y.kick == "y_kick"


def test_component_pairing_generation_is_valid_from_quadrupole(lattice_setup):
    lattice = lattice_setup
    quadrupole_name = lattice.quads_names[0]
    components_pair = generate_component_pairings(lattice, quadrupole_name)
    component_x, component_y = components_pair

    assert component_x.bpm_name == component_y.bpm_name
    assert component_x.quadrupoles_names == component_y.quadrupoles_names
    assert component_x.axis == "x"
    assert component_y.axis == "y"
    assert component_x.kick == "x_kick"
    assert component_y.kick == "y_kick"


def test_component_generation_with_invalid_element_raises_error(lattice_setup):
    lattice = lattice_setup
    corrector_name = lattice.hstrs_names[0]
    with pytest.raises(ComponentConstructionError):
        generate_component_pairings(lattice, corrector_name)
