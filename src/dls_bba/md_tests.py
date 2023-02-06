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
import pytac
from cothread import Sleep
from cothread.catools import caget, caput

from dls_bba import accelerator as acc
from dls_bba.common import PLANE_VALUES, Algorithm
from dls_bba.fbba import FBBA
from dls_bba.sbba import SBBA

CONSOLE_LOG_FORMAT = "%(levelname)-7s: [%(filename)s:%(lineno)d] — %(message)s"
FILE_LOG_FORMAT = (
    "%(levelname)-7s: %(asctime)s — [%(filename)s:%(lineno)d] — %(message)s"
)

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "7Feb2023")


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
        "-f",
        "--freq",
        dest="freq_t",
        action="store_true",
        default=False,
        help="Freq test",
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
    freq_test = args.freq_t
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
        algorithm: Algorithm = fbba
    elif method == "SBBA":
        algorithm: Algorithm = sbba

    log.info("Starting Test")

    if honing_test:
        log.info("Honing Test")
        honing(algorithm, element_list[0], method, directions)

    if freq_test:
        log.info("Frequency Test")
        frequency(algorithm, element_list[0], method, directions)

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
        whole_offsets(algorithm)


def repeat_test(
    algorithm,
    element,
    method,
    directions_list,
    repeats,
    apply,
    quadrupole_scalar_=0.02,
    corrector_scalar_=2,
    cycles_=16,
    frequency_=8,
    decimated_=False,
    fft_=False,
    fofb_trigger_=False,
    delay_=0,
):
    """For repeating BBA a number of times with the same arguments."""
    log.info(f"Starting repeats: {repeats}, with apply: {apply}.")
    plot = False
    max_orbit = 15
    offsets = defaultdict(list)
    errors = defaultdict(list)

    for i in range(repeats):
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
                raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
                if algorithm.check_beam_current(initial_current):
                    break
            raw_data.save(filename_prefix, TEMP_FILEPATH_ROOT)
            results = algorithm.analyse_data(raw_data, plot, fft_)
            filename = results.save(filename_prefix, TEMP_FILEPATH_ROOT)
            filename_store.append([filename])
            for quad, answers in results.results.items():
                offsets[axis] += [answers[0]]
                errors[axis] += [answers[1]]
        if apply:
            for filename in filename_store:
                results_filepath = os.path.join(TEMP_FILEPATH_ROOT, filename)
                results.from_file(results_filepath)
        Sleep(delay_)
    return offsets, errors


def honing(algorithm, element, method, directions_list):
    """Honing Test"""
    repeats = 8
    fft_ = False
    fofb_trigger_ = False
    current = 300
    offsets, errors = repeat_test(
        algorithm,
        element,
        method,
        directions_list,
        repeats,
        apply=True,
        fft_=fft_,
        fofb_trigger_=fofb_trigger_,
    )

    matrix = np.zeros(shape=(2, repeats))
    matrix[0, :] = offsets[direction_dict["x"]]
    matrix[1, :] = errors[direction_dict["x"]]
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/honing_{method}_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_x.csv",
        matrix,
        delimiter=",",
    )
    matrix = np.zeros(shape=(2, repeats))
    matrix[0, :] = offsets[direction_dict["y"]]
    matrix[1, :] = errors[direction_dict["y"]]
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/honing_{method}_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_y.csv",
        matrix,
        delimiter=",",
    )


def frequency(algorithm, element, method, directions_list):
    """Frequency test"""
    repeats = 5
    MAX_TIME = 2  # Seconds
    fft_ = True
    fofb_trigger_ = True

    frequency_list = [int(num) for num in range(0, 251)]

    value_dictionary_x = defaultdict(list)
    error_dictionary_x = defaultdict(list)
    value_dictionary_y = defaultdict(list)
    error_dictionary_y = defaultdict(list)

    for freq in frequency_list:
        cycles = int(np.floor(MAX_TIME * frequency))
        offsets, errors = repeat_test(
            algorithm,
            element,
            method,
            directions_list,
            repeats,
            apply=False,
            cycles_=cycles,
            frequency_=freq,
            fft_=fft_,
            fofb_trigger_=fofb_trigger_,
        )

        value_dictionary_x[freq] = offsets[direction_dict["x"]]
        error_dictionary_x[freq] = errors[direction_dict["x"]]
        value_dictionary_y[freq] = offsets[direction_dict["y"]]
        error_dictionary_y[freq] = errors[direction_dict["y"]]

        matrix = np.zeros(shape=(len(frequency_list) * 2, repeats))
        for index, freq in enumerate(frequency_list):
            matrix[(index * 2), :] = value_dictionary_x[freq]
            matrix[(index * 2) + 1, :] = error_dictionary_x[freq]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/frequency_r10_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{frequency_list[0]}_{frequency_list[-1]}_x.csv",
            matrix,
            delimiter=",",
        )

        matrix = np.zeros(shape=(len(frequency_list) * 2, repeats))
        for index, freq in enumerate(frequency_list):
            matrix[(index * 2), :] = value_dictionary_y[freq]
            matrix[(index * 2) + 1, :] = error_dictionary_y[freq]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/frequency_r10_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{frequency_list[0]}_{frequency_list[-1]}_y.csv",
            matrix,
            delimiter=",",
        )


