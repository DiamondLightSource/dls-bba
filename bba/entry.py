"""This is the entry point for the bba module."""
import argparse
import logging as log
from datetime import datetime

from bba import accelerator as acc
from bba.common import PLANE_VALUES, Algorithm
from bba.fbba import FBBA
from bba.sbba import SBBA

LOG_FORMAT = "%(levelname)-7s: %(message)s"


def get_filename_prefix(method):
    """Returns a time string for the filename."""
    now = datetime.now()
    datestring = now.strftime("%Y-%m-%dT%H-%M-%S")
    return "{}-{}".format(method, datestring)


def get_new_logger(method):
    logger = log.getLogger()
    filename = "data/{}.log".format(get_filename_prefix(method))
    file_handler = log.FileHandler(filename)
    file_handler.setLevel(log.DEBUG)
    formatter = log.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(log.StreamHandler())
    logger.setLevel(log.DEBUG)


def parse_args():
    parser = argparse.ArgumentParser(description="Take BBA measurements")
    # parser.add_argument(
    #     "-p",
    #     "--plane",
    #     dest="plane",
    #     action="store_const",
    #     default="HORIZONTAL",
    #     const="VERTICAL",
    #     help="Which plane to measure",
    # )
    parser.add_argument(
        "-m",
        "--method",
        dest="method",
        action="store_const",
        default="FBBA",
        const="SBBA",
        help="Which BBA method to use"
    )
    parser.add_argument(
        "-o",
        "--orbit",
        dest="max_orbit",
        action="store",
        default=15,
        help="The maximum orbit size to invoke FOFB in um."
    )
    parser.add_argument(
        "-a",
        "--apply",
        dest="apply",
        action="store_true",
        default=False,
        help="Apply the result of each bba?"
    )
    parser.add_argument(
        "-p",
        "--plot",
        dest="plot",
        action="store_true",
        default=False,
        help="Plot the results?"
    )
    parser.add_argument(
        "-f",
        "-fft",
        dest="fft",
        action="store_true",
        default=False,
        help="Use fft analysis?"
    )
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    method: str = args.method
    max_orbit: int = args.max_orbit
    apply: bool = args.apply
    plot: bool = args.plot
    fft: bool = args.fft

    get_new_logger(method)

    # TODO: System that will accept a number of quads (or cell).
    # TODO: System that will accept bpm selection.

    #pv_list = ['SR01C-DI-EBPM-01'] # First BPM
    #pv_list = ["SR24C-DI-EBPM-07"] # Last BPM

    pv_list = ["SR01A-PC-Q2AB-07"]  # single bpm
    
    # pv_list = ["SR01C-DI-EBPM-05"]  # single quad
    # pv_list = ["SR10C-DI-EBPM-02"]  # multiple quads

    accelerator = acc.Accelerator(ringmode=None)

    element_list = []
    for pv in pv_list:
        element_list.append(accelerator.pv_prefix_to_element(pv))

    # TODO: fbba or sbba selection system in UI.

    fbba = FBBA(accelerator)
    sbba = SBBA(accelerator)

    if method == "FBBA":
        algorithm: Algorithm = fbba
    elif method == "SBBA":
        algorithm: Algorithm = sbba

    # algorithm.configure() #  Only for changing config values.
    for element in element_list:
        for axis in ["VERTICAL", "HORIZONTAL"]:
            filename_prefix = get_filename_prefix(method)
            raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
            raw_data.save(filename_prefix)
            results = algorithm.analyse_data(raw_data, plot, fft)
            results.save(filename_prefix)
            if apply:
                algorithm.apply_results(results)


if __name__ == "__main__":
    main()
