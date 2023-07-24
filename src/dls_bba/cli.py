from typing import Any
import logging as log

# from dls_bba.algorithm import Algorithm
# from dls_bba.common import ALGORITHMS, setup_beam_based_alignment, setup_folders
# from dls_bba.components import get_component_pairs
from dls_bba.machine import Machine
from dls_bba.plotting import bowtie_plot


def cli_show_bpm_options(
    extra_config_files: list[str],
    additional_options: dict[str, Any],
):
    """"""
    machine = Machine(extra_config_files, additional_options)
    log.info(machine.bpms_names)


def cli_show_cell_options(
    cell_number: str,
    extra_config_files: list[str],
    additional_options: dict[str, Any],
):
    """"""
    machine = Machine(extra_config_files, additional_options)
    if cell_number not in machine.cell_dictionary.keys():
        log.info("Invalid cell selected. Try cells '00' to '24'")
    else:
        log.info(machine.cell_dictionary[cell_number])


# def cli_entrypoint(
#     method: str,
#     element: str,
#     folder_path: str,
#     extra_config_files: list[str],
#     additional_options: dict[str, Any],
# ):
#     """"""
#     save_location = setup_folders(method, folder_path)

#     machine = Machine(extra_config_files, additional_options)

#     # TODO: Can be moved inside setup_beam_based_alignment.
#     # Currently outside so setup will work with multiple component pairs.
#     component_pairings = get_component_pairs(machine, element)

#     # Argparse stops invalid methods being selected.
#     algorithm: Algorithm = ALGORITHMS[method](machine)

#     setup_beam_based_alignment(machine, algorithm, component_pairings, save_location)


def cli_quadcenter_plot(filepath: str, save_location: str, save: bool = False):
    """"""
    bowtie_plot(filepath, save_location, save)