def triple_freq(algorithm, element, method, directions_list):
    """Honing but for three specific frequencies."""

    frequencies = [8, 83, 137, 179, 223, 269]
    for freq in frequencies:
        pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
        pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
        current_x = caget(pv_x)
        current_y = caget(pv_y)
        log.info(f"Freq: {freq}. Start: x={current_x}, y={current_y}")
        repeats = 8
        fft_ = True
        fofb_trigger_ = True
        current = 300
        offsets, errors = repeat_test(
            algorithm,
            element,
            method,
            directions_list,
            repeats,
            frequency_=freq,
            apply=True,
            fft_=fft_,
            fofb_trigger_=fofb_trigger_,
        )

        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["x"]]
        matrix[1, :] = errors[direction_dict["x"]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/triple_r8_c16_f{freq}_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_x.csv",
            matrix,
            delimiter=",",
        )
        matrix = np.zeros(shape=(2, repeats))
        matrix[0, :] = offsets[direction_dict["y"]]
        matrix[1, :] = errors[direction_dict["y"]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/triple_r8_c16_f{freq}_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_y.csv",
            matrix,
            delimiter=",",
        )
        final_x = caget(pv_x)
        final_y = caget(pv_y)
        log.info(f"Final: x={final_x}, y={final_y}")
        caput(pv_x, current_x)
        caput(pv_y, current_y)
        log.info(f"Reset: x={current_x}, y={current_y}")
        Sleep(1)


def cell(algorithm, cell_list, method, directions_list):
    """Cell corrector amplitudes test"""
    repeats = 8
    MAX_TIME = 2  # Seconds
    fft_ = True
    fofb_trigger_ = True

    # TODO: CORRECTOR AND QUAD RANGES for mutliplier.
    # correctors_list = []
    # quadrupole_list = []

    frequency_list = [int(num) for num in range(0, 251)]
    for index, element in enumerate(cell_list):
        value_dictionary_x = defaultdict(list)
        error_dictionary_x = defaultdict(list)
        value_dictionary_y = defaultdict(list)
        error_dictionary_y = defaultdict(list)
        for freq in frequency_list:
            cycles = int(np.floor(MAX_TIME * frequency))
            offsets, errors = repeat_test(
                algorithm,
                element,
                method,
                directions_list,
                repeats,
                apply=False,
                cycles_=cycles,
                frequency_=freq,
                fft_=fft_,
                fofb_trigger_=fofb_trigger_,
            )

            value_dictionary_x[freq] = offsets[direction_dict["x"]]
            error_dictionary_x[freq] = errors[direction_dict["x"]]
            value_dictionary_y[freq] = offsets[direction_dict["y"]]
            error_dictionary_y[freq] = errors[direction_dict["y"]]

            matrix = np.zeros(shape=(len(frequency_list) * 2, repeats))
            for index, freq in enumerate(frequency_list):
                matrix[(index * 2), :] = value_dictionary_x[freq]
                matrix[(index * 2) + 1, :] = error_dictionary_x[freq]
            np.savetxt(
                f"{TEMP_FILEPATH_ROOT}/cell_1.{index}_r10_c16_f{freq}_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_x.csv",
                matrix,
                delimiter=",",
            )

            matrix = np.zeros(shape=(len(frequency_list) * 2, repeats))
            for index, freq in enumerate(frequency_list):
                matrix[(index * 2), :] = value_dictionary_y[freq]
                matrix[(index * 2) + 1, :] = error_dictionary_y[freq]
            np.savetxt(
                f"{TEMP_FILEPATH_ROOT}/cell_1.{index}_r10_c16_f{freq}_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_y.csv",
                matrix,
                delimiter=",",
            )


def running_(algorithm, element, method, directions_list):
    """Repeat running of F/S BBA."""

    repeats = 40
    fft_ = True
    apply = True
    fofb_trigger_ = True
    current = 300
    delay = 40  # second
    note = "warming"
    topup = "topup1"
    for i in range(1, repeats + 1):
        log.info(f"Run: {i}")
        pv_x = "SR01C-DI-EBPM-05:CF:BBA_X_S"
        pv_y = "SR01C-DI-EBPM-05:CF:BBA_Y_S"
        repeat = 8
        current_x = caget(pv_x)
        current_y = caget(pv_y)
        log.info(f"Start: x={current_x}, y={current_y}")
        offsets, errors = repeat_test(
            algorithm,
            element,
            method,
            directions_list,
            repeat,
            apply=apply,
            fft_=fft_,
            fofb_trigger_=fofb_trigger_,
        )

        matrix = np.zeros(shape=(2, repeat))
        matrix[0, :] = offsets[direction_dict["x"]]
        matrix[1, :] = errors[direction_dict["x"]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/running_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_delay{delay}_{note}_{topup}_x_{i}.csv",
            matrix,
            delimiter=",",
        )
        matrix = np.zeros(shape=(2, repeat))
        matrix[0, :] = offsets[direction_dict["y"]]
        matrix[1, :] = errors[direction_dict["y"]]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/running_r8_c16_f8_qs0.02_cs2_fft{fft_}_fofb{fofb_trigger_}_{current}_delay{delay}_{note}_{topup}_y_{i}.csv",
            matrix,
            delimiter=",",
        )
        final_x = caget(pv_x)
        final_y = caget(pv_y)
        log.info(f"Final: x={final_x}, y={final_y}")
        # caput(pv_x, current_x)
        # caput(pv_y, current_y)
        # log.info(f"Reset: x={current_x}, y={current_y}")
        Sleep(delay)


def whole_offsets(algorithm):
    log.info("Measuring all BBA offsets.")
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
    # plt.show()
    plt.close()


if __name__ == "__main__":
    main()
