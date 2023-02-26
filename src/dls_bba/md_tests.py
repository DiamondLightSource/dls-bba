"""MD Tests."""
# frequency_scan(accelerator, quad, plane)
# cycle_scan(accelerator, quad, plane)
# repeatability_scan(accelerator, quad, plane, counts)
# compare_decimated_data(accelerator, quad, plane)
# scan_cell(accelerator, cell)
# scan_amplitudes(accelerator, quad, plane, scale_quad=True, scale_corr=True)

import argparse
import logging as log
import os
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt  # noqa
import numpy as np
from cothread import Sleep
from cothread.catools import caget, caput

from dls_bba import accelerator as acc
from dls_bba.common import Algorithm
from dls_bba.fbba import FBBA
from dls_bba.sbba import SBBA

CONSOLE_LOG_FORMAT = "%(levelname)-7s: [%(filename)s:%(lineno)d] — %(message)s"
FILE_LOG_FORMAT = (
    "%(levelname)-7s: %(asctime)s — [%(filename)s:%(lineno)d] — %(message)s"
)

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "28Feb2023")


def get_filename_prefix(method):
    """Returns a time string for the filename."""
    now = datetime.now()
    datestring = now.strftime("%Y-%m-%dT%H-%M-%S")
    return "{}-{}".format(method, datestring)


def get_new_logger(method, filepath="data"):
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
        "-o",
        "--orbit",
        dest="max_orbit",
        action="store",
        default=15,
        help="The maximum orbit size to invoke FOFB in um.",
    )
    parser.add_argument(
        "-j",
        "--honing",
        dest="honing_test",
        action="store_true",
        default=False,
        help="honing test",
    )
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    method = str(args.method)

    honing_test = args.honing_test

    get_new_logger("SIM", TEMP_FILEPATH_ROOT)
    pv_list = ["SR01A-PC-Q2AB-07"]  # Single BPM

    accelerator = acc.Accelerator(ringmode=None)

    element_list = []
    for pv in pv_list:
        element_list.append(accelerator.pv_prefix_to_element(pv))

    fbba = FBBA(accelerator)
    sbba = SBBA(accelerator)

    if method == "FBBA":
        algorithm: Algorithm = fbba  # type: ignore
    elif method == "SBBA":
        algorithm: Algorithm = sbba  # type: ignore

    method = "SIM"
    log.info("Starting Test")

    if honing_test:
        log.info("Starting honing test")
        honing(algorithm, element_list[0], method)


def repeat_test(
    algorithm,
    element,
    method,
    repeats,
    apply=True,
    quadrupole_scalar=0.01,
    corrector_scalar=1,
    cycles=[22, 26],
    frequency=[11, 13],
    decimated=False,
    delay=0,
    runtime=3,
    waittime=0,
):
    log.info(f"Starting repeats: {repeats}")
    plot = False
    max_orbit = 15
    plane_info = None
    offsets = defaultdict(list)
    errors = defaultdict(list)

    for i in range(repeats):
        log.info(f"Repeat number {i} of {repeats}")
        filename_prefix = get_filename_prefix(method)
        algorithm.configure(
            quadrupole_scalar=quadrupole_scalar,
            corrector_scalar=corrector_scalar,
            cycles=cycles,
            frequency=frequency,
            decimated=decimated,
            runtime=runtime,
            waittime=waittime,
        )
        while True:
            initiial_current = algorithm._accelerator.get_beam_current()
            algorithm.apply_feedbacks(runtime, waittime)
            raw_data = algorithm.run(element, plane_info, max_orbit)
            if algorithm.check_beam_current(initiial_current):
                break
        raw_data.save(filename_prefix, TEMP_FILEPATH_ROOT)
        results = algorithm.analyse_data(raw_data, plot)
        filename = results.save(filename_prefix, TEMP_FILEPATH_ROOT)  # noqa
        for key, values in results.results.items():
            axis = key.split("_"[:-1])
            offsets[axis] += [values[0]]
            errors[axis] += [values[1]]
        if apply:
            algorithm.apply_results(results)
        Sleep(delay)
    return offsets, errors


def honing(algorithm, element, method):
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    repeats = 20

    pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
    pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
    current_x = caget(pv_x)
    current_y = caget(pv_y)
    log.info(f"Start = x: {current_x}, y: {current_y}")
    for offset in [0, 0.1]:
        caput(pv_x, current_x + offset, wait=True)
        caput(pv_y, current_y + offset, wait=True)
        Sleep(0.2)
        offset_x = caget(pv_x)
        offset_y = caget(pv_y)
        log.info(f"Offset applied: x={offset_x}, y={offset_y}")

        accepted = False
        while not accepted:
            input_value = input(
                "Check if topup required. 'y'  when ready to continue. : "
            )
            if input_value == "y":
                accepted = True
            else:
                print("Try again˝")

        algorithm.apply_feedback(10, 10)
        offsets, errors = repeat_test(
            algorithm,
            element,
            method,
            repeats,
            apply=True,
            quadrupole_scalar=quadrupole_scalar,
            corrector_scalar=corrector_scalar,
        )

        matrix = np.zeroes(shape=(2, repeats))
        matrix[0, :] = offsets["x"]
        matrix[1, :] = errors["x"]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/SIM_honing_r{repeats}_qs{quadrupole_scalar}_cs{corrector_scalar}_offset{offset}_x.csv"
        )

        matrix = np.zeroes(shape=(2, repeats))
        matrix[0, :] = offsets["y"]
        matrix[1, :] = errors["y"]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/SIM_honing_r{repeats}_qs{quadrupole_scalar}_cs{corrector_scalar}_offset{offset}_y.csv"
        )

        final_x = caget(pv_x)
        final_y = caget(pv_y)
        log.info(f"Final: x={final_x}, y={final_y}")
        caput(pv_x, current_x, wait=True)
        caput(pv_y, current_y, wait=True)
        Sleep(0.2)
        log.info(f"Reset: x={current_x}, y={current_y}")


if __name__ == "__main__":
    main()
