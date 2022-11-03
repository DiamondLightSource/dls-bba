# This script generates the horizontal_bba_new.txt and vertical_bba_new.txt's that are used during bba.
# This process requires the response matrix csv (Full 2x2 grid)
# The file is layed out as:
# BPM that relates to Quad -> Quad -> 1% of Quad current -> A -> corrector that has the most effect on that BPM (RM) -> current needed for 10 microrad chnage in that corrector -> A

from cothread.catools import caget
import pytac
import numpy as np
from typing import NamedTuple
import csv


LIVE_RINGMODE = caget("SR-CS-RING-01:MODE", datatype = str)
REQUIRED_RAD = 2e-5
QUADRUPOLE_SCALAR = 0.01
MASTER_CALIBRATION_PATH = "/dls_sw/work/common/matlab/mml/machine-new/diamond/master_calibration.csv"
RESPONSE_MATRIX_PATH = "RM-20221018T161052.csv"

#RESPONSE_MATRIX_PATH = /dls_sw/work/common/matlab/mml/machine-new/diamondopsdata/I04/GoldenBPMResp.mat -> Need .mat formatting
Axis = NamedTuple("Axis", [("axis", str)])
AXIS = {
    "X": Axis("x_kick"),
    "Y": Axis("y_kick"),
}

# There are three cases where the quad should not be linked to the closest BPM: Cell 2, Straight 9, Straight 13.
SPECIAL_QUADS = [204, 778, 1181]
SPECIAL_BPMS = [193, 769, 1172]


class LatticeModel:
    """LatticeModel class stores all lattice data and functions."""

    def __init__(self, ringmode):
        """Initialising the lattice, Quadrupole and BPM arrays."""
        self.lattice = pytac.load_csv.load(ringmode)
        self.lattice._data_source_manager._data_sources[pytac.LIVE]._devices["beam_current"]._cs._timeout = 5.0

        self.quadrupoles = self.lattice.get_elements("quadrupole")
        self.bpms = self.lattice.get_elements("BPM")
        self.hstr = self.lattice.get_elements("HSTR")
        self.vstr = self.lattice.get_elements("VSTR")


    def quad2bpm(self, quad):
        """Quad is a single quadrupole element"""
        # TODO: Sort special cases programatically.
        quad_midpoint = quad.s + quad.length / 2
        quad_bpm_distance = 1000
        closest_bpm = None

        # Special cases
        special_quads = [quads for quads in self.quadrupoles if quads.index in SPECIAL_QUADS]
        special_bpms = [bpms for bpms in self.bpms if bpms.index in SPECIAL_BPMS]

        if quad in special_quads:
            closest_bpm = special_bpms[special_quads.index(quad)]
        else:
            for bpm in self.bpms:
                if abs(bpm.s - quad_midpoint) < quad_bpm_distance:
                    closest_bpm = bpm
                    quad_bpm_distance = abs(bpm.s - quad_midpoint)
        #q_index = self.quadrupoles.index(quad)
        #b_index = self.bpms.index(closest_bpm)
        return closest_bpm


    def measure_quads(self):
        """
        """
        values = self.lattice.get_element_values("quadrupole","b1", pytac.RB, pytac.ENG)
        return values


    def sort_quads(self, quad_values):
        """
        """
        value_list = []
        for quad in quad_values:
            value = quad * QUADRUPOLE_SCALAR
            value = np.format_float_positional(value, precision=6)
            value_list.append(str(value))
        return value_list


    def use_rm(self, matrix, bpm_list):
        """
        """
        maximum = []
        for bpm in bpm_list:
            row = list(matrix[self.bpms.index(bpm)])
            maximum.append(row.index(max(row, key=abs)))
            corr_elements = [self.hstr[index] for index in maximum]
        return corr_elements


    def microrads(self, corrector_pvs):
        """Find the current required for a corrector kick of 10 microrads
        """
        with open (MASTER_CALIBRATION_PATH) as file:
            data = np.genfromtxt(file, delimiter=",", dtype = str)
        pv_column = data[:, 0]
        rad_values = []
        for corr_pv in corrector_pvs:
            corr_pv = corr_pv[:-2]
            corr_pv = corr_pv.replace("-", "_")
            result = np.where(pv_column == corr_pv)
            initial_current, initial_rad = data[result][0][3:5]
            final_current, final_rad = data[result][1][3:5]
            gradient = (float(final_current) - float(initial_current))/(float(final_rad) - float(initial_rad))
            linear_value = gradient * REQUIRED_RAD
            rad_value = str(np.format_float_positional(linear_value, precision=6))
            rad_values.append(rad_value)
        return rad_values


    def units(self):
        """
        """
        zeros = np.zeros(len(self.quadrupoles))
        a_list = ["A" for zero in zeros]
        return a_list


    def quad_pv(self, quad_list):
        """
        """
        pv_list = []
        for quad in quad_list:
            pv = quad.get_pv_name("b1", pytac.RB)
            pv_list.append(pv)
        return pv_list


    def bpm_pv(self, bpm_list):
        """
        """
        pv_list = []
        for bpm in bpm_list:
            pv = bpm.get_pv_name("x", pytac.RB)
            pv_list.append(pv[:-5])
        return pv_list


    def correctors_pv(self, correctors, axis):
        """
        """
        pv_list = []
        axis_field = AXIS[axis][0]
        for corr in correctors:
            pv = corr.get_pv_name(axis_field, pytac.RB)
            pv_list.append(pv)
        return pv_list


