"""MD Tests analysis."""

from datetime import datetime
import argparse
import logging as log
from statistics import mean, stdev

from bba.common import Algorithm, PLANE_VALUES
from bba.fbba import FBBA
from bba.sbba import SBBA
from bba import accelerator as acc

import matplotlib.pyplot as plt
import numpy as np

def parse_args():
    parser = argparse.ArgumentParser(description="testing")
    parser.add_argument(
        "-c", "--cycle",
        dest="cycle",
        action="store_true",
        default=False,
        help="Cycle test"
    )
    parser.add_argument(
        "-f", "--freq",
        dest="freq",
        action="store_true",
        default=False,
        help="Freq test"
    )
    parser.add_argument(
        "-q", "--quads",
        dest="quads_amp_test",
        action="store_true",
        default=False,
        help="Quad test"
    )
    parser.add_argument(
        "-k", "--corrector",
        dest="corr_amp_test",
        action="store_true",
        default=False,
        help="Corrector test"
    )
    parser.add_argument(
        "-j", "--honing",
        dest="honing_test",
        action="store_true",
        default=False,
        help="honing complex test"
    )
    parser.add_argument(
        "-s", "--special",
        dest="combi",
        action="store_true",
        default=False,
        help="combination test"
    )
    return parser.parse_args()
    

