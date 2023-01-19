import numpy as np


def analyse(data):
    # Rearranging data
    bpm = data["bpm"] - 1  # Zero Index
    enabled_bpms = np.equal(data["enabled_bpms"], 1)
    # We're removing disabled bpms so we need to shift the index.
    bpm_index = bpm - np.sum(enabled_bpms[:bpm] == False)  # noqa false positive
    q_low = data["low"][:, enabled_bpms] * 1e-3
    q_high = data["high"][:, enabled_bpms] * 1e-3
    # Actual calculation
    q_diff = q_high - q_low
    fit = np.polynomial.polynomial.polyfit(q_high[:, bpm_index], q_diff, 1)
    intersections = np.array(-fit[0] / fit[1])
    return intersections.mean()
