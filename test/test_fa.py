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
    def setUp(self):
        self.now = fa.get_timestamp()

    def test_Buffer_collects_1000_pts(self):
        b = fa.Buffer([1], self.now + 1000, 1000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (1000,1,2))

    def test_Buffer_collects_1000_pts_decimated(self):
        b = fa.Buffer([1], self.now + 1000, 10000, True)
        d = b.get_data()
        self.assertEqual(d.shape, (1000,1,2))

    def test_Buffer_collects_10000_pts(self):
        b = fa.Buffer([1], self.now + 1000, 10000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (10000,1,2))

    @unittest.skip('Takes too long.')
    def test_Buffer_collects_100000_pts(self):
        '''
        This test takes 10 seconds.
        '''
        b = fa.Buffer([1], self.now + 1000, 100000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (100000,1,2))

    def test_Buffer_collects_30000_pts_for_all_BPMs(self):
        '''
        This test takes 3 seconds.
        '''
        b = fa.Buffer(range(1,174), self.now + 1000, 30000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (30000,173,2))

    def test_Buffer_collects_10000_pts_for_all_BPMs(self):
        b = fa.Buffer(range(1,174), self.now + 1000, 10000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (10000,173,2))

    def test_Buffer_collects_timestamps(self):
        b = fa.Buffer([0,1], self.now + 1000, 1000, False)
        d = b.get_data()
        self.assertEqual(d.shape, (1000,2,2))
        # The first timestamp should be the one requested.
        self.assertEqual(self.now + 1000, d[0,0,0])
        # The timestamps should be sequential starting from the first
        timecounts = d[:,0,0] - d[0,0,0]
        numpy.testing.assert_array_equal(timecounts, numpy.arange(1000))

    def test_Buffer_collects_timestamps_decimated(self):
        start_time = self.now + 1000
        log.debug('Requesting a start time of %s', start_time)
        b = fa.Buffer([0,1], start_time, 1000, True)
        d = b.get_data()
        self.assertEqual(d.shape, (100,2,2))
        # The first timestamp should be less than 10 ticks greater than the
        # one requested.
        self.assertIn(d[0,0,0] - start_time, range(10))
        # The timestamps should be sequential in steps of 10
        # starting from the first
        timecounts = d[:,0,0] - d[0,0,0]
        numpy.testing.assert_array_equal(timecounts, numpy.arange(0, 1000, 10))

if __name__ == '__main__':
    unittest.main()
