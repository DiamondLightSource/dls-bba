"""MD Tests analysis."""

import argparse
import json
import os
from statistics import mean, stdev

import matplotlib.pyplot as plt
import numpy as np

from dls_bba.md_tests import direction_dict

# import scienceplots


# plt.style.use(["science", "no-latex"])

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "21Feb2023")


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


spread_value = 3
x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8]

initial = {
    "x": 0.7890,
    "y": 0.4230,
}
initial_offset = {"x": 0.8890, "y": 0.5230}


def bba_stats(values, spread=spread_value):
    spread_mean = str(np.round(mean(values[spread:]) * 1000, 1))
    spread_stdev = str(np.round(stdev(values[spread:]) * 1000, 1))
    stats = f"{spread_mean} $\pm$ {spread_stdev} $\mu$m"
    return stats


def find_honing_indices(
    honing_dict,
    method=["BBA", "FBBA", "SBBA"],
    axis=["x", "y"],
    offset=[0, 0.1],
    fofb=[False, True],
    fft=[False, True],
):
    options = list(range(len(honing_dict)))
    for key, value in honing_dict.items():
        remove = False
        if value[0] not in method:
            remove = True
        if value[1] not in axis:
            remove = True
        if value[2] not in offset:
            remove = True
        if value[3] not in fofb:
            remove = True
        if value[4] not in fft:
            remove = True
        if remove:
            options.remove(key)
    return options


def plot_setup(method, fofb, fft=False):
    if method == "FBBA":
        line = "-"
        if fofb is True and fft is True:
            color = "cyan"
        if fofb is False and fft is True:
            color = "dodgerblue"
        if fofb is True and fft is False:
            color = "blue"
        if fofb is False and fft is False:
            color = "darkblue"
    if method == "SBBA":
        line = "-"
        if fofb is True and fft is False:
            color = "red"
        if fofb is False and fft is False:
            color = "darkred"
    if method == "BBA":
        line = "--"
        if fofb is True and fft is False:
            color = "green"
        if fofb is False and fft is False:
            color = "darkgreen"
    return line, color


def plot_honing(honing_dict, key):
    data_info = honing_dict[key]
    line, color = plot_setup(data_info[0], data_info[3], data_info[4])
    plt.errorbar(
        x_axis,
        data_info[5],
        data_info[6],
        marker=".",
        linestyle=line,
        capsize=5,
        color=color,
        label=f"{data_info[0]}, fofb{data_info[3]}, fft{data_info[4]}: {bba_stats(data_info[5])}",
    )


def finalise_honing(title):
    lower_title = title.lower()
    filename = lower_title.replace(" ", "_")
    plt.xlim(0, 8)
    plt.xlabel("Run Number")
    plt.ylabel("Offset Value (mm)")
    plt.grid(which="major", axis="both")
    plt.legend("xx-small")
    plt.savefig(f"{TEMP_FILEPATH_ROOT}/{filename}.png", bbox_inches="tight", dpi=300)
    plt.close()


