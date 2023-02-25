"""MD Tests analysis."""

import argparse
import os
from statistics import mean, stdev

import matplotlib.pyplot as plt
import numpy as np

# import scienceplots


# plt.style.use(["science", "no-latex"])

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "28Feb2023")


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
        "-r",
        "--running",
        dest="running_t",
        action="store_true",
        default=False,
        help="Running test",
    )
    parser.add_argument(
        "-f",
        "--feedback",
        dest="feedbacks_t",
        action="store_true",
        default=False,
        help="feedbacks test",
    )
    parser.add_argument(
        "-w",
        "--swap",
        dest="swap_t",
        action="store_true",
        default=False,
        help="swap test",
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
    pm = r"$\pm$"
    um = r"$\mu$m"
    stats = f"{spread_mean} {pm} {spread_stdev} {um}"
    return stats


def main():
    args = parse_args()
    honing = args.honing_t
    time = args.timing_t
    running = args.running_t
    feedbacks = args.feedbacks_t
    swap = args.swap_t

    if feedbacks:
        runtime_values = [2, 3, 4]
        waittime_values = [1, 3, 5]
        repeats = 16
        x = np.arange(0, repeats)
        quadrupole_scalar = 0.01
        corrector_scalar = 1
        cycles = 16
        frequency = 8
        data = {}

        for run in runtime_values:
            for wait in waittime_values:
                d = np.genfromtxt(
                    f"{TEMP_FILEPATH_ROOT}/feedbacks_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_x_run{run}_wait{wait}.csv",
                    delimiter=",",
                )
                data[f"{run},{wait}_x"] = [d[0, :], d[1, :]]
                d = np.genfromtxt(
                    f"{TEMP_FILEPATH_ROOT}/feedbacks_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_y_run{run}_wait{wait}.csv",
                    delimiter=",",
                )
                data[f"{run},{wait}_y"] = [d[0, :], d[1, :]]

        for key, (values, errors) in data.items():
            init = initial_offset[key[-1]]
            cum_values = np.cumsum(values)
            y_values = [init] + [value + init for value in cum_values]
            y_errors = [0] + [e for e in errors]
            data[key] = [y_values, y_errors]

        for axis in ["x", "y"]:
            fig, axs = plt.subplots(
                ncols=len(runtime_values),
                nrows=len(waittime_values),
                sharex=True,
                sharey=True,
                layout="constrained",
            )

            for row, run in enumerate(runtime_values):
                for col, wait in enumerate(waittime_values):
                    values, errors = data[f"{run},{wait}_{axis}"]
                    axs[row, col].errorbar(
                        x, values, errors, label=f"{bba_stats(values)}"
                    )
                    axs[row, col].legend(fontsize="xx-small", loc=1)
                    axs[row, col].grid(which="both", axis="both")
                    axs[row, col].set_xlim(0, len(values))
                    if row == len(runtime_values) - 1:
                        plt.setp(axs[row, col], xlabel=f"{wait}")
                    if col == 0:
                        plt.setp(axs[row, col], ylabel=f"{run}")
            fig.suptitle(f"Feedback timings with 100micron offset {axis}")
            fig.supxlabel("Run time (s)")
            fig.supylabel("Wait time (s)")
            plt.savefig(
                f"{TEMP_FILEPATH_ROOT}/feedbacks_test_plot_{axis}.png",
                bbox_inches="tight",
                dpi=300,
            )
            plt.close()

    if honing:
        repeats = 20
        cycles = 16
        frequency = 8
        qs = 0.01
        cs = 1

        # 0 micron offset
        honing_dict = {  # method, axis, offset, colour, linestyle, values, errors
            # 0 micron offset
            1: ["BBA", "x", 0, "green", "-", [], []],
            2: ["BBA", "y", 0, "green", "--", [], []],
            3: ["FBBA", "x", 0, "blue", "-"],
            4: ["FBBA", "y", 0, "red", "--"],
            # 0.1 micron offset
            5: ["BBA", "x", 0.1, "darkgreen", "-", [], []],
            6: ["BBA", "y", 0.1, "darkgreen", "--", [], []],
            7: ["FBBA", "x", 0.1, "darkblue", "-"],
            8: ["FBBA", "y", 0.1, "darkred", "--"],
        }

        for key, values in honing_dict.items():
            if values[0] != "BBA":
                data = np.genfromtxt(
                    f"{TEMP_FILEPATH_ROOT}/honing_{values[0]}_r{repeats}_c{cycles}_f{frequency}_qs{qs}_cs{cs}_{values[1]}_offset{values[2]}.csv",
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

        def find_honing_indices(
            method=["BBA", "FBBA"], axis=["x", "y"], offset=[0, 0.1]
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
                if remove:
                    options.remove(key)
            return options

        def plot_honing(key):
            data_info = honing_dict[key]
            plt.errorbar(
                x_axis,
                data_info[4],
                data_info[5],
                marker=".",
                linestyle=data_info[4],
                capsize=5,
                color=data_info[3],
                label=f"{data_info[0]} in {data_info[1]} at {data_info[2]}: {bba_stats(data_info[4])}",
            )

        def finalise_honing(title):
            lower_title = title.lower()
            filename = f"honing_{lower_title.replace(' ', '_')}"
            plt.xlim(0, 8)
            plt.xlabel("Run Number")
            plt.ylabel("Offset Value (mm)")
            plt.grid(which="major", axis="both")
            plt.legend("xx-small")
            plt.savefig(
                f"{TEMP_FILEPATH_ROOT}/{filename}.png", bbox_inches="tight", dpi=300
            )
            plt.close()

        # FBBA vs BBA plot for each axis.
        for axis in ["x", "y"]:
            indices = find_honing_indices(axis=[axis])
            for i in indices:
                plot_honing(i)
            finalise_honing(f"FBBA vs BBA in {axis}")

        # FBBA vs BBA for each offset
        for offset in [0, 0.1]:
            indices = find_honing_indices(offset=[offset])
            for i in indices:
                plot_honing(i)
            finalise_honing(f"FBBA vs BBA at {offset}")

        # FBBA vs BBA all options.
        indices = find_honing_indices()
        for i in indices:
            plot_honing(i)
        finalise_honing("FBBA vs BBA all options")

    if time:
        repeats = 10
        frequencies = [8, 37, 83, 107, 137, 179]
        total_time = [0.5, 1, 1.5, 2]
        quadrupole_scalar = 0.01
        corrector_scalar = 1
        repeats = 10
        offset = 0.1
        data = {}

        for time in total_time:
            for freq in frequencies:
                for axis in ["x", "y"]:
                    cycles = int(np.floor(time * freq))
                    d = np.genfromtxt(
                        f"{TEMP_FILEPATH_ROOT}/time_freq_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_{axis}_offset{offset}.csv",
                        delimiter=",",
                    )
                    data[f"{time},{freq}_{axis}"] = [d[0, :], d[1, :]]

        for key, (values, errors) in data.items():
            init = initial_offset[key[-1]]
            cum_values = np.cumsum(values)
            y_values = [init] + [value + init for value in cum_values]
            y_errors = [0] + [e for e in errors]
            data[key] = [y_values, y_errors]

        for axis in ["x", "y"]:
            fig, axs = plt.subplots(
                ncols=len(total_time),
                nrows=len(frequencies),
                sharex=True,
                sharey=True,
                layout="constrained",
            )

            for row, time in enumerate(total_time):
                for col, freq in enumerate(frequencies):
                    values, errors = data[f"{time},{freq}_{axis}"]
                    axs[row, col].errorbar(
                        x, values, errors, label=f"{bba_stats(values)}"
                    )
                    axs[row, col].legend(fontsize="xx-small", loc=1)
                    axs[row, col].grid(which="both", axis="both")
                    axs[row, col].set_xlim(0, len(values))
                    if row == len(total_time) - 1:
                        plt.setp(axs[row, col], xlabel=f"{freq}")
                    if col == 0:
                        plt.setp(axs[row, col], ylabel=f"{time}")
            fig.suptitle(
                f"Time of measurement and Frequency with 100micron offset {axis}"
            )
            fig.supxlabel("Aquisition time (s)")
            fig.supylabel("Frequency (Hz)")
            plt.savefig(
                f"{TEMP_FILEPATH_ROOT}/frequency_time_plot_{axis}.png",
                bbox_inches="tight",
                dpi=300,
            )
            plt.close()

        pass

    if running:
        situation = ["baseline", "cooling", "warming"]

        freq = 8
        quadrupole_scalar = 0.01
        corrector_scalar = 1
        cycles = 16
        repeats = 30
        x = np.arange(0, repeats)

        data = {}
        for sit in situation:
            for axis in ["x", "y"]:
                d = np.genfromtxt(
                    f"{TEMP_FILEPATH_ROOT}/running_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_{axis}_{situation}.csv",
                    delimiter=",",
                )
                data[f"{sit},{axis}"] = [d[0, :], d[1, :]]

        for key, (values, errors) in data.items():
            init = initial_offset[key[-1]]
            cum_values = np.cumsum(values)
            y_values = [init] + [value + init for value in cum_values]
            y_errors = [0] + [e for e in errors]
            data[key] = [y_values, y_errors]

        for axis in ["x", "y"]:
            for key, (values, errors) in data.items():
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
            plt.legend("xx-small")
            plt.savefig(
                f"{TEMP_FILEPATH_ROOT}/running_{axis}.png", bbox_inches="tight", dpi=300
            )
            plt.close()

        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/running_cooling_down_plot.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.close()

    if swap:
        quadrupole_scalar = 0.01
        corrector_scalar = 1
        offset = 0.1
        repeats = 16
        x = np.arange(0, repeats)
        cycles = 16
        frequency = 8
        directions = [["HORIZONTAL", "VERTICAL"], ["VERTICAL", "HORIZONTAL"]]
        data = {}

        for order in directions:
            for axis in ["x", "y"]:
                d = np.genfromtxt(
                    f"{TEMP_FILEPATH_ROOT}/swap_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_{axis}_order_{order[0]}.csv",
                    delimiter=",",
                )
                data[f"{order[0]},{axis}"] = [d[0, :], d[1, :]]

        for key, (values, errors) in data.items():
            init = initial_offset[key[-1]]
            cum_values = np.cumsum(values)
            y_values = [init] + [value + init for value in cum_values]
            y_errors = [0] + [e for e in errors]
            data[key] = [y_values, y_errors]

        for key, (values, errors) in data.items():
            if key[-1] == "x":
                linestyle = "-"
            else:
                linestyle = "--"
            plt.errorbar(
                x,
                values,
                errors,
                capsize=5,
                marker=".",
                linestyle=linestyle,
                label=f"Order: {key}, {bba_stats(values)}",
            )
        plt.ylabel("Offset Value (mm)")
        plt.xlabel("Run Number")
        plt.xlim(0, repeats)
        plt.grid(which="major", axis="both")
        plt.legend("xx-small")
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/swapped_order.png", bbox_inches="tight", dpi=300
        )
        plt.close()

        pass


if __name__ == "__main__":
    main()
