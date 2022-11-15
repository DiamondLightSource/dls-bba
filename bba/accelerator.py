import pytac
from cothread.catools import DBR_STRING, caget
class Accelerator:
    """Accelerator class stores all accelerator data and functions."""

    def __init__(self, ringmode = None):
        """Initialising the accelerator, HSTR, VSTR and BPM arrays."""
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
        corr = self.accelerator.get_elements(plane)
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
        value = quad.get_value("b1", pytac.RB, pytac.ENG)
        return value

    def set_quad(self, quad, value):
        quad.set_value("b1", value, pytac.ENG)
