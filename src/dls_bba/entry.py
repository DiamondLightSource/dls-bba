"""This is the entry point for the bba module."""
import argparse
import logging as log
import os
from datetime import datetime

from dls_bba import accelerator as acc
from dls_bba.common import Algorithm
from dls_bba.fbba import FBBA
from dls_bba.sbba import SBBA

CONSOLE_LOG_FORMAT = "%(levelname)-7s: [%(filename)s:%(lineno)d] — %(message)s"
FILE_LOG_FORMAT = (
    "%(levelname)-7s: %(asctime)s — [%(filename)s:%(lineno)d] — %(message)s"
)

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "28Feb2023")

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
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    method: str = args.method  # type: ignore
    filepath: str = args.directory  # noqa
    max_orbit: int = args.max_orbit  # type: ignore
    apply: bool = args.apply  # type: ignore
    plot: bool = args.plot  # type: ignore

    get_new_logger("SIM", TEMP_FILEPATH_ROOT)
    pv_list = ["SR01A-PC-Q2AB-07"]

    accelerator = acc.Accelerator(ringmode=None)

    element_list = []
    for pv in pv_list:
        element_list.append(accelerator.pv_prefix_to_element(pv))

    if method == "FBBA":
        algorithm: Algorithm = FBBA(accelerator)  # type: ignore
    elif method == "SBBA":
        algorithm: Algorithm = SBBA(accelerator)  # type: ignore
    method = "SIM"

    plane_info = None

    for element in element_list:
        filename_prefix = get_filename_prefix(method)
        initial_current = algorithm._accelerator.get_beam_current()
        while True:
            algorithm.apply_feedbacks()
            raw_data = algorithm.run(element, plane_info, max_orbit)
            if algorithm.check_beam_current(initial_current):
                break
        raw_data.save(filename_prefix, TEMP_FILEPATH_ROOT)
        results = algorithm.analyse_data(raw_data, plot)
        filename = results.save(filename_prefix, TEMP_FILEPATH_ROOT)  # noqa
        if apply:
            algorithm.apply_results(results)


if __name__ == "__main__":
    main()
