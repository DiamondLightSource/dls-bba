from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import numpy as np
import scipy.io as io


@dataclass
class QuadStrength:
    """The offset data for a single BPM PV."""

    high: np.ndarray[float] = None
    low: np.ndarray[float] = None

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        return setattr(self, item, value)


@dataclass
class BPMOffset:
    """The offset data for a single BPM PV."""

    old_value: float
    new_value: float
    diff_value: float
    diff_error: float

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        return setattr(self, item, value)


@dataclass
class QuadResults:
    """The mean offset and standard deviation of offsets for a Quadrupole."""

    mean_offset: float
    std_dev_offset: float

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        return setattr(self, item, value)


@dataclass
class OscillationPlane:
    """The offset data for a single BPM PV."""

    x: QuadStrength | BPMOffset | QuadResults = None
    y: QuadStrength | BPMOffset | QuadResults = None

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        return setattr(self, item, value)


@dataclass
class RawData:
    """Raw data from a BBA measurement."""

    rawdata: Dict[str, Any]
    metadata: Dict[str, Any]

    def save_old(self, folder_path: str) -> None:
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
    def old_from_old_file(cls, filepath: str) -> RawData:
        """Load a RawData object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            A RawData object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)
        return cls(dct["rawdata"], dct["metadata"])

    @classmethod
    def new_from_old_file(cls, filepath: str) -> RawData:
        """Load a RawData object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            A RawData object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)
        rawdata: Dict[str, List[float]] = {}
        for key, values in dct["rawdata"].items():
            quad_name, position = key.split("__")
            quad_name = quad_name.replace("_", "-")
            plane, quad_strength, corr_strength = position.lower().split("_")
            num_bpms = len(values)
            if quad_name not in rawdata:
                rawdata[quad_name] = OscillationPlane(
                    QuadStrength(np.zeros((5, num_bpms)), np.zeros((5, num_bpms))),
                    QuadStrength(np.zeros((5, num_bpms)), np.zeros((5, num_bpms))),
                )
            rawdata[quad_name][plane][quad_strength][int(corr_strength) - 1, :] = values
        # TODO: metadata
        return cls(rawdata, dct["metadata"])

    @classmethod
    def new_from_new_file(cls, filepath: str) -> RawData:
        """Load a RawData object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            A RawData object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)
        rawdata: Dict[str, List[float]] = {}
        for key, value in dct["rawdata"].items():
            quad_name = key.replace("_", "-")
            rawdata[quad_name] = OscillationPlane()
            for plane, quad_data in value.items():
                rawdata[quad_name][plane] = QuadStrength()
                for quad_strength, raw_array in quad_data.items():
                    rawdata[quad_name][plane][quad_strength] = raw_array
        # TODO: metadata
        return cls(rawdata, dct["metadata"])

    def save_new(self, folder_path: str) -> None:
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

        raw_dict = {}
        for key, value in rawdata.items():
            raw_dict[key.replace("-", "_")] = value
        dct = {"rawdata": raw_dict, "metadata": metadata}
        io.savemat(
            os.path.join(folder_path, filename),
            dct,
            oned_as="row",
            long_field_names=True,
        )


@dataclass
class FullResults:
    """The results of a BBA measurement and analysis."""

    def __init__(
        self,
        quad_results: Dict[str, List[float]],
        metadata: Dict[str, Any],
        plotting: Dict[str, Dict[str, np.ndarray]],
        bpm_offsets: Dict[str, BPMOffset],
    ) -> None:
        self.quad_results: Dict[str, List[float]] = quad_results
        self.metadata: Dict[str, Any] = metadata
        self.plotting: Dict[str, Dict[str, np.ndarray]] = plotting
        self.bpm_offsets: Dict[str, BPMOffset] = bpm_offsets
        # TODO: string representation

    @classmethod
    def old_from_old_file(cls, filepath: str) -> FullResults:
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

        offsets: Dict[str, BPMOffset] = {}
        for key, values in dct["offsets"].items():
            offsets[key] = BPMOffset(**values)

        return cls(results, dct["metadata"], dct["plotting"], offsets)

    @classmethod
    def new_from_old_file(cls, filepath: str) -> FullResults:
        """Load a Results object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            The loaded Results object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)

        results: Dict[str, List[float]] = {}
        for key, values in dct["results"].items():
            quad_name, plane = key.split("__")
            quad_name = quad_name.replace("_", "-")
            if quad_name not in results.keys():
                results[quad_name] = OscillationPlane()
            results[quad_name][plane] = QuadResults(*values)

        offsets: Dict[str, BPMOffset] = {}
        for key, values in dct["offsets"].items():
            bpm_name, _, plane = key.split("__")
            bpm_name = bpm_name.replace("_", "-")
            _, plane, _ = plane.lower().split("_")
            if bpm_name not in offsets.keys():
                offsets[bpm_name] = OscillationPlane()
            offsets[bpm_name][plane] = BPMOffset(**values)
        # TODO: metadata & plotting
        return cls(results, dct["metadata"], dct["plotting"], offsets)

    @classmethod
    def new_from_new_file(cls, filepath: str) -> FullResults:
        """Load a Results object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            The loaded Results object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)

        results: Dict[str, List[float]] = {}
        for key, planes in dct["results"].items():
            quad_name = key.replace("_", "-")
            for plane, values in planes.items():
                if quad_name not in results.keys():
                    results[quad_name] = OscillationPlane()
                results[quad_name][plane] = QuadResults(**values)

        offsets: Dict[str, BPMOffset] = {}
        for key, planes in dct["offsets"].items():
            bpm_name = key.replace("_", "-")
            for plane, values in planes.items():
                if bpm_name not in offsets.keys():
                    offsets[bpm_name] = OscillationPlane()
                offsets[bpm_name][plane] = BPMOffset(**values)
        # TODO: metadata & plotting
        return cls(results, dct["metadata"], dct["plotting"], offsets)

    def save_old(self, folder_path: str) -> None:
        """Save the Results object to a .mat file.

        Can load files in MATLAB with object.("key").

        Args:
            folder_path: The path to the folder to save the .mat file to.
        """
        results: Dict[str, List[float]] = self.quad_results
        metadata: Dict[str, Any] = self.metadata
        plotting: Dict[str, Dict[str, np.ndarray]] = self.plotting
        offsets: Dict[str, BPMOffset] = self.bpm_offsets

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

    def save_new(self, folder_path: str) -> None:
        """Save the Results object to a .mat file.

        Can load files in MATLAB with object.("key").

        Args:
            folder_path: The path to the folder to save the .mat file to.
        """
        results: Dict[str, List[float]] = self.quad_results
        metadata: Dict[str, Any] = self.metadata
        plotting: Dict[str, Dict[str, np.ndarray]] = self.plotting
        offsets: Dict[str, BPMOffset] = self.bpm_offsets

        method: str = metadata["method"]
        isotime: str = metadata["isotime"]
        bpm_name: str = metadata["bpm_name"]
        filename = f"{method}-{isotime}-{bpm_name}-results.mat"

        results_dict = {}
        for key, value in results.items():
            results_dict[key.replace("-", "_")] = value
        offsets_dict: Dict[str, Dict[str, float]] = {}
        for key, values in offsets.items():
            offsets_dict[key.replace("-", "_")] = asdict(values)

        dct = {
            "results": results_dict,
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


RawData.save = RawData.save_new
RawData.from_file = RawData.new_from_new_file
FullResults.save = FullResults.save_new
FullResults.from_file = FullResults.new_from_new_file
