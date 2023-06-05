import logging as log
from typing import Any

# import matplotlib
import matplotlib.pyplot as plt

from dls_bba.algorithm import Algorithm
from dls_bba.common import ALGORITHMS, setup_beam_based_alignment, setup_folders
from dls_bba.datatypes import Results
from dls_bba.lattice import Lattice

# matplotlib.use("Qt5Agg")


def cli_show_bpm_options(
    extra_config_files: list[str],
    additional_options: dict[str, Any],
):
    """"""
    lattice = Lattice(extra_config_files, additional_options)
    print(lattice.bpms_names)


def cli_entrypoint(
    method: str,
    element: str,
    folder_path: str,
    extra_config_files: list[str],
    additional_options: dict[str, Any],
):
    """"""
    lattice = Lattice(extra_config_files, additional_options)
    save_location = setup_folders(method, folder_path)

    # TODO: Can be moved inside setup_beam_based_alignment.
    # Currently outside so setup will work with multiple component pairs.
    components_pair_list = [lattice.generate_component_pairings(element)]

    try:
        algorithm: Algorithm = ALGORITHMS[method](lattice)
    except KeyError as e:
        message = f"Invalid BBA method selected: {method}"
        log.critical(message)
        raise e

    setup_beam_based_alignment(lattice, algorithm, components_pair_list, save_location)


def cli_quadcenter_plot(file_path: str):
    """"""
    results_object = Results.from_file(file_path)

    keys = results_object.results.keys()

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

            value, error = results_object.offsets[key]
            axs[a_index, q_index].axvline(x=value, color="k")
            axs[a_index, q_index].axvspan(
                xmin=value - abs(error), xmax=value + abs(error), color="gray"
            )
            axs[a_index, q_index].grid(which="both", axis="both")
    plt.show()
