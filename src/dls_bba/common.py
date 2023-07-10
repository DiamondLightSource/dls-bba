import os
from typing import List, Optional

from dls_bba.algorithm import Algorithm
from dls_bba.components import Components
from dls_bba.datatypes import Results
from dls_bba.excite import cancel_all_oscillations
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
"""The algorithm names and classes that are available."""


def setup_folders(method: str, folder_path: Optional[str] = None) -> str:
    """This function performs the setup of BBA, including creating a folder
    that is named from the ISO time, and starting the logging process.

    Args:
        method: The algorithm class name.
        folderpath: The folderpath to create the data saving folder in.
    """
    foldername = f"{method}-{get_isotime()}"
    file = os.getcwd() if folder_path is None else folder_path
    bba_folderpath = os.path.join(file, foldername)
    os.makedirs(bba_folderpath)
    get_new_logger(bba_folderpath)
    return bba_folderpath


def setup_beam_based_alignment(
    machine: Machine,
    algorithm: Algorithm,
    component_pairs: list[list[Components]],
    save_location: str,
) -> None:
    """This function performs the setup of the order of BBA processes with the machine,
    such as zeroing origins and when to apply the results.

    Args:
        machine: The machine object
        algorithm: The algorithm class.
        component_pairs: The list of component pairs chosen.
        save_location: The location within which to save the data.
    """
    results_list: List[Results] = []
    machine.zero_origins(save_location)

    for component_pair in component_pairs:
        results = paired_beam_based_alignment(
            algorithm, machine, component_pair, save_location
        )
        results_list.append(results)

    algorithm.use_bba_offsets(results_list, save_location)

    cancel_all_oscillations(machine.config)
    machine.restore_origins(save_location)


def paired_beam_based_alignment(
    algorithm: Algorithm,
    machine: Machine,
    component_pair: list[Components],
    save_location: str,
) -> Results:
    """This function controls the order of performing a paired BBA on both axes.

    Args:
        machine: The machine object
        algorithm: The algorithm class.
        component_pair: A component pair.
        save_location: The location within which to save the data.
    """
    machine.store_starting_beam_current()

    while True:
        machine.check_feedbacks()
        rawdata = algorithm.run(component_pair)

        if machine.check_beam_current():
            break

    rawdata.save(save_location)
    results = algorithm.analyse(rawdata)
    results.save(save_location)
    return results
