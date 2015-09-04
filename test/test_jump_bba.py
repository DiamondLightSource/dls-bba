import pkg_resources
pkg_resources.require('numpy')
pkg_resources.require('scipy')
pkg_resources.require('cothread')
pkg_resources.require('mock')
pkg_resources.require('aphla')
pkg_resources.require('fa-archiver')
import numpy
import unittest
import jump_bba
import pml
import mock

class SelectDataTest(unittest.TestCase):

    def setUp(self):
        self.data = numpy.zeros((2000,2,2))
        self.data[:,0,0] = numpy.arange(2000)
        self.data[:,0,1] = numpy.arange(2000)
        self.data[100,1,0] = 3
        self.data[1100,1,1] = 4
        self.exc_high = mock.MagicMock(count=1000, time=100)
        self.exc_low = mock.MagicMock(count=1000, time=1100)

    def test_select_data_throws_AssertionError_if_exc_high_low_different_counts(self):
        self.exc_low.count = 101
        self.assertRaises(AssertionError, jump_bba.select_data, self.data,
                          pml.X, self.exc_high, self.exc_low)

    def test_select_data_returns_correct_shape(self):
        high_data, low_data = jump_bba.select_data(self.data, pml.X,
                                                   self.exc_high, self.exc_low)
        expected_shape = (100, 1)
        self.assertEqual(high_data.shape, expected_shape)
        self.assertEqual(low_data.shape, expected_shape)

    def test_select_data_selects_first_timestamp(self):
        high_data_x, _ = jump_bba.select_data(self.data, pml.X,
                                                   self.exc_high, self.exc_low)
        _, low_data_y = jump_bba.select_data(self.data, pml.Y,
                                                   self.exc_high, self.exc_low)
        self.assertEqual(high_data_x[0,0], 3)
        self.assertEqual(low_data_y[0,0], 4)


if __name__ == '__main__':
    unittest.main()
