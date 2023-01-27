"""MD Tests analysis."""

import argparse
import os
from statistics import mean

import matplotlib.pyplot as plt
import numpy as np

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "31Jan2023")


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
    # cell_test = args.cell_t
    # freq_test = args.freq_t
    honing_test = args.honing_t
    triple = args.triple_t
    running = args.running_t
    # fmt: off

    # 300ma FBBA
    data_x_300_FBBA_fftT_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbTrue_300_x.csv", delimiter=",")
    data_y_300_FBBA_fftT_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbTrue_300_y.csv", delimiter=",")
    data_x_300_FBBA_fftF_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_300_x.csv", delimiter=",")
    data_y_300_FBBA_fftF_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_300_y.csv", delimiter=",")
    data_x_300_FBBA_fftT_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbFalse_300_x.csv", delimiter=",")
    data_y_300_FBBA_fftT_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbFalse_300_y.csv", delimiter=",")
    data_x_300_FBBA_fftF_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_300_x.csv", delimiter=",")
    data_y_300_FBBA_fftF_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_300_y.csv", delimiter=",")
    # 300ma SBBA
    data_x_300_SBBA_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_300_x.csv", delimiter=",")
    data_y_300_SBBA_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_300_y.csv", delimiter=",")
    data_x_300_SBBA_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_300_x.csv", delimiter=",")
    data_y_300_SBBA_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_300_y.csv", delimiter=",")
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
    data_x_10_FBBA_fftT_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbTrue_10_x.csv", delimiter=",")
    data_y_10_FBBA_fftT_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbTrue_10_y.csv", delimiter=",")
    data_x_10_FBBA_fftF_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_10_x.csv", delimiter=",")
    data_y_10_FBBA_fftF_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_10_y.csv", delimiter=",")
    data_x_10_FBBA_fftT_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbFalse_10_x.csv", delimiter=",")
    data_y_10_FBBA_fftT_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftTrue_fofbFalse_10_y.csv", delimiter=",")
    data_x_10_FBBA_fftF_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_10_x.csv", delimiter=",")
    data_y_10_FBBA_fftF_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_10_y.csv", delimiter=",")
    # 10ma SBBA
    data_x_10_SBBA_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_10_x.csv", delimiter=",")
    data_y_10_SBBA_fofbF = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbFalse_10_y.csv", delimiter=",")
    data_x_10_SBBA_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_10_x.csv", delimiter=",")
    data_y_10_SBBA_fofbT = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r8_c16_f8_qs0.02_cs2_fftFalse_fofbTrue_10_y.csv", delimiter=",")
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
            "data_x_300_FBBA_fftT_fofbT": [data_x_300_FBBA_fftT_fofbT, "x", "True", "True", "cyan", "-"],
            "data_y_300_FBBA_fftT_fofbT": [data_y_300_FBBA_fftT_fofbT, "y", "True", "True", "cyan", "--"],
            "data_x_300_FBBA_fftF_fofbT": [data_x_300_FBBA_fftF_fofbT, "x", "False", "True", "teal", "-"],
            "data_y_300_FBBA_fftF_fofbT": [data_y_300_FBBA_fftF_fofbT, "y", "False", "True", "teal", "--"],
            "data_x_300_FBBA_fftT_fofbF": [data_x_300_FBBA_fftT_fofbF, "x", "True", "False", "deepskyblue", "-"],
            "data_y_300_FBBA_fftT_fofbF": [data_y_300_FBBA_fftT_fofbF, "y", "True", "False", "deepskyblue", "--"],
            "data_x_300_FBBA_fftF_fofbF": [data_x_300_FBBA_fftF_fofbF, "x", "True", "False", "dodgerblue", "-"],
            "data_y_300_FBBA_fftF_fofbF": [data_y_300_FBBA_fftF_fofbF, "y", "True", "False", "dodgerblue", "--"],
        }
        bba_300_dict = {
            "data_x_300_BBA_fofbF": [data_x_300_BBA_fofbF, data_x_300_BBA_fofbF_error, "x", "False", "darkred", "-"],
            "data_y_300_BBA_fofbF": [data_y_300_BBA_fofbF, data_y_300_BBA_fofbF_error, "y", "False", "darkred", "--"],
            "data_x_300_BBA_fofbT": [data_x_300_BBA_fofbT, data_x_300_BBA_fofbT_error, "x", "True", "chocolate", "-"],
            "data_y_300_BBA_fofbT": [data_y_300_BBA_fofbT, data_y_300_BBA_fofbT_error, "y", "True", "chocolate", "--"],
        }
        sbba_300_dict = {
            "data_x_300_SBBA_fofbF": [data_x_300_SBBA_fofbF, "x", "False", "lime", "-"],
            "data_y_300_SBBA_fofbF": [data_y_300_SBBA_fofbF, "y", "False", "lime", "--"],
            "data_x_300_SBBA_fofbT": [data_x_300_SBBA_fofbT, "x", "True", "darkgreen", "-"],
            "data_y_300_SBBA_fofbT": [data_y_300_SBBA_fofbT, "y", "True", "darkgreen", "--"],
        }
        fbba_10_dict = {
            "data_x_10_FBBA_fftT_fofbT": [data_x_10_FBBA_fftT_fofbT, "x", "True", "True", "darkslategray", "-"],
            "data_y_10_FBBA_fftT_fofbT": [data_y_10_FBBA_fftT_fofbT, "y", "True", "True", "darkslategray", "--"],
            "data_x_10_FBBA_fftF_fofbT": [data_x_10_FBBA_fftF_fofbT, "x", "False", "True", "royalblue", "-"],
            "data_y_10_FBBA_fftF_fofbT": [data_y_10_FBBA_fftF_fofbT, "y", "False", "True", "royalblue", "--"],
            "data_x_10_FBBA_fftT_fofbF": [data_x_10_FBBA_fftT_fofbF, "x", "True", "False", "blue", "-"],
            "data_y_10_FBBA_fftT_fofbF": [data_y_10_FBBA_fftT_fofbF, "y", "True", "False", "blue", "--"],
            "data_x_10_FBBA_fftF_fofbF": [data_x_10_FBBA_fftF_fofbF, "x", "True", "False", "navy", "-"],
            "data_y_10_FBBA_fftF_fofbF": [data_y_10_FBBA_fftF_fofbF, "y", "True", "False", "navy", "--"],
        }
        bba_10_dict = {
            "data_x_10_BBA_fofbF": [data_x_10_BBA_fofbF, data_x_10_BBA_fofbF_error, "x", "False", "darkred", "-"],
            "data_y_10_BBA_fofbF": [data_y_10_BBA_fofbF, data_y_10_BBA_fofbF_error, "y", "False", "darkred", "--"],
            "data_x_10_BBA_fofbT": [data_x_10_BBA_fofbT, data_x_10_BBA_fofbT_error, "x", "True", "chocolate", "-"],
            "data_y_10_BBA_fofbT": [data_y_10_BBA_fofbT, data_y_10_BBA_fofbT_error, "y", "True", "chocolate", "--"],
        }
        sbba_10_dict = {
            "data_x_10_SBBA_fofbF": [data_x_10_SBBA_fofbF, "x", "False", "lime", "-"],
            "data_y_10_SBBA_fofbF": [data_y_10_SBBA_fofbF, "y", "False", "lime", "--"],
            "data_x_10_SBBA_fofbT": [data_x_10_SBBA_fofbT, "x", "True", "darkgreen", "-"],
            "data_y_10_SBBA_fofbT": [data_y_10_SBBA_fofbT, "y", "True", "darkgreen", "--"],
        }

        # FBBA 300mA comparison
        for key, value in fbba_300_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"FBBA {value[1]}: fft:{value[2]}, fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
        for key, value in bba_300_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        plt.hlines(y=initial_x_300 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x initial: {initial_x_300}")
        plt.hlines(y=initial_y_300 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y initial: {initial_y_300}")

        plt.title("Honing Test of FBBA / bba at 300mA")
        plt.xlim(0 , 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which = "both", axis = "both")
        plt.legend()
        plt.savefig(f"{TEMP_FILEPATH_ROOT}/honing_fbba_bba_300mA_comparison.png", bbox_inches="tight", dpi=1200)
        #plt.show()
        plt.close()


        # FBBA 10mA comparison
        for key, value in fbba_10_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_10] + [value + initial_x_10 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"FBBA {value[1]}: fft:{value[2]}, fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
        for key, value in bba_10_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        plt.hlines(y=initial_x_10 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x initial: {initial_x_10}")
        plt.hlines(y=initial_y_10 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y initial: {initial_y_10}")

        plt.title("Honing Test of FBBA / bba at 10mA")
        plt.xlim(0 , 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which = "both", axis = "both")
        plt.legend()
        plt.savefig(f"{TEMP_FILEPATH_ROOT}/honing_fbba_bba_10mA_comparison.png", bbox_inches="tight", dpi=1200)
        #plt.show()
        plt.close()


        # SBBA vs BBA comparison 300 and 10mA
        for key, value in sbba_300_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[3],linestyle=value[4],
                label=f"SBBA {value[1]}: fofb:{value[2]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
        for key, value in bba_300_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        plt.hlines(y=initial_x_300 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x initial: {initial_x_300}")
        plt.hlines(y=initial_y_300 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y initial: {initial_y_300}")

        plt.title("SBBA/BBA comparison at 300mA")
        plt.xlim(0 , 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which = "both", axis = "both")
        plt.legend()
        plt.savefig(f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_300mA_comparison.png", bbox_inches="tight", dpi=1200)
        #plt.show()
        plt.close()

        for key, value in sbba_10_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_10] + [value + initial_x_10 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[3],linestyle=value[4],
                label=f"SBBA {value[1]}: fofb:{value[2]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
        for key, value in bba_10_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        plt.hlines(y=initial_x_10 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x initial: {initial_x_10}")
        plt.hlines(y=initial_y_10 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y initial: {initial_y_10}")

        plt.title("SBBA/BBA comparison at 10mA")
        plt.xlim(0 , 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which = "both", axis = "both")
        plt.legend()
        plt.savefig(f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_10mA_comparison.png", bbox_inches="tight", dpi=1200)
        #plt.show()
        plt.close()

        # FBBA vs SBBA vs BBA 300mA comparison
        for key, value in fbba_300_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"FBBA {value[1]}: fft:{value[2]}, fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
        for key, value in bba_300_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
        for key, value in sbba_300_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[3],linestyle=value[4],
                label=f"SBBA {value[1]}: fofb:{value[2]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        plt.hlines(y=initial_x_300 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x initial: {initial_x_300}")
        plt.hlines(y=initial_y_300 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y initial: {initial_y_300}")

        plt.title("FBBA/SBBA/BBA comparison at 300mA")
        plt.xlim(0 , 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which = "both", axis = "both")
        plt.legend()
        plt.savefig(f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_bba_300mA_comparison.png", bbox_inches="tight", dpi=1200)
        #plt.show()
        plt.close()

        # FBBA vs SBBA vs BBA 10mA comparison
        for key, value in fbba_10_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_10] + [value + initial_x_10 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"FBBA {value[1]}: fft:{value[2]}, fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
        for key, value in bba_10_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
        for key, value in sbba_10_dict:
            y_change = np.cumsum((value[0])[0, :])
            y_values = [initial_x_10] + [value + initial_x_10 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[3],linestyle=value[4],
                label=f"SBBA {value[1]}: fofb:{value[2]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        plt.hlines(y=initial_x_10 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x initial: {initial_x_10}")
        plt.hlines(y=initial_y_10 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y initial: {initial_y_10}")

        plt.title("FBBA/SBBA/BBA comparison at 10mA")
        plt.xlim(0 , 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which = "both", axis = "both")
        plt.legend()
        plt.savefig(f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_bba_100mA_comparison.png", bbox_inches="tight", dpi=1200)
        #plt.show()
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
            8: "",
            83: "",
            137: "",
            179: "",
            223: "",
            269: "",
        }
        bba_300_dict = {
            "data_x_300_BBA_fofbT": [data_x_300_BBA_fofbT, data_x_300_BBA_fofbT_error, "x", "True", "chocolate", "-"],
            "data_y_300_BBA_fofbT": [data_y_300_BBA_fofbT, data_y_300_BBA_fofbT_error, "y", "True", "chocolate", "--"],
        }

        for freq in frequencies:
            data_x = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/triple_r8_c16_f{freq}_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_x.csv", delimiter=",")
            data_y = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/triple_r8_c16_f{freq}_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_y.csv", delimiter=",")
            y_change = np.cumsum((data_x[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=freq_dict[freq],linestyle="-",
                label=f"FBBA x: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
            y_change = np.cumsum((data_y[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=freq_dict[freq],linestyle="-",
                label=f"FBBA x: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        for key, value in bba_300_dict:
            y_values = value[0]
            y_errors = [0] + [v for v in value[1]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x_axis, y_values, y_errors, marker=".",capsize=5,color=value[4],linestyle=value[5],
                label=f"BBA {value[2]}: fofb:{value[3]},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        plt.hlines(y=initial_x_300 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x initial: {initial_x_300}")
        plt.hlines(y=initial_y_300 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y initial: {initial_y_300}")

        plt.title("FBBA / BBA frequency comparison at 300mA, fofb and fft on.")
        plt.xlim(0 , 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which = "both", axis = "both")
        plt.legend()
        plt.savefig(f"{TEMP_FILEPATH_ROOT}/triple_frequency_comparison_300_fftT_fofbT.png", bbox_inches="tight", dpi=1200)
        #plt.show()
        plt.close()

    if running:
        fft_ = True
        fofb_trigger_ = True
        current = 300
        delay = 40
        # x_axis = [int(num) for num in range(0, 30+1)]
        spread_index = 3
        initial_x_300 = 0
        initial_y_300 = 0
        settled_x_10 = 0
        settled_y_10 = 0

        repeats = 30
        for i in range(1, repeats + 1):
            x = [int(num) for num in range(1, ((i)*10)+1)][-9:] # To give the spacing between each set of 8 +1 runs.
            data_x = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/running_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_delay{delay}_x_{i}.csv", delimiter=",")
            y_change = np.cumsum((data_x[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))

            plt.errorbar(x, y_values, y_errors, marker=".",capsize=5,color=freq_dict[freq],linestyle="-",
                label=f"FBBA x: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")
            data_y = np.genfromtxt(f"{TEMP_FILEPATH_ROOT}/running_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_delay{delay}_y_{i}.csv", delimiter=",")
            y_change = np.cumsum((data_y[0])[0, :])
            y_values = [initial_x_300] + [value + initial_x_300 for value in y_change]
            y_errors = [0] + [value for value in (value[0])[1, :]]
            spread_mean = mean(y_values[spread_index:])
            spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread_index, 9)]
            spread_error = spread_mean * np.sqrt(sum(spread_list))
            plt.errorbar(x, y_values, y_errors, marker=".",capsize=5,color=freq_dict[freq],linestyle="-",
                label=f"FBBA y: fft:{fft_}, fofb:{fofb_trigger_},  Spread:{str(spread_mean)[:6]} +- {str(spread_error)[:6]}")

        plt.hlines(y=initial_x_300 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x initial: {initial_x_300}")
        plt.hlines(y=initial_y_300 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y initial: {initial_y_300}")

        plt.hlines(y=settled_x_10 , xmin=0, xmax=8.1, color="black", linestyles="--", label=f"x final: {settled_x_10}")
        plt.hlines(y=settled_y_10 , xmin=0, xmax=8.1, color="gray", linestyles="--", label=f"y final: {settled_y_10}")

        plt.title("FBBA / BBA frequency comparison at 300mA, fofb and fft on.")
        plt.xlim(0 , 8.1)
        plt.xlabel("Run number - Time to be determined later")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which = "both", axis = "both")
        plt.legend()
        plt.savefig(f"{TEMP_FILEPATH_ROOT}/running_cooling_down_plot.png", bbox_inches="tight", dpi=1200)
        #plt.show()
        plt.close()


# fmt: on

if __name__ == "__main__":
    main()
