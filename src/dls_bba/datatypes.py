from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import numpy as np
import scipy.io as io


@dataclass
class RawData:
    """Raw data from a BBA measurement."""

    rawdata: Dict[str, Any]
    metadata: Dict[str, Any]

    def save(self, folder_path: str) -> None:
        """Save the RawData object to a .mat file.

        Can load files in MATLAB with object.("key").

        Args:
            folder_path: The path to the folder to save the .mat file to.
        """
        rawdata = self.rawdata
        metadata = self.metadata

        method: str = metadata["method"]
        isotime: str = metadata["isotime"]
        bpm_name: str = metadata["bpm_name"]
        filename = f"{method}-{isotime}-{bpm_name}-rawdata.mat"

        dct = {"rawdata": rawdata, "metadata": metadata}
        io.savemat(
            os.path.join(folder_path, filename),
            dct,
            oned_as="row",
            long_field_names=True,
        )

    @classmethod
    def from_file(cls, filepath: str) -> RawData:
        """Load a RawData object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            A RawData object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)
        return cls(dct["rawdata"], dct["metadata"])


@dataclass
class CalculatedOffset:
    """The offset data for a single BPM PV."""

    old_value: float
    new_value: float
    diff_value: float
    diff_error: float


class Results:
    """The results of a BBA measurement and analysis."""

    def __init__(
        self,
        results: Dict[str, List[float]],
        metadata: Dict[str, Any],
        plotting: Dict[str, Dict[str, np.ndarray]],
        offsets: Dict[str, CalculatedOffset],
    ):
        self.results: Dict[str, List[float]] = results
        self.metadata: Dict[str, Any] = metadata
        self.plotting: Dict[str, Dict[str, np.ndarray]] = plotting
        self.offsets: Dict[str, CalculatedOffset] = offsets

    @classmethod
    def from_file(cls, filepath: str) -> Results:
        """Load a Results object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            The loaded Results object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)

        results: Dict[str, List[float]] = {}
        for keys, values in dct["results"].items():
            results[keys] = values.tolist()

        offsets: Dict[str, CalculatedOffset] = {}
        for key, values in dct["offsets"].items():
            offsets[key] = CalculatedOffset(**values)

        return cls(results, dct["metadata"], dct["plotting"], offsets)

    def save(self, folder_path: str) -> None:
        """Save the Results object to a .mat file.

        Can load files in MATLAB with object.("key").

        Args:
            folder_path: The path to the folder to save the .mat file to.
        """
        results: Dict[str, List[float]] = self.results
        metadata: Dict[str, Any] = self.metadata
        plotting: Dict[str, Dict[str, np.ndarray]] = self.plotting
        offsets: Dict[str, CalculatedOffset] = self.offsets

        method: str = metadata["method"]
        isotime: str = metadata["isotime"]
        bpm_name: str = metadata["bpm_name"]
        filename = f"{method}-{isotime}-{bpm_name}-results.mat"

        offsets_dict: Dict[str, Dict[str, float]] = {}
        for key, values in offsets.items():
            offsets_dict[key] = asdict(values)

        dct = {
            "results": results,
            "metadata": metadata,
            "plotting": plotting,
            "offsets": offsets_dict,
        }
        io.savemat(
            os.path.join(folder_path, filename),
            dct,
            oned_as="row",
            long_field_names=True,
        )
