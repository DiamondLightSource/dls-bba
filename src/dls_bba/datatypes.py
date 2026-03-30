from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Generic, TypeVar

import numpy as np
import numpy.typing as npt
import scipy.io as io


class DictDataclass:
    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        return setattr(self, item, value)


@dataclass
class QuadStrength(DictDataclass):
    """The offset data for a single BPM PV."""

    high: npt.NDArray[np.float64] | None = None
    low: npt.NDArray[np.float64] | None = None


@dataclass
class BPMOffset(DictDataclass):
    """The offset data for a single BPM PV."""

    old_value: float
    new_value: float
    diff_value: float
    diff_error: float


@dataclass
class QuadResults(DictDataclass):
    """The mean offset and standard deviation of offsets for a Quadrupole."""

    mean_offset: float
    std_dev_offset: float


T = TypeVar("T", QuadStrength, QuadResults, BPMOffset)


@dataclass
class OscillationPlane(Generic[T], DictDataclass):
    """The offset data for a single BPM PV."""

    x: T | None = None
    y: T | None = None


@dataclass
class RawData:
    """Raw data from a BBA measurement."""

    rawdata: dict[str, OscillationPlane[QuadStrength]]
    metadata: dict[str, Any]

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
        rawdata: dict[str, OscillationPlane[QuadStrength]] = {}
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
        rawdata: dict[str, OscillationPlane[QuadStrength]] = {}
        for key, value in dct["rawdata"].items():
            quad_name = key.replace("_", "-")
            rawdata[quad_name] = OscillationPlane()
            for plane, quad_data in value.items():
                rawdata[quad_name][plane] = QuadStrength()
                for quad_strength, raw_array in quad_data.items():
                    rawdata[quad_name][plane][quad_strength] = raw_array
        # TODO: metadata
        return cls(rawdata, dct["metadata"])

    @classmethod
    def from_file(cls, filepath: str) -> RawData:
        return cls.new_from_new_file(filepath)

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

    def save(self, folder_path: str) -> None:
        self.save_new(folder_path)


@dataclass
class FullResults:
    """The results of a BBA measurement and analysis."""

    quad_results: dict[str, OscillationPlane[QuadResults]]
    metadata: dict[str, Any]
    bpm_offsets: dict[str, OscillationPlane[BPMOffset]]

    @classmethod
    def old_from_old_file(cls, filepath: str) -> FullResults:
        """Load a Results object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            The loaded Results object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)

        results: dict[str, list[float]] = {}
        for key, values in dct["results"].items():
            results[key] = values.tolist()

        offsets: dict[str, BPMOffset] = {}
        for key, values in dct["offsets"].items():
            offsets[key] = BPMOffset(**values)

        return cls(results, dct["metadata"], offsets)  # type: ignore

    @classmethod
    def new_from_old_file(cls, filepath: str) -> FullResults:
        """Load a Results object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            The loaded Results object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)

        results: dict[str, OscillationPlane[QuadResults]] = {}
        for key, values in dct["results"].items():
            quad_name, plane = key.split("__")
            quad_name = quad_name.replace("_", "-")
            if quad_name not in results.keys():
                results[quad_name] = OscillationPlane()
            results[quad_name][plane] = QuadResults(*values)

        offsets: dict[str, OscillationPlane[BPMOffset]] = {}
        for key, values in dct["offsets"].items():
            bpm_name, _, plane = key.split("__")
            bpm_name = bpm_name.replace("_", "-")
            _, plane, _ = plane.lower().split("_")
            if bpm_name not in offsets.keys():
                offsets[bpm_name] = OscillationPlane()
            offsets[bpm_name][plane] = BPMOffset(**values)
        return cls(results, dct["metadata"], offsets)

    @classmethod
    def new_from_new_file(cls, filepath: str) -> FullResults:
        """Load a Results object from a .mat file.

        Args:
            filepath: The path to the .mat file.

        Returns:
            The loaded Results object.
        """
        dct = io.loadmat(filepath, simplify_cells=True)

        results: dict[str, OscillationPlane[QuadResults]] = {}
        for key, planes in dct["results"].items():
            quad_name = key.replace("_", "-")
            for plane, values in planes.items():
                if quad_name not in results.keys():
                    results[quad_name] = OscillationPlane()
                results[quad_name][plane] = QuadResults(**values)

        offsets: dict[str, OscillationPlane[BPMOffset]] = {}
        for key, planes in dct["offsets"].items():
            bpm_name = key.replace("_", "-")
            for plane, values in planes.items():
                if bpm_name not in offsets.keys():
                    offsets[bpm_name] = OscillationPlane()
                offsets[bpm_name][plane] = BPMOffset(**values)
        return cls(results, dct["metadata"], offsets)

    @classmethod
    def from_file(cls, filepath: str) -> FullResults:
        return cls.new_from_new_file(filepath)

    def save_old(self, folder_path: str) -> None:
        """Save the Results object to a .mat file.

        Can load files in MATLAB with object.("key").

        Args:
            folder_path: The path to the folder to save the .mat file to.
        """
        results: dict[str, OscillationPlane[QuadResults]] = self.quad_results
        metadata: dict[str, Any] = self.metadata
        offsets: dict[str, OscillationPlane[BPMOffset]] = self.bpm_offsets

        method: str = metadata["method"]
        isotime: str = metadata["isotime"]
        bpm_name: str = metadata["bpm_name"]
        filename = f"{method}-{isotime}-{bpm_name}-results.mat"

        offsets_dict: dict[str, dict[str, float]] = {}
        for key, values in offsets.items():
            offsets_dict[key] = asdict(values)

        dct = {"results": results, "metadata": metadata, "offsets": offsets_dict}
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
        results: dict[str, OscillationPlane[QuadResults]] = self.quad_results
        metadata: dict[str, Any] = self.metadata
        offsets: dict[str, OscillationPlane[BPMOffset]] = self.bpm_offsets

        method: str = metadata["method"]
        isotime: str = metadata["isotime"]
        bpm_name: str = metadata["bpm_name"]
        filename = f"{method}-{isotime}-{bpm_name}-results.mat"

        results_dict = {}
        for key, value in results.items():
            results_dict[key.replace("-", "_")] = value
        offsets_dict: dict[str, dict[str, float]] = {}
        for key, values in offsets.items():
            offsets_dict[key.replace("-", "_")] = asdict(values)

        dct = {"results": results_dict, "metadata": metadata, "offsets": offsets_dict}
        io.savemat(
            os.path.join(folder_path, filename),
            dct,
            oned_as="row",
            long_field_names=True,
        )

    def save(self, folder_path: str) -> None:
        self.save_new(folder_path)
