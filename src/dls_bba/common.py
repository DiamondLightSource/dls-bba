import os
from typing import Optional

from dls_bba.algorithm import Algorithm
from dls_bba.datatypes import Results
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
    method: str, folder_path: Optional[str] = None, gui=None
) -> str:
    """"""
    foldername = f"{method}-{get_isotime()}"
    file = os.getcwd() if folder_path is None else folder_path
    bba_folderpath = os.path.join(file, foldername)
    os.makedirs(bba_folderpath)
    get_new_logger(bba_folderpath, gui)
    return bba_folderpath


def apply_golden(filepath, machine=None, config_files=None, additional_config=None):
    if machine is None:
        machine = Machine(config_files, additional_config)
    selected_file = os.path.dirname(filepath)
    machine.restore_origins(selected_file)


def apply_single(filepath, machine=None, config_files=None, additional_config=None):
    if machine is None:
        machine = Machine(config_files, additional_config)
    results_file = Results.from_file(filepath)
    algorithm = FastBBA(machine)
    algorithm.apply_bba_offsets(results_file.offsets)


def apply_folder(folderpath, machine=None, config_files=None, additional_config=None):
    if machine is None:
        machine = Machine(config_files, additional_config)

    good_files = []
    for file in os.listdir(folderpath):
        if file.endswith("-results.mat"):
            good_files.append(os.path.join(folderpath, file))

    load_folder_results = [Results.from_file(file) for file in good_files]

    offsets_dict = {}
    for results in load_folder_results:
        offsets_dict.update(results.offsets.items())

    algorithm = FastBBA(machine)
    algorithm.apply_bba_offsets(offsets_dict)
