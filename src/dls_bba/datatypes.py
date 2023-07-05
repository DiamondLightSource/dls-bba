import os
from dataclasses import dataclass
from typing import Any, List, Union

import scipy.io as io


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
        io.savemat(
            os.path.join(folder_path, filename),
            dct,
            oned_as="row",
            long_field_names=True,
        )

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
        offsets: dict[str, dict[str, Union[List[float], float]]],
    ):
        self.results: dict = results
        self.metadata: dict = metadata
        self.plotting: dict = plotting
        self.offsets: dict = offsets

    @classmethod
    def from_file(cls, filepath: str):
        """"""
        dct = io.loadmat(filepath, simplify_cells=True)

        results = {}
        for keys, values in dct["results"].items():
            results[keys] = values.tolist()

        offsets: dict[str, dict[str, Union[List[float], float]]] = {}
        for key, values in dct["offsets"].items():
            offsets[key] = {}
            for id, value in values.items():
                if isinstance(value, float):
                    offsets[key][id] = value
                else:
                    offsets[key][id] = value.tolist()

        return cls(results, dct["metadata"], dct["plotting"], offsets)

    def save(self, folder_path):
        """"""
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
        # Can load files in matlab: object.("key")
        io.savemat(
            os.path.join(folder_path, filename),
            dct,
            oned_as="row",
            long_field_names=True,
        )
