import os
from typing import List

# isort: off
import matplotlib

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt  # noqa E402

# isort: on
from dls_bba.datatypes import CalculatedOffset, Results  # noqa E402
from dls_bba.machine import Machine  # noqa E402


def bba_offsets_folder(
    machine: Machine,
    results_list: List[Results],
    save_location: str,
    save: bool = False,
) -> None:
    offsets_dict: dict[str, CalculatedOffset] = {}
    for results in results_list:
        offsets_dict.update(results.offsets.items())

    bba_offsets_plot(machine, offsets_dict, save_location, save)


def bba_offsets_plot(
    machine: Machine,
    offsets_dict: dict[str, CalculatedOffset],
    save_location: str,
    save: bool = False,
) -> plt.figure:
    change_in_x = []
    change_in_dx = []
    for bpm_name in machine.bba_x_pvs:
        if bpm_name in offsets_dict.keys():
            calc_offsets = offsets_dict[bpm_name]
            change_in_x.append(calc_offsets.diff_value)
            change_in_dx.append(calc_offsets.diff_value)
        else:
            change_in_x.append(0)
            change_in_dx.append(0)

    change_in_y = []
    change_in_dy = []
    for bpm_name in machine.bba_y_pvs:
        if bpm_name in offsets_dict.keys():
            calc_offsets = offsets_dict[bpm_name]
            change_in_x.append(calc_offsets.diff_value)
            change_in_dx.append(calc_offsets.diff_value)
        else:
            change_in_y.append(0)
            change_in_dy.append(0)

    fig, (ax1, ax2) = plt.subplots(2, sharex=True, tight_layout=True)
    fig.suptitle("Change in BBA values")
    ax1.set_xlim(0, 174)
    ax1.axhline(y=0, color="k", linestyle="-", alpha=0.5)
    ax1.plot(change_in_x, color="b")
    ax1.set_ylabel("Horizontal")
    ax1.grid(which="both", axis="both")
    ax2.plot(change_in_y, color="r")
    ax2.axhline(y=0, color="k", linestyle="-", alpha=0.5)
    ax2.set_ylabel("Vertical")
    ax2.grid(which="both", axis="both")
    fig.supxlabel("BPM Number")
    fig.supylabel("Change in BBA offset [mm]")
    if save:
        path = os.path.join(save_location, "bba_offsets_plot.png")
        plt.savefig(path, dpi=300)
    plt.show()

    return fig


def bowtie_plot(filepath: str, save_location: str, save: bool = False) -> plt.figure:
    results_object = Results.from_file(filepath)
    bpm_name = results_object.metadata["bpm_name"]
    keys = results_object.results.keys()
    keys = keys
    quad_names = []
    for key in keys:
        quad_name = key.split("_")[0]
        if quad_name not in quad_names:
            quad_names.append(quad_name)

    fig, axs = plt.subplots(nrows=2, ncols=len(quad_names))

    for q_index, quad_name in enumerate(quad_names):
        for a_index, axis in enumerate(["x", "y"]):
            key = f"{quad_name}_{axis}"

            if a_index == 0:
                axs[a_index, q_index].set_title(f"{quad_name}")
            if q_index == 0:
                axs[a_index, q_index].set_ylabel(f"Axis: {axis}")

            color = "b" if axis == "x" else "r"

            x = results_object.plotting[key]["x"]
            y = results_object.plotting[key]["y"]

            axs[a_index, q_index].plot(x, y, color=color)

            value = results_object.offsets[key].diff_value
            error = results_object.offsets[key].diff_error
            axs[a_index, q_index].axvline(x=value, color="k")
            axs[a_index, q_index].axvspan(
                xmin=value - abs(error), xmax=value + abs(error), color="gray"
            )
            axs[a_index, q_index].grid(which="both", axis="both")

    if save:
        path = os.path.join(save_location, f"{bpm_name}_bowtie_plot.png")
        plt.savefig(path, dpi=300)

    plt.show()

    return fig