def import_rm():
    """
    """
    with open(RESPONSE_MATRIX_PATH) as file:
        full_matrix = np.genfromtxt(file)
        xCxB_yCxB, xCyB_yCyC = np.vsplit(full_matrix, 2)
        xCxB, yCxB = np.hsplit(xCxB_yCxB, 2)
        xCyB, yCyB = np.hsplit(xCyB_yCyC, 2)
        return xCxB, yCyB


def write_csvs(bpms, quads, quad_values, hstr_pvs, hstr_values, vstr_pvs, vstr_values, unit):
    """
    """
    horizontal_data = [bpms, quads, quad_values, unit, hstr_pvs, hstr_values, unit]
    horizontal_zipped = zip(*horizontal_data)
    vertical_data = [bpms, quads, quad_values, unit, vstr_pvs, vstr_values, unit]
    vertical_zipped = zip(*vertical_data)
    f_hor = open("horizontal_bba.csv", "w")
    writer = csv.writer(f_hor, delimiter=",")
    for row in horizontal_zipped:
        writer.writerow(row)
        writer.writerow("")
    f_hor.close()

    f_ver = open("vertical_bba.csv", "w")
    writer = csv.writer(f_ver, delimiter=",")
    for row in vertical_zipped:
        writer.writerow(row)
        writer.writerow("")
    f_ver.close()
    return


def hv_bba(ringmode = LIVE_RINGMODE):
    """
    """
    #temporary override
    ringmode = "I04"
    print("Initialising Lattice")
    lattice_model = LatticeModel(ringmode)

    quad_list = lattice_model.quadrupoles
    bpm_list = []
    print("Starting Quad2Bpm")
    for quad in quad_list:
        bpm_list.append(lattice_model.quad2bpm(quad))

    bpm_pvs = lattice_model.bpm_pv(bpm_list)

    # 1% of quads current
    print("Measuring Quads")
    quad_values = lattice_model.measure_quads()
    quad_formatted = lattice_model.sort_quads(quad_values)
    quad_pvs = lattice_model.quad_pv(quad_list)

    # search response matrix for corrected that has most effect on that bpm.
    print("Importing RM")
    xx, yy = import_rm()
    
    print("Using RM")
    hstr = lattice_model.use_rm(xx, bpm_list)
    vstr = lattice_model.use_rm(yy, bpm_list)

    print("Measuring correctors")
    hstr_pvs = lattice_model.correctors_pv(hstr, "X")
    vstr_pvs = lattice_model.correctors_pv(vstr, "Y")
    
    hstr_rad = lattice_model.microrads(hstr_pvs)
    vstr_rad = lattice_model.microrads(vstr_pvs)

    #Units (Purely to keep formatting uniform)
    print("Making A's")
    unit = lattice_model.units()

    #Append to a .csv
    print("Appending to .csv")
    write_csvs(bpm_pvs, quad_pvs, quad_formatted, hstr_pvs, hstr_rad, vstr_pvs, vstr_rad, unit)


def main():
    hv_bba()


if __name__ == "__main__":
    main()
