"""MD Tests."""
# frequency_scan(accelerator, quad, plane)
# cycle_scan(accelerator, quad, plane)
# repeatability_scan(accelerator, quad, plane, counts)
# compare_decimated_data(accelerator, quad, plane)
# scan_cell(accelerator, cell)
# scan_amplitudes(accelerator, quad, plane, scale_quad=True, scale_corr=True)

import argparse
import json
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

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "21Feb2023")


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
        "-c",
        "--cell",
        dest="cell_t",
        action="store_true",
        default=False,
        help="Cell test",
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
        "-t",
        "--triple",
        dest="triple_t",
        action="store_true",
        default=False,
        help="triple frequency test",
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
        "-w",
        "--whole",
        dest="whole_t",
        action="store_true",
        default=False,
        help="Whole machine bba offsets",
    )
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    method = str(args.method)
    directions = direction_dict[args.directions]
    cell_test = args.cell_t
    honing_test = args.honing_t
    triple = args.triple_t
    running = args.running_t
    whole = args.whole_t

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

    if cell_test:
        log.info("Cell Test")
        cell(algorithm, cell_list, method, directions)

    if triple:
        log.info("Triple frequency Test")
        triple_freq(algorithm, element_list[0], method, directions)

    if running:
        log.info("Running Test")
        running_(algorithm, element_list[0], method, directions)

    if whole:
        log.info("Snapshot of all BBA offsets.")
        whole_offsets(algorithm)


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
    fft_=True,
    fofb_trigger_=True,
    delay_=0,
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
            )
            initial_current = algorithm._accelerator.get_beam_current()
            while True:
                if fofb_trigger_:
                    algorithm.toggle_fofb()
                    algorithm.toggle_tune()
                raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
                if algorithm.check_beam_current(initial_current):
                    break
            raw_data.save(filename_prefix, TEMP_FILEPATH_ROOT)
            results = algorithm.analyse_data(raw_data, plot, fft_)
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
    offset = 0  # 0.1  # 100 microns

    if method == "FBBA":
        options = {  # FFT, FOFB
            "first": [True, True],
            "second": [False, True],
            "third": [True, False],
            "fourth": [False, False],
        }
    elif method == "SBBA":
        options = {  # FFT, FOFB (Cannot run FFT analysis)
            "first": [False, True],
            "second": [False, False],
        }
    else:
        log.critical("No method selected.")

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

    for key, (fft, fofb) in options.items():
        algorithm.toggle_fofb()  # Align for set of 8.
        algorithm.toggle_tune()
        log.info(f"Key: {key}: FFT: {fft}, FOFB: {fofb}")
        repeats = 8
        cycles = 16
        frequency = 8
        current = 300
        offsets, errors = repeat_test(
            algorithm,
            element,
            method,
            directions_list,
            repeats,
            apply=True,
            fft_=fft,
            fofb_trigger_=fofb,
            quadrupole_scalar_=quadrupole_scalar,
            corrector_scalar_=corrector_scalar,
        )

        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["x"][0]]
        matrix[1, :] = errors[direction_dict["x"][0]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/honing_{method}_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_fft{fft}_fofb{fofb}_{current}_x_offset{offset}.csv",
            matrix,
            delimiter=",",
        )
        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["y"][0]]
        matrix[1, :] = errors[direction_dict["y"][0]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/honing_{method}_r{repeats}_c{cycles}_f{frequency}_qs{quadrupole_scalar}_cs{corrector_scalar}_fft{fft}_fofb{fofb}_{current}_y_offset{offset}.csv",
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


def triple_freq(algorithm, element, method, directions_list):
    """Honing but for three specific frequencies."""

    frequencies = [8, 83, 137, 179]
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    fft = True
    fofb = True
    MAX_TIME = 2
    directions_list = ["VERTICAL", "HORIZONTAL"]
    offset = 0

    pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
    pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
    current_x = caget(pv_x)
    current_y = caget(pv_y)
    log.info(f"Start: x={current_x}, y={current_y}")

    for freq in frequencies:
        algorithm.toggle_fofb()  # Align for set of 8.
        algorithm.toggle_tune()
        log.info(f"Freq: {freq}: FFT: {fft}, FOFB: {fofb}")
        repeats = 8
        cycles = int(np.floor(MAX_TIME * freq))
        current = 300
        offsets, errors = repeat_test(
            algorithm,
            element,
            method,
            directions_list,
            repeats,
            apply=True,
            fft_=fft,
            fofb_trigger_=fofb,
            frequency_=freq,
            cycles_=cycles,
            quadrupole_scalar_=quadrupole_scalar,
            corrector_scalar_=corrector_scalar,
        )

        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["x"][0]]
        matrix[1, :] = errors[direction_dict["x"][0]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/triple_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_fft{fft}_fofb{fofb}_{current}_x_swap_offset{offset}.csv",
            matrix,
            delimiter=",",
        )
        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["y"][0]]
        matrix[1, :] = errors[direction_dict["y"][0]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/triple_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_fft{fft}_fofb{fofb}_{current}_y_swap_offset{offset}.csv",
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


def cell(algorithm, cell_list, method, directions_list):
    """Cell corrector amplitudes test"""
    repeats = 8
    fft_ = True
    fofb_trigger_ = False
    freq = 8
    cycles = 16
    apply = True

    results = {}
    for quad in cell_list:
        quadx = quad + ":CF:BBA_X_S"
        quady = quad + ":CF:BBA_Y_S"
        x = caget(quadx)
        y = caget(quady)
        results[quadx] = x
        results[quady] = y
        log.debug(quadx, x)
        log.debug(quady, y)

    correctors_list = [0.5, 1, 1.5]
    quadrupole_list = [0.5, 1, 1.5]
    x_d = direction_dict["x"]
    y_d = direction_dict["y"]
    for corr in correctors_list:
        for quad in quadrupole_list:
            data_dict_x = defaultdict(list)
            data_dict_y = defaultdict(list)
            for index, element in enumerate(cell_list):
                offsets, errors = repeat_test(
                    algorithm,
                    element,
                    method,
                    directions_list,
                    repeats,
                    apply=apply,
                    cycles_=cycles,
                    frequency_=freq,
                    corrector_scalar_=corr,
                    quadrupole_scalar_=quad,
                    fft_=fft_,
                    fofb_trigger_=fofb_trigger_,
                )
                data_dict_x[f"{index},{x_d},value"] = offsets[x_d]
                data_dict_x[f"{index},{x_d},error"] = errors[x_d]
                data_dict_y[f"{index},{y_d},value"] = offsets[y_d]
                data_dict_y[f"{index},{y_d},error"] = errors[y_d]

            filename_x = f"cell_c{corr}_q{quad}_x_f8_c16_FFT_FOFB_5repeats.json"
            with open(os.path.join(TEMP_FILEPATH_ROOT, filename_x), "w") as outfile:
                json.dump(data_dict_x, outfile, indent=4, ensure_ascii=False)

            filename_y = f"cell_c{corr}_q{quad}_y_f8_c16_FFT_FOFB_5repeats.json"
            with open(os.path.join(TEMP_FILEPATH_ROOT, filename_y), "w") as outfile:
                json.dump(data_dict_y, outfile, indent=4, ensure_ascii=False)

            # reset bba offsets.
            for key, value in results.items():
                caput(key, value, wait=True)
            log.info("Reset BBA offsets.")


def running_(algorithm, element, method, directions_list):
    """Repeat running of F/S BBA."""

    freq = 8
    quadrupole_scalar = 0.01
    corrector_scalar = 1
    fft = True
    fofb = True
    MAX_TIME = 2
    sitation = "cooling"  # "warming"

    pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
    pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
    current_x = caget(pv_x)
    current_y = caget(pv_y)
    log.info(f"Start: x={current_x}, y={current_y}")

    algorithm.toggle_fofb()  # Align for set of 8.
    algorithm.toggle_tune()
    log.info(f"Freq: {freq}: FFT: {fft}, FOFB: {fofb}")
    repeats = 80
    cycles = int(np.floor(MAX_TIME * freq))

    offsets, errors = repeat_test(
        algorithm,
        element,
        method,
        directions_list,
        repeats,
        apply=True,
        fft_=fft,
        fofb_trigger_=fofb,
        frequency_=freq,
        cycles_=cycles,
        quadrupole_scalar_=quadrupole_scalar,
        corrector_scalar_=corrector_scalar,
    )

    matrix = np.zeros(shape=(2, repeats))
    matrix[0, :] = offsets[direction_dict["x"][0]]
    matrix[1, :] = errors[direction_dict["x"][0]]
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/running_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_fft{fft}_fofb{fofb}_x_{sitation}.csv",
        matrix,
        delimiter=",",
    )
    matrix = np.zeros(shape=(2, repeats))
    matrix[0, :] = offsets[direction_dict["y"][0]]
    matrix[1, :] = errors[direction_dict["y"][0]]
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/running_FBBA_r{repeats}_c{cycles}_f{freq}_qs{quadrupole_scalar}_cs{corrector_scalar}_fft{fft}_fofb{fofb}_y_{sitation}.csv",
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


