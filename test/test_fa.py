import pkg_resources
pkg_resources.require('numpy')
pkg_resources.require('scipy')
pkg_resources.require('cothread')
pkg_resources.require('fa-archiver')
import numpy
import unittest
import fa


class FaBufferTest(unittest.TestCase):
    '''
    These are not unit tests since they interact with the real FA server.
    '''
    def test_Buffer_collects_1000_pts(self):
        b = fa.Buffer([1], 1000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (1000,1,2))

    def test_Buffer_collects_10000_pts(self):
        b = fa.Buffer([1], 10000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (10000,1,2))

    @unittest.skip('Takes too long.')
    def test_Buffer_collects_100000_pts(self):
        '''
        This test takes 10 seconds.
        '''
        b = fa.Buffer([1], 100000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (100000,1,2))

    #@unittest.skip('Takes too long.')
    def test_Buffer_collects_30000_pts_for_all_BPMs(self):
        '''
        This test takes 3 seconds.
        '''
        b = fa.Buffer(range(1,174), 50000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (30000,173,2))

    def test_Buffer_collects_10000_pts_for_all_BPMs(self):
        b = fa.Buffer(range(1,174), 10000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (10000,173,2))

    def test_Buffer_collects_timestamps(self):
        b = fa.Buffer([0,1], 1000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (1000,2,2))
        timecounts = d[:,0,0] - d[0,0,0]
        numpy.testing.assert_array_equal(timecounts, numpy.arange(1000))

if __name__ == '__main__':
    unittest.main()