def main():
    args = parse_args()
    cell = args.cell_t
    honing = args.honing_t
    triple = args.triple_t
    running = args.running_t

    if honing:
        repeats = 8
        cycles = 16
        frequency = 8
        qs = 0.01
        cs = 1
        current = 300

        # 0 micron offset

        honing_dict = {  # method, axis, offset, fofb, fft, values, errors
            # 0 micron offset
            1: ["BBA", "x", 0, False, False, [], []],
            2: ["BBA", "y", 0, False, False, [], []],
            3: ["BBA", "x", 0, True, False, [], []],
            4: ["BBA", "y", 0, True, False, [], []],
            5: ["FBBA", "x", 0, False, False],
            6: ["FBBA", "y", 0, False, False],
            7: ["FBBA", "x", 0, True, False],
            8: ["FBBA", "y", 0, True, False],
            9: ["FBBA", "x", 0, False, True],
            10: ["FBBA", "y", 0, False, True],
            11: ["FBBA", "x", 0, True, True],
            12: ["FBBA", "y", 0, True, True],
            13: ["SBBA", "x", 0, False, False],
            14: ["SBBA", "y", 0, False, False],
            15: ["SBBA", "x", 0, True, False],
            16: ["SBBA", "y", 0, True, False],
            # 0.1 micron offset
            17: ["BBA", "x", 0.1, False, False, [], []],
            18: ["BBA", "y", 0.1, False, False, [], []],
            19: ["BBA", "x", 0.1, True, False, [], []],
            20: ["BBA", "y", 0.1, True, False, [], []],
            21: ["FBBA", "x", 0.1, False, False],
            22: ["FBBA", "y", 0.1, False, False],
            23: ["FBBA", "x", 0.1, True, False],
            24: ["FBBA", "y", 0.1, True, False],
            25: ["FBBA", "x", 0.1, False, True],
            26: ["FBBA", "y", 0.1, False, True],
            27: ["FBBA", "x", 0.1, True, True],
            28: ["FBBA", "y", 0.1, True, True],
            29: ["SBBA", "x", 0.1, False, False],
            30: ["SBBA", "y", 0.1, False, False],
            31: ["SBBA", "x", 0.1, True, False],
            32: ["SBBA", "y", 0.1, True, False],
        }

        for key, values in honing_dict.items():
            if values[0] != "BBA":
                data = np.genfromtxt(
                    f"{TEMP_FILEPATH_ROOT}/honing_{values[0]}_r{repeats}_c{cycles}_f{frequency}_qs{qs}_cs{cs}_fft{values[4]}_fofb{values[3]}_{current}_{values[1]}_offset{values[2]}.csv",
                    delimiter=",",
                )
                if values[2] == 0:
                    initial_value = initial[values[1]]
                elif values[2] == 0.1:
                    initial_value = initial_offset[values[1]]
                else:
                    raise ValueError("offset issue")

                values = np.cumsum(data[0, :])
                y_values = [initial_value] + [value + initial_value for value in values]
                y_errors = [0] + [value for value in data[1, :]]
                honing_dict[key].append(y_values)
                honing_dict[key].append(y_errors)

        # FBBA vs BBA plot x
        indices = find_honing_indices(
            honing_dict, method=["FBBA", "BBA"], axis=["x"], offset=[0]
        )
        for i in indices:
            plot_honing(honing_dict, i)
        finalise_honing("FBBA vs BBA in X at 0 Offset")

        # False fofb

        # FBBA vs BBA plot y

        # False fofb

        # True fofb

        # SBBA vs BBA plot x

        # False fofb

        # True fofb

        # SBBA vs BBA plot y

        # False fofb

        # True fofb

        # FBBA vs SBBA vs BBA x

        # False fofb

        # True fofb

        # FBBA vs SBBA vs BBA y

        # False fofb

        # True fofb

    if triple:
        frequencies = [8, 83, 137, 179]
        fft_ = True
        fofb_trigger_ = False
        current = 300
        x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        spread_index = 3

        initial_x = 0.7890
        initial_y = 0.4230

        freq_dict = {
            8: "darkred",
            83: "red",
            137: "darkorange",
            179: "lime",
            223: "darkgreen",
            269: "dodgerblue",
        }

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

        data_x = np.genfromtxt(
            f"{TEMP_FILEPATH_ROOT}/running_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_delay{delay}_{note}_{topup}_x_{i}.csv",
            delimiter=",",
        )
        data_y = np.genfromtxt(
            f"{TEMP_FILEPATH_ROOT}/running_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_delay{delay}_{note}_{topup}_y_{i}.csv",
            delimiter=",",
        )
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/running_cooling_down_plot.png",
            bbox_inches="tight",
            dpi=1200,
        )
        # plt.show()
        plt.close()


if __name__ == "__main__":
    main()