def whole_offsets(algorithm):
    x = []
    y = []
    bpm_pvs = algorithm._accelerator.lattice.get_element_pv_names("BPM", "x", pytac.RB)
    now = datetime.now()
    datestring = now.strftime("%Y-%m-%dT%H-%M-%S")
    for bpm in bpm_pvs:
        root_pv = bpm.split(":")[0]
        x_value = caget(root_pv + ":CF:BBA_X_S")
        y_value = caget(root_pv + ":CF:BBA_Y_S")
        x.append(x_value)
        y.append(y_value)
    matrix = np.zeros(shape=(2, len(x)))
    matrix[0, :] = x
    matrix[1, :] = y
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/all_bpm_offsets_{datestring}.csv",
        matrix,
        delimiter=",",
    )
    length = len(x)
    x_axis = list(np.arange(1, length + 1))
    plt.plot(x_axis, x, label="x")
    plt.plot(x_axis, y, label="y")
    plt.legend()
    plt.xlim(0, x_axis[-1] + 1)
    # plt.ylim(-2, 2)
    plt.xlabel("BPM number")
    plt.title("BPM BBA Offsets")
    plt.ylabel("Offset in mm")
    plt.grid(which="both", axis="both")
    plt.savefig(
        f"{TEMP_FILEPATH_ROOT}/whole_offsets_{datestring}.png",
        bbox_inches="tight",
        dpi=1200,
    )
    plt.close()


if __name__ == "__main__":
    main()
