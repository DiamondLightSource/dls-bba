"""This file contains slow BBA specific functions and classes"""

from bba.common import Algorithm


class SBBA(Algorithm):
    def __init__(self):
        pass

    def setup(self, accelerator, quad, plane_dict):
        """This are required arguments."""
        self.accelerator = accelerator
        self.quad = quad
        self.plane_dict = plane_dict

    def config(self):
        """These are optional arguments, which are used during testing."""
        pass

    def run_bba(self):
        print("sbba")