import os
from dataclasses import asdict

from dls_bba.datatypes import CalculatedOffset, RawData, Results

TEST_RAWDATA = {"DATA_1": [1, 2, 3], "DATA_2": "TEST_DATA"}
TEST_METADATA = {
    "method": "TEST_METHOD",
    "isotime": "TEST_ISOTIME",
    "bpm_name": "TEST_BPM_NAME",
}
TEST_CALC_OFFSETS = [1, 2, 3, 4]
TEST_RESULTS = {"DATA_1": [0, 1, 2, 3, 4, 5, 6], "DATA_2": [1, 2, 3, 4, 5, 6, 7]}
TEST_PLOTTING = {
    "DATA_1": {"x": [1, 2, 3], "y": [6, 5, 4]},
    "DATA_2": {"x": [9, 8, 7], "y": [4, 5, 6]},
}
TEST_OFFSETS = {
    "DATA_1": CalculatedOffset(1, 2, 3, 4),
    "DATA_2": CalculatedOffset(9, 8, 7, 6),
}


def test_RawData_object_contains_expected_attributes():
    rawdata_object = RawData(TEST_RAWDATA, TEST_METADATA)
    assert isinstance(rawdata_object, RawData)
    assert isinstance(rawdata_object.rawdata, dict)
    assert isinstance(rawdata_object.metadata, dict)


def test_RawData_object_can_be_saved(tmp_path):
    rawdata_object = RawData(TEST_RAWDATA, TEST_METADATA)
    rawdata_object.save(tmp_path)

    method = TEST_METADATA["method"]
    isotime = TEST_METADATA["isotime"]
    bpm_name = TEST_METADATA["bpm_name"]
    filename = f"{method}-{isotime}-{bpm_name}-rawdata.mat"
    assert os.path.isfile(os.path.join(tmp_path, filename))


def test_RawData_object_can_be_loaded_from_saved_object(tmp_path):
    rawdata_object = RawData(TEST_RAWDATA, TEST_METADATA)
    rawdata_object.save(tmp_path)

    method = TEST_METADATA["method"]
    isotime = TEST_METADATA["isotime"]
    bpm_name = TEST_METADATA["bpm_name"]
    filename = f"{method}-{isotime}-{bpm_name}-rawdata.mat"
    rawdata_object_2 = RawData.from_file(os.path.join(tmp_path, filename))

    assert all(rawdata_object.rawdata["DATA_1"] == rawdata_object_2.rawdata["DATA_1"])
    assert rawdata_object.rawdata["DATA_2"] == rawdata_object_2.rawdata["DATA_2"]
    assert rawdata_object.metadata["method"] == rawdata_object_2.metadata["method"]
    assert rawdata_object.metadata["isotime"] == rawdata_object_2.metadata["isotime"]
    assert rawdata_object.metadata["bpm_name"] == rawdata_object_2.metadata["bpm_name"]


def test_CalculatedOffsets_has_expected_attributes():
    a, b, c, d = TEST_CALC_OFFSETS
    calc_offset = CalculatedOffset(a, b, c, d)
    assert calc_offset.old_value == a
    assert calc_offset.new_value == b
    assert calc_offset.diff_value == c
    assert calc_offset.diff_error == d


def test_CalculatedOffsets_convert_to_dict_is_valid():
    a, b, c, d = TEST_CALC_OFFSETS
    calc_offset = CalculatedOffset(a, b, c, d)
    calc_offset_dict = asdict(calc_offset)
    assert calc_offset_dict["old_value"] == a
    assert calc_offset_dict["new_value"] == b
    assert calc_offset_dict["diff_value"] == c
    assert calc_offset_dict["diff_error"] == d


def test_CalculatedOffsets_convert_from_dict_is_valid():
    a, b, c, d = TEST_CALC_OFFSETS
    calc_offset = CalculatedOffset(a, b, c, d)
    calc_offset_dict = asdict(calc_offset)
    calc_offset_2 = CalculatedOffset(**calc_offset_dict)
    assert calc_offset.old_value == calc_offset_2.old_value
    assert calc_offset.new_value == calc_offset_2.new_value
    assert calc_offset.diff_value == calc_offset_2.diff_value
    assert calc_offset.diff_error == calc_offset_2.diff_error


def test_Results_object_contains_expected_attributes():
    results_object = Results(TEST_RESULTS, TEST_METADATA, TEST_PLOTTING, TEST_OFFSETS)
    assert isinstance(results_object, Results)
    assert isinstance(results_object.results, dict)
    assert isinstance(results_object.metadata, dict)
    assert isinstance(results_object.plotting, dict)
    assert isinstance(results_object.offsets, dict)


def test_Results_object_can_be_saved(tmp_path):
    results_object = Results(TEST_RESULTS, TEST_METADATA, TEST_PLOTTING, TEST_OFFSETS)
    results_object.save(tmp_path)

    method = TEST_METADATA["method"]
    isotime = TEST_METADATA["isotime"]
    bpm_name = TEST_METADATA["bpm_name"]
    filename = f"{method}-{isotime}-{bpm_name}-results.mat"
    assert os.path.isfile(os.path.join(tmp_path, filename))


def test_Results_object_can_be_loaded_from_saved_object(tmp_path):
    results_object = Results(TEST_RESULTS, TEST_METADATA, TEST_PLOTTING, TEST_OFFSETS)
    results_object.save(tmp_path)

    method = TEST_METADATA["method"]
    isotime = TEST_METADATA["isotime"]
    bpm_name = TEST_METADATA["bpm_name"]
    filename = f"{method}-{isotime}-{bpm_name}-results.mat"
    results_object_2 = Results.from_file(os.path.join(tmp_path, filename))

    assert results_object.results["DATA_1"] == results_object_2.results["DATA_1"]
    assert results_object.results["DATA_2"] == results_object_2.results["DATA_2"]
    assert results_object.metadata["method"] == results_object_2.metadata["method"]
    assert results_object.metadata["isotime"] == results_object_2.metadata["isotime"]
    assert results_object.metadata["bpm_name"] == results_object_2.metadata["bpm_name"]
    rp = results_object.plotting
    r2p = results_object_2.plotting
    assert all(rp["DATA_1"]["x"] == r2p["DATA_1"]["x"])
    assert all(rp["DATA_1"]["y"] == r2p["DATA_1"]["y"])
    assert all(rp["DATA_2"]["x"] == r2p["DATA_2"]["x"])
    assert all(rp["DATA_2"]["y"] == r2p["DATA_2"]["y"])
    assert results_object.offsets["DATA_1"] == results_object_2.offsets["DATA_1"]
    assert results_object.offsets["DATA_2"] == results_object_2.offsets["DATA_2"]
