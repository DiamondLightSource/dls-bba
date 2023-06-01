import logging as log
from typing import Any

from dls_bba.algorithm import Algorithm
from dls_bba.common import ALGORITHMS, setup_beam_based_alignment, setup_folders
from dls_bba.lattice import Lattice


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
