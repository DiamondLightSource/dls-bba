import os

# isort: off
import matplotlib
import numpy as np

matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt  # noqa E402

# isort: on
from dls_bba.datatypes import BPMOffset, FullResults, OscillationPlane  # noqa E402
from dls_bba.machine import Machine  # noqa E402

MM_TO_UM_UNIT_CONV = 1000
"""The conversion factor from millimeters to micrometers."""


def bba_offsets_folder(
    machine: Machine,
    folder_path: str,
    save: bool = False,
) -> None:
    """Load all results.mat files in a folder and plot the change in BBA offsets.

    Args:
        machine: The machine object.
        folder_path: The path to the folder containing the results.mat files.
        save: Whether to save the plot to the same directory as the results.mat files.
    """
    good_files = []
    for file in os.listdir(folder_path):
        if file.endswith("-results.mat"):
            good_files.append(os.path.join(folder_path, file))

    load_folder_results = [FullResults.from_file(file) for file in good_files]

    offsets_dict: dict[str, OscillationPlane[BPMOffset]] = {}
    for results in load_folder_results:
        offsets_dict.update(results.bpm_offsets.items())

    bba_offsets_plot(machine, offsets_dict, folder_path, save)


def bba_offsets_plot(
    machine: Machine,
    offsets_dict: dict[str, OscillationPlane[BPMOffset]],
    save_location: str,
    save: bool = False,
) -> plt.Figure:
    """Plot the change in BBA offsets for all BPMs.

    Args:
        machine: The machine object.
        offsets_dict: The dictionary of BPM BBA PVs and calculated offsets.
        save_location: The directory to save the plot to.
        save: Whether to save the plot to the save_location directory.

    Returns:
        The figure object.
    """
    x = np.arange(1, len(machine.bba_x_pvs) + 1)
    change_in_x = []
    change_in_dx = []
    for bpm_name in machine.bba_x_pvs:
        if bpm_name.replace("-", "_").replace(":", "__") in offsets_dict.keys():
            calc_offsets = offsets_dict[bpm_name.replace("-", "_").replace(":", "__")].x
            change_in_x.append(calc_offsets.diff_value * MM_TO_UM_UNIT_CONV)  # type: ignore
            change_in_dx.append(abs(calc_offsets.diff_value * MM_TO_UM_UNIT_CONV))  # type: ignore
        else:
            change_in_x.append(0)
            change_in_dx.append(0)

    change_in_y = []
    change_in_dy = []
    for bpm_name in machine.bba_y_pvs:
        if bpm_name.replace("-", "_").replace(":", "__") in offsets_dict.keys():
            calc_offsets = offsets_dict[bpm_name.replace("-", "_").replace(":", "__")].y
            change_in_y.append(calc_offsets.diff_value * MM_TO_UM_UNIT_CONV)  # type: ignore
            change_in_dy.append(abs(calc_offsets.diff_value * MM_TO_UM_UNIT_CONV))  # type: ignore
        else:
            change_in_y.append(0)
            change_in_dy.append(0)
    fig, (ax1, ax2) = plt.subplots(2, sharex=True, tight_layout=True)
    fig.suptitle("Change in BBA values")
    ax1.set_xlim(0, 174)
    ax1.axhline(y=0, color="k", linestyle="-", alpha=0.5)
    ax1.errorbar(
        x, change_in_x, yerr=change_in_dx, color="b", capsize=5, ecolor=(0.5, 0.5, 0.5)
    )
    ax1.set_ylabel("Horizontal [um]")
    ax1.grid(which="both", axis="both")
    ax2.errorbar(
        x, change_in_y, yerr=change_in_dy, color="r", capsize=5, ecolor=(0.5, 0.5, 0.5)
    )
    ax2.axhline(y=0, color="k", linestyle="-", alpha=0.5)
    ax2.set_ylabel("Vertical [um]")
    ax2.grid(which="both", axis="both")
    fig.supxlabel("BPM Number")
    fig.supylabel("Change in BBA offset")

    plt.tight_layout()

    if save:
        path = os.path.join(save_location, "bba_offsets_plot.png")
        plt.savefig(path, dpi=300)

    plt.show()

    return fig


def bowtie_plot(filepath: str, save: bool = False) -> plt.Figure:
    """Plot the bowtie/quadcentre results from a BBA.

    Args:
        filepath: The path to the results.mat file.
        save: Whether to save the plot to the same directory as the results.mat file.

    Returns:
        The figure object.
    """
    results_object: FullResults = FullResults.from_file(filepath)
    bpm_name = results_object.metadata["bpm_name"]
    quad_names = []
    for key in results_object.quad_results.keys():
        quad_name = key.split("__")[0]
        if quad_name not in quad_names:
            quad_names.append(quad_name)

    fig, axes = plt.subplots(nrows=2, ncols=len(quad_names), squeeze=False)

    for q_index, quad_name in enumerate(quad_names):
        for a_index, axis in enumerate(["x", "y"]):
            # Show axis labels and title
            if a_index == 0:
                axes[a_index, q_index].set_title(f"{quad_name.replace('_', '-')}")
            if q_index == 0:
                axes[a_index, q_index].set_ylabel(f"Axis: {axis} [um]")
            # Set colour and create gridlines
            color = "b" if axis == "x" else "r"
            axes[a_index, q_index].grid(which="both", axis="both")
            # Plot measurements
            measurements = results_object.metadata[f"plotting__{quad_name}__{axis}"]
            x = [value * MM_TO_UM_UNIT_CONV for value in measurements["x"]]
            y = [value * MM_TO_UM_UNIT_CONV for value in measurements["y"]]
            axes[a_index, q_index].plot(x, y, color=color, lw=0.5)
            # Display indicator for calculated offset and its standard deviation
            results = results_object.quad_results[quad_name][axis]
            offset = results.mean_offset * MM_TO_UM_UNIT_CONV
            error = results.std_dev_offset * MM_TO_UM_UNIT_CONV
            axes[a_index, q_index].axvline(x=offset, color="k")
            axes[a_index, q_index].axvspan(
                xmin=offset - abs(error), xmax=offset + abs(error), color="gray"
            )
            # Add markers to x axis to indicate location of our 5 sets of x values.
            ylim = axes[a_index, q_index].get_ylim()
            ap = {"edgecolor": color, "fill": False, "headwidth": 5, "headlength": 5}
            for i in range(len(x)):
                axes[a_index, q_index].annotate(" ", (x[i], ylim[0]), arrowprops=ap)

    fig.supylabel("Oscillation Difference [um]")
    fig.supxlabel(f"Oscillation at BPM: {bpm_name} [um]")
    plt.tight_layout()

    if save:
        path = os.path.join(os.path.dirname(filepath), f"{bpm_name}_bowtie_plot.png")
        plt.savefig(path, dpi=300)

    plt.show()

    return fig
