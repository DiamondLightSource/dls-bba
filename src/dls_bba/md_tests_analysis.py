"""MD Tests analysis."""

import argparse
import json
import os
from statistics import mean, stdev

import matplotlib.pyplot as plt
import numpy as np

from dls_bba.md_tests import direction_dict

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "14Feb2023")


def parse_args():
    parser = argparse.ArgumentParser(description="testing")
    parser.add_argument(
        "-c",
        "--cell",
        dest="cell_t",
        action="store_true",
        default=False,
        help="Cell test",
    )
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
    honing = args.honing_t
    triple = args.triple_t
    running = args.running_t

    x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8]

    initial_x = 0.750
    initial_y = 0.450

    def fbba_values(rawdata, initial, spread=3):
        values = np.cumsum(rawdata[0, :])
        y_values = [initial] + [value + initial for value in values]
        y_errors = [0] + [value for value in rawdata[1, :]]

        spread_mean = mean(y_values[spread:])
        spread_stdev = stdev(y_values[spread:])
        spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread, 9)]
        spread_error = spread_mean * np.sqrt(sum(spread_list))
        return y_values, y_errors, spread_mean, spread_error, spread_stdev

    def sbba_values(rawdata, initial, spread=3):
        values = np.cumsum(rawdata[0, :])
        y_values = [initial] + [value + initial for value in values]
        y_errors = [0] + [value for value in rawdata[1, :]]

        spread_mean = mean(y_values[spread:])
        spread_stdev = stdev(y_values[spread:])
        spread_list = [(y_errors[n] / y_values[n]) ** 2 for n in range(spread, 9)]
        spread_error = spread_mean * np.sqrt(sum(spread_list))
        return y_values, y_errors, spread_mean, spread_error, spread_stdev

    def bba_values(data, error, spread=3):
        spread_mean = mean(data[spread:])
        spread_stdev = stdev(data[spread:])
        spread_list = [(error[n] / data[n]) ** 2 for n in range(spread, 9)]
        spread_error = spread_mean * np.sqrt(sum(spread_list))
        return spread_mean, spread_error, spread_stdev

    if honing:
        repeats = 8
        cycles = 16
        frequency = 8
        qs = 0.01
        cs = 1
        current = 300

        fbba_options = {  # fft, fofb, color
            "first": [True, True, "cyan"],
            "second": [False, True, "dodgerblue"],
            "third": [True, False, "blue"],
            "fourth": [False, False, "darkblue"],
        }
        sbba_options = {  # fofb, color
            "first": [False, "darkred"],
            "second": [True, "red"],
        }
        bba_options = {  # fofb, linestyle, color
            "f": [False, "--", "darkgreen"],
            "t": [True, "--", "green"],
        }
        fbba_data_x = {}
        for key, (fft, fofb, _) in fbba_options.items():
            fbba_data_x[key] = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r{repeats}_c{cycles}_f{frequency}_qs{qs}_cs{cs}_fft{fft}_fofb{fofb}_{current}_x.csv",
                delimiter=",",
            )
        fbba_data_y = {}
        for key, (fft, fofb, _) in fbba_options.items():
            fbba_data_y[key] = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/honing_FBBA_r{repeats}_c{cycles}_f{frequency}_qs{qs}_cs{cs}_fft{fft}_fofb{fofb}_{current}_y.csv",
                delimiter=",",
            )

        sbba_data_x = {}
        for key, (fofb, _) in sbba_options.items():
            sbba_data_x[key] = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r{repeats}_c{cycles}_f{frequency}_qs{qs}_cs{cs}_fftFalse_fofb{fofb}_{current}_x.csv",
                delimiter=",",
            )
        sbba_data_y = {}
        for key, (fofb, _) in sbba_options.items():
            sbba_data_y[key] = np.genfromtxt(
                f"{TEMP_FILEPATH_ROOT}/honing_SBBA_r{repeats}_c{cycles}_f{frequency}_qs{qs}_cs{cs}_fftFalse_fofb{fofb}_{current}_y.csv",
                delimiter=",",
            )

        bba_f_x = [initial_x] + [value for value in []]
        bba_f_x_e = [0] + [value for value in []]

        bba_t_x = [initial_x] + [value for value in []]
        bba_t_x_e = [0] + [value for value in []]

        bba_f_y = [initial_y] + [value for value in []]
        bba_f_y_e = [0] + [value for value in []]

        bba_t_y = [initial_y] + [value for value in []]
        bba_t_y_e = [0] + [value for value in []]

        # FBBA vs BBA plot x
        for key, value in fbba_data_x:
            y_values, y_errors, spread_mean, spread_error, spread_stdev = fbba_values(
                value, initial_x
            )
            options = fbba_options[key]
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                marker="+",
                color=options[2],
                label=f"FBBA: fft{options[0]}, fofb{options[1]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
            )
        # False fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_f_x, bba_f_x_e)
        options = bba_options["f"]
        plt.errorbar(
            x_axis,
            bba_f_x,
            bba_f_x_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        # True fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_t_x, bba_t_x_e)
        options = bba_options["t"]
        plt.errorbar(
            x_axis,
            bba_t_x,
            bba_t_x_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        plt.title("Honing Test of FBBA / bba at 300mA in x.")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_and_bba_300mA_comparison_x.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.close()
        # FBBA vs BBA plot y
        for key, value in fbba_data_y:
            y_values, y_errors, spread_mean, spread_error, spread_stdev = fbba_values(
                value, initial_y
            )
            options = fbba_options[key]
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                color=options[2],
                label=f"FBBA: fft{options[0]}, fofb{options[1]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
            )
        # False fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_f_y, bba_f_y_e)
        options = bba_options["f"]
        plt.errorbar(
            x_axis,
            bba_f_x,
            bba_f_y_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        # True fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_t_y, bba_t_y_e)
        options = bba_options["t"]
        plt.errorbar(
            x_axis,
            bba_f_y,
            bba_t_y_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        plt.title("Honing Test of FBBA / bba at 300mA in y.")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_and_bba_300mA_comparison_y.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.close()

        """"""

        # SBBA vs BBA plot x
        for key, value in sbba_data_x:
            y_values, y_errors, spread_mean, spread_error, spread_stdev = sbba_values(
                value, initial_x
            )
            options = sbba_options[key]
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                color=options[2],
                label=f"SBBA: fft{options[0]}, fofb{options[1]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
            )
        # False fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_f_x, bba_f_x_e)
        options = bba_options["f"]
        plt.errorbar(
            x_axis,
            bba_f_x,
            bba_f_x_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        # True fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_t_x, bba_t_x_e)
        options = bba_options["t"]
        plt.errorbar(
            x_axis,
            bba_t_x,
            bba_t_x_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        plt.title("Honing Test of SBBA / bba at 300mA in x.")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_sbba_and_bba_300mA_comparison_x.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.close()
        # SBBA vs BBA plot y
        for key, value in sbba_data_y:
            y_values, y_errors, spread_mean, spread_error, spread_stdev = sbba_values(
                value, initial_y
            )
            options = sbba_options[key]
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                color=options[2],
                label=f"SBBA: fft{options[0]}, fofb{options[1]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
            )
        # False fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_f_y, bba_f_y_e)
        options = bba_options["f"]
        plt.errorbar(
            x_axis,
            bba_f_x,
            bba_f_x_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        # True fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_t_y, bba_t_y_e)
        options = bba_options["t"]
        plt.errorbar(
            x_axis,
            bba_t_x,
            bba_t_y_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        plt.title("Honing Test of SBBA / bba at 300mA in y.")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_sbba_and_bba_300mA_comparison_y.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.close()

        """"""

        # FBBA vs SBBA vs BBA x
        for key, value in fbba_data_x:
            y_values, y_errors, spread_mean, spread_error, spread_stdev = fbba_values(
                value, initial_x
            )
            options = fbba_options[key]
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                color=options[2],
                label=f"FBBA: fft{options[0]}, fofb{options[1]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
            )
        for key, value in sbba_data_x:
            y_values, y_errors, spread_mean, spread_error, spread_stdev = sbba_values(
                value, initial_x
            )
            options = sbba_options[key]
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                color=options[2],
                label=f"SBBA: fft{options[0]}, fofb{options[1]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
            )
        # False fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_f_x, bba_f_x_e)
        options = bba_options["f"]
        plt.errorbar(
            x_axis,
            bba_f_x,
            bba_f_x_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        # True fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_t_x, bba_t_x_e)
        options = bba_options["t"]
        plt.errorbar(
            x_axis,
            bba_t_x,
            bba_t_x_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        plt.title("Honing Test of FBBA / bba at 300mA in x.")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_bba_300mA_comparison_x.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.close()
        # FBBA vs SBBA vs BBA y
        for key, value in fbba_data_y:
            y_values, y_errors, spread_mean, spread_error, spread_stdev = fbba_values(
                value, initial_y
            )
            options = fbba_options[key]
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                color=options[2],
                label=f"FBBA: fft{options[0]}, fofb{options[1]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
            )
        for key, value in sbba_data_y:
            y_values, y_errors, spread_mean, spread_error, spread_stdev = sbba_values(
                value, initial_y
            )
            options = sbba_options[key]
            plt.errorbar(
                x_axis,
                y_values,
                y_errors,
                color=options[2],
                label=f"SBBA: fft{options[0]}, fofb{options[1]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
            )
        # False fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_f_y, bba_f_y_e)
        options = bba_options["f"]
        plt.errorbar(
            x_axis,
            bba_f_y,
            bba_f_y_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        # True fofb
        spread_mean, spread_error, spread_stdev = bba_values(bba_t_y, bba_t_y_e)
        options = bba_options["t"]
        plt.errorbar(
            x_axis,
            bba_t_y,
            bba_t_y_e,
            linestyle=options[1],
            color=options[2],
            label=f"BBA: fofb{options[0]}: {spread_mean} +- ep {spread_error} or stdev {spread_stdev}",
        )
        plt.title("Honing Test of FBBA / bba at 300mA in y.")
        plt.xlim(0, 8.1)
        plt.xlabel("Run number")
        plt.ylabel("Offset Value (mm)")
        plt.grid(which="both", axis="both")
        plt.legend()
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/honing_fbba_sbba_bba_300mA_comparison_y.png",
            bbox_inches="tight",
            dpi=1200,
        )
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
        # correctors_list = [0.5, 1, 1.5]
        # quadrupole_list = [0.5, 1, 1.5]
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
