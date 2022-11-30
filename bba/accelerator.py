import pytac
from cothread.catools import DBR_STRING, caget
import scipy.io as io
import numpy as np


DATAROOT = "/dls_sw/work/common/matlab/mml/machine/diamondopsdata/"
MASTER_CALIBRATION_PATH = "/dls_sw/work/common/matlab/mml/machine-new/diamond/master_calibration.csv"
REQUIRED_RAD = 2e-5 # Radians


class Accelerator:
    """Accelerator class stores all accelerator data and functions."""

    def __init__(self, ringmode = None):
        """Initialising the accelerator model."""
        self.ringmode = self.get_ring_mode(ringmode)
        self.accelerator = pytac.load_csv.load(self.ringmode)

        # Required to stop timeout on the machine.
        self.accelerator._data_source_manager._data_sources[pytac.LIVE]._devices["beam_current"]._cs._timeout = 5.0

        self.bpms = self.accelerator.get_elements("BPM")
        self.quads = self.accelerator.get_elements("quadrupole")
        self.hstr_pvs = self.accelerator.get_element_pv_names("HSTR", "x_kick", pytac.RB)
        self.vstr_pvs = self.accelerator.get_element_pv_names("VSTR", "y_kick", pytac.RB)

        self.quad_pvs = self.accelerator.get_element_pv_names("quadrupole", "b1", pytac.RB)
        self.quad_pvs = [quad[:-2] for quad in self.quad_pvs]

    def get_ring_mode(self, ringmode = None):
        """Get ringmode if one not provided"""
        if ringmode is None:
            ringmode = caget("SR-CS-RING-01:MODE", datatype=DBR_STRING)
        return ringmode

    def enabled_bpms(self):
        good_bpms = self.accelerator.get_element_values("BPM", "enabled")
        return good_bpms

    def quad_to_pv(self, quad, field=None):
        if field is None:
            index = self.quads.index(quad)
            pv = self.quad_pvs[index]
        else:
            pv = quad.get_pv_name(field, pytac.SP)
        return pv

    def pv_to_quad(self, quad_pv):
        base_pv = quad_pv.split(":")[0]
        index = self.quad_pvs.index(base_pv)
        return self.quads[index]

    def prefix_from_element(self, element, device):
        pv = element.get_device(device).get_pv_name(pytac.SP)
        return pv.split(":")[0]

    def get_correctors(self, plane):
       # TODO: sort plane values between hstr, 0, horizontal etc.
        corr = self.accelerator.get_elements(plane.corrector)
        return corr

    def quads_from_cell(self, cell):
    # Can we get this from pytac?
    # TODO: Make this work in pytac - there is a function it just doesnt work.
        cell_quads = []
        for quad in self.quads:
            pv = self.prefix_from_element(quad, "b1")
            cell_from_pv = int(pv[2:4])
            if cell_from_pv == cell:
                cell_quads.append(quad)
        return cell_quads

    def measure_quad(self, quad):
        """This is returning the current quadrupole current value."""
        value = quad.get_value("b1", pytac.RB, pytac.ENG)
        return value

    def set_quad(self, quad, value):
        quad.set_value("b1", value, pytac.ENG)

    def special_correctors(self): 
        "SR01A -> SR01S or HSTR -> HSCOR"
        special_correctors = []
        for corrector_pv in self.hstr_pvs:
            pv_split = corrector_pv.split("-")
            if pv_split[0][-1] == "S" or len(pv_split[2]) == 5:
                special_correctors.append(corrector_pv[:-2])
        for corrector_pv in self.vstr_pvs:
            pv_split = corrector_pv.split("-")
            if pv_split[0][-1] == "S" or len(pv_split[2]) == 5:
                special_correctors.append(corrector_pv[:-2])
        return special_correctors

    def quad_to_bpm(self, quad):
        """Finds the closest bpm to a quadrupole. (Deals with special cases)"""
        quad1_midpoint = quad.s + quad.length / 2
        quad1_bpm_distance = 1000
        quad1_closest_bpm = None
        # Checking the quad before to check for special cases.
        quad2 = self.quads[self.quads.index(quad) - 1]
        quad2_midpoint = quad2.s + quad2.length / 2
        quad2_bpm_distance = 1000
        quad2_closest_bpm = None

        for bpm in self.bpms:
            if abs(bpm.s - quad1_midpoint) < quad1_bpm_distance:
                quad1_closest_bpm = bpm
                quad1_bpm_distance = abs(bpm.s - quad1_midpoint)
            if abs(bpm.s - quad2_midpoint) < quad2_bpm_distance:
                quad2_closest_bpm = bpm
                quad2_bpm_distance = abs(bpm.s - quad2_midpoint)
        
        quad1_bpm_index = self.bpms.index(quad1_closest_bpm)
        quad2_bpm_index = self.bpms.index(quad2_closest_bpm)

        if quad1_bpm_index != quad2_bpm_index and quad1_bpm_index != quad2_bpm_index + 1:
            quad1_bpm_index = quad1_bpm_index - 1
            quad1_closest_bpm = self.bpms[quad1_bpm_index]

        return quad1_bpm_index, quad1_closest_bpm

    def get_rm_file(self):
        rm_file = DATAROOT + "/" + self.ringmode +"/GoldenBPMResp.mat"
        return rm_file

    def effective_corrector(self, quad, plane):
        """Find most effective corrector for a quad.

        Return (id, corrector element)
        """
        bpm_index, bpm_element = self.quad_to_bpm(quad)
        rm = self.get_rm_file()
        data = io.loadmat(rm, appendmat=False, struct_as_record=False)
        rm = data["Rmat"][plane.index, plane.index].Data
        row = rm[bpm_index - 1, :]
        # Note that ids are 1-indexed but arrays are 0-indexed.
        zero_indexed_corr_id = np.argmax(abs(row))
        corrs = self.get_correctors(plane)
        return zero_indexed_corr_id + 1, corrs[zero_indexed_corr_id]

    def element_to_pv(self, element, plane):
        """Corrector element to pv"""
        pv = element.get_pv_name(plane.kick, pytac.RB)
        return pv[:-2]

    def microrads(self, corr_pv):
        """Find the current required for a corrector kick of x microrads"""

        with open(MASTER_CALIBRATION_PATH) as file:
            data = np.genfromtxt(file, delimiter=",", dtype = str)
        pv_column = data[:, 0]
        corr_pv = corr_pv.replace("-", "_")
        result = np.where(pv_column == corr_pv)
        initial_current, initial_rad = data[result][0][3:5]
        final_current, final_rad = data[result][1][3:5]
        gradient = (float(final_current) - float(initial_current))/(float(final_rad) - float(initial_rad))
        linear_value = gradient * REQUIRED_RAD
        rad_value = str(np.format_float_positional(linear_value, precision=6))
        return rad_value
