

import unittest

import pml


class TestPML(unittest.TestCase):

    def test_effective_corrector(self):
        # Most effective BPM is 1
        corr_index, corr = pml.effective_corrector('SR01A-PC-Q1D-01', pml.X)
        self.assertEqual(corr_index, 11)
        corr_index, corr = pml.effective_corrector('SR24A-PC-Q1D-10', pml.X)
        self.assertEqual(corr_index, 162)
        bpm_index, bpm = pml.effective_corrector('SR07A-PC-Q1B-01', pml.X)
        self.assertEqual(bpm_index, 162)
        bpm_index, bpm = pml.effective_corrector('SR21A-PC-Q1D-01', pml.X)
        self.assertEqual(bpm_index, 141)

    def test_quad_to_bpm(self):
        bpm_index, bpm = pml.quad_to_bpm('SR01A-PC-Q1D-01')
        self.assertEqual(bpm_index, 1)
        corr_index, corr = pml.quad_to_bpm('SR07A-PC-Q1B-01')
        self.assertEqual(corr_index, 43)
        bpm_index, bpm = pml.quad_to_bpm('SR24A-PC-Q1D-10')
        self.assertEqual(bpm_index, 172)

if __name__ == '__main__':
    unittest.main()
