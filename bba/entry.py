"""This is the entry point for the bba module."""
from datetime import datetime
import argparse
import logging as log

from bba.common import Algorithm, PLANE_VALUES
from bba.fbba import FBBA
from bba.sbba import SBBA
from bba import accelerator as acc


LOG_FORMAT = "%(levelname)-7s: %(message)s"


def get_filename_prefix():
    """Returns a time string for the filename."""
    now = datetime.now()
    datestring = now.strftime("%Y-%m-%dT%H-%M-%S")
    return "bba-{}".format(datestring)


def get_new_logger():
    logger = log.getLogger()
    filename = "data/{}.log".format(get_filename_prefix())
    file_handler = log.FileHandler(filename)
    file_handler.setLevel(log.DEBUG)
    formatter = log.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(log.StreamHandler())
    logger.setLevel(log.DEBUG)

"""
fbba = FBBA()
sbba = SBBA()
algorithm: Algorithm = fbba

fbba.do_fbba_specific_thing()
algorithm.do_fbba_specific_thing()
"""

def parse_args():
    parser = argparse.ArgumentParser(description="Take BBA measurements")
    parser.add_argument(
        "-p",
        "--plane",
        dest="plane",
        action="store_const",
        default="HORIZONTAL",
        const="VERTICAL",
        help="Which plane to measure",
    )
    parser.add_argument(
        "-m",
        "--method",
        dest="method",
        action="store_const",
        default="fbba",
        const ="sbba",
        help="Which BBA method to use"
    )
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    # TODO: At the moment we are testing one plane: existing SBBA defaults to do BOTH planes when called.
    plane = str(args.plane)
    method = str(args.method)

    # Setup logger
    # TODO: Setup logger in its on logger.py?
    quad_scale = 1
    corr_scale = 1
    get_new_logger()
    log.warning(
        "Method: {}, Plane: {}, Quad scale: {}, Corr scale: {}\n".format(
            method, plane, quad_scale, corr_scale))

    # TODO: System that will accept a number of quads (or cell).
    # TODO: System that will accept bpm selection.

    pv = "SR01A-PC-Q2B-09"

    accelerator = acc.Accelerator(ringmode = None)
    quad = accelerator.pv_to_quad(pv)

    # TODO: fbba or sbba selection system in UI.

    fbba = FBBA()
    sbba = SBBA()

    if method == "fbba":
        algorithm: Algorithm = fbba
    elif method == "sbba":
        algorithm: Algorithm = sbba
    else:
        raise ValueError("This should never happen!")

    
    algorithm.setup(accelerator, quad, PLANE_VALUES[plane])
    algorithm.config()
    algorithm.run_bba()

if __name__ == "__main__":
    main()
