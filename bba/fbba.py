"""This file contains fast BBA specific functions and classes"""

from bba.common import Algorithm


class FBBA(Algorithm):
    def __init__(self):
        pass

    def setup(self, accelerator, quad, plane_dict):
        """This are required arguments."""
        self.accelerator = accelerator
        self.quad = quad
        self.plane_dict = plane_dict

    def config(self, cycles = 1, frequency = 8):
        """These are optional arguments, which are used during testing."""
        self.cycles = cycles
        self.frequency = frequency

    def run_bba(self):
        print("fbba")

    def do_fbba_specific_thing(self):
        ...