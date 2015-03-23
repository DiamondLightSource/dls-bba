import scipy.io
import numpy
from cothread.catools import caget, DBR_STRING
import sys
import os
sys.path.append('/dls_sw/work/common/python/hla')
try:
    import aphla as ap
    ap.machines.load('SRI0913')
    ap.machines.use('SR')
except ImportError:
    print('We need APHLA!')
    sys.exit()


DATAROOT = "/home/diamond/common/matlab/middlelayer/2-0/machine/diamondopsdata"
BPM_ENABLED = 'SR-DI-EBPM-01:ENABLED'

# Planes
X = 0
Y = 1
AXIS_NAMES = {X: 'X', Y: 'Y'}
BPM_FAMILY = {X: 'HSTR', Y: 'VSTR'}


def quad_from_pv(quad_pv):
    prefix = quad_pv.split(':')[0]
    quads = ap.getElements('QUAD')
    for q in quads:
        if q.pv()[0].split(':')[0] == prefix:
            return q


def get_rm_file():
    ringmode = caget("SR-CS-RING-01:MODE", datatype=DBR_STRING)
    rm_file = os.path.join(DATAROOT, ringmode, "GoldenBPMResp.mat")
    return rm_file


def enabled_bpms():
    good_bpms = numpy.array(caget(BPM_ENABLED) == 0, dtype=numpy.bool)
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
    for i, bpm in enumerate(bpms):
        if not enabled_bpms()[i]:
            continue
        if abs(bpm.sb - qs) < bpm_dist:
            closest_bpm = bpm
            closest_bpm_index = i + 1
            bpm_dist = abs(bpm.sb - qs)

    return closest_bpm_index, closest_bpm


def effective_corrector(quad, plane):
    """
    Given an hlapa quad element, find the corrector magnet
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
