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

    if honing_test:
        honing()


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


if __name__ == "__main__":
    main()
