
import numpy as np

def analyse(data):
    # Rearranging data
    bpm = data['bpm'] - 1    # Zero Index
    enabled_bpms = np.equal(data['enabled_bpms'], 1)
    q_low = data['low'][:, enabled_bpms] * 1E-3
    q_high = data['high'][:, enabled_bpms] * 1E-3
    # Actual calculation
    q_diff = q_high - q_low
    fit = np.polynomial.polynomial.polyfit(q_high[:, bpm], q_diff, 1)
    p = np.array(-fit[0] / fit[1]).T
    return (p.mean(), p.std())


