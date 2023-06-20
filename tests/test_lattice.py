import pytest

from dls_bba.lattice import Lattice


@pytest.fixture(scope="module")
def lattice_setup():
    lattice = Lattice()
    return lattice


def test_pytac_lattice_loaded_config_correctly(lattice_setup):
    lattice = lattice_setup
    config = lattice._config
    pytac_lattice = lattice._lattice
    assert pytac_lattice.name == config["RINGMODE"]
    assert pytac_lattice.get_default_data_source() == config["DATASOURCE"]
    assert pytac_lattice.get_default_units()[:3] in config["UNITS"].lower()


def test_element_and_name_lists_equal_length(lattice_setup):
    lattice = lattice_setup
    assert len(lattice.bpms) == len(lattice.bpms_names)
    assert len(lattice.quads) == len(lattice.quads_names)
    assert len(lattice.hstrs) == len(lattice.hstrs_names)
    assert len(lattice.vstrs) == len(lattice.vstrs_names)


def test_bpm2quad(lattice_setup):
    lattice = lattice_setup
    exceptions = lattice._config["BPM2QUAD_EXCEPTIONS"]
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


def test_quad2bpm(lattice_setup):
    lattice = lattice_setup
    exceptions = lattice._config["QUAD2BPM_EXCEPTIONS"]

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
