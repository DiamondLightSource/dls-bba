import logging as log
import os
from typing import Any

from dls_bba.algorithm import Algorithm
from dls_bba.datatypes import BPMOffset, FullResults, OscillationPlane
from dls_bba.fbba import FastBBA
from dls_bba.isotime import get_isotime
from dls_bba.logger import get_new_logger
from dls_bba.machine import Machine
from dls_bba.sbba import SlowBBA
from dls_bba.simfbba import SimFastBBA

ALGORITHMS: dict[str, type[Algorithm]] = {
    "SlowBBA": SlowBBA,
    "FastBBA": FastBBA,
    "SimFastBBA": SimFastBBA,
}


def setup_folders_and_logger(
    method: str, folder_path: str | None = None, gui: log.Handler | None = None
) -> str:
    """Setup the folders and logger for the BBA run.

    Args:
        method: The method of BBA.
        folder_path: The parent folder path to save to.
        gui: The GUI logging handler if it exists.

    Returns:
        The folder path to save/load from/to.
    """
    foldername = f"{method}-{get_isotime()}"
    file = os.getcwd() if folder_path is None else folder_path
    bba_folderpath = os.path.join(file, foldername)
    os.makedirs(bba_folderpath)
    get_new_logger(bba_folderpath, gui)
    # Avoid filling log files with matplotlib logging junk.
    log.getLogger("matplotlib.font_manager").disabled = True
    return bba_folderpath


def apply_offsets_files(
    filepath: str,
    machine: Machine | None = None,
    config_files: list[Any] | None = None,
    additional_config: dict[str, Any] | None = None,
) -> None:
    """Apply the supplied offsets file to the machine.

    Args:
        filepath: The full filepath to the offsets .json file.
        machine: The machine object.
        config_files: List of extra configuration files to load.
        additional_config: Dictionary of configuration overrides.
    """
    if machine is None:
        machine = Machine(config_files, additional_config)
    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    machine.restore_offsets(dirname, [filename])


def apply_single(
    filepath: str,
    machine: Machine | None = None,
    config_files: list[Any] | None = None,
    additional_config: dict[str, Any] | None = None,
) -> None:
    """Apply a single BBA results file to the machine.

    Args:
        filepath: The full filepath to the results.mat file.
        machine: The machine object.
        config_files: List of extra configuration files to load.
        additional_config: Dictionary of configuration overrides.
    """
    if machine is None:
        machine = Machine(config_files, additional_config)
    results_file = FullResults.from_file(filepath)
    algorithm = FastBBA(machine)
    algorithm.apply_bba_offsets(results_file.bpm_offsets)


def apply_folder(
    folderpath: str,
    machine: Machine | None = None,
    config_files: list[Any] | None = None,
    additional_config: dict[str, Any] | None = None,
) -> None:
    """Apply multiple BBA results files to the machine.

    Args:
        folderpath: The full filepath to the folder which contains results.mat files.
        machine: The machine object.
        config_files: List of extra configuration files to load.
        additional_config: Dictionary of configuration overrides.
    """
    if machine is None:
        machine = Machine(config_files, additional_config)

    good_files = []
    for file in os.listdir(folderpath):
        if file.endswith("-results.mat"):
            good_files.append(os.path.join(folderpath, file))

    load_folder_results = [FullResults.from_file(file) for file in good_files]

    offsets_dict: dict[str, OscillationPlane[BPMOffset]] = {}
    for results in load_folder_results:
        offsets_dict.update(results.bpm_offsets.items())

    algorithm = FastBBA(machine)
    algorithm.apply_bba_offsets(offsets_dict)
