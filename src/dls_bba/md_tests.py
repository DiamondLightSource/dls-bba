"""MD Tests."""
import argparse
import logging as log
import os
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt  # noqa
import numpy as np
import pytac
from cothread import Sleep
from cothread.catools import caget, caput

from dls_bba import accelerator as acc
from dls_bba.common import PLANE_VALUES, Algorithm, Results
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
        "-j",
        "--honing",
        dest="honing_t",
        action="store_true",
        default=False,
        help="honing simple test",
    )
    parser.add_argument(
        "-r",
        "--running",
        dest="running_t",
        action="store_true",
        default=False,
        help="Running test",
    )
    parser.add_argument(
        "-y",
        "--yestime",
        dest="time_t",
        action="store_true",
        default=False,
        help="Time test",
    )
    parser.add_argument(
        "-c",
        "--swaptest",
        dest="swaptest",
        action="store_true",
        default=False,
        help="Swapping axis test",
    )
    parser.add_argument(
        "-f",
        "--feedbacks",
        dest="feedbacks",
        action="store_true",
        default=False,
        help="feedbacks test",
    )
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    method = str(args.method)
    directions = direction_dict[args.directions]
    honing_test = args.honing_t
    running = args.running_t
    time = args.time_t
    swaptest = args.swaptest
    feedbacks = args.feedbacks

    get_new_logger(method, TEMP_FILEPATH_ROOT)

    pv_list = ["SR01A-PC-Q2AB-07"]  # Single BPM
    cell_pv_list = [
        "SR01A-PC-Q1D-01",
        "SR01A-PC-Q2D-02",
        "SR01A-PC-Q3D-03",
        "SR01A-PC-Q2AD-04",
        "SR01A-PC-Q1AD-05",
        "SR01A-PC-Q1AB-06",
        "SR01A-PC-Q2AB-07",
        "SR01A-PC-Q3B-08",
        "SR01A-PC-Q2B-09",
        "SR01A-PC-Q1B-10",
    ]

    accelerator = acc.Accelerator(ringmode=None)

    element_list = []
    for pv in pv_list:
        element_list.append(accelerator.pv_prefix_to_element(pv))
    cell_list = []
    for item in cell_pv_list:
        cell_list.append(accelerator.pv_prefix_to_element(item))

    fbba = FBBA(accelerator)
    sbba = SBBA(accelerator)

    if method == "FBBA":
        algorithm: Algorithm = fbba  # type: ignore
    elif method == "SBBA":
        algorithm: Algorithm = sbba  # type: ignore

    quad_pvs = algorithm._accelerator.lattice.get_element_pv_names(
        "quadrupole", "b1", pytac.RB
    )
    full_machine_quad_pvs = [quad[:-2] for quad in quad_pvs]  # noqa

    log.info("Starting Test")

    if honing_test:
        log.info("Honing Test")
        honing(algorithm, element_list[0], method, directions)

    if time:
        log.info("Time test.")
        time_freq(algorithm, element_list[0], method, directions)

    if running:
        log.info("Running Test")
        running_(algorithm, element_list[0], method, directions)

    if swaptest:
        log.info("Swap test")
        swap_test(algorithm, element_list[0], method, directions)

    if feedbacks:
        log.info("Feedbacks Test")
        feedbacks_test()


