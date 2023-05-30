import logging as log
import os

from dls_bba.algorithm import Algorithm, FastBBA, SimFastBBA, SlowBBA
from dls_bba.lattice import Lattice
from dls_bba.logger import get_new_logger
from dls_bba.isotime import get_isotime

ALGORITHMS: dict[str, type[Algorithm]] = {
    "SlowBBA": SlowBBA,
    "FastBBA": FastBBA,
    "SimFastBBA": SimFastBBA,
}


def entrypoints(elements: list[str], method: str, **kwargs):
    """"""
    # Setup folders and lattice.
    folderpath = setup_folders(method)

    # kwargs = parse_args(...)
    # lattice = Lattice(kwargs)
    # TODO: Need to create a dictionary with cli/gui args, which is passed into lattice when Lattice is created.
    lattice = Lattice()

    component_pair_list = []
    for element in elements:
        component_pair = lattice.generate_component_pairings(element)
        component_pair_list.append(component_pair)

    lattice.zero_origins()

    try:
        algorithm: Algorithm = ALGORITHMS[method](lattice)
    except KeyError as e:
        message = f"Invalid BBA method selected: {method}"
        log.critical(message)
        raise e

    results = {}
    for component_pair in component_pair_list:
        results_list = bba(algorithm, component_pair_list, folderpath)
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
    algorithm._lattice.check_feedbacks()
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
