import os
from dataclasses import dataclass

import scipy.io as io

# setup folders + logger in here?


@dataclass
class RawData:
    rawdata: dict
    metadata: dict

    def save(self, folder_path):
        rawdata = self.rawdata
        metadata = self.metadata

        method = metadata["method"]
        isotime = metadata["isotime"]
        bpm_prefix = metadata["bpm_prefix"]
        filename = f"{method}-{isotime}-{bpm_prefix}-rawdata.mat"

        dct = {"rawdata": rawdata, "metadata": metadata}
        # TODO: Cannot load this in matlab as object contains strings with - instead of _.
        io.savemat(os.path.join(folder_path, filename), dct, oned_as="row")

    @classmethod
    def from_file(cls, filepath):
        dct = io.loadmat(filepath, simplify_cells=True)
        return cls(dct["rawdata"], dct["metadata"])


@dataclass
class Results:
    results: dict
    metadata: dict

    def save(self, folder_path):
        results = self.results
        metadata = self.metadata

        method = metadata["method"]
        isotime = metadata["isotime"]
        bpm_prefix = metadata["bpm_prefix"]
        filename = f"{method}-{isotime}-{bpm_prefix}-results.mat"

        dct = {"results": results, "metadata": metadata}
        # TODO: Cannot load this in matlab as object contains strings with - instead of _.
        io.savemat(os.path.join(folder_path, filename), dct, oned_as="row")

    @classmethod
    def from_file(cls, filepath):
        dct = io.loadmat(filepath, simplify_cells=True)
        return cls(dct["results"], dct["metadata"])