def main():
    args = parse_args()
    cycle_test = args.cycle
    freq_test = args.freq
    corr_test = args.corr_amp_test
    quad_test = args.quad_amp_test
    honing_test = args.honing_test
    combination_test = args.combi

    if cycle_test:
        repeats = 20
        cycle_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        data = np.genfromtxt(f"cycle_scan_repeats_{repeats}_len_{len(cycle_list)}.csv", delimiter=",")
        y = []
        y_err = []
        for index, cycle in enumerate(cycle_list):
            value_list = data[(index*2), :]
            y.append(mean(value_list))
            y_err.append(stdev(value_list))
        plt.errorbar(cycle_list, y, y_err, marker = ".", capsize=5)
        # plt.hlines(y= , xmin=0, xmax=(max(cycle_list) + 1), color="r", linestyles="-")
        plt.title(f"Cycles Test - {repeats} Repeats")
        plt.xlim(0, max(cycle_list) + 1)
        plt.xlabel("Cycles")
        plt.ylabel("Offset Value")
        plt.grid(which = "both", axis = "both")
        plt.savefig(f"cycle_scan_repeats_{repeats}_len_{len(cycle_list)}_plot.png", bbox_inches="tight", dpi=1200)
        plt.show()

    if freq_test:
        repeats = 10
        frequency_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
        data = np.genfromtxt(f"frequency_scan_repeats_{repeats}_len_{len(frequency_list)}.csv", delimiter=",")
        y = []
        y_err = []
        for index, cycle in enumerate(frequency_list):
            value_list = data[(index*2), :]
            y.append(mean(value_list))
            y_err.append(stdev(value_list))
        plt.errorbar(frequency_list, y, y_err, marker = ".", capsize=5)
        # plt.hlines(y= , xmin=0, xmax=(max(frequency_list) + 1), color="r", linestyles="-")
        plt.title(f"Frequency Test - {repeats} Repeats")
        plt.xlim(0, max(frequency_list) + 1)
        plt.xlabel("Frequency")
        plt.ylabel("Offset Value")
        plt.grid(which = "both", axis = "both")
        plt.savefig(f"frequency_scan_repeats_{repeats}_len_{len(frequency_list)}_plot.csv.png", bbox_inches="tight", dpi=1200)
        plt.show()

    if corr_test:
        repeats = 10
        #As a multiplier (default 1)
        corr_amp_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.20, 1.4, 1.6, 1.8, 2, 2.25, 2.5, 3, 3.5, 4, 4.5, 5]
        data = np.genfromtxt(f"corr_amp_scan_repeats_{repeats}_len_{len(corr_amp_list)}.csv", delimiter=",")
        y = []
        y_err = []
        for index, cycle in enumerate(corr_amp_list):
            value_list = data[(index*2), :]
            y.append(mean(value_list))
            y_err.append(stdev(value_list))
        plt.errorbar(corr_amp_list, y, y_err, marker = ".", capsize=5)
        # plt.hlines(y= , xmin=0, xmax=(max(corr_amp_list) + 0.1), color="r", linestyles="-")
        plt.title(f"Corrector amplitude Test - {repeats} Repeats")
        plt.xlim(0 , max(corr_amp_list) + 0.1)
        plt.xlabel("Corrector Amplitude")
        plt.ylabel("Offset Value")
        plt.grid(which = "both", axis = "both")
        plt.savefig(f"corr_amp_scan_repeats_{repeats}_len_{len(corr_amp_list)}_plot.png", bbox_inches="tight", dpi=1200)
        plt.show()

    if quad_test:
        repeats = 10
        #As a multiplier (default 0.01 for 1% of current value)
        quad_amp_list = [0.001, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]
        data = np.genfromtxt(f"quad_amp_scan_repeats_{repeats}_len_{len(quad_amp_list)}.csv", delimiter=",")
        y = []
        y_err = []
        for index, cycle in enumerate(quad_amp_list):
            value_list = data[(index*2), :]
            y.append(mean(value_list))
            y_err.append(stdev(value_list))
        plt.errorbar(quad_amp_list, y, y_err, marker = ".", capsize=5)
        # plt.hlines(y= , xmin=0, xmax=(max(quad_amp_list) + 0.005), color="r", linestyles="-")
        plt.title(f"Quad amplitude Test - {repeats} Repeats")
        plt.xlim(0 , max(quad_amp_list) + 0.005)
        plt.xlabel("Quad Amplitude (0.01 is 1%)")
        plt.ylabel("Offset Value")
        plt.grid(which = "both", axis = "both")
        plt.savefig(f"quad_amp_scan_repeats_{repeats}_len_{len(quad_amp_list)}_plot.png", bbox_inches="tight", dpi=1200)
        plt.show()

    if honing_test:
        #Add comparison to slow bba.
        repeats = 5
        cycles = 1
        frequency = 8
        quad_scalar = 0.01
        corr_scalar = 1
        data = np.genfromtxt(f"honing_simple_repeats_{repeats}_c{cycles}_f{frequency}_q{quad_scalar}_cs{corr_scalar}.csv", delimiter=",")
        y = data[index, :]
        y_err = data[index+1, :]
        x_axis = [1, 2, 3, 4, 5]
        plt.errorbar(x_axis, y, y_err, marker = ".", capsize=5)
        # plt.hlines(y= , xmin=0, xmax=5.1, color="r", linestyles="-")
        plt.title(f"Honing Test")
        plt.xlim(0 , 5.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value")
        plt.grid(which = "both", axis = "both")
        plt.savefig(f"honing_simple_repeats_{repeats}_c{cycles}_f{frequency}_q{quad_scalar}_cs{corr_scalar}_plot.png", bbox_inches="tight", dpi=1200)
        plt.show()

    if combination_test:
        repeats = 5
        corr_amps = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.20, 1.4, 1.6, 1.8, 2, 2.25, 2.5, 3, 3.5, 4, 4.5, 5]
        cycles_list = [1, 10, 20]
        for cycle in cycles_list:
            data = np.genfromtxt(f"combination_scan_repeats_{repeats}_cycle_{cycle}.csv", delimiter=",")
            y = []
            y_err = []
            for index, cycle in enumerate(corr_amps):
                value_list = data[(index*2), :]
                y.append(mean(value_list))
                y_err.append(stdev(value_list))
            plt.errorbar(corr_amps, y, y_err, marker = ".", capsize=5, label=f"Cycle={cycle}")
        # plt.hlines(y= , xmin=0, xmax=5.1, color="r", linestyles="-")
        plt.title(f"Corrector amplitude and cycles Test")
        plt.xlim(0 , 5.1)
        plt.xlabel("Corrector amplitude")
        plt.ylabel("Offset Value")
        plt.grid(which = "both", axis = "both")
        plt.savefig(f"combination_scan_repeats_{repeats}_cycle_full_plot.png", bbox_inches="tight", dpi=1200)
        plt.show()


if __name__ == "__main__":
    main()
