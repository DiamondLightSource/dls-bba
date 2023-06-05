import os
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import scipy.io as io

from dls_bba.lattice import ORIGIN_SUFFIXES


@dataclass
class RawData:
    rawdata: dict
    metadata: dict

    def save(self, folder_path):
        """"""
        rawdata = self.rawdata
        metadata = self.metadata

        method = metadata["method"]
        isotime = metadata["isotime"]
        bpm_name = metadata["bpm_name"]
        filename = f"{method}-{isotime}-{bpm_name}-rawdata.mat"

        dct = {"rawdata": rawdata, "metadata": metadata}
        # Can load files in matlab: object.("key")
        io.savemat(os.path.join(folder_path, filename), dct, oned_as="row")

    @classmethod
    def from_file(cls, filepath):
        """"""
        dct = io.loadmat(filepath, simplify_cells=True)
        return cls(dct["rawdata"], dct["metadata"])


class Results:
    def __init__(
        self,
        results: dict[str, Any],
        metadata: dict[str, Any],
        plotting: dict[str, Any],
        offsets: Optional[dict[str, list[float]]] = None,
    ):
        self.results: dict = results
        self.metadata: dict = metadata
        self.plotting: dict = plotting
        self.offsets: dict = (
            self.find_true_bba_offsets() if offsets is None else offsets
        )

    def find_true_bba_offsets(self) -> dict[str, list[float]]:
        offsets = {}
        bpm_name = self.metadata["bpm_name"]

        for axis in ["x", "y"]:
            keys = [key for key in self.results.keys() if axis in key]

            values = []
            errors = []
            for key in keys:
                values.append(self.results[key][0])
                errors.append(self.results[key][1])

            sum_error = 0
            mean_value = np.mean(values)
            for value, error in zip(values, errors):
                sum_error += (error / value) ** 2
            total_error = np.sqrt(sum_error) * mean_value

            bpm_key = bpm_name + ORIGIN_SUFFIXES["BBA"].format(axis=axis.upper())
            offsets[bpm_key] = [mean_value, total_error]
        return offsets

    @classmethod
    def from_file(cls, filepath: str):
        """"""
        dct = io.loadmat(filepath, simplify_cells=True)
        return cls(dct["results"], dct["metadata"], dct["plotting"], dct["offsets"])

    def save(self, folder_path):
        """"""
        results = self.results
        metadata = self.metadata
        offsets = self.offsets
        plotting = self.plotting

        method = metadata["method"]
        isotime = metadata["isotime"]
        bpm_name = metadata["bpm_name"]
        filename = f"{method}-{isotime}-{bpm_name}-results.mat"

        dct = {
            "results": results,
            "metadata": metadata,
            "plotting": plotting,
            "offsets": offsets,
        }
        # TODO: Cannot load this in matlab as object contains strings with - instead of _.
        io.savemat(os.path.join(folder_path, filename), dct, oned_as="row")
