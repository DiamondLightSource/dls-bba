import os

import numpy
import pytac
import scipy.io
from cothread.catools import DBR_STRING, caget

import bba


DATAROOT = "/dls_sw/work/common/matlab/mml/machine/diamondopsdata/"
BPM_ENABLED = "SR-DI-EBPM-01:ENABLED"


# Lazy load current lattice
_lattice = None


def get_ring_mode():
    ringmode = caget("SR-CS-RING-01:MODE", datatype=DBR_STRING)
    return ringmode


def get_structured_orbit_response_matrix():
    data = scipy.io.loadmat(get_rm_file(), appendmat=False, struct_as_record=False)
    rms = (data["Rmat"][0, 0].Data, data["Rmat"][1, 1].Data)
    return rms


def get_inverse_orbit_response_matrix():  # We should use SVD for this
    rms = get_structured_orbit_response_matrix()
    irms = [numpy.linalg.pinv(rms[0]), numpy.linalg.pinv(rms[1])]
    return irms


def prefix_from_pv(pv):
    return pv.split(":")[0]


def prefix_from_element(element, device):
    pv = element.get_device(device).get_pv_name(pytac.SP)
    return prefix_from_pv(pv)


def quad_from_pv(quad_pv, lattice):
    prefix = prefix_from_pv(quad_pv)
    quads = lattice.get_elements("quadrupole")
    for q in quads:
        if prefix_from_element(q, "b1") == prefix:
            return q


def get_rm_file():
    ringmode = get_ring_mode()
    rm_file = os.path.join(DATAROOT, ringmode, "GoldenBPMResp.mat")
    return rm_file


def enabled_bpms():
    good_bpms = numpy.equal(caget(BPM_ENABLED), 0)
    return good_bpms


def quad_to_bpm(quad, lattice):
    """Simply find the BPM closest to the quad."""
    bpms = lattice.get_elements("BPM")
    # Find centre of quad.
    qs = quad.s + quad.length / 2
    closest_bpm = None
    closest_bpm_index = None
    bpm_dist = 1000
    enabled = enabled_bpms()
    for i, bpm in enumerate(bpms):
        if not enabled[i]:
            continue
        if abs(bpm.s - qs) < bpm_dist:
            closest_bpm = bpm
            closest_bpm_index = i + 1
            bpm_dist = abs(bpm.s - qs)

    print("ID {}, dist {}".format(closest_bpm_index, bpm_dist))
    return closest_bpm_index, closest_bpm


def effective_corrector(quad, plane, lattice):
    """Find most effective corrector for a quadrupole.

    Given an pytac quad element, find the corrector magnet
    that will have the most effect at that quad.
    Return (id, corrector element)

    """
    bpm_id, bpm = quad_to_bpm(quad, lattice)
    data = scipy.io.loadmat(get_rm_file(), appendmat=False, struct_as_record=False)
    rm = data["Rmat"][plane, plane].Data
    row = rm[bpm_id - 1, :]
    # Note that ids are 1-indexed but arrays are 0-indexed.
    zero_indexed_corr_id = numpy.argmax(abs(row))
    corrs = lattice.get_elements(bba.CORRECTOR_FAMILIES[plane])
    return zero_indexed_corr_id + 1, corrs[zero_indexed_corr_id]


def quads_from_cell(cell, lattice):
    # Can we get this from pytac?
    quads = lattice.get_elements("quadrupole")
    cell_quads = []
    for quad in quads:
        pv = prefix_from_element(quad, "b1")
        cell_from_pv = int(pv[2:4])
        if cell_from_pv == cell:
            cell_quads.append(quad)
    return cell_quads


def get_lattice(mode=None):
    if not mode:
        mode = get_ring_mode()
    return pytac.load_csv.load(mode)
