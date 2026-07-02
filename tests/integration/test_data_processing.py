from unittest.mock import MagicMock

import numpy as np
from tests.conftest import TEST_DATA_DIR

from dls_bba.datatypes import RawData
from dls_bba.sbba import SlowBBA


def test_rawdata_produces_correct_fulldata():
    """Pass our rawdata into the analysis function and verify that the
    correct results are calculated."""

    # This raw data file was initially taken in 2024 using an old data format,
    # it was converted to the current data format for this test.
    rawdata_path = (
        TEST_DATA_DIR / "SlowBBA-20240820T140919-SR01C-DI-EBPM-01-rawdata.mat"
    )

    machine = MagicMock()
    sbba = SlowBBA(machine)
    rawdata = RawData.from_file(str(rawdata_path))
    full_results = sbba.analyse(rawdata)

    assert full_results.bpm_offsets["SR01C-DI-EBPM-01"]["x"].new_value == 0.998
    assert full_results.bpm_offsets["SR01C-DI-EBPM-01"]["y"].new_value == 1.0
    assert full_results.quad_results["SR01A-PC-Q1D-01"]["x"].mean_offset == np.float64(
        -0.0020373769667987817
    )
    assert full_results.quad_results["SR01A-PC-Q1D-01"]["y"].mean_offset == np.float64(
        -2.786686706569358e-13
    )
    assert full_results.metadata["plotting__SR01A-PC-Q1D-01__x"][
        "x"
    ].max() == np.float64(0.32420216027248705)
    assert full_results.metadata["plotting__SR01A-PC-Q1D-01__y"][
        "y"
    ].max() == np.float64(0.012995105223497755)
