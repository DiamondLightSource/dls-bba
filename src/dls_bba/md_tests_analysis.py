"""MD Tests analysis."""

import argparse
import os
from statistics import mean, stdev

import matplotlib.pyplot as plt
import numpy as np

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "28Feb2023")


def parse_args():
    parser = argparse.ArgumentParser(description="testing")
    parser.add_argument(
        "-j",
        "--honing",
        dest="honing_test",
        action="store_true",
        default=False,
        help="honing complex test",
    )
    parser.add_argument(
        "-f",
        "--freq",
        dest="freq_test",
        action="store_true",
        default=False,
        help="freq test",
    )
    return parser.parse_args()


initial = {"x": 0.7890, "y": 0.4230}
initial_offset = {"x": 0.8890, "y": 0.5230}


def bba_stats(values, spread=3):
    spread_mean = str(np.round(mean(values[spread:]) * 1000, 1))
    spread_stdev = str(np.round(stdev(values[spread:]) * 1000, 1))
    pm = r"$\pm$"
    um = r"$\mu$m"
    stats = f"{spread_mean} {pm} {spread_stdev} {um}"
    return stats


def main():
    args = parse_args()
    honing_test = args.honing_test
    freq_tests = args.freq_test

    if honing_test:
        honing()

    if freq_tests:
        frequency()


def honing():
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    repeats = 20
    x = np.arange(0, repeats)

    data = {}

    for offset in [0, 0.1]:
        for axis in ["x", "y"]:
            d = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/SIM_honing_r{repeats}_qs{quadrupole_scalar}_cs{corrector_scalar}_offset{offset}_{axis}.csv",
                delimiter=",",
            )
            data[f"{offset},{axis}"] = [d[0, :], d[1, :]]

    for key, (values, errors) in data.items():
        offset, axis = key.split(",")
        if offset == 0:
            init = initial[axis]
        else:
            init = initial_offset[axis]
        cum_values = np.cumsum(values)
        y_values = [init] + [value + init for value in cum_values]
        y_errors = [0] + [e for e in errors]
        data[key] = [y_values, y_errors]

    for axis in ["x", "y"]:
        for key, (values, errors) in data.items():
            if axis in key:
                plt.errorbar(
                    x,
                    values,
                    errors,
                    marker=".",
                    capsize=5,
                    label=f"{key}: {bba_stats(values)}",
                )
        plt.ylabel("Offset Value (mm)")
        plt.xlabel("Run Number")
        plt.xlim(0, repeats)
        plt.grid(which="major", axis="both")
        plt.legend(fontsize="xx-small")
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/sim_honing_{axis}_plot.png",
            bbox_inches="tight",
            dpi=300,
        )
        plt.close()


def frequency():
    frequency1 = [11, 13, 137, 179]  # X
    frequency2 = [13, 41, 139, 181]  # Y
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    repeats = 20
    max_time = 2
    x = np.arange(0, repeats)
    data = {}

    for freq1 in frequency1:
        for freq2 in frequency2:
            for axis in ["x", "y"]:
                cycles1 = int(np.floor(max_time * freq1))
                cycles2 = int(np.floor(max_time * freq2))
                d = np.genfromtxt(
                    f"{TEMP_FILEPATH_ROOT}/SIM_freq_r{repeats}_f{freq1}_{freq2}_c{cycles1}_{cycles2}_qs{quadrupole_scalar}_cs{corrector_scalar}_{axis}.csv",
                    delimiter=",",
                )
                data[f"{freq1},{freq2}_{axis}"] = [d[0, :], d[1, :]]

    for key, (values, errors) in data.items():
        init = initial_offset[key[-1]]
        cum_values = np.cumsum(values)
        y_values = [init] + [value + init for value in cum_values]
        y_errors = [0] + [e for e in errors]
        data[key] = [y_values, y_errors]

    for axis in ["x", "y"]:
        fig, axs = plt.subplots(
            ncols=len(frequency1),
            nrows=len(frequency2),
            sharex=True,
            sharey=True,
            layout="constrained",
        )

        for row, freq1 in enumerate(frequency1):
            for col, freq2 in enumerate(frequency2):
                values, errors = data[f"{freq1},{freq2}_{axis}"]
                axs[row, col].errorbar(x, values, errors, label=f"{bba_stats(values)}")
                axs[row, col].legend(fontsize="xx-small", loc=1)
                axs[row, col].grid(which="both", axis="both")
                axs[row, col].set_xlim(0, len(values))
                if row == len(frequency1) - 1:
                    plt.setp(axs[row, col], xlabel=f"{freq2}")
                if col == 0:
                    plt.setp(axs[row, col], ylabel=f"{freq1}")
        fig.suptitle(f"Time of measurement and Frequency with 100micron offset {axis}")
        fig.supxlabel("Y Frequency (Hz)")
        fig.supylabel("X Frequency (Hz)")
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/sim_frequency_time_plot_{axis}.png",
            bbox_inches="tight",
            dpi=300,
        )
        plt.close()


if __name__ == "__main__":
    main()
