import os

import numpy as np
import pytest
from scipy import io

from dls_bba.datatypes import (
    OscillationPlane,
    QuadStrength,
    RawData,
)


@pytest.fixture(scope="module")
def old_rawdata_setup():
    """Creates the old style of rawdata"""
    num_bpms = 5
    rawdata = {
        "SR01A-PC-Q1D-01_x_High_1": np.arange(num_bpms, dtype=np.float64),
        "SR01A-PC-Q1D-01_y_High_1": np.arange(num_bpms, dtype=np.float64),
        "SR01A-PC-Q1D-01_x_Low_1": np.arange(num_bpms, dtype=np.float64),
        "SR01A-PC-Q1D-01_y_Low_1": np.arange(num_bpms, dtype=np.float64),
        "SR01A-PC-Q1D-01_x_High_2": np.arange(num_bpms, 2 * num_bpms, dtype=np.float64),
        "SR01A-PC-Q1D-01_y_High_2": np.arange(num_bpms, 2 * num_bpms, dtype=np.float64),
        "SR01A-PC-Q1D-01_x_Low_2": np.arange(num_bpms, 2 * num_bpms, dtype=np.float64),
        "SR01A-PC-Q1D-01_y_Low_2": np.arange(num_bpms, 2 * num_bpms, dtype=np.float64),
        "SR01A-PC-Q1D-01_x_High_3": np.arange(
            2 * num_bpms, 3 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_y_High_3": np.arange(
            2 * num_bpms, 3 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_x_Low_3": np.arange(
            2 * num_bpms, 3 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_y_Low_3": np.arange(
            2 * num_bpms, 3 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_x_High_4": np.arange(
            3 * num_bpms, 4 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_y_High_4": np.arange(
            3 * num_bpms, 4 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_x_Low_4": np.arange(
            3 * num_bpms, 4 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_y_Low_4": np.arange(
            3 * num_bpms, 4 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_x_High_5": np.arange(
            4 * num_bpms, 5 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_y_High_5": np.arange(
            4 * num_bpms, 5 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_x_Low_5": np.arange(
            4 * num_bpms, 5 * num_bpms, dtype=np.float64
        ),
        "SR01A-PC-Q1D-01_y_Low_5": np.arange(
            4 * num_bpms, 5 * num_bpms, dtype=np.float64
        ),
    }
    metadata = {
        "method": "rawdata_method",
        "isotime": "rawdata_isotime",
        "bpm_name": "rawdata_bpm_name",
    }
    return RawData(rawdata, metadata)


@pytest.fixture(scope="module")
def new_rawdata_setup():
    """Creates the new style of rawdata"""
    num_bpms = 5
    corr_array = np.arange(num_bpms * num_bpms, dtype=np.float64).reshape(
        num_bpms, num_bpms
    )  # noqa: E501
    oscillation_plane = OscillationPlane(
        QuadStrength(corr_array, corr_array),
        QuadStrength(corr_array, corr_array),
    )
    rawdata = {"SR01A-PC-Q1D-01": oscillation_plane}
    metadata = {
        "method": "rawdata_method",
        "isotime": "rawdata_isotime",
        "bpm_name": "rawdata_bpm_name",
    }
    return RawData(rawdata, metadata)


def sofb_save_old_raw_data_format(self, folder_path: str) -> None:
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


def sofb_load_old_raw_data_from_old_file(filepath: str) -> RawData:
    """Load the RawData object from a .mat file. The .mat file contains the old
    data format for RawData and loads it into the old data format for the RawData
    object.

    Args:
        filepath: The path to the .mat file.

    Returns:
        A RawData object.
    """
    dct = io.loadmat(filepath, simplify_cells=True)
    return RawData(dct["rawdata"], dct["metadata"])


def sofb_load_new_raw_data_from_old_file(filepath: str) -> RawData:
    """Load a RawData object from a .mat file. The .mat file contains the old
    data format for RawData and loads it into the new data format for the RawData
    Object.

    Args:
        filepath: The path to the .mat file.

    Returns:
        A RawData object.
    """
    dct = io.loadmat(filepath, simplify_cells=True)
    rawdata: dict[str, OscillationPlane[QuadStrength]] = {}
    for key, values in dct["rawdata"].items():
        quad_name, position = key.split("_", 1)
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
    return RawData(rawdata, dct["metadata"])


