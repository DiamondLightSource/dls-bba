import logging as log
import os
from typing import Any, Optional

from cothread.catools import caget

from dls_bba.algorithm import Algorithm, FastBBA, SimFastBBA, SlowBBA
from dls_bba.components import Components
from dls_bba.datatypes import Results
from dls_bba.isotime import get_isotime
from dls_bba.lattice import ORIGIN_SUFFIXES, Lattice
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


def setup_beam_based_alignment(
    lattice: Lattice,
    algorithm: Algorithm,
    components_pairs: list[list[Components]],
    save_location: str,
):
    """"""
    results_list = []
    lattice.zero_origins()

    for components_pair in components_pairs:

        results = paired_beam_based_alignment(algorithm, components_pair, save_location)
        results_list.append(results)

    confirm_and_apply_results(lattice, results_list, save_location)

    lattice.restore_origins()


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


def confirm_and_apply_results(
    lattice: Lattice, results_list: list[Results], save_location: str
):
    """"""
    results_dict = {}

    for results in results_list:
        bpm_name, bpm_results = results.sort()
        for axis, bpm_result in zip(["x", "y"], bpm_results):
            key = bpm_name + ORIGIN_SUFFIXES["BBA"].format(axis=axis.upper())
            old_value = caget(key)
            results_dict[key] = [old_value + bpm_result[0], bpm_result[1]]

    write_result_txt(results_dict, save_location)

    # TODO: Wont work as needs the results object with additional info.
    lattice.confirm_results()


def write_result_txt(results_dictionary: dict[str, list[float]], save_location: str):
    """"""
    filename = os.path.join(save_location, "results.txt")
    with open(filename, "w") as writer:

        for key, (value, error) in results_dictionary.items():
            old_value = caget(key)
            line = f"{key}, Old: {old_value}, New: {value} +- {error}"
            writer.write(line)

        writer.close()
