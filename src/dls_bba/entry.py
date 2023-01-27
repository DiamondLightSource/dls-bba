"""This is the entry point for the bba module."""
import argparse
import logging as log
import os
from datetime import datetime

from dls_bba import accelerator as acc
from dls_bba.common import PLANE_VALUES, Algorithm
from dls_bba.fbba import FBBA
from dls_bba.sbba import SBBA

CONSOLE_LOG_FORMAT = "%(levelname)-7s: [%(filename)s:%(lineno)d] — %(message)s"
FILE_LOG_FORMAT = (
    "%(levelname)-7s: %(asctime)s — [%(filename)s:%(lineno)d] — %(message)s"
)

direction_dict = {
    "x": ["HORIZONTAL"],
    "y": ["VERTICAL"],
    "both": ["HORIZONTAL", "VERTICAL"],
}


def get_filename_prefix(method):
    """Returns a time string for the filename."""
    now = datetime.now()
    datestring = now.strftime("%Y-%m-%dT%H-%M-%S")
    return "{}-{}".format(method, datestring)


def get_new_logger(method, filepath):
    if filepath is None:
        filepath = "data"
    logger = log.getLogger()
    logger.setLevel(log.NOTSET)
    filename = "{}/{}.log".format(filepath, get_filename_prefix(method))
    # Console handler
    console_handler = log.StreamHandler()
    console_handler.setLevel(log.INFO)
    console_handler.setFormatter(log.Formatter(CONSOLE_LOG_FORMAT))
    logger.addHandler(console_handler)
    # File handler
    file_handler = log.FileHandler(filename)
    file_handler.setLevel(log.DEBUG)
    file_handler.setFormatter(log.Formatter(FILE_LOG_FORMAT))
    logger.addHandler(file_handler)


def parse_args():
    parser = argparse.ArgumentParser(description="Take BBA measurements")
    parser.add_argument(
        "-m",
        "--method",
        dest="method",
        action="store_const",
        default="FBBA",
        const="SBBA",
        help="Which BBA method to use",
    )
    parser.add_argument(
        "-l",
        "--location",
        dest="directory",
        default=os.getcwd(),
        help="The directory path to where the data should be stored.",
    )
    parser.add_argument(
        "-d",
        "--direction",
        dest="directions",
        choices=direction_dict.keys(),
        default=list(direction_dict)[2],
        help="The directions that bba will be performed in.",
    )
    parser.add_argument(
        "-o",
        "--orbit",
        dest="max_orbit",
        action="store",
        default=15,
        help="The maximum orbit size to invoke FOFB in um.",
    )
    parser.add_argument(
        "-a",
        "--apply",
        dest="apply",
        action="store_true",
        default=False,
        help="Apply the result of each bba?",
    )
    parser.add_argument(
        "-p",
        "--plot",
        dest="plot",
        action="store_true",
        default=False,
        help="Plot the results?",
    )
    parser.add_argument(
        "-f",
        "-fft",
        dest="fft",
        action="store_true",
        default=False,
        help="Use fft analysis?",
    )
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    method: str = args.method
    filepath: str = args.directory
    directions_list: list = direction_dict[args.directions]
    max_orbit: int = args.max_orbit
    apply: bool = args.apply
    plot: bool = args.plot
    fft: bool = args.fft

    get_new_logger(method, filepath)
    pv_list = ["SR01A-PC-Q2AB-07"]

    accelerator = acc.Accelerator(ringmode=None)

    element_list = []
    for pv in pv_list:
        element_list.append(accelerator.pv_prefix_to_element(pv))

    if method == "FBBA":
        algorithm: Algorithm = FBBA(accelerator)
    elif method == "SBBA":
        algorithm: Algorithm = SBBA(accelerator)

    for element in element_list:
        filename_store = []
        for axis in directions_list:
            filename_prefix = get_filename_prefix(method)
            initial_current = algorithm._accelerator.get_beam_current()
            while True:
                # if fofb_trigger:
                #     algorithm.toggle_fofb()
                raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
                if algorithm.check_beam_current(initial_current):
                    break
            raw_data.save(filename_prefix, filepath)
            results = algorithm.analyse_data(raw_data, plot, fft)
            filename = results.save(filename_prefix, filepath)
            filename_store.append([filename])
        if apply:
            for filename in filename_store:
                results_filepath = os.path.join(filepath, filename)
                results.from_file(results_filepath)
                algorithm.apply_results(results)


if __name__ == "__main__":
    main()
