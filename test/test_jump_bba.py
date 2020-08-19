import unittest

import mock
import numpy
import pytac
import pytest

from bba import jump_bba, pml


@pytest.fixture
def lattice():
    return pytac.load_csv.load("DIAD")


class SelectDataTest(unittest.TestCase):
    def setUp(self):
        self.data = numpy.zeros((2000, 2, 2))
        self.data[:, 0, 0] = numpy.arange(2000)
        self.data[:, 0, 1] = numpy.arange(2000)
        self.data[100, 1, 0] = 3
        self.data[1100, 1, 1] = 4
        self.exc_high = mock.MagicMock(count=1000, start_time=100)
        self.exc_low = mock.MagicMock(count=1000, start_time=1100)

    def test_select_data_throws_AssertionError_if_exc_high_low_different_counts(self):
        self.exc_low.count = 101
        self.assertRaises(
            AssertionError,
            jump_bba.select_data,
            self.data,
            pml.X,
            self.exc_high,
            self.exc_low,
        )

    def test_select_data_returns_correct_shape(self):
        high_data, low_data = jump_bba.select_data(
            self.data, pml.X, self.exc_high, self.exc_low
        )
        expected_shape = (100, 1)
        self.assertEqual(high_data.shape, expected_shape)
        self.assertEqual(low_data.shape, expected_shape)

    def test_select_data_selects_first_timestamp(self):
        high_data_x, _ = jump_bba.select_data(
            self.data, pml.X, self.exc_high, self.exc_low
        )
        _, low_data_y = jump_bba.select_data(
            self.data, pml.Y, self.exc_high, self.exc_low
        )
        self.assertEqual(high_data_x[0, 0], 3)
        self.assertEqual(low_data_y[0, 0], 4)


@mock.patch("bba.pml.excite.caput")
@mock.patch("bba.jump_bba.caget")
@mock.patch("bba.jump_bba.caput")
def test_jump_bba_sets_expected_pvs(jump_caput, jump_caget, excite_caput, lattice):
    jump_caget.return_value = 10
    quad = lattice.get_elements("QUAD")[0]
    print(quad.get_device("b1"))
    # one 1Hz cycle
    osc = pml.excite.Oscillation(1, 0, 1, 1)
    jump_bba.jump_bba(quad, 1, osc, lattice)

    jump_caput.assert_has_calls(
        [
            mock.call("SR01A-PC-Q1D-01:SETI", 10.5),
            mock.call("SR01A-PC-Q1D-01:SETI", 9.5),
            mock.call("SR01A-PC-Q1D-01:SETI", 10),
        ]
    )

    # Note you can assert excite_caput's calls to be [] and it will tell
    # what they actually were.
