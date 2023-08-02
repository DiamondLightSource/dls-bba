# import os

# import pytest

# from dls_bba.datatypes import CalculatedOffset, RawData, Results


# @pytest.fixture(scope="module")
# def rawdata_setup():
#     rawdata = {"rawdata_key": "rawdata_value"}
#     metadata = {
#         "method": "rawdata_method",
#         "isotime": "rawdata_isotime",
#         "bpm_name": "rawdata_bpm_name",
#     }
#     return RawData(rawdata, metadata)


# @pytest.fixture(scope="module")
# def results_without_offsets_setup():
#     results = {"data_x": [10, 1], "data_y": [5, 1]}
#     metadata = metadata = {
#         "method": "results_method",
#         "isotime": "results_isotime",
#         "bpm_name": "results_bpm_name",
#     }
#     plotting = {"plotting": "results_plotting"}
#     offsets = {
#         "BPM1": CalculatedOffset(1.0, 1.1, 1.2, 1.3),
#         "BPM2": CalculatedOffset(2.0, 2.1, 2.2, 2.3),
#     }
#     return Results(results, metadata, plotting, offsets)


# def test_rawdata_saving_is_valid(tmp_path, rawdata_setup):
#     rawdata = rawdata_setup
#     rawdata.save(tmp_path)
#     assert any(file.endswith("-rawdata.mat") for file in os.listdir(tmp_path))


# def test_rawdata_construction_from_file_is_valid(tmp_path, rawdata_setup):
#     rawdata = rawdata_setup
#     rawdata.save(tmp_path)

#     method = rawdata.metadata["method"]
#     isotime = rawdata.metadata["isotime"]
#     bpm_name = rawdata.metadata["bpm_name"]
#     filename = f"{method}-{isotime}-{bpm_name}-rawdata.mat"

#     loaded_rawdata = RawData.from_file(os.path.join(tmp_path, filename))

#     assert loaded_rawdata.rawdata == rawdata.rawdata
#     assert loaded_rawdata.metadata == rawdata.metadata


# def test_results_saving_is_valid(tmp_path, results_without_offsets_setup):
#     results = results_without_offsets_setup
#     results.save(tmp_path)
#     assert any(file.endswith("-results.mat") for file in os.listdir(tmp_path))


# def test_results_construction_from_file_is_valid(
#     tmp_path, results_without_offsets_setup
# ):
#     results = results_without_offsets_setup
#     results.save(tmp_path)

#     method = results.metadata["method"]
#     isotime = results.metadata["isotime"]
#     bpm_name = results.metadata["bpm_name"]
#     filename = f"{method}-{isotime}-{bpm_name}-results.mat"

#     loaded_results = Results.from_file(os.path.join(tmp_path, filename))

#     assert loaded_results.results["data_x"] == results.results["data_x"]
#     assert loaded_results.results["data_y"] == results.results["data_y"]
#     assert loaded_results.metadata == results.metadata
#     assert loaded_results.offsets == results.offsets
