import os
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import scipy.io as io

from dls_bba.lattice import ORIGIN_SUFFIXES


@dataclass
class RawData:
    """This RawData dataclass allows saving and loading for the rawdata and metadata."""

    rawdata: dict
    metadata: dict

    def save(self, folder_path) -> None:
        """This function saves the rawdata and metadata.

        Args:
            folder_path: The folderpath to save the data to.
        """
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
        """This function loads the rawdata and metadata.

        Args:
            filepath: The filepath of the xxx-rawdata.mat file to load.
        """
        dct = io.loadmat(filepath, simplify_cells=True)
        return cls(dct["rawdata"], dct["metadata"])


class Results:
    """This Results class allows saving and loading for the results, metadata and
    plotting information as well as calculating the offsets as required."""

    def __init__(
        self,
        results: dict[str, Any],
        metadata: dict[str, Any],
        plotting: dict[str, Any],
        offsets: Optional[dict[str, list[float]]] = None,
    ):
        """The default constructor which stores results, metadata and plotting,
        with an optional offsets storing or calculating option.

        Args:
            results: The results dictionary.
            metadata: The metadata dictionary.
            plotting: The plotting dictionary.
            offsets: The calculated offsets dictionary.

        """
        self.results: dict = results
        self.metadata: dict = metadata
        self.plotting: dict = plotting
        self.offsets: dict = (
            self.find_true_bba_offsets() if offsets is None else offsets
        )

    def find_true_bba_offsets(self) -> dict[str, list[float]]:
        """This function calculates the bba offsets with the results and metadata.

        Returns:
            A dictionary with the calculated offsets.
        """
        offsets: dict[str, list[float]] = {}
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
        """This constructor loads a Results object when given a filepath.

        Args:
            filepath: The filepath to a xxx-results.mat file.

        Returns:
            A constructed Results object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)

        results = {}
        for keys, values in dct["results"].items():
            results[keys] = values.tolist()

        return cls(results, dct["metadata"], dct["plotting"], dct["offsets"])

    def save(self, folder_path) -> None:
        """This function saves the current Results object to the given folder path.
        Note: Files with complex keys can be loaded in MATLAB. eg: object.("key").

        Args:
            folder_path: The path to the folder to save the file in.
        """
        results = self.results
        metadata = self.metadata
        plotting = self.plotting
        offsets = self.offsets

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
        io.savemat(os.path.join(folder_path, filename), dct, oned_as="row")
