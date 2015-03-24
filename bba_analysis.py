
import sys
import StringIO; err = sys.stderr; sys.stderr = StringIO.StringIO()
import dls_packages; sys.stderr = err  # Suppress stderr
import numpy as np
import scipy.io as io
import matplotlib.pyplot as plt
import time


# BENCHMARKING
tic = time.time()


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


# Setup parameters, we should load these from file
raw_data = io.loadmat('/home/gr58/fast_bba.mat')

bpm = 1
freq = 8
bin_size = TICKS_PER_SECOND / freq

# Extract data from file and change units
q_low = raw_data['q_low'][1:] * 1E-3
q_high = raw_data['q_high'][1:] * 1E-3


# Extract the DC componenet of the orbit, and add it to the 8Hz excitation
q_high_dc = q_high.mean(0)
q_low_dc = q_low.mean(0)

if sys.argv[1:]:  # Use FFT when given any argument
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
fit = np.polynomial.polynomial.polyfit(q_high[:, bpm - 1], q_diff_good, 1)
p = np.array([1 / fit[1], -fit[0] / fit[1]]).T

# Check output
#plt.plot(q_diff[:, 0], q_diff); plt.show()
#plt.plot(q_diff_good[:, 0], q_diff_good); plt.show()
print p[:, 1].mean(), p[:, 1].std()

print 'Took', time.time() - tic, 'seconds'  # BENCHMARKING