def repeat_test(
    algorithm,
    element,
    method,
    directions_list,
    repeats,
    apply,
    quadrupole_scalar_=0.01,
    corrector_scalar_=1,
    cycles_=16,
    frequency_=8,
    decimated_=False,
    fofb_trigger_=True,
    delay_=0,
    runtime_=3,
    waittime_=3,
):
    """For repeating BBA a number of times with the same arguments."""
    log.info(f"Starting repeats: {repeats}, with apply: {apply}.")
    plot = False
    max_orbit = 15
    offsets = defaultdict(list)
    errors = defaultdict(list)

    for i in range(repeats):
        log.info(f"Repeat number {i} of {repeats}")
        filename_store = []
        for axis in directions_list:
            filename_prefix = get_filename_prefix(method)
            algorithm.configure(
                quadrupole_scalar=quadrupole_scalar_,
                corrector_scalar=corrector_scalar_,
                cycles=cycles_,
                frequency=frequency_,
                decimated=decimated_,
                runtime=runtime_,
                waittime=waittime_,
            )
            initial_current = algorithm._accelerator.get_beam_current()
            while True:
                if fofb_trigger_:
                    algorithm.apply_feedbacks(runtime_, waittime_)
                raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
                if algorithm.check_beam_current(initial_current):
                    break
            raw_data.save(filename_prefix, TEMP_FILEPATH_ROOT)
            results = algorithm.analyse_data(raw_data, plot)
            filename = results.save(filename_prefix, TEMP_FILEPATH_ROOT)
            filename_store.append(filename)
            for quad, answers in results.results.items():
                offsets[axis] += [answers[0]]
                errors[axis] += [answers[1]]
        if apply:
            for filename in filename_store:
                results_filepath = filename
                results = Results.from_file(results_filepath)
                algorithm.apply_results(results)
        Sleep(delay_)
    return offsets, errors


def honing(algorithm, element, method, directions_list):
    """Honing Test"""
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    repeats = 20
    cycles = 16
    frequency = 8

    pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
    pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
    current_x = caget(pv_x)
    current_y = caget(pv_y)
    log.info(f"Start: x={current_x}, y={current_y}")
    for offset in [0, 0.1]:
        caput(pv_x, current_x + offset, wait=True)
        caput(pv_y, current_y + offset, wait=True)
        Sleep(0.2)
        offset_x = caget(pv_x)
        offset_y = caget(pv_y)
        log.info(f"Offset applied: x={offset_x}, y={offset_y}")

        algorithm.apply_feedbacks(10, 10)  # Align for set of 8.
        log.info(f"Offset: {offset}")
        offsets, errors = repeat_test(
            algorithm,
            element,
            method,
            directions_list,
            repeats,
            apply=True,
            quadrupole_scalar_=quadrupole_scalar,
            corrector_scalar_=corrector_scalar,
        )

        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["x"][0]]
        matrix[1, :] = errors[direction_dict["x"][0]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/honing_{method}_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_x_offset{offset}.csv",
            matrix,
            delimiter=",",
        )
        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["y"][0]]
        matrix[1, :] = errors[direction_dict["y"][0]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/honing_{method}_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_y_offset{offset}.csv",
            matrix,
            delimiter=",",
        )

        final_x = caget(pv_x)
        final_y = caget(pv_y)
        log.info(f"Final: x={final_x}, y={final_y}")
        caput(pv_x, current_x, wait=True)
        caput(pv_y, current_y, wait=True)
        Sleep(0.2)
        log.info(f"Reset: x={current_x}, y={current_y}")
        Sleep(1)


def swap_test(algorithm, element, method, directions_list):
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    offset = 0.1
    repeats = 16
    cycles = 16
    frequency = 8

    pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
    pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
    current_x = caget(pv_x)
    current_y = caget(pv_y)
    log.info(f"Start: x={current_x}, y={current_y}")
    offset_x = caget(pv_x)
    offset_y = caget(pv_y)
    log.info(f"Offset applied: x={offset_x}, y={offset_y}")
    directions = [["HORIZONTAL", "VERTICAL"], ["VERTICAL", "HORIZONTAL"]]

    for order in directions:
        caput(pv_x, current_x + offset, wait=True)
        caput(pv_y, current_y + offset, wait=True)
        Sleep(0.2)
        offset_x = caget(pv_x)
        offset_y = caget(pv_y)
        log.info(f"Offset applied: x={offset_x}, y={offset_y}")
        algorithm.apply_feedbacks(10, 10)  # Align for set of 8.
        log.info(f"Order: {order}")
        offsets, errors = repeat_test(
            algorithm,
            element,
            method,
            order,
            repeats,
            apply=True,
            quadrupole_scalar_=quadrupole_scalar,
            corrector_scalar_=corrector_scalar,
        )

        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["x"][0]]
        matrix[1, :] = errors[direction_dict["x"][0]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/swap_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_x_order_{order[0]}.csv",
            matrix,
            delimiter=",",
        )
        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["y"][0]]
        matrix[1, :] = errors[direction_dict["y"][0]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/swap_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_y_order_{order[0]}.csv",
            matrix,
            delimiter=",",
        )

        final_x = caget(pv_x)
        final_y = caget(pv_y)
        log.info(f"Final: x={final_x}, y={final_y}")
        caput(pv_x, current_x, wait=True)
        caput(pv_y, current_y, wait=True)
        Sleep(0.2)
        log.info(f"Reset: x={current_x}, y={current_y}")
        Sleep(1)


