import numpy as np
import pytac
import scipy.io as io
from cothread.catools import DBR_STRING, caget

DATAROOT = "/dls_sw/work/common/matlab/mml/machine/diamondopsdata/"
MASTER_CALIBRATION_PATH = "/dls_sw/work/common/matlab/mml/machine-new/diamond/master_calibration.csv"
CORRECTOR_KICK_RAD = 2e-5  # Radians
QUAD_TO_BPM_SPECIAL = {  # In these cases, no quad is closest to these BPMs.
    "SR02A-PC-Q3E-08": "SR02C-DI-EBPM-07",  # Quad 2-8 -> BPM 2-7
    "SR09S-PC-QUADD-02": "SR09S-DI-EBPM-01",  # Quad 9S-2 -> BPM 9S-1
    "SR13S-PC-QUADD-02": "SR13S-DI-EBPM-01"  # Quad 13S-2 -> BPM 13S-1
}
BPM_TO_QUAD_SPECIAL = {
    "SR02C-DI-EBPM-01": ["SR02A-PC-Q1BE-01"],  # Quad 2,1 only
    "SR02C-DI-EBPM-08": ["SR02A-PC-Q1BE-10"],  # Quad 2,9 only
    "SR08C-DI-EBPM-07": ["SR08A-PC-QUADF-01"],  # 9S-1 is pv 08-1
    "SR09C-DI-EBPM-01": ["SR09A-PC-QUADF-04"],  # Cell 9 discrepency.
    "SR10C-DI-EBPM-01": ["SR10A-PC-Q1B-01"],  # Cell 10, magnet length inconsistency.
    "SR10C-DI-EBPM-02": ["SR10A-PC-Q2B-02", "SR10A-PC-Q3B-03"],  # Cell 10, magnet length inconsistency.
    "SR12C-DI-EBPM-07": ["SR12A-PC-QUADF-01"],  # 13S-1 is pv 12-1
    "SR13C-DI-EBPM-01": ["SR13A-PC-QUADF-04"],  # Cell 13 discrepency.
}


