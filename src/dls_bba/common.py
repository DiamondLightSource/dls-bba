import os
from typing import List, Optional
import logging as log

from dls_bba.algorithm import Algorithm
from dls_bba.beam_current import BeamCurrentCheck
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


def setup_folders(method: str, folder_path: Optional[str] = None) -> str:
    """"""
    foldername = f"{method}-{get_isotime()}"
    file = os.getcwd() if folder_path is None else folder_path
    bba_folderpath = os.path.join(file, foldername)
    os.makedirs(bba_folderpath)
    get_new_logger(bba_folderpath)
    return bba_folderpath


def setup_beam_based_alignment(
    machine: Machine,
    algorithm: Algorithm,
    components_pairs: list[list[Components]],
    save_location: str,
):
    """"""
    results_list: List[Results] = []
    machine.zero_origins(save_location)
    beam_current_decay = BeamCurrentCheck(machine)

    for components_pair in components_pairs:
        results = paired_beam_based_alignment(
            algorithm, machine, components_pair, save_location
        )
        results_list.append(results)
        beam_current_decay.check_beam_decay()

    algorithm.use_bba_offsets(results_list, save_location)

    cancel_all_oscillations(machine.config)
    machine.restore_origins(save_location)


def paired_beam_based_alignment(
    algorithm: Algorithm,
    machine: Machine,
    components_pair: list[Components],
    save_location: str,
):
    """"""
    beam_current_drop = BeamCurrentCheck(machine)

    while True:
        machine.check_feedbacks()
        rawdata = algorithm.run(components_pair)

        if beam_current_drop.check_beam_drop():
            break

    rawdata.save(save_location)
    results = algorithm.analyse(rawdata)
    results.save(save_location)
    return results
