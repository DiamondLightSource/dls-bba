from typing import Any, Dict, List

from dls_bba.algorithm import Algorithm
from dls_bba.common import ALGORITHMS, setup_beam_based_alignment, setup_folders
from dls_bba.components import get_component_pairs
from dls_bba.machine import Machine


def cli_entrypoint(
    method: str,
    element: List[str],
    folder_path: str,
    extra_config_files: List[str],
    additional_options: Dict[str, Any],
) -> None:
    """Entry point for the CLI.

    Args:
        method: The method to use.
        element: The element to use.
        folder_path: The folder path to use.
        extra_config_files: The extra config files to use.
        additional_options: The additional options to use.
    """
    save_location = setup_folders(method, folder_path)

    machine = Machine(extra_config_files, additional_options)

    # TODO: Can be moved inside setup_beam_based_alignment.
    # Currently outside so setup will work with multiple component pairs.
    component_pairings = get_component_pairs(machine, element)

    # Argparse stops invalid methods being selected.
    algorithm: Algorithm = ALGORITHMS[method](machine)

    setup_beam_based_alignment(machine, algorithm, component_pairings, save_location)
