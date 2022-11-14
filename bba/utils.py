import os

import numpy
import scipy.io

from bba import constants


def get_rm_file(accelerator):
    ringmode = accelerator.ringmode
    rm_file = os.path.join(constants.DATAROOT, ringmode, "GoldenBPMResp.mat")
    return rm_file


def get_structured_orbit_response_matrix():
    data = scipy.io.loadmat(get_rm_file(), appendmat=False, struct_as_record=False)
    rms = (data["Rmat"][0, 0].Data, data["Rmat"][1, 1].Data)
    return rms


def get_inverse_orbit_response_matrix():  # We should use SVD for this
    rms = get_structured_orbit_response_matrix()
    irms = [numpy.linalg.pinv(rms[0]), numpy.linalg.pinv(rms[1])]
    return irms


def quad_to_bpm(quad, accelerator):
    """Simply find the BPM closest to the quad."""
    #bpms = accelerator.get_elements("BPM")
    # Find centre of quad.
    qs = quad.s + quad.length / 2
    closest_bpm = None
    closest_bpm_index = None
    bpm_dist = 1000
    enabled = accelerator.enabled_bpms()
    for i, bpm in enumerate(accelerator.bpms):
        if not enabled[i]:
            continue
        if abs(bpm.s - qs) < bpm_dist:
            closest_bpm = bpm
            closest_bpm_index = i + 1
            bpm_dist = abs(bpm.s - qs)

    print("ID {}, dist {}".format(closest_bpm_index, bpm_dist))
    return closest_bpm_index, closest_bpm


def effective_corrector(quad, plane, accelerator):
    """Find most effective corrector for a quadrupole.

    Given an pytac quad element, find the corrector magnet
    that will have the most effect at that quad.
    Return (id, corrector element)
    """
    bpm_id, bpm = quad_to_bpm(quad, accelerator)
    rm = get_rm_file(accelerator)
    data = scipy.io.loadmat(rm, appendmat=False, struct_as_record=False)
    rm = data["Rmat"][plane.index, plane.index].Data
    row = rm[bpm_id - 1, :]
    # Note that ids are 1-indexed but arrays are 0-indexed.
    zero_indexed_corr_id = numpy.argmax(abs(row))
    corrs = accelerator.get_correctors(plane.corrector)
    return zero_indexed_corr_id + 1, corrs[zero_indexed_corr_id]
