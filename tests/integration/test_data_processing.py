from unittest.mock import MagicMock

from numpy.testing import assert_approx_equal

from conftest import TEST_DATA_DIR
from dls_bba.datatypes import RawData
from dls_bba.fbba import FastBBA
from dls_bba.sbba import SlowBBA
from dls_bba.simfbba import SimFastBBA


def test_fbba_rawdata_produces_correct_fulldata():
    """Pass rawdata from a matlab file into the fbba analysis function and verify
    that the correct results are calculated."""

    # This raw data file was initially taken in 2023 using an old data format,
    # it was converted to the current data format for this test.
    rawdata_path = (
        TEST_DATA_DIR / "FastBBA-20230726T012011-SR01C-DI-EBPM-05-rawdata.mat"
    )

    machine = MagicMock()
    fbba = FastBBA(machine)
    rawdata = RawData.from_file(str(rawdata_path))
    full_results = fbba.analyse(rawdata)

    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-05"]["x"].diff_value, -0.0339
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-05"]["x"].diff_error, -0.0022
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-05"]["y"].diff_value, 0.0272
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-05"]["y"].diff_error, 0.0005
    )


def test_simfbba_rawdata_produces_correct_fulldata():
    """Pass rawdata from a matlab file into the simfbba analysis function and verify
    that the correct results are calculated."""

    # This raw data file was initially taken in 2023 using an old data format,
    # it was converted to the current data format for this test.
    rawdata_path = (
        TEST_DATA_DIR / "SimFastBBA-20230726T005414-SR01C-DI-EBPM-05-rawdata.mat"
    )

    machine = MagicMock()
    fbba = SimFastBBA(machine)
    rawdata = RawData.from_file(str(rawdata_path))
    full_results = fbba.analyse(rawdata)

    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-05"]["x"].diff_value, -0.1681
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-05"]["x"].diff_error, -0.0097
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-05"]["y"].diff_value, -0.2416
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-05"]["y"].diff_error, -0.002
    )


def test_sbba_rawdata_produces_correct_fulldata():
    """Pass rawdata from a matlab file into the sbba analysis function and verify
    that the correct results are calculated."""

    # This raw data file was initially taken in 2024 using an old data format,
    # it was converted to the current data format for this test.
    rawdata_path = (
        TEST_DATA_DIR / "SlowBBA-20240820T140919-SR01C-DI-EBPM-01-rawdata.mat"
    )

    machine = MagicMock()
    sbba = SlowBBA(machine)
    rawdata = RawData.from_file(str(rawdata_path))
    full_results = sbba.analyse(rawdata)

    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-01"]["x"].diff_value, -0.002
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-01"]["x"].diff_error, -0.0005
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-01"]["y"].diff_value, -0.0
    )
    assert_approx_equal(
        full_results.bpm_offsets["SR01C-DI-EBPM-01"]["y"].diff_error, -0.0
    )
