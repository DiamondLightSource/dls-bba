"""MD Tests analysis."""

import argparse
import os
from statistics import mean, stdev

import matplotlib.pyplot as plt
import numpy as np

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "24Jan2023")


def parse_args():
    parser = argparse.ArgumentParser(description="testing")
    parser.add_argument(
        "-c",
        "--cycle",
        dest="cycle",
        action="store_true",
        default=False,
        help="Cycle test",
    )
    parser.add_argument(
        "-f",
        "--freq",
        dest="freq",
        action="store_true",
        default=False,
        help="Freq test",
    )
    parser.add_argument(
        "-q",
        "--quads",
        dest="quads_amp_test",
        action="store_true",
        default=False,
        help="Quad test",
    )
    parser.add_argument(
        "-k",
        "--corrector",
        dest="corr_amp_test",
        action="store_true",
        default=False,
        help="Corrector test",
    )
    parser.add_argument(
        "-j",
        "--honing",
        dest="honing_test",
        action="store_true",
        default=False,
        help="honing complex test",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    # cycle_test = args.cycle
    freq_test = args.freq
    corr_test = args.corr_amp_test
    # quad_test = args.quad_amp_test
    honing_test = args.honing_test

    # if cycle_test:
    #     repeats = 20
    #     cycle_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    #     data = np.genfromtxt(f"cycle_scan_repeats_{repeats}_len_{len(cycle_list)}.csv", delimiter=",")
    #     y = []
    #     y_err = []
    #     for index, cycle in enumerate(cycle_list):
    #         value_list = data[(index*2), :]
    #         y.append(mean(value_list))
    #         y_err.append(stdev(value_list))
    #     plt.errorbar(cycle_list, y, y_err, marker = ".", capsize=5)
    #     # plt.hlines(y= , xmin=0, xmax=(max(cycle_list) + 1), color="r", linestyles="-")
    #     plt.title(f"Cycles Test - {repeats} Repeats")
    #     plt.xlim(0, max(cycle_list) + 1)
    #     plt.xlabel("Cycles")
    #     plt.ylabel("Offset Value")
    #     plt.grid(which = "both", axis = "both")
    #     plt.savefig(f"cycle_scan_repeats_{repeats}_len_{len(cycle_list)}_plot.png", bbox_inches="tight", dpi=1200)
    #     plt.show()

    if freq_test:
        repeats = 10
        MAX_TIME = 2  # 2 seconds
        frequency_list = [int(num) for num in range(0, 251)]

        data = np.genfromtxt(
            f"{TEMP_FILEPATH_ROOT}/frequency_scan_repeats_{repeats}_{MAX_TIME}_len_{len(frequency_list)}.csv",
            delimiter=",",
        )
        y = []
        y_err = []
        for index, cycle in enumerate(frequency_list):
            value_list = data[(index * 2), :]
            y.append(mean(value_list))
            y_err.append(stdev(value_list))
        plt.errorbar(frequency_list, y, y_err, marker=".", capsize=5)
        # plt.hlines(y= , xmin=0, xmax=(max(frequency_list) + 1), color="r", linestyles="-")
        plt.title(f"Frequency Test - {repeats} Repeats of 2 seconds")
        plt.xlim(0, max(frequency_list) + 1)
        plt.xlabel("Frequency")
        plt.ylabel("Offset Value")
        plt.grid(which="both", axis="both")
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/frequency_scan_repeats_{repeats}_{MAX_TIME}_len_{len(frequency_list)}.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.show()

    if corr_test:
        # element = ['SR04A-PC-Q1B-01', 'SR04A-PC-Q2B-02', 'SR04A-PC-Q3B-03', 'SR04A-PC-Q2AB-04', 'SR04A-PC-Q1AB-05', 'SR04A-PC-Q1AD-06', 'SR04A-PC-Q2AD-07', 'SR04A-PC-Q3D-08', 'SR04A-PC-Q2D-09', 'SR04A-PC-Q1D-10']
        element = [
            "SR07A-PC-Q1B-01",
            "SR07A-PC-Q2B-02",
            "SR07A-PC-Q3B-03",
            "SR07A-PC-Q2AB-04",
            "SR07A-PC-Q1AB-05",
            "SR07A-PC-Q1AB-06",
            "SR07A-PC-Q2AB-07",
            "SR07A-PC-Q3B-08",
            "SR07A-PC-Q2B-09",
            "SR07A-PC-Q1B-10",
        ]
        corr_amp_list = [
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            0.9,
            1,
            1.20,
            1.4,
            1.6,
            1.8,
            2,
            2.25,
            2.5,
            3,
            3.5,
        ]
        repeats = 10
        for ele in element:
            # As a multiplier (default 1)
            data = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/corr_amp_scan_repeats_{repeats}_{ele}.csv",
                delimiter=",",
            )
            y = []
            y_err = []
            for index, cycle in enumerate(corr_amp_list):
                value_list = data[(index * 2), :]
                y.append(mean(value_list))
                y_err.append(stdev(value_list))
            plt.errorbar(corr_amp_list, y, y_err, marker=".", capsize=5, label=f"{ele}")
            # plt.hlines(y= , xmin=0, xmax=(max(corr_amp_list) + 0.1), color="r", linestyles="-")
        plt.title(f"Corrector amplitude Test - {repeats} Repeats, Cell 7")
        plt.xlim(0, max(corr_amp_list) + 0.1)
        plt.xlabel("Corrector Amplitude")
        plt.ylabel("Offset Value")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/corr_amp_scan_repeats_{repeats}_cell4_plot.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.show()
        plt.close()

    # if quad_test:
    #     repeats = 10
    #     #As a multiplier (default 0.01 for 1% of current value)
    #     quad_amp_list = [0.001, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
    #     data = np.genfromtxt(f"quad_amp_scan_repeats_{repeats}_len_{len(quad_amp_list)}.csv", delimiter=",")
    #     y = []
    #     y_err = []
    #     for index, cycle in enumerate(quad_amp_list):
    #         value_list = data[(index*2), :]
    #         y.append(mean(value_list))
    #         y_err.append(stdev(value_list))
    #     plt.errorbar(quad_amp_list, y, y_err, marker = ".", capsize=5)
    #     # plt.hlines(y= , xmin=0, xmax=(max(quad_amp_list) + 0.005), color="r", linestyles="-")
    #     plt.title(f"Quad amplitude Test - {repeats} Repeats")
    #     plt.xlim(0 , max(quad_amp_list) + 0.005)
    #     plt.xlabel("Quad Amplitude (0.01 is 1%)")
    #     plt.ylabel("Offset Value")
    #     plt.grid(which = "both", axis = "both")
    #     plt.savefig(f"quad_amp_scan_repeats_{repeats}_len_{len(quad_amp_list)}_plot.png", bbox_inches="tight", dpi=1200)
    #     plt.show()

    if honing_test:
        # Add comparison to slow bba.
        repeats = 8
        cycles = 16
        frequency = 8
        quadrupole_scalar = 0.02
        corrector_scalar = 2
        x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        index = 0
        spread_index = 1

        offset_0_original = 0.7890
        plt.hlines(y=offset_0_original, xmin=0, xmax=8.1, color="r", linestyle="--")

        offset_100_original = 0.8890
        plt.hlines(y=offset_100_original, xmin=0, xmax=8.1, color="r", linestyle="--")

        # BBA matlab 0 offset:
        method = "Matlab BBA"
        offset = 0
        y = [0.789, 0.7160, 0.7110, 0.7180, 0.7140, 0.7200, 0.7170, 0.7160, 0.7200]
        plt.plot(
            x_axis,
            y,
            marker="x",
            color="k",
            linestyle="--",
            label=f"{method}, Offset:{offset}, Spread: {str(mean(y[spread_index:]))[:6]} +- {str(stdev(y[spread_index:]))[:6]}",
        )

        # BBA matlab 100 offset:
        method = "Matlab BBA"
        offset = 100
        y = [0.889, 0.7340, 0.7130, 0.713, 0.7190, 0.7150, 0.713, 0.7080, 0.7170]
        plt.plot(
            x_axis,
            y,
            marker="x",
            color="k",
            label=f"{method}, Offset:{offset}, Spread: {str(mean(y[spread_index:]))[:6]} +- {str(stdev(y[spread_index:]))[:6]}",
        )

        _fft = False
        offset = 0
        method = "FBBA"
        data = np.genfromtxt(
            f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
            delimiter=",",
        )
        y = data[index, :]
        cumy = np.cumsum(y)
        ydata = [offset_0_original] + [value + offset_0_original for value in cumy]
        y_err = [0]
        y_err.extend(data[index + 1, :])
        spread_mean = mean(ydata[spread_index:])
        spread_list = [(y_err[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
        spread_error = spread_mean * np.sqrt(sum(spread_list))
        plt.errorbar(
            x_axis,
            ydata,
            y_err,
            marker=".",
            capsize=5,
            color="b",
            linestyle="--",
            label=f"{method}, Offset:{offset}, fft:{_fft}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
        )

        _fft = True
        offset = 0
        method = "FBBA"
        data = np.genfromtxt(
            f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
            delimiter=",",
        )
        y = data[index, :]
        cumy = np.cumsum(y)
        ydata = [offset_0_original] + [value + offset_0_original for value in cumy]
        y_err = [0]
        y_err.extend(data[index + 1, :])
        spread_mean = mean(ydata[spread_index:])
        spread_list = [(y_err[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
        spread_error = spread_mean * np.sqrt(sum(spread_list))
        plt.errorbar(
            x_axis,
            ydata,
            y_err,
            marker=".",
            capsize=5,
            color="g",
            linestyle="--",
            label=f"{method}, Offset:{offset}, fft:{_fft}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
        )

        # method = "SBBA"
        # _fft = False
        # offset = 0
        # data = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv", delimiter=",")
        # y = data[index, :]
        # cumy = np.cumsum(y)
        # ydata = [value + offset_0_original for value in cumy]
        # y_err = data[index+1, :]
        # plt.errorbar(x_axis, ydata, y_err, marker = ".", capsize=5, label=f"{method}, Offset:{offset}, fft:{_fft}")

        _fft = False
        offset = 100
        method = "FBBA"
        data = np.genfromtxt(
            f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
            delimiter=",",
        )
        y = data[index, :]
        cumy = np.cumsum(y)
        ydata = [offset_100_original] + [value + offset_100_original for value in cumy]
        y_err = [0]
        y_err.extend(data[index + 1, :])
        spread_mean = mean(ydata[spread_index:])
        spread_list = [(y_err[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
        spread_error = spread_mean * np.sqrt(sum(spread_list))
        plt.errorbar(
            x_axis,
            ydata,
            y_err,
            marker=".",
            capsize=5,
            color="c",
            label=f"{method}, Offset:{offset}, fft:{_fft}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
        )

        _fft = True
        offset = 100
        method = "FBBA"
        data = np.genfromtxt(
            f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
            delimiter=",",
        )
        y = data[index, :]
        cumy = np.cumsum(y)
        ydata = [offset_100_original] + [value + offset_100_original for value in cumy]
        y_err = [0]
        y_err.extend(data[index + 1, :])
        spread_mean = mean(ydata[spread_index:])
        spread_list = [(y_err[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
        spread_error = spread_mean * np.sqrt(sum(spread_list))
        plt.errorbar(
            x_axis,
            ydata,
            y_err,
            marker=".",
            capsize=5,
            color="y",
            label=f"{method}, Offset:{offset}, fft:{_fft}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
        )

        # method = "SBBA"
        # _fft = False
        # offset = 100
        # data = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv", delimiter=",")
        # y = data[index, :]
        # cumy = np.cumsum(y)
        # ydata = [value + offset_0_original for value in cumy]
        # y_err = data[index+1, :]
        # plt.errorbar(x_axis, ydata,  marker = ".", capsize=5, label=f"{method}, Offset:{offset}, fft:{_fft}")

        plt.title(f"Honing Test of BPM 1-5, Spread is from point {spread_index}")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_plot.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.show()


if __name__ == "__main__":
    main()
