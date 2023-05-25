from dataclasses import dataclass
import os

from dls_bba.lattice import NamedTuple
from dls_bba.common import get_isotime


# setup folders + logger in here?


@dataclass
class RawData:
    rawdata: dict
    classname: str
    metadata: dict

    def save(self, folder_path):
        rawdata = self.rawdata
        classname = self.classname
        metadata = self.metadata

        filename = "{}-rawdata.mat".format()

    @classmethod
    def from_file(cls):
        pass


@dataclass
class Results:
    pass

    def save(self, folder_path):
        pass

    @classmethod
    def from_file(cls):
        pass
