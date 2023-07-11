from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, List

import scipy.io as io


@dataclass
class RawData:
    """This RawData dataclass allows saving and loading for the rawdata and metadata."""

    rawdata: dict
    metadata: dict

    def save(self, folder_path: str) -> None:
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
        io.savemat(
            os.path.join(folder_path, filename),
            dct,
            oned_as="row",
            long_field_names=True,
        )

    @classmethod
    def from_file(cls, filepath: str) -> RawData:
        """This function loads the rawdata and metadata.

        Args:
            filepath: The filepath of the xxx-rawdata.mat file to load.

        Returns:
            A constructed RawData object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)
        return cls(dct["rawdata"], dct["metadata"])


@dataclass
class CalculatedOffset:
    old_value: float
    new_value: float
    diff_value: float
    diff_error: float


class Results:
    """This Results dataclass allows saving and loading for the results, metadata,
    plotting and offset data."""

    def __init__(
        self,
        results: dict[str, List[float]],
        metadata: dict[str, Any],
        plotting: dict[str, dict[str, List[float]]],
        offsets: dict[str, CalculatedOffset],
    ):
        """The default constructor which stores results, metadata and plotting
        and offsets.

        Args:
            results: The results dictionary.
            metadata: The metadata dictionary.
            plotting: The plotting dictionary.
            offsets: The offsets dictionary.
        """
        self.results: dict = results
        self.metadata: dict = metadata
        self.plotting: dict = plotting
        self.offsets: dict = offsets

    @classmethod
    def from_file(cls, filepath: str) -> Results:
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

        offsets: dict[str, CalculatedOffset] = {}
        for key, values in dct["offsets"].items():
            offsets[key] = CalculatedOffset(**values)

        return cls(results, dct["metadata"], dct["plotting"], offsets)

    def save(self, folder_path: str) -> None:
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

        offsets_dict = {}
        for key, values in offsets.items():
            offsets_dict[key] = asdict(values)

        dct = {
            "results": results,
            "metadata": metadata,
            "plotting": plotting,
            "offsets": offsets_dict,
        }
        # Can load files in matlab: object.("key")
        io.savemat(
            os.path.join(folder_path, filename),
            dct,
            oned_as="row",
            long_field_names=True,
        )
