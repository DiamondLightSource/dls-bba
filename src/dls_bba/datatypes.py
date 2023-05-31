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

    def sort(self) -> Tuple[str, list[list[float]]]:
        """"""
        # These are the changes in BBA value relative to current position.
        results = self.results
        metadata = self.metadata
        bpm_name = metadata["bpm_name"]

        sorted_results = []

        for axis in ["x", "y"]:
            keys = [key for key in results.keys() if axis in key]

            values, errors = [], []
            for key in keys:
                values.append(results[key][0])
                errors.append(results[key][1])

            sum_error = 0
            mean_value = np.mean(values)
            for value, error in zip(values, errors):
                sum_error += (error / value) ** 2
            total_error = np.sqrt(sum_error) * mean_value

            sorted_results.append([mean_value, total_error])
        return bpm_name, sorted_results
