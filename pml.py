import scipy.io
import numpy
from cothread.catools import caget, DBR_STRING
import sys
import os
import aphla as ap
ap.machines.load('SRI21')
ap.machines.use('SR')

DATAROOT = "/home/diamond/common/matlab/middlelayer/2-0/machine/diamondopsdata"
BPM_ENABLED = 'SR-DI-EBPM-01:ENABLED'

# Planes
X = 0
Y = 1
AXIS_NAMES = {X: 'X', Y: 'Y'}
BPM_FAMILY = {X: 'HSTR', Y: 'VSTR'}


def prefix_from_pv(pv):
    return pv.split(':')[0]


def prefix_from_element(element):
    pv = element.pv()[0]
    return prefix_from_pv(pv)


def quad_from_pv(quad_pv):
    prefix = prefix_from_pv(quad_pv)
    quads = ap.getElements('QUAD')
    for q in quads:
        if prefix_from_element(q) == prefix:
            return q


def get_rm_file():
    ringmode = caget("SR-CS-RING-01:MODE", datatype=DBR_STRING)
    rm_file = os.path.join(DATAROOT, ringmode, "GoldenBPMResp.mat")
    return rm_file


def enabled_bpms():
    good_bpms = numpy.equal(caget(BPM_ENABLED), 0)
    return good_bpms


def quad_to_bpm(quad):
    """
    Simply find the BPM closest to the quad.
    """
    bpms = ap.getBpms()
    # Find centre of quad.
    qs = quad.sb + quad.length / 2
    closest_bpm = None
    closest_bpm_index = None
    bpm_dist = 1000
    enabled = enabled_bpms()
    for i, bpm in enumerate(bpms):
        if not enabled[i]:
            continue
        if abs(bpm.sb - qs) < bpm_dist:
            closest_bpm = bpm
            closest_bpm_index = i + 1
            bpm_dist = abs(bpm.sb - qs)

    return closest_bpm_index, closest_bpm


def effective_corrector(quad, plane):
    """
    Given an aphla quad element, find the corrector magnet
    that will have the most effect at that quad.
    Return (id, corrector element)
    """
    bpm_id, bpm = quad_to_bpm(quad)
    data = scipy.io.loadmat(get_rm_file(), appendmat=False,
                            struct_as_record=False)
    rm = data["Rmat"][plane, plane].Data
    row = rm[bpm_id-1,:]
    # Note that ids are 1-indexed but arrays are 0-indexed.
    corr_id = numpy.argmax(abs(row)) + 1
    corrs = ap.getElements(BPM_FAMILY[plane])
    return corr_id, corrs[corr_id]


def quads_from_cell(cell):
    '''
    This a work-around method until we get the cell number properly imported
    into hla.
    '''
    quads = ap.getElements('QUAD')
    cell_quads = []
    for quad in quads:
        pv = prefix_from_element(quad)
        cell_from_pv = int(pv[2:4])
        if cell_from_pv == cell:
            cell_quads.append(quad)
    return cell_quads
