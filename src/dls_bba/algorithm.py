from abc import ABC, abstractmethod
from typing import List, Union

import numpy as np

from dls_bba.components import Components
from dls_bba.datatypes import RawData, Results
from dls_bba.lattice import ORIGIN_SUFFIXES, Lattice


class Algorithm(ABC):
    def __init__(self, lattice: Lattice):
        self._lattice = lattice

    @abstractmethod
    def run(self, component_pair: list[Components]) -> RawData:
        pass

    @abstractmethod
    def analyse(self, rawdata: RawData) -> Results:
        pass

    def create_offsets_dict(
        self, results, metadata
    ) -> dict[str, dict[str, Union[List[float], float]]]:
        offsets = {}
        bpm_name = metadata["bpm_name"]
        bpm_index = metadata["bpm_index"]

        for index, axis in enumerate(["x", "y"]):
            bpm_key = bpm_name + ORIGIN_SUFFIXES["BBA"].format(axis=axis.upper())
            # Get current BBA offset.
            old_bba = self._lattice.get_bba_offsets()[index][bpm_index]
            # Calculate the change needed.
            difference = self.calculate_new_offsets(results, axis)
            # Calculate the new BBA offset.
            new_bba = [old_bba + difference[0], difference[1]]

        offsets[bpm_key] = {"new": new_bba, "old": old_bba, "diff": difference}
        return offsets

    def calculate_new_offsets(
        self, results: dict[str, List[float]], axis: str
    ) -> List[float]:
        keys = [key for key in results.keys() if axis in key]
        values = []
        errors = []
        for key in keys:
            values.append(results[key][0])
            errors.append(results[key][1])

        sum_error = 0.0
        mean_value = float(np.mean(values))
        for value, error in zip(values, errors):
            sum_error += (error / value) ** 2
        total_error = np.sqrt(sum_error) * mean_value
        return [mean_value, total_error]
