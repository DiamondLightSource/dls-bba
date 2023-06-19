import os
from typing import Optional

from dls_bba.algorithm import Algorithm, FastBBA, SimFastBBA, SlowBBA
from dls_bba.components import Components
from dls_bba.isotime import get_isotime
from dls_bba.lattice import Lattice
from dls_bba.logger import get_new_logger

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
    lattice: Lattice,
    algorithm: Algorithm,
    components_pairs: list[list[Components]],
    save_location: str,
):
    """"""
    results_list = []
    # lattice.zero_origins()

    for components_pair in components_pairs:
        results = paired_beam_based_alignment(algorithm, components_pair, save_location)
        results_list.append(results)

    lattice.draw_bba_plot_and_apply(results_list, save_location)

    # lattice.restore_origins()


def paired_beam_based_alignment(
    algorithm: Algorithm, components_pair: list[Components], save_location: str
):
    """"""
    algorithm._lattice.store_starting_beam_current()
    algorithm._lattice.check_feedbacks()

    while True:
        rawdata = algorithm.run(components_pair)
        if algorithm._lattice.check_beam_current():
            break

    rawdata.save(save_location)
    results = algorithm.analyse(rawdata)
    results.save(save_location)
    return results
