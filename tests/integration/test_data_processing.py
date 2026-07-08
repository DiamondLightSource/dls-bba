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

    # This raw data file was initially taken in 2024 using an old data format,
    # it was converted to the current data format for this test.
    rawdata_path = (
        TEST_DATA_DIR / "FastBBA-20230726T012011-SR01C-DI-EBPM-05-rawdata.mat"
    )

    machine = MagicMock()
    fbba = FastBBA(machine)
    rawdata = RawData.from_file(str(rawdata_path))
    full_results = fbba.analyse(rawdata)

    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q2AB-07"]["x"].mean_offset,
        -0.034,
        significant=2,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q2AB-07"]["x"].std_dev_offset,
        0.0022,
        significant=2,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q2AB-07"]["y"].mean_offset,
        0.0273,
        significant=3,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q2AB-07"]["y"].std_dev_offset,
        0.00049759,
        significant=5,
    )


def test_simfbba_rawdata_produces_correct_fulldata():
    """Pass rawdata from a matlab file into the simfbba analysis function and verify
    that the correct results are calculated."""

    # This raw data file was initially taken in 2024 using an old data format,
    # it was converted to the current data format for this test.
    rawdata_path = (
        TEST_DATA_DIR / "SimFastBBA-20230726T005414-SR01C-DI-EBPM-05-rawdata.mat"
    )

    machine = MagicMock()
    fbba = SimFastBBA(machine)
    rawdata = RawData.from_file(str(rawdata_path))
    full_results = fbba.analyse(rawdata)

    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q2AB-07"]["x"].mean_offset,
        -0.1677,
        significant=4,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q2AB-07"]["x"].std_dev_offset,
        0.0098,
        significant=2,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q2AB-07"]["y"].mean_offset,
        -0.2415,
        significant=4,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q2AB-07"]["y"].std_dev_offset,
        0.0019,
        significant=2,
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
        full_results.quad_results["SR01A-PC-Q1D-01"]["x"].mean_offset,
        -0.002037,
        significant=4,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q1D-01"]["x"].std_dev_offset,
        0.0005196,
        significant=4,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q1D-01"]["y"].mean_offset,
        -2.786e-13,
        significant=4,
    )
    assert_approx_equal(
        full_results.quad_results["SR01A-PC-Q1D-01"]["y"].std_dev_offset,
        1.899e-13,
        significant=4,
    )