def time_freq(algorithm, element, method, directions_list):
    """Honing but for three specific frequencies."""

    frequencies = [8, 37, 83, 107, 137, 179]
    total_time = [0.5, 1, 1.5, 2]
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    repeats = 10
    offset = 0.1

    pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
    pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
    current_x = caget(pv_x)
    current_y = caget(pv_y)
    log.info(f"Start: x={current_x}, y={current_y}")

    for time in total_time:
        for freq in frequencies:
            caput(pv_x, current_x + offset, wait=True)
            caput(pv_y, current_y + offset, wait=True)
            Sleep(0.2)
            offset_x = caget(pv_x)
            offset_y = caget(pv_y)
            log.info(f"Offset applied: x={offset_x}, y={offset_y}")

            accepted = False
            while not accepted:
                input_value = input(
                    "Check if beam needs topup. 'y' when ready to continue. If not then cancel. : "
                )
                if input_value == "y":
                    accepted = True
                else:
                    print("Try again: ")

            algorithm.apply_feedbacks(10, 10)  # Align for set of 8.
            log.info(f"Time: {time}, Freq: {freq}")
            cycles = int(np.floor(time * freq))

            offsets, errors = repeat_test(
                algorithm,
                element,
                method,
                directions_list,
                repeats,
                apply=True,
                frequency_=freq,
                cycles_=cycles,
                quadrupole_scalar_=quadrupole_scalar,
                corrector_scalar_=corrector_scalar,
            )

            matrix = np.zeros(shape=(2, repeats))
            matrix[0, :] = offsets[direction_dict["x"][0]]
            matrix[1, :] = errors[direction_dict["x"][0]]
            np.savetxt(
                f"{TEMP_FILEPATH_ROOT}/time_freq_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_x_offset{offset}.csv",
                matrix,
                delimiter=",",
            )
            matrix = np.zeros(shape=(2, repeats))
            matrix[0, :] = offsets[direction_dict["y"][0]]
            matrix[1, :] = errors[direction_dict["y"][0]]
            np.savetxt(
                f"{TEMP_FILEPATH_ROOT}/time_freq_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_y_offset{offset}.csv",
                matrix,
                delimiter=",",
            )

            final_x = caget(pv_x)
            final_y = caget(pv_y)
            log.info(f"Final: x={final_x}, y={final_y}")
            caput(pv_x, current_x, wait=True)
            caput(pv_y, current_y, wait=True)
            Sleep(0.2)
            log.info(f"Reset: x={current_x}, y={current_y}")
            Sleep(1)


