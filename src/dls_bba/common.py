import logging as log
import os
from typing import NamedTuple, Union
from datetime import datetime
from dls_bba.algorithm import Algorithm, FastBBA, SimFastBBA, SlowBBA
from dls_bba.lattice import Lattice
from dls_bba.logger import get_new_logger

ISO_TIME_FORMAT_STRING: str = "%Y%m%dT%H%M%S"
"""ISO 8601 in the format YYYYMMDDThhmmss. Note. T seperates date and time."""

ALGORITHMS: dict[str, type[Algorithm]] = {
    "Slow BBA": SlowBBA,
    "Fast BBA": FastBBA,
    "Sim Fast BBA": SimFastBBA,
}


def get_isotime():
    """"""
    now = datetime.now()
    isotime = now.strftime(ISO_TIME_FORMAT_STRING)
    return isotime


def entrypoints(elements: list[str], method: str):
    """"""
    # Setup folders and lattice.
    folderpath = setup_folders(method)

    # kwargs = parse_args(...)
    # lattice = Lattice(kwargs)
    # TODO: Need to create a dictionary with cli/gui args, which is passed into lattice when Lattice is created.
    lattice = Lattice()

    element_tuple_list = []
    for element in elements:
        tuples = lattice.generate_bba_namedtuples(element)
        element_tuple_list.append(tuples)

    lattice.zero_origins()

    try:
        algorithm: Algorithm = ALGORITHMS[method](lattice)
    except KeyError as e:
        message = f"Invalid BBA method selected: {method}"
        log.critical(message)
        raise e

    # if method == "Slow BBA":
    #     algorithm: Algorithm = SlowBBA(lattice)  # type: ignore
    # elif method == "Fast BBA":
    #     algorithm: Algorithm = FastBBA(lattice)  # type: ignore
    # elif method == "Sim Fast BBA":
    #     algorithm: Algorithm = SimFastBBA(lattice)  # type: ignore
    # else:
    #     message = "Invalid method selected."
    #     log.critical(message)
    #     raise ValueError(message)

    results = {}
    for element_tuple_pair in element_tuple_list:
        results_list = beam_based_alignment(algorithm, element_tuple_pair, folderpath)
        # TODO sort unpacking
        for key, value in results_list:
            results[key] = value

    lattice.apply_bba(results)
    lattice.restore_origins()


def setup_folders(method: str):
    """"""
    foldername = f"{method}-{get_isotime()}"
    cwd = os.getcwd()
    bba_folderpath = os.path.join(cwd, foldername)
    os.makedirs(bba_folderpath)
    get_new_logger(bba_folderpath)
    # TODO: Create a txt file to write to.
    return bba_folderpath

    # def beam_based_alignment(algorithm, element_tuples, folderpath):
    #     """"""
    #     # If key is bpm pv with axis?
    #     # just save immediately to a dictionary?

    #     if algorithm.__name__ in ["FastBBA", "SlowBBA"]:
    #         # iterate through element_tuple seperately.
    #         for element_tuple in element_tuples:
    #             [(key, value)] = bba(algorithm, element_tuple, folderpath)

    #     elif algorithm.__name__ in ["SimFastBBA"]:
    #         # dont
    #         [(key1, value1), (key2, value2)] = bba(algorithm, element_tuples, folderpath)

    # TODO: All get passed x, y pair,
    # slow and fast just do them one at a time,
    # vs sim that does both.

    # KEY/value MUST HAVE AXIS INDICATOR. either key=pv_x/y or value = ["x", value]
    # return key, value
    # return  # key, value


def bba(algorithm, element_tuple, folderpath, save=False):
    """"""
    # TODO: Has to handle multiple tuples?
    algorithm._lattice.check_beam_current(start=True)
    algorithm._lattice.apply_feedbacks()
    while True:
        rawdata = algorithm.run(element_tuple)  # run x y together but seperately .
        if algorithm._lattice.check_beam_current(end=True):
            break
    rawdata.save(folderpath)
    results, results_list = algorithm.analyse(rawdata)
    results.save(folderpath)
    # TODO: must plot and ask for approval.
    results.apply(folderpath)
    return results_list
