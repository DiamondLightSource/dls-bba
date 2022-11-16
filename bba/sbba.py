"""This file contains slow BBA specific functions and classes"""

from bba.common import Algorithm


class SBBA(Algorithm):
    def __init__(self, accelerator):
        self._accelerator = accelerator
        self.configure()

    def configure(self, quadrupole_scalar = 0.01, decimated = False):
        """These are optional arguments, which are used during testing."""
        self.quadrupole_scalar = quadrupole_scalar
        self.decimated = decimated
        #self.PLOT_GRAPHS = PLOT_GRAPHS

    def run(self, quad, plane_dict):
        self.quad = quad
        self.plane_dict = plane_dict
    
    def save_data(self):
        pass
    
    def analyse_data(self):
        pass

    def apply_results(self):
        pass