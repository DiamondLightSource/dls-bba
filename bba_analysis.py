
import sys
import StringIO; err = sys.stderr; sys.stderr = StringIO.StringIO()
import dls_packages; sys.stderr = err  # Suppress stderr
import numpy as np
import scipy.io as io
import matplotlib.pyplot as plt
import time


TICKS_PER_SECOND = 10072


def extract_freq_fft(data, freq):
    index = freq - 2
    data_i = np.fft.rfft(data, axis=0)
    data_i_f = np.zeros(data_i.shape, 'complex')
    data_i_f[index] = data_i[index]
    return np.fft.irfft(data_i_f, axis=0)


def extract_freq_excite(data, freq):
    data_length = data.shape[0]
    num_oscs = data_length * freq / TICKS_PER_SECOND

    osc = np.exp(np.linspace(0, 2j*np.pi*num_oscs, data_length))
    osc = np.tile(osc, (data.shape[1], 1)).T
    data_es = np.mean(data * osc, 0)

    reverse_osc = np.exp(np.linspace(0, -2j*np.pi*num_oscs, data_length))
    reverse_osc = np.tile(reverse_osc, (data.shape[1], 1)).T
    return 2 * np.real(reverse_osc * data_es)


def analyse(data, use_fft=False, plot_output=False):
    bpm = data['bpm'] - 1  # Zero Index
    enabled_bpms = np.equal(data['enabled_bpms'], 0)  # Zero is enabled
    freq = TICKS_PER_SECOND / data['period']
    bin_size = TICKS_PER_SECOND / freq

    # Remove bad BPMs and change units to um
    q_low = data['low'][:, enabled_bpms] * 1E-3
    q_high = data['high'][:, enabled_bpms] * 1E-3

    # Extract the DC componenet of the orbit, and add it to the 8Hz excitation
    q_high_dc = q_high.mean(0)
    q_low_dc = q_low.mean(0)
    if use_fft:
        q_high_clean = np.add(extract_freq_fft(q_high, freq), q_high_dc)
        q_low_clean = np.add(extract_freq_fft(q_low, freq), q_low_dc)
    else:
        q_high_clean = np.add(extract_freq_excite(q_high, freq), q_high_dc)
        q_low_clean = np.add(extract_freq_excite(q_low, freq), q_low_dc)

    # Take the difference between fits
    q_diff = q_high_clean - q_low_clean
    good = q_diff.std(0) > q_diff.std(0).max()/2
    q_diff_good = q_diff[:, good]

    # Use a single fit operation, then transform with the straight line equation
    fit = np.polynomial.polynomial.polyfit(q_high[:, bpm], q_diff_good, 1)
    p = np.array([1 / fit[1], -fit[0] / fit[1]]).T

    # Check output
    if plot_output:
        plt.plot(q_diff_good[:, 0], q_diff_good);
        plt.show()

    return (p[:, 1].mean(), p[:, 1].std())


if __name__ == '__main__':
    tic = time.time()  # BENCHMARKING
    print analyse(io.loadmat('data/gr_data.mat', squeeze_me=True))
    print 'Took', time.time() - tic, 'seconds'  # BENCHMARKING