class Accelerator:
    """Accelerator class stores all accelerator data and functions."""

    def __init__(self, ringmode=None):
        """Initialising the accelerator model."""
        self.ringmode = self.get_ring_mode(ringmode)
        self.accelerator = pytac.load_csv.load(self.ringmode)

        # Required to stop timeout on the machine.
        self.accelerator._data_source_manager._data_sources[pytac.LIVE]._devices["beam_current"]._cs._timeout = 5.0

        self.bpms = self.accelerator.get_elements("BPM")
        self.enabled_bpms = self.accelerator.get_element_values("BPM", "enabled")
        self.bpm_h_fofb_enabled = self.accelerator.get_element_values("BPM", "x_fofb_disabled", pytac.RB)
        self.bpm_v_fofb_enabled = self.accelerator.get_element_values("BPM", "y_fofb_disabled", pytac.RB)
        self.bpm_disabled = self.accelerator.get_element_values("BPM", "enabled")

        self.hstrs = self.accelerator.get_elements("HSTR")
        self.vstrs = self.accelerator.get_elements("VSTR")

        self.quads = self.accelerator.get_elements("quadrupole")

        self.quad_to_bpm_dict = {}
        self.bpm_to_quad_dict = {}

        for quad in self.quads:
            closest_bpm = self.quad_to_bpm(quad)
            quad_pv_prefix = self.element_to_pv_prefix(quad)
            bpm_pv_prefix = self.element_to_pv_prefix(closest_bpm)
            self.quad_to_bpm_dict[quad_pv_prefix] = bpm_pv_prefix
        for bpm in self.bpms:
            quads = self.bpm_to_quad(bpm)
            quad_pv_prefix = []
            for quad in quads:
                quad_pv_prefix.append(self.element_to_pv_prefix(quad))
            bpm_pv_prefix = self.element_to_pv_prefix(bpm)
            self.bpm_to_quad_dict[bpm_pv_prefix] = quad_pv_prefix

    def get_ring_mode(self, ringmode=None):
        """Get ringmode if one not provided."""
        if ringmode is None:
            ringmode = caget("SR-CS-RING-01:MODE", datatype=DBR_STRING)
        return ringmode

    def element_to_pv_prefix(self, element, plane=None):
        if element in self.quads:
            pv = element.get_pv_name("b1", pytac.SP)
        elif element in self.bpms:
            pv = element.get_pv_name("x", pytac.RB)
        elif element in self.hstrs and plane.corrector == "HSTR":
            pv = element.get_pv_name(plane.kick, pytac.SP)
        elif element in self.vstrs and plane.corrector == "VSTR":
            pv = element.get_pv_name(plane.kick, pytac.SP)
        else:
            ValueError(f"Unexpected element: {element}.")

        return pv.split(":")[0]

    def pv_prefix_to_element(self, pv_prefix, plane=None):
        element = None
        # print(pv_prefix)
        family = pv_prefix.split("-")[2]
        if family[0] == "Q":
            for quad in self.quads:
                if self.element_to_pv_prefix(quad) == pv_prefix:
                    element = quad
        elif family == "EBPM":
            for bpm in self.bpms:
                if self.element_to_pv_prefix(bpm) == pv_prefix:
                    element = bpm
        else:
            ValueError(f"Not Implimented yet for: {pv_prefix}")
        return element

    def measure_quad(self, quad):
        """Returns the current quadrupole current value."""
        return quad.get_value("b1", pytac.RB, pytac.ENG)

    def set_quad(self, quad, value):
        quad.set_value("b1", value, pytac.ENG)

    def measure_corrector(self, corrector, plane_info):
        """Returns the current corrector current value."""
        return corrector.get_value(plane_info.kick, pytac.RB, pytac.ENG)

    def set_corrector(self, corrector, plane_info, value):
        corrector.get_value(plane_info.kick, pytac.ENG)

    def measure_bpms(self, plane_info):
        return self.bpms.get_element_values("BPM", plane_info.axis.lower())

    def special_correctors(self, plane):
        """SR01A -> SR01S or HSTR -> HSCOR."""
        special_correctors = []
        if plane.corrector == "HSTR":
            corrector_pv_roots = [self.element_to_pv_prefix(corrector_pv_root, plane) for corrector_pv_root in self.hstrs]
        elif plane.corrector == "VSTR":
            corrector_pv_roots = [self.element_to_pv_prefix(corrector_pv_root, plane) for corrector_pv_root in self.vstrs]
        for corrector_pv_root in corrector_pv_roots:
            pv_split = corrector_pv_root.split("-")
            if pv_split[0][-1] == "S" or len(pv_split[2]) == 5:
                special_correctors.append(corrector_pv_root)
        return special_correctors

    def quad_to_bpm(self, quad):
        """Input of quad element, returns closest bpm element."""
        quad_midpoint = quad.s + quad.length / 2
        quad_bpm_distance = 1000
        quad_closest_bpm = None

        quad_pv_prefix = self.element_to_pv_prefix(quad)
        if quad_pv_prefix not in QUAD_TO_BPM_SPECIAL:
            for bpm in self.bpms:
                if abs(bpm.s - quad_midpoint) < quad_bpm_distance:
                    quad_closest_bpm = bpm
                    quad_bpm_distance = abs(bpm.s - quad_midpoint)

        else:
            bpm_pv = QUAD_TO_BPM_SPECIAL[self.element_to_pv_prefix(quad)]
            for bpm in self.bpms:
                if bpm_pv == self.element_to_pv_prefix(bpm):
                    quad_closest_bpm = bpm
        return quad_closest_bpm

    def bpm_to_quad(self, bpm):
        """Input bpm element, return list of closest quad elements."""
        bpm_pv_prefix = self.element_to_pv_prefix(bpm)

        if bpm_pv_prefix not in BPM_TO_QUAD_SPECIAL:
            quads_keys = [quad_key for quad_key, bpm_value in self.quad_to_bpm_dict.items() if bpm_value == bpm_pv_prefix]
            quads_list = []
            for quad_pv_prefix in quads_keys:
                quads_list.append(self.pv_prefix_to_element(quad_pv_prefix))
        else:
            quads_list = []
            quads_pvs = BPM_TO_QUAD_SPECIAL[bpm_pv_prefix]
            for quad_pv_prefix in quads_pvs:
                quads_list.append(self.pv_prefix_to_element(quad_pv_prefix))
        return quads_list

    def get_rm_file(self):
        rm_file = DATAROOT + "/" + self.ringmode + "/GoldenBPMResp.mat"
        return rm_file

    def effective_corrector(self, bpm_pv_prefix, plane):
        """Find most effective corrector for a bpm.

        Return (id, corrector element)
        """
        rm = self.get_rm_file()
        data = io.loadmat(rm, appendmat=False, struct_as_record=False)
        rm = data["Rmat"][plane.index, plane.index].Data
        row = rm[self.bpms.index(self.pv_prefix_to_element(bpm_pv_prefix)) - 1, :]
        # Note that ids are 1-indexed but arrays are 0-indexed.
        zero_indexed_corr_id = np.argmax(abs(row))
        # TODO: Make this more elegant?
        if plane.corrector == "HSTR":
            corrs = self.hstrs
        if plane.corrector == "VSTR":
            corrs = self.vstrs
        return corrs[zero_indexed_corr_id]

    def microrads(self, corrector, plane) -> float:
        """Find the current required for a corrector kick of x microrads."""
        with open(MASTER_CALIBRATION_PATH) as file:
            data = np.genfromtxt(file, delimiter=",", dtype=str)

        pv_column = data[:, 0]
        corr_pv_prefix = self.element_to_pv_prefix(corrector, plane)
        corr_pv_prefix = corr_pv_prefix.replace("-", "_")
        result = np.where(pv_column == corr_pv_prefix)
        initial_current, initial_rad = data[result][0][3:5]
        final_current, final_rad = data[result][1][3:5]
        gradient = (float(final_current) - float(initial_current)) / (float(final_rad) - float(initial_rad))
        linear_value = gradient * CORRECTOR_KICK_RAD
        rad_value = float(np.format_float_positional(linear_value, precision=6))
        return rad_value
