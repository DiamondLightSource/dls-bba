
import sys
import StringIO; err = sys.stderr; sys.stderr = StringIO.StringIO()
import dls_packages; sys.stderr = err  # Suppress stderr
import numpy as np
import scipy.io as io
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import argparse
import time
from fa import TICKS_PER_SECOND


DECIMATED = True


def extract_freq_fft(data, freq):
    index = freq - 2
    data_i = np.fft.rfft(data, axis=0)
    data_i_f = np.zeros(data_i.shape, 'complex')
    data_i_f[index] = data_i[index]
    return np.fft.irfft(data_i_f, axis=0)


def extract_freq_excite(data, freq):
    data_length = data.shape[0]
    num_oscs = 1.0 * data_length * freq / TICKS_PER_SECOND
    num_oscs = num_oscs * 10 if DECIMATED else num_oscs

    osc = np.exp(np.linspace(0, 2j*np.pi*num_oscs, data_length))
    osc = np.tile(osc, (data.shape[1], 1)).T
    data_es = np.mean(data * osc, 0)

    reverse_osc = np.exp(np.linspace(0, -2j*np.pi*num_oscs, data_length))
    reverse_osc = np.tile(reverse_osc, (data.shape[1], 1)).T
    # Force the phase to zero by using only the imaginary part of the mean
    return 2 * np.real(reverse_osc * 1j*np.imag(data_es))


def analyse(data, use_fft=False, plot_output=False):
    bpm = data['bpm'] - 1  # Zero Index
    enabled_bpms = np.equal(data['enabled_bpms'], 1)
    freq = TICKS_PER_SECOND / data['period']

    # Remove bad BPMs and change units to um
    q_low = data['low'][:, enabled_bpms] * 1E-3
    q_high = data['high'][:, enabled_bpms] * 1E-3

    # Extract the DC componenet of the orbit, and add it to the 8Hz excitation
    q_high_dc = q_high.mean(0)
    q_low_dc = q_low.mean(0)
    if use_fft:
        q_high_clean = np.add(extract_freq_fft(q_high - q_high_dc, freq), q_high_dc)
        q_low_clean = np.add(extract_freq_fft(q_low - q_low_dc, freq), q_low_dc)
    else:
        q_high_clean = np.add(extract_freq_excite(q_high - q_high_dc, freq), q_high_dc)
        q_low_clean = np.add(extract_freq_excite(q_low - q_low_dc, freq), q_low_dc)

    # Take the difference between fits
    q_diff = q_high_clean - q_low_clean
    good = q_diff.std(0) > q_diff.std(0).max()/2
    q_diff_good = q_diff[:, good]

    # Use a single fit operation, then transform with the straight line equation
    fit = np.polynomial.polynomial.polyfit(q_high_clean[:, bpm], q_diff_good, 1)
    p = np.array([1 / fit[1], -fit[0] / fit[1]]).T

    # Produce a large graph
    if plot_output:
        to_plot = [q_high_clean, q_low_clean, q_diff, q_diff_good, p]
        plot_labels = [
                'quad high clean', 'quad low clean,', 'quad diff,',
                'quad diff good,', 'fit coefficients']
        # Make a grid three wide and N high
        # Fill with 1D plot, image plot, and colourbar
        gs = GridSpec(
                len(to_plot) + 1, 3, width_ratios=(20,20,1),
                height_ratios=([1]*len(to_plot) + [3]))
        for i in range(len(to_plot)):
            plt.subplot(gs[i, 0]).plot(to_plot[i])
            plt.ylabel(plot_labels[i])
            im = plt.subplot(gs[i, 1]).imshow(
                    to_plot[i], aspect='auto', interpolation='nearest')
            plt.colorbar(im, cax=plt.subplot(gs[i, 2]))
        # Add a large 1D plot to show end result
        plt.subplot(gs[-1, :]).plot(q_high_clean[:, bpm], q_diff_good)
        plt.ylabel('BPM %d aginst BPMs' % bpm)
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        plt.show()

    return (p[:, 1].mean(), p[:, 1].std())


def parse_args():
    parser = argparse.ArgumentParser(description='Run BBA analysis')
    parser.add_argument('filename', type=str, help='path to data file')
    parser.add_argument(
            '-p', '--plot', dest='plot', action='store_true',
            default=False, help='plot BPM fit data')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    analyse(
            io.loadmat(args.filename, squeeze_me=True),
            plot_output=args.plot, use_fft=False)