def running_(algorithm, element, method, directions_list):
    """Repeat running of F/S BBA."""

    freq = 8
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    cycles = 16
    repeats = 30
    situation = ["baseline", "cooling", "warming"]
    situation = situation[0]
    offset = 0.1

    pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
    pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
    current_x = caget(pv_x)
    current_y = caget(pv_y)
    log.info(f"Start: x={current_x}, y={current_y}")
    caput(pv_x, current_x + offset, wait=True)
    caput(pv_y, current_y + offset, wait=True)
    Sleep(0.2)
    offset_x = caget(pv_x)
    offset_y = caget(pv_y)
    log.info(f"Offset applied: x={offset_x}, y={offset_y}")

    algorithm.apply_feedbacks(10, 10)  # Align for set
    offsets, errors = repeat_test(
        algorithm,
        element,
        method,
        directions_list,
        repeats,
        apply=True,
        frequency_=freq,
        cycles_=cycles,
        quadrupole_scalar_=quadrupole_scalar,
        corrector_scalar_=corrector_scalar,
    )

    matrix = np.zeros(shape=(2, repeats))
    matrix[0, :] = offsets[direction_dict["x"][0]]
    matrix[1, :] = errors[direction_dict["x"][0]]
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/running_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_x_{situation}.csv",
        matrix,
        delimiter=",",
    )
    matrix = np.zeros(shape=(2, repeats))
    matrix[0, :] = offsets[direction_dict["y"][0]]
    matrix[1, :] = errors[direction_dict["y"][0]]
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/running_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_y_{situation}.csv",
        matrix,
        delimiter=",",
    )

    final_x = caget(pv_x)
    final_y = caget(pv_y)
    log.info(f"Final: x={final_x}, y={final_y}")
    caput(pv_x, current_x, wait=True)
    caput(pv_y, current_y, wait=True)
    Sleep(0.2)
    log.info(f"Reset: x={current_x}, y={current_y}")


def feedbacks_test(algorithm, element, method, directions_list):
    runtime_values = [2, 3, 4]
    waittime_values = [1, 3, 5]
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    repeats = 16
    cycles = 16
    frequency = 8
    offset = 0.1

    pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
    pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
    current_x = caget(pv_x)
    current_y = caget(pv_y)
    log.info(f"Start: x={current_x}, y={current_y}")

    for runtime in runtime_values:
        for waittime in waittime_values:
            caput(pv_x, current_x + offset, wait=True)
            caput(pv_y, current_y + offset, wait=True)
            Sleep(0.2)
            offset_x = caget(pv_x)
            offset_y = caget(pv_y)
            log.info(f"Offset applied: x={offset_x}, y={offset_y}")

            accepted = False
            while not accepted:
                input_value = input(
                    "Check if beam needs topup. 'y' when ready to continue. If not then cancel. : "
                )
                if input_value == "y":
                    accepted = True
                else:
                    print("Try again: ")

            algorithm.apply_feedbacks(10, 10)
            log.info(f"Runtime: {runtime}, Waittime: {waittime}")
            offsets, errors = repeat_test(
                algorithm,
                element,
                method,
                directions_list,
                repeats,
                apply=True,
                fofb_trigger_=True,
                quadrupole_scalar_=quadrupole_scalar,
                corrector_scalar_=corrector_scalar,
                runtime_=runtime,
                waittime_=waittime,
            )

            matrix = np.zeros(shape=(2, repeats))
            matrix[0, :] = offsets[direction_dict["x"][0]]
            matrix[1, :] = errors[direction_dict["x"][0]]
            np.savetxt(
                f"{TEMP_FILEPATH_ROOT}/feedbacks_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_x_run{runtime}_wait{waittime}.csv",
                matrix,
                delimiter=",",
            )
            matrix = np.zeros(shape=(2, repeats))
            matrix[0, :] = offsets[direction_dict["y"][0]]
            matrix[1, :] = errors[direction_dict["y"][0]]
            np.savetxt(
                f"{TEMP_FILEPATH_ROOT}/feedbacks_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_y_run{runtime}_wait{waittime}.csv",
                matrix,
                delimiter=",",
            )

            final_x = caget(pv_x)
            final_y = caget(pv_y)
            log.info(f"Final: x={final_x}, y={final_y}")
            caput(pv_x, current_x, wait=True)
            caput(pv_y, current_y, wait=True)
            Sleep(0.2)
            log.info(f"Reset: x={current_x}, y={current_y}")
            Sleep(1)


if __name__ == "__main__":
    main()
