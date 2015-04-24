from pkg_resources import require
require('cothread')
require('fa-archiver')
require('scipy')
require('numpy')


import unittest

import pml


class TestPML(unittest.TestCase):

    def test_effective_corrector(self):
        quad_corr_map = {'SR01A-PC-Q1D-01': 11,
                         'SR24A-PC-Q1D-10': 113,
                         'SR07A-PC-Q1B-01': 162,
                         'SR21A-PC-Q1D-01': 141}  #? I got 141 from MML.
        for quad_pv, corr_id in quad_corr_map.iteritems():
            quad = pml.quad_from_pv(quad_pv)
            corr_index, corr = pml.effective_corrector(quad, pml.X)
            self.assertEqual(corr_index, corr_id)

    def test_quad_to_bpm(self):
        quad_bpm_map = {'SR01A-PC-Q1D-01': 1,
                        'SR07A-PC-Q1B-01': 43,
                        'SR24A-PC-Q1D-10': 172}

        for quad_pv, bpm_id in quad_bpm_map.iteritems():
            quad = pml.quad_from_pv(quad_pv)
            bpm_index, bpm = pml.quad_to_bpm(quad)
            self.assertEqual(bpm_index, bpm_id)


if __name__ == '__main__':
    unittest.main()
