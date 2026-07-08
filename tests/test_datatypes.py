import os

import numpy as np
import pytest

from dls_bba.datatypes import (
    BPMOffset,
    FullResults,
    OscillationPlane,
    QuadResults,
    QuadStrength,
    RawData,
)


@pytest.fixture(scope="module")
def rawdata_setup():
    num_bpms = 5
    rawdata = {
        "SR01A-PC-Q1D-01": OscillationPlane(
            QuadStrength(np.zeros(num_bpms), np.zeros(num_bpms)),
            QuadStrength(np.zeros(num_bpms), np.zeros(num_bpms)),
        )
    }
    metadata = {
        "method": "rawdata_method",
        "isotime": "rawdata_isotime",
        "bpm_name": "rawdata_bpm_name",
    }
    return RawData(rawdata, metadata)


@pytest.fixture(scope="module")
def results_setup():
    results = {"data": OscillationPlane(QuadResults(1.5, 1.6), QuadResults(1.5, 1.6))}
    metadata = metadata = {
        "method": "results_method",
        "isotime": "results_isotime",
        "bpm_name": "results_bpm_name",
    }
    offsets = {
        "BPM1": OscillationPlane(
            BPMOffset(1.0, 1.1, 1.2, 1.3), BPMOffset(1.0, 1.1, 1.2, 1.3)
        ),
        "BPM2": OscillationPlane(
            BPMOffset(2.0, 2.1, 2.2, 2.3), BPMOffset(2.0, 2.1, 2.2, 2.3)
        ),
    }
    return FullResults(results, metadata, offsets)


def test_rawdata_saving_is_valid(tmp_path, rawdata_setup):
    rawdata = rawdata_setup
    rawdata.save(tmp_path)
    assert any(file.endswith("-rawdata.mat") for file in os.listdir(tmp_path))


def test_rawdata_construction_from_file_gives_correct_data(tmp_path, rawdata_setup):
    rawdata = rawdata_setup
    rawdata.save(tmp_path)

    method = rawdata.metadata["method"]
    isotime = rawdata.metadata["isotime"]
    bpm_name = rawdata.metadata["bpm_name"]
    filename = f"{method}-{isotime}-{bpm_name}-rawdata.mat"
    loaded_rawdata = RawData.from_file(os.path.join(tmp_path, filename))

    assert loaded_rawdata.metadata == rawdata.metadata

    planes = ["x", "y"]
    quad_strengths = ["high", "low"]
    for osc_plane_ref in rawdata.rawdata.values():
        for osc_plane_loaded in loaded_rawdata.rawdata.values():
            for plane, quad_strength in zip(planes, quad_strengths, strict=True):
                ref_data = getattr(getattr(osc_plane_ref, plane), quad_strength)
                loaded_data = getattr(getattr(osc_plane_loaded, plane), quad_strength)
                np.testing.assert_array_equal(ref_data, loaded_data)


def test_results_saving_is_valid(tmp_path, results_setup):
    results = results_setup
    results.save(tmp_path)
    assert any(file.endswith("-results.mat") for file in os.listdir(tmp_path))


def test_results_construction_from_file_gives_correct_data(tmp_path, results_setup):
    results = results_setup
    results.save(tmp_path)

    method = results.metadata["method"]
    isotime = results.metadata["isotime"]
    bpm_name = results.metadata["bpm_name"]
    filename = f"{method}-{isotime}-{bpm_name}-results.mat"

    loaded_results = FullResults.from_file(os.path.join(tmp_path, filename))

    assert loaded_results.quad_results["data"] == results.quad_results["data"]
    assert loaded_results.metadata == results.metadata
    assert loaded_results.bpm_offsets == results.bpm_offsets
