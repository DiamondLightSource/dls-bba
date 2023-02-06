"""MD Tests analysis."""

import argparse
import json
import os
from statistics import mean

import matplotlib.pyplot as plt
import numpy as np

from dls_bba.md_tests import direction_dict

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "7Feb2023")


def parse_args():
    parser = argparse.ArgumentParser(description="testing")
    # parser.add_argument(
    #     "-c",
    #     "--cell",
    #     dest="cell_t",
    #     action="store_true",
    #     default=False,
    #     help="Cell test",
    # )
    # parser.add_argument(
    #     "-f",
    #     "--freq",
    #     dest="freq_t",
    #     action="store_true",
    #     default=False,
    #     help="Freq test",
    # )
    parser.add_argument(
        "-j",
        "--honing",
        dest="honing_t",
        action="store_true",
        default=False,
        help="honing simple test",
    )
    parser.add_argument(
        "-t",
        "--triple",
        dest="triple_t",
        action="store_true",
        default=False,
        help="triple frequency test",
    )
    parser.add_argument(
        "-r",
        "--running",
        dest="running_t",
        action="store_true",
        default=False,
        help="Running test",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    cell = args.cell_t
    frequency = args.freq_t
    honing_test = args.honing_t
    triple = args.triple_t
    running = args.running_t

    # 300ma FBBA
    data_x_300_FBBA_fftT_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbTrue_300_x.csv",
        delimiter=",",
    )
    data_y_300_FBBA_fftT_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbTrue_300_y.csv",
        delimiter=",",
    )
    data_x_300_FBBA_fftF_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_300_x.csv",
        delimiter=",",
    )
    data_y_300_FBBA_fftF_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_300_y.csv",
        delimiter=",",
    )
    data_x_300_FBBA_fftT_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbFalse_300_x.csv",
        delimiter=",",
    )
    data_y_300_FBBA_fftT_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbFalse_300_y.csv",
        delimiter=",",
    )
    data_x_300_FBBA_fftF_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_300_x.csv",
        delimiter=",",
    )
    data_y_300_FBBA_fftF_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_300_y.csv",
        delimiter=",",
    )
    # 300ma SBBA
    data_x_300_SBBA_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_300_x.csv",
        delimiter=",",
    )
    data_y_300_SBBA_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_300_y.csv",
        delimiter=",",
    )
    data_x_300_SBBA_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_300_x.csv",
        delimiter=",",
    )
    data_y_300_SBBA_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_300_y.csv",
        delimiter=",",
    )
    # 300ma BBA
    data_x_300_BBA_fofbF = []
    data_y_300_BBA_fofbF = []
    data_x_300_BBA_fofbT = []
    data_y_300_BBA_fofbT = []
    data_x_300_BBA_fofbF_error = []
    data_y_300_BBA_fofbF_error = []
    data_x_300_BBA_fofbT_error = []
    data_y_300_BBA_fofbT_error = []
    """"""
    initial_x_10 = 0
    initial_y_10 = 0
    # 10ma FBBA
    data_x_10_FBBA_fftT_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbTrue_10_x.csv",
        delimiter=",",
    )
    data_y_10_FBBA_fftT_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbTrue_10_y.csv",
        delimiter=",",
    )
    data_x_10_FBBA_fftF_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_10_x.csv",
        delimiter=",",
    )
    data_y_10_FBBA_fftF_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_10_y.csv",
        delimiter=",",
    )
    data_x_10_FBBA_fftT_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbFalse_10_x.csv",
        delimiter=",",
    )
    data_y_10_FBBA_fftT_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbFalse_10_y.csv",
        delimiter=",",
    )
    data_x_10_FBBA_fftF_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_10_x.csv",
        delimiter=",",
    )
    data_y_10_FBBA_fftF_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_10_y.csv",
        delimiter=",",
    )
    # 10ma SBBA
    data_x_10_SBBA_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_10_x.csv",
        delimiter=",",
    )
    data_y_10_SBBA_fofbF = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_10_y.csv",
        delimiter=",",
    )
    data_x_10_SBBA_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_10_x.csv",
        delimiter=",",
    )
    data_y_10_SBBA_fofbT = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_10_y.csv",
        delimiter=",",
    )
    # 10ma BBA
    data_x_10_BBA_fofbF = []
    data_y_10_BBA_fofbF = []
    data_x_10_BBA_fofbT = []
    data_y_10_BBA_fofbT = []
    data_x_10_BBA_fofbF_error = []
    data_y_10_BBA_fofbF_error = []
    data_x_10_BBA_fofbT_error = []
    data_y_10_BBA_fofbT_error = []

    if honing_test:
        """"""
        x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        spread_index = 3

        initial_x_300 = 0
        initial_y_300 = 0

        fbba_300_dict = {
            "data_x_300_FBBA_fftT_fofbT": [
                data_x_300_FBBA_fftT_fofbT,
                "x",
                "True",
                "True",
                "cyan",
                "-",
            ],
            "data_y_300_FBBA_fftT_fofbT": [
                data_y_300_FBBA_fftT_fofbT,
                "y",
                "True",
                "True",
                "cyan",
                "--",
            ],
            "data_x_300_FBBA_fftF_fofbT": [
                data_x_300_FBBA_fftF_fofbT,
                "x",
                "False",
                "True",
                "teal",
                "-",
            ],
            "data_y_300_FBBA_fftF_fofbT": [
                data_y_300_FBBA_fftF_fofbT,
                "y",
                "False",
                "True",
                "teal",
                "--",
            ],
            "data_x_300_FBBA_fftT_fofbF": [
                data_x_300_FBBA_fftT_fofbF,
                "x",
                "True",
                "False",
                "deepskyblue",
                "-",
            ],
            "data_y_300_FBBA_fftT_fofbF": [
                data_y_300_FBBA_fftT_fofbF,
                "y",
                "True",
                "False",
                "deepskyblue",
                "--",
            ],
            "data_x_300_FBBA_fftF_fofbF": [
                data_x_300_FBBA_fftF_fofbF,
                "x",
                "True",
                "False",
                "dodgerblue",
                "-",
            ],
            "data_y_300_FBBA_fftF_fofbF": [
                data_y_300_FBBA_fftF_fofbF,
                "y",
                "True",
                "False",
                "dodgerblue",
                "--",
            ],
        }
        bba_300_dict = {
            "data_x_300_BBA_fofbF": [
                data_x_300_BBA_fofbF,
                data_x_300_BBA_fofbF_error,
                "x",
                "False",
                "darkred",
                "-",
            ],
            "data_y_300_BBA_fofbF": [
                data_y_300_BBA_fofbF,
                data_y_300_BBA_fofbF_error,
                "y",
                "False",
                "darkred",
                "--",
            ],
            "data_x_300_BBA_fofbT": [
                data_x_300_BBA_fofbT,
                data_x_300_BBA_fofbT_error,
                "x",
                "True",
                "chocolate",
                "-",
            ],
            "data_y_300_BBA_fofbT": [
                data_y_300_BBA_fofbT,
                data_y_300_BBA_fofbT_error,
                "y",
                "True",
                "chocolate",
                "--",
            ],
        }
        sbba_300_dict = {
            "data_x_300_SBBA_fofbF": [data_x_300_SBBA_fofbF, "x", "False", "lime", "-"],
            "data_y_300_SBBA_fofbF": [
                data_y_300_SBBA_fofbF,
                "y",
                "False",
                "lime",
                "--",
            ],
            "data_x_300_SBBA_fofbT": [
                data_x_300_SBBA_fofbT,
                "x",
                "True",
                "darkgreen",
                "-",
            ],
            "data_y_300_SBBA_fofbT": [
                data_y_300_SBBA_fofbT,
                "y",
                "True",
                "darkgreen",
                "--",
            ],
        }
        fbba_10_dict = {
            "data_x_10_FBBA_fftT_fofbT": [
                data_x_10_FBBA_fftT_fofbT,
                "x",
                "True",
                "True",
                "darkslategray",
                "-",
            ],
            "data_y_10_FBBA_fftT_fofbT": [
                data_y_10_FBBA_fftT_fofbT,
                "y",
                "True",
                "True",
                "darkslategray",
                "--",
            ],
            "data_x_10_FBBA_fftF_fofbT": [
                data_x_10_FBBA_fftF_fofbT,
                "x",
                "False",
                "True",
                "royalblue",
                "-",
            ],
            "data_y_10_FBBA_fftF_fofbT": [
                data_y_10_FBBA_fftF_fofbT,
                "y",
                "False",
                "True",
                "royalblue",
                "--",
            ],
            "data_x_10_FBBA_fftT_fofbF": [
                data_x_10_FBBA_fftT_fofbF,
                "x",
                "True",
                "False",
                "blue",
                "-",
            ],
            "data_y_10_FBBA_fftT_fofbF": [
                data_y_10_FBBA_fftT_fofbF,
                "y",
                "True",
                "False",
                "blue",
                "--",
            ],
            "data_x_10_FBBA_fftF_fofbF": [
                data_x_10_FBBA_fftF_fofbF,
                "x",
                "True",
                "False",
                "navy",
                "-",
            ],
            "data_y_10_FBBA_fftF_fofbF": [
                data_y_10_FBBA_fftF_fofbF,
                "y",
                "True",
                "False",
                "navy",
                "--",
            ],
        }
        bba_10_dict = {
            "data_x_10_BBA_fofbF": [
                data_x_10_BBA_fofbF,
                data_x_10_BBA_fofbF_error,
                "x",
                "False",
                "darkred",
                "-",
            ],
            "data_y_10_BBA_fofbF": [
                data_y_10_BBA_fofbF,
                data_y_10_BBA_fofbF_error,
                "y",
                "False",
                "darkred",
                "--",
            ],
            "data_x_10_BBA_fofbT": [
                data_x_10_BBA_fofbT,
                data_x_10_BBA_fofbT_error,
                "x",
                "True",
                "chocolate",
                "-",
            ],
            "data_y_10_BBA_fofbT": [
                data_y_10_BBA_fofbT,
                data_y_10_BBA_fofbT_error,
                "y",
                "True",
                "chocolate",
                "--",
            ],
        }
        sbba_10_dict = {
            "data_x_10_SBBA_fofbF": [data_x_10_SBBA_fofbF, "x", "False", "lime", "-"],
            "data_y_10_SBBA_fofbF": [data_y_10_SBBA_fofbF, "y", "False", "lime", "--"],
            "data_x_10_SBBA_fofbT": [
                data_x_10_SBBA_fofbT,
                "x",
                "True",
                "darkgreen",
                "-",
            ],
            "data_y_10_SBBA_fofbT": [
                data_y_10_SBBA_fofbT,
                "y",
                "True",
                "darkgreen",
                "--",
            ],
        }

        # FBBA 300mA comparison
        for key, value in fbba_300_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"FBBA {value[1]}: fft:{value[2]}, fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        for key, value in bba_300_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        plt.hlines(
            y=initial_x_300,
            xmin=0,
            xmax=8.1,
            color="black",
            linestyles="--",
            label=f"x initial: {initial_x_300}",
        )
        plt.hlines(
            y=initial_y_300,
            xmin=0,
            xmax=8.1,
            color="gray",
            linestyles="--",
            label=f"y initial: {initial_y_300}",
        )

        plt.title("Honing Test of FBBA / bba at 300mA")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_bba_300mA_comparison.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()

        # FBBA 10mA comparison
        for key, value in fbba_10_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_10] + [value + initial_x_10 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"FBBA {value[1]}: fft:{value[2]}, fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        for key, value in bba_10_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        plt.hlines(
            y=initial_x_10,
            xmin=0,
            xmax=8.1,
            color="black",
            linestyles="--",
            label=f"x initial: {initial_x_10}",
        )
        plt.hlines(
            y=initial_y_10,
            xmin=0,
            xmax=8.1,
            color="gray",
            linestyles="--",
            label=f"y initial: {initial_y_10}",
        )

        plt.title("Honing Test of FBBA / bba at 10mA")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_bba_10mA_comparison.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()

        # SBBA vs BBA comparison 300 and 10mA
        for key, value in sbba_300_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[3],
                linestyle=value[4],
                label=f"SBBA {value[1]}: fofb:{value[2]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        for key, value in bba_300_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        plt.hlines(
            y=initial_x_300,
            xmin=0,
            xmax=8.1,
            color="black",
            linestyles="--",
            label=f"x initial: {initial_x_300}",
        )
        plt.hlines(
            y=initial_y_300,
            xmin=0,
            xmax=8.1,
            color="gray",
            linestyles="--",
            label=f"y initial: {initial_y_300}",
        )

        plt.title("SBBA/BBA comparison at 300mA")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_300mA_comparison.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()

        for key, value in sbba_10_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_10] + [value + initial_x_10 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[3],
                linestyle=value[4],
                label=f"SBBA {value[1]}: fofb:{value[2]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        for key, value in bba_10_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        plt.hlines(
            y=initial_x_10,
            xmin=0,
            xmax=8.1,
            color="black",
            linestyles="--",
            label=f"x initial: {initial_x_10}",
        )
        plt.hlines(
            y=initial_y_10,
            xmin=0,
            xmax=8.1,
            color="gray",
            linestyles="--",
            label=f"y initial: {initial_y_10}",
        )

        plt.title("SBBA/BBA comparison at 10mA")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_10mA_comparison.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()

        # FBBA vs SBBA vs BBA 300mA comparison
        for key, value in fbba_300_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"FBBA {value[1]}: fft:{value[2]}, fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        for key, value in bba_300_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        for key, value in sbba_300_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[3],
                linestyle=value[4],
                label=f"SBBA {value[1]}: fofb:{value[2]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        plt.hlines(
            y=initial_x_300,
            xmin=0,
            xmax=8.1,
            color="black",
            linestyles="--",
            label=f"x initial: {initial_x_300}",
        )
        plt.hlines(
            y=initial_y_300,
            xmin=0,
            xmax=8.1,
            color="gray",
            linestyles="--",
            label=f"y initial: {initial_y_300}",
        )

        plt.title("FBBA/SBBA/BBA comparison at 300mA")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_bba_300mA_comparison.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()

        # FBBA vs SBBA vs BBA 10mA comparison
        for key, value in fbba_10_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_10] + [value + initial_x_10 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"FBBA {value[1]}: fft:{value[2]}, fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        for key, value in bba_10_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        for key, value in sbba_10_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_10] + [value + initial_x_10 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[3],
                linestyle=value[4],
                label=f"SBBA {value[1]}: fofb:{value[2]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        plt.hlines(
            y=initial_x_10,
            xmin=0,
            xmax=8.1,
            color="black",
            linestyles="--",
            label=f"x initial: {initial_x_10}",
        )
        plt.hlines(
            y=initial_y_10,
            xmin=0,
            xmax=8.1,
            color="gray",
            linestyles="--",
            label=f"y initial: {initial_y_10}",
        )

        plt.title("FBBA/SBBA/BBA comparison at 10mA")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_bba_100mA_comparison.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()

    if frequency:
        # Incomplete: Unsure if needed.
        repeats = 5
        fft_ = True
        fofb_trigger_ = True
        frequency_list = [int(num) for num in range(0, 251)]
        start_x = 0
        # start_y = 0

        for freq in frequency_list:
            data_x = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/frequency_r10_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{frequency_list[0]}_{frequency_list[-1]}_x.csv",
                delimiter=",",
            )
            y_change = np.cumsum((data_x[0])[0, :])
            y_values = [start_x] + [value + start_x for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                # color=freq_dict[freq],
                linestyle="-",
                label=f"FBBA x: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
        plt.hlines(
            y=start_x,
            xmin=0,
            xmax=250.1,
            color="gray",
            linestyles="--",
            label=f"x initial: {start_x}",
        )

        plt.title("Frequency Plot fft, fofb on: x")
        plt.xlim(0, 250.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/frequency_r10_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{frequency_list[0]}_{frequency_list[-1]}_x.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()

    if triple:
        frequencies = [8, 83, 137, 179, 223, 269]
        fft_ = True
        fofb_trigger_ = True
        current = 300
        x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        spread_index = 3

        initial_x_300 = 0
        initial_y_300 = 0

        freq_dict = {
            8: "darkred",
            83: "red",
            137: "darkorange",
            179: "lime",
            223: "darkgreen",
            269: "dodgerblue",
        }
        bba_300_dict = {
            "data_x_300_BBA_fofbT": [
                data_x_300_BBA_fofbT,
                data_x_300_BBA_fofbT_error,
                "x",
                "True",
                "chocolate",
                "-",
            ],
            "data_y_300_BBA_fofbT": [
                data_y_300_BBA_fofbT,
                data_y_300_BBA_fofbT_error,
                "y",
                "True",
                "chocolate",
                "--",
            ],
        }

        for freq in frequencies:
            data_x = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/triple_r8_c16_f{freq}_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_x.csv",
                delimiter=",",
            )
            data_y = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/triple_r8_c16_f{freq}_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_y.csv",
                delimiter=",",
            )
            y_change = np.cumsum((data_x[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=freq_dict[freq],
                linestyle="-",
                label=f"FBBA x: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
            y_change = np.cumsum((data_y[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=freq_dict[freq],
                linestyle="--",
                label=f"FBBA x: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        for key, value in bba_300_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=value[4],
                linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        plt.hlines(
            y=initial_x_300,
            xmin=0,
            xmax=8.1,
            color="black",
            linestyles="--",
            label=f"x initial: {initial_x_300}",
        )
        plt.hlines(
            y=initial_y_300,
            xmin=0,
            xmax=8.1,
            color="gray",
            linestyles="--",
            label=f"y initial: {initial_y_300}",
        )

        plt.title(f"FBBA / BBA frequency comparison at {current}mA, fofb and fft on.")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/triple_frequency_comparison_{current}_fftT_fofbT.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()

    if cell:
        cell_pv_list = [
            "SR01A-PC-Q1D-01",
            "SR01A-PC-Q2D-02",
            "SR01A-PC-Q3D-03",
            "SR01A-PC-Q2AD-04",
            "SR01A-PC-Q1AD-05",
            "SR01A-PC-Q1AB-06",
            "SR01A-PC-Q2AB-07",
            "SR01A-PC-Q3B-08",
            "SR01A-PC-Q2B-09",
            "SR01A-PC-Q1B-10",
        ]
        # correctors_list = [1, 1.5, 2]
        # quadrupole_list = [1, 1.5, 2]
        x_d = direction_dict["x"]
        # y_d = direction_dict["y"]
        x = np.arange(1, 11)

        def cell_comparison(result_dict, starting_value, average=3):
            values = []
            errors = []
            for index, _ in enumerate(cell_pv_list):
                y = result_dict[f"{index},{x_d},value"]
                y_err = result_dict[f"{index},{x_d},error"]

                y_change = np.cumsum(y)
                y_values = [starting_value] + [
                    value + starting_value for value in y_change
                ]
                y_errors = [0] + [value for value in y_err]
                spread_mean = mean(y_values[average:])
                spread_list = [
                    (y_errors[n] / y_values[n]) ** 2 for n in range(average, 5)
                ]
                spread_error = spread_mean * np.sqrt(sum(spread_list))
                values.append(spread_mean)
                errors.append(spread_error)
            return values, errors

        axis = "x"
        starting_x = 0
        # starting_y = 0

        filename_x_c1_q1 = f"cell_c1_q1_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c1_q1)) as f:
            data_dict_x_c1_q1 = json.load(f)
            c1_q1 = cell_comparison(data_dict_x_c1_q1, starting_x, average=3)
        filename_x_c15_q1 = f"cell_c1.5_q1_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c15_q1)) as f:
            data_dict_x_c15_q1 = json.load(f)
            c15_q1 = cell_comparison(data_dict_x_c15_q1, starting_x, average=3)
        filename_x_c2_q1 = f"cell_c2_q1_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c2_q1)) as f:
            data_dict_x_c2_q1 = json.load(f)
            c2_q1 = cell_comparison(data_dict_x_c2_q1, starting_x, average=3)
        filename_x_c1_q15 = f"cell_c1_q1.5_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c1_q15)) as f:
            data_dict_x_c1_q15 = json.load(f)
            c1_q15 = cell_comparison(data_dict_x_c1_q15, starting_x, average=3)
        filename_x_c15_q15 = f"cell_c1.5_q1.5_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c15_q15)) as f:
            data_dict_x_c15_q15 = json.load(f)
            c15_q15 = cell_comparison(data_dict_x_c15_q15, starting_x, average=3)
        filename_x_c2_q15 = f"cell_c2_q1.5_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c2_q15)) as f:
            data_dict_x_c2_q15 = json.load(f)
            c2_q15 = cell_comparison(data_dict_x_c2_q15, starting_x, average=3)
        filename_x_c1_q2 = f"cell_c1_q2_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c1_q2)) as f:
            data_dict_x_c1_q2 = json.load(f)
            c1_q2 = cell_comparison(data_dict_x_c1_q2, starting_x, average=3)
        filename_x_c15_q2 = f"cell_c1.5_q2_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c15_q2)) as f:
            data_dict_x_c15_q2 = json.load(f)
            c15_q2 = cell_comparison(data_dict_x_c15_q2, starting_x, average=3)
        filename_x_c2_q2 = f"cell_c2_q2_{x}_f8_c16_FFT_FOFB_5repeats.json"
        with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x_c2_q2)) as f:
            data_dict_x_c2_q2 = json.load(f)
            c2_q2 = cell_comparison(data_dict_x_c2_q2, starting_x, average=3)

        figure, axis = plt.subplot(3, 3, sharex=True, sharey=True)
        figure.suptitle(
            "Change in BBA values across Cell 1 due to quadrupole/corrector amplitudes."
        )
        # axis[correctors, quads]
        axis[2, 0].errorbar(x, c1_q1[0], c1_q1[1])
        axis[2, 0].set_title("Quad:1, Corr:1")

        axis[2, 1].errorbar(x, c15_q1[0], c15_q1[1])
        axis[2, 1].set_title("Quad:1, Corr:1.5")

        axis[2, 2].errorbar(x, c2_q1[0], c2_q1[1])
        axis[2, 2].set_title("Quad:1, Corr:2")

        axis[1, 0].errorbar(x, c1_q15[0], c15_q1[1])
        axis[1, 0].set_title("Quad:1.5, Corr:1")

        axis[1, 1].errorbar(x, c15_q15[0], c15_q15[1])
        axis[1, 1].set_title("Quad:1.5, Corr:1.5")

        axis[1, 2].errorbar(x, c2_q15[0], c2_q15[1])
        axis[1, 2].set_title("Quad:1.5, Corr:2")

        axis[0, 0].errorbar(x, c1_q2[0], c1_q2[1])
        axis[0, 0].set_title("Quad:2, Corr:1")

        axis[0, 1].errorbar(x, c15_q2[0], c15_q2[1])
        axis[0, 1].set_title("Quad:2, Corr:1.5")

        axis[0, 2].errorbar(x, c2_q2[0], c2_q2[1])
        axis[0, 2].set_title("Quad:2, Corr:2")

        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/cell1_comparison_x.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.close()

    if running:
        fft_ = True
        fofb_trigger_ = True
        current = 300
        delay = 40
        # x_axis = [int(num) for num in range(0, 30+1)]
        spread_index = 3
        initial_x_300 = [0]
        initial_y_300 = [0]
        # note = "warming"
        note = "cooling"
        topup = "topup1"

        repeats = 40
        for i in range(1, repeats + 1):
            x = [int(num) for num in range(1, ((i) * 10) + 1)][
                -9:
            ]  # To give the spacing between each set of 8 +1 runs.
            data_x = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/running_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_delay{delay}_{note}_{topup}_x_{i}.csv",
                delimiter=",",
            )
            y_change = np.cumsum((data_x[0])[0, :])
            y_values = [initial_x_300[-1]] + [
                value + initial_x_300[-1] for value in y_change
            ]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            initial_x_300.append(initial_x_300[-1] + y_values[-1])
            plt.errorbar(
                x,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=freq_dict[freq],
                linestyle="-",
                label=f"FBBA x: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )
            data_y = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/running_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_delay{delay}_{note}_{topup}_y_{i}.csv",
                delimiter=",",
            )
            y_change = np.cumsum((data_y[0])[0, :])
            y_values = [initial_y_300[-1]] + [
                value + initial_y_300[-1] for value in y_change
            ]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [
                (y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)
            ]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            initial_y_300.append(initial_y_300[-1] + y_values[-1])
            plt.errorbar(
                x,
                y_values,
                y_errors,
                marker=".",
                capsize=5,
                color=freq_dict[freq],
                linestyle="-",
                label=f"FBBA y: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
            )

        plt.hlines(
            y=initial_x_300,
            xmin=0,
            xmax=400.1,
            color="black",
            linestyles="--",
            label=f"x initial: {initial_x_300}",
        )
        plt.hlines(
            y=initial_y_300,
            xmin=0,
            xmax=400.1,
            color="gray",
            linestyles="--",
            label=f"y initial: {initial_y_300}",
        )

        DUMP = "Dumptime"
        DUMP_CURRENT = "300"
        FILL = "Filled"
        FILL_CURRENT = "10"

        FIRST = "ISOSTART"
        FINISH = "ISOFINISH"

        plt.title(
            f"FBBA {note} decay offsets. Dumped: {DUMP} from {DUMP_CURRENT}, Filled to 10mA: {FILL} to {FILL_CURRENT}"
        )
        plt.xlim(0, 400.1)
        plt.xlabel(f"Run number: 0->400 : {FIRST}->{FINISH}")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/running_cooling_down_plot.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()


if __name__ == "__main__":
    main()
