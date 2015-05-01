from pkg_resources import require
require('cothread')
require('fa-archiver')
require('scipy')
require('numpy')


import unittest

import pml


class TestPML(unittest.TestCase):

    def test_effective_corrector(self):
        # The correct answers were fetched from MML.
        quad_corr_map = [{'SR24A-PC-Q1D-10': 113,
                          'SR07A-PC-Q1B-01': 162,
                          'SR21A-PC-Q1D-01': 141},
                         {'SR21A-PC-Q1D-01': 30,
                          'SR13A-PC-Q1D-01': 101,
                          'SR24A-PC-Q1D-10': 115}]
        for plane in (pml.X, pml.Y):
            for quad_pv, corr_id in quad_corr_map[plane].iteritems():
                quad = pml.quad_from_pv(quad_pv)
                corr_index, corr = pml.effective_corrector(quad, plane)
                self.assertEqual(corr_index, corr_id)

    def test_quad_to_bpm(self):
        # The correct answers were fetched from MML.
        quad_bpm_map = {'SR01A-PC-Q1D-01': 1,
                        'SR20A-PC-Q1D-10': 145,
                        'SR24A-PC-Q1D-10': 173}

        for quad_pv, bpm_id in quad_bpm_map.iteritems():
            quad = pml.quad_from_pv(quad_pv)
            bpm_index, bpm = pml.quad_to_bpm(quad)
            self.assertEqual(bpm_index, bpm_id)

    def test_prefix_from_pv_handles_prefix(self):
        prefix = 'DUMMY'
        self.assertEqual(prefix, pml.prefix_from_pv(prefix))

    def test_prefix_from_pv_handles_pv(self):
        pv = 'DUMMY:SOMETHING'
        expected = 'DUMMY'
        self.assertEqual(expected, pml.prefix_from_pv(pv))

if __name__ == '__main__':
    unittest.main()
