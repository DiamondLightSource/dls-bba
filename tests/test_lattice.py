import sys
from importlib.resources import files

import pytest

from dls_bba.lattice import Lattice

if sys.version_info > (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files


@pytest.fixture(scope="module")
def lattice_setup():
    config_filepath = files("dls_bba").joinpath("config.json")
    lattice = Lattice(config_folderpath=config_filepath, ringmode="I04")
    return lattice


def test_pytac_lattice_loaded_config_correctly(lattice_setup):
    lattice = lattice_setup
    config = lattice._config
    pytac_lattice = lattice._lattice
    assert pytac_lattice.name == config["RINGMODE"]
    assert pytac_lattice.get_default_data_source() == config["DATASOURCE"]
    assert pytac_lattice.get_default_units()[:3] in config["UNITS"].lower()


def test_element_and_pv_lists_equal_length(lattice_setup):
    lattice = lattice_setup
    assert len(lattice.bpms) == len(lattice.bpms_pvs)
    assert len(lattice.quads) == len(lattice.quads_pvs)
    assert len(lattice.hstrs) == len(lattice.hstrs_pvs)
    assert len(lattice.vstrs) == len(lattice.vstrs_pvs)


def test_bpm2quad(lattice_setup):
    lattice = lattice_setup
    exceptions = lattice._config["BPM2QUAD_EXCEPTIONS"]
    for bpm_pv_1 in lattice.bpms_pvs:
        quad_pv = lattice.bpm2quad(bpm_pv_1, pv=True)
        if len(quad_pv) == 2:
            bpm_pv_2a = lattice.quad2bpm(quad_pv[0], pv=True)
            bpm_pv_2b = lattice.quad2bpm(quad_pv[1], pv=True)
            bpm_pv_2 = [bpm_pv_2a, bpm_pv_2b]
        else:
            bpm_pv_2 = [lattice.quad2bpm(quad_pv[0], pv=True)]

        if bpm_pv_1 not in bpm_pv_2:
            if bpm_pv_1 in exceptions:
                if bpm_pv_2 is exceptions[bpm_pv_1]:
                    continue
                else:
                    assert False
            else:
                assert False


def test_quad2bpm(lattice_setup):
    lattice = lattice_setup
    exceptions = lattice._config["QUAD2BPM_EXCEPTIONS"]

    for quad_pv_1 in lattice.quads_pvs:
        bpm_pv = lattice.quad2bpm(quad_pv_1, pv=True)
        quad_pv_2 = lattice.bpm2quad(bpm_pv, pv=True)
        if quad_pv_1 not in quad_pv_2:
            if quad_pv_1 in exceptions:
                if quad_pv_2[0] == exceptions[quad_pv_1]:
                    continue
                else:
                    assert False
            else:
                assert False


def test_element_to_pv_for_all_elements(lattice_setup):
    lattice = lattice_setup
    for bpm_pv in lattice.bpms_pvs:
        element = lattice.get_element_from_pv(bpm_pv)
        assert "bpm" in element.families
    for quad_pv in lattice.quads_pvs:
        element = lattice.get_element_from_pv(quad_pv)
        assert "quadrupole" in element.families
    for hstr_pv in lattice.hstrs_pvs:
        element = lattice.get_element_from_pv(hstr_pv)
        assert "hstr" in element.families
    for vstr_pv in lattice.vstrs_pvs:
        element = lattice.get_element_from_pv(vstr_pv)
        assert "vstr" in element.families


def test_effective_corrector_for_elements_and_pvs(lattice_setup):
    lattice = lattice_setup
    bpm, bpm_pv = lattice.bpms[0], lattice.bpms_pvs[0]

    correctors = lattice.effective_correctors(bpm)
    correctors_pvs = lattice.effective_correctors(bpm_pv, pv=True)

    for corrector, corrector_pv in zip(correctors, correctors_pvs):
        assert corrector is lattice.get_element_from_pv(corrector_pv)


# def test_corrector_kick_for_element_and_pvs(lattice_setup):
#     lattice = lattice_setup

#     c_pvs = lattice.effective_correctors(lattice.bpms_pvs[0], pv=True)
#     cs = lattice.effective_correctors(lattice.bpms[0])

#     assert lattice.corrector_kick(c_pvs, pv=True) == lattice.corrector_kick(cs)


# def test_element_to_pv_for_all_pvs():
#     assert False