def fbba_load_new_raw_data_from_old_file(filepath: str) -> RawData:
    """Ingest the old matlab file format for fbba data and return
    a RawData object using the new data format.
    """
    dct = io.loadmat(filepath, simplify_cells=True)
    rawdata: dict[str, OscillationPlane[QuadStrength]] = {}
    for key, values in dct["rawdata"].items():
        quad_name, position = key.split("_", 1)
        plane, quad_strength = position.lower().split("_")
        num_samples = values.shape[0]
        num_bpms = values.shape[1]
        if quad_name not in rawdata:
            rawdata[quad_name] = OscillationPlane(
                QuadStrength(
                    np.zeros((num_samples, num_bpms)),
                    np.zeros((num_samples, num_bpms)),
                ),
                QuadStrength(
                    np.zeros((num_samples, num_bpms)),
                    np.zeros((num_samples, num_bpms)),
                ),
            )
        rawdata[quad_name][plane][quad_strength] = values
    return RawData(rawdata, dct["metadata"])


def sofb_save_old_and_new_data(tmpdir, old_rawdata_setup, new_rawdata_setup):
    """Get the old sofb RawData and the new sofb RawData objects and save them to .m
    files. Return the paths to these .m files."""

    dirpath_rawdata_old_file_format = os.path.join(tmpdir, "old")
    dirpath_rawdata_new_file_format = os.path.join(tmpdir, "new")
    os.mkdir(dirpath_rawdata_old_file_format)
    os.mkdir(dirpath_rawdata_new_file_format)

    sofb_save_old_raw_data_format(old_rawdata_setup, dirpath_rawdata_old_file_format)
    new_rawdata_setup.save(dirpath_rawdata_new_file_format)

    method = old_rawdata_setup.metadata["method"]
    isotime = old_rawdata_setup.metadata["isotime"]
    bpm_name = old_rawdata_setup.metadata["bpm_name"]
    filename_old = f"{method}-{isotime}-{bpm_name}-rawdata.mat"

    method = new_rawdata_setup.metadata["method"]
    isotime = new_rawdata_setup.metadata["isotime"]
    bpm_name = new_rawdata_setup.metadata["bpm_name"]
    filename_new = f"{method}-{isotime}-{bpm_name}-rawdata.mat"

    return os.path.join(dirpath_rawdata_old_file_format, filename_old), os.path.join(
        dirpath_rawdata_new_file_format, filename_new
    )


def test_new_raw_data_from_old_file_equals_new_raw_data_from_new_file(
    tmpdir, old_rawdata_setup, new_rawdata_setup
):
    """Load the new rawdata format from the both the old file format and the new
    file format and ensure that the loaded rawdata is identical."""

    filepath_old, filepath_new = sofb_save_old_and_new_data(
        tmpdir, old_rawdata_setup, new_rawdata_setup
    )

    new_rawdata_old_file_format = sofb_load_new_raw_data_from_old_file(filepath_old)
    new_rawdata_new_file_format = RawData.from_file(filepath_new)

    planes = ["x", "y"]
    quad_strengths = ["high", "low"]
    for corr_old, osc_plane_old in new_rawdata_old_file_format.rawdata.items():
        for corr_new, osc_plane_new in new_rawdata_new_file_format.rawdata.items():
            assert corr_old == corr_new
            for plane, quad_strength in zip(planes, quad_strengths, strict=True):
                data_old = getattr(getattr(osc_plane_old, plane), quad_strength)
                data_new = getattr(getattr(osc_plane_new, plane), quad_strength)
                np.testing.assert_array_equal(data_old, data_new)


def test_old_raw_data_from_old_file_equals_new_raw_data_from_new_file(
    tmpdir, old_rawdata_setup, new_rawdata_setup
):
    """Load the old matlab file format and the new matlab file format and ensure that
    the loaded rawdata is in a different format but contains the same values."""

    filepath_old, filepath_new = sofb_save_old_and_new_data(
        tmpdir, old_rawdata_setup, new_rawdata_setup
    )

    old_rawdata_old_file_format = sofb_load_old_raw_data_from_old_file(filepath_old)
    new_rawdata_new_file_format = RawData.from_file(filepath_new)

    planes = ["x", "y"]
    quad_strengths = ["high", "low"]
    for corr_old, data_old in old_rawdata_old_file_format.rawdata.items():
        corr_strength = int(corr_old[-1:])
        for (
            corr_new,
            osc_plane_new,
        ) in new_rawdata_new_file_format.rawdata.items():
            # The old data format stored the corr string differently
            assert corr_old != corr_new
            for plane, quad_strength in zip(planes, quad_strengths, strict=True):
                data_new = getattr(getattr(osc_plane_new, plane), quad_strength)
                # Assert arrays are not equal
                np.testing.assert_raises(
                    AssertionError, np.testing.assert_array_equal, data_new, data_old
                )
                # Assert old data is in new data
                np.testing.assert_array_equal(data_old, data_new[corr_strength - 1, :])
