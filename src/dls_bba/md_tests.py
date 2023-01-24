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

import matplotlib.pyplot as plt
import numpy as np

from dls_bba import accelerator as acc
from dls_bba.common import PLANE_VALUES, Algorithm
from dls_bba.fbba import FBBA
from dls_bba.sbba import SBBA

CONSOLE_LOG_FORMAT = "%(levelname)-7s: [%(filename)s:%(lineno)d] — %(message)s"
FILE_LOG_FORMAT = (
    "%(levelname)-7s: %(asctime)s — [%(filename)s:%(lineno)d] — %(message)s"
)

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "13Jan2023")


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
        "-a", "--faa", dest="faa", action="store_true", default=False, help="Faa test"
    )
    parser.add_argument(
        "-c",
        "--cycle",
        dest="cycle",
        action="store_true",
        default=False,
        help="Cycle test",
    )
    parser.add_argument(
        "-f",
        "--freq",
        dest="freq",
        action="store_true",
        default=False,
        help="Freq test",
    )
    parser.add_argument(
        "-q",
        "--quads",
        dest="quads_amp_test",
        action="store_true",
        default=False,
        help="Quad test",
    )
    parser.add_argument(
        "-k",
        "--corrector",
        dest="corr_amp_test",
        action="store_true",
        default=False,
        help="Corrector test",
    )
    parser.add_argument(
        "-j",
        "--honing",
        dest="honing_test",
        action="store_true",
        default=False,
        help="honing simple test",
    )
    parser.add_argument(
        "-t",
        "--time",
        dest="time_test",
        action="store_true",
        default=False,
        help="Time test",
    )
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    method = str(args.method)

    faa_test = args.faa
    cycle_test = args.cycle
    freq_test = args.freq
    corr_test = args.corr_amp_test
    quad_test = args.quads_amp_test
    honing_test = args.honing_test
    # timer_test = args.time_test

    get_new_logger(method, TEMP_FILEPATH_ROOT)

    pv_list = ["SR01A-PC-Q2AB-07"]
    cell_list = [  # Cell 4
        "SR04A-PC-Q1B-01",
        "SR04A-PC-Q2B-02",
        "SR04A-PC-Q3B-03",
        "SR04A-PC-Q2AB-04",
        "SR04A-PC-Q1AB-05",
        "SR04A-PC-Q1AD-06",
        "SR04A-PC-Q2AD-07",
        "SR04A-PC-Q3D-08",
        "SR04A-PC-Q2D-09",
        "SR04A-PC-Q1D-10",
    ]
    backup_cell_list = [  # Cell 7
        "SR07A-PC-Q1B-01",
        "SR07A-PC-Q2B-02",
        "SR07A-PC-Q3B-03",
        "SR07A-PC-Q2AB-04",
        "SR07A-PC-Q1AB-05",
        "SR07A-PC-Q1AB-06",
        "SR07A-PC-Q2AB-07",
        "SR07A-PC-Q3B-08",
        "SR07A-PC-Q2B-09",
        "SR07A-PC-Q1B-10",
    ]
    accelerator = acc.Accelerator(ringmode=None)

    element_list = []
    cell_element_list = []
    for pv in pv_list:
        element_list.append(accelerator.pv_prefix_to_element(pv))
    for e in cell_element_list:
        cell_element_list.append(accelerator.pv_prefix_to_element(e))

    fbba = FBBA(accelerator)
    sbba = SBBA(accelerator)

    if method == "FBBA":
        algorithm: Algorithm = fbba
    elif method == "SBBA":
        algorithm: Algorithm = sbba

    log.info("Starting Test")
    # Note: All tests occur in the x-axis only.
    axis = "HORIZONTAL"

    if faa_test:
        log.info("FAA High Frequency Test")
        frequencies = [80, 120, 145, 185, 210, 235, 260, 290]
        faa_scan(algorithm, element_list[0], method, axis, 1, False, frequencies)

    if cycle_test:
        repeats = 20
        cycle_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        cycle_scan(algorithm, element_list[0], method, axis, repeats, False, cycle_list)

    if freq_test:
        log.info("Frequncy up to 2sec of data Test")
        repeats = 10
        frequency_list = [int(num) for num in range(0, 251)]
        frequency_scan(
            algorithm, element_list[0], method, axis, repeats, False, frequency_list
        )

    if corr_test:
        log.info("Cell4 corrector amplitude Test")
        repeats = 10
        # As a multiplier (default 1)
        corr_amp_list = [
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            0.9,
            1,
            1.20,
            1.4,
            1.6,
            1.8,
            2,
            2.25,
            2.5,
            3,
            3.5,
        ]
        cell_element_list = backup_cell_list
        corrector_amplitude_scan(
            algorithm,
            cell_element_list,
            method,
            axis,
            repeats,
            False,
            corr_amp_list,
            cell_list,
        )

    if quad_test:
        repeats = 10
        # As a multiplier (default 0.01 for 1% of current value)
        quad_amp_list = [
            0.001,
            0.005,
            0.01,
            0.015,
            0.02,
            0.025,
            0.03,
            0.035,
            0.04,
            0.045,
            0.05,
        ]
        quadrupole_amplitude_scan(
            algorithm, element_list[0], method, axis, repeats, False, quad_amp_list
        )

    if honing_test:
        log.info("Honing Test")
        # Simple honing test.
        repeats = 8
        cycles = 16
        frequency = 8
        quad_scalar = 0.02
        corr_scalar = 2
        honing_simple(
            algorithm,
            element_list[0],
            method,
            axis,
            repeats,
            quadrupole_scalar=quad_scalar,
            corrector_scalar=corr_scalar,
            cycles=cycles,
            frequency=frequency,
        )


def repeat_test(
    algorithm,
    element,
    method,
    axis,
    repeats,
    apply,
    quadrupole_scalar_=0.01,
    corrector_scalar_=1,
    cycles_=1,
    frequency_=8,
    decimated_=False,
    fft=False,
):
    """For repeating BBA a number of times with the same arguments."""
    log.info(f"Starting repeats: {repeats}, with apply: {apply}.")
    plot = False
    max_orbit = 15
    offsets = []
    errors = []

    for i in range(repeats):
        filename_prefix = get_filename_prefix(method)
        initial_current = algorithm._accelerator.get_beam_current()
        while True:
            algorithm.configure(
                quadrupole_scalar=quadrupole_scalar_,
                corrector_scalar=corrector_scalar_,
                cycles=cycles_,
                frequency=frequency_,
                decimated=decimated_,
            )
            raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
            if algorithm.check_beam_current(initial_current):
                break
        raw_data.save(filename_prefix, TEMP_FILEPATH_ROOT)
        results = algorithm.analyse_data(raw_data, plot, use_fft=fft)
        results.save(filename_prefix, TEMP_FILEPATH_ROOT)
        if apply:
            algorithm.apply_results(results)
        for quad, answers in results.results.items():
            offsets += [answers[0]]
            errors += [answers[1]]
    return offsets, errors


def faa_scan(algorithm, element, method, axis, repeats, apply, freq_list):
    for freq in freq_list:
        print(f"Freq: {freq}")
        cycles = 20
        algorithm.configure(frequency=freq, cycles=cycles)
        filename_prefix = get_filename_prefix(method)
        initial_current = algorithm._accelerator.get_beam_current()
        while True:
            now = datetime.now()
            raw_data = algorithm.run(element, PLANE_VALUES[axis], 15)
            if algorithm.check_beam_current(initial_current):
                break
        raw_data.save(filename_prefix, TEMP_FILEPATH_ROOT)
        raw_name = raw_data.raw_data.keys()[0]
        raw_name_data = raw_data.raw_data.values()[0]
        datestring = now.strftime("%Y-%m-%dT%H-%M-%S")
        plt.plot(raw_name_data)
        plt.title(f"{raw_name} Python Data ({freq} Hz)at {datestring}")
        plt.xlabel("Time (In FAA Ticks)")
        plt.ylabel("Amplitude")
        plt.savefig(
            f"{TEMP_FILEPATH_ROOT}/faa_test_{freq}_{raw_name}.png",
            bbox_inches="tight",
            dpi=1200,
        )
        plt.close()


def cycle_scan(algorithm, element, method, axis, repeats, apply, cycle_list):
    """For repeating FBBA for different numbers of cycles."""
    value_dictionary = defaultdict(list)
    error_dictionary = defaultdict(list)

    for cycle in cycle_list:
        cycle_values, cycle_errors = repeat_test(
            algorithm, element, method, axis, repeats, apply, cycles_=cycle
        )
        value_dictionary[cycle] = cycle_values
        error_dictionary[cycle] = cycle_errors

    matrix = np.zeros(shape=(len(cycle_list) * 2, repeats))
    for index, cycle in enumerate(cycle_list):
        matrix[(index * 2), :] = value_dictionary[cycle]
        matrix[(index * 2) + 1, :] = error_dictionary[cycle]
    np.savetxt(
        f"cycle_scan_repeats_{repeats}_len_{len(cycle_list)}.csv", matrix, delimiter=","
    )


def frequency_scan(algorithm, element, method, axis, repeats, apply, frequency_list):
    # For repeating FBBA for different frequencies.

    value_dictionary = defaultdict(list)
    error_dictionary = defaultdict(list)
    MAX_TIME = 2  # 2 seconds

    for frequency in frequency_list:
        cycles = int(np.floor(MAX_TIME * frequency))
        frequency_values, frequency_errors = repeat_test(
            algorithm,
            element,
            method,
            axis,
            repeats,
            apply,
            frequency_=frequency,
            cycles_=cycles,
        )
        value_dictionary[frequency] = frequency_values
        error_dictionary[frequency] = frequency_errors

    matrix = np.zeros(shape=(len(frequency_list) * 2, repeats))
    for index, frequency in enumerate(frequency_list):
        matrix[(index * 2), :] = value_dictionary[frequency]
        matrix[(index * 2) + 1, :] = error_dictionary[frequency]
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/frequency_scan_repeats_{repeats}_{MAX_TIME}_len_{len(frequency_list)}.csv",
        matrix,
        delimiter=",",
    )


def corrector_amplitude_scan(
    algorithm, element, method, axis, repeats, apply, corr_amplitude_list, cell_list
):
    # For repeating FBBA at different amplitudes.
    for ele in element:
        pv_name = cell_list[element.index(ele)]

        value_dictionary = defaultdict(list)
        error_dictionary = defaultdict(list)

        for amplitude in corr_amplitude_list:
            amp_values, amp_errors = repeat_test(
                algorithm,
                ele,
                method,
                axis,
                repeats,
                apply,
                corrector_scalar_=amplitude,
            )
            value_dictionary[amplitude] = amp_values
            error_dictionary[amplitude] = amp_errors

        matrix = np.zeros(shape=(len(corr_amplitude_list) * 2, repeats))
        for index, amplitude in enumerate(corr_amplitude_list):
            matrix[(index * 2), :] = value_dictionary[amplitude]
            matrix[(index * 2) + 1, :] = error_dictionary[amplitude]
        np.savetxt(
            f"{TEMP_FILEPATH_ROOT}/corr_amp_scan_repeats_{repeats}_{pv_name}.csv",
            matrix,
            delimiter=",",
        )


def quadrupole_amplitude_scan(
    algorithm, element, method, axis, repeats, apply, quad_amplitude_list
):
    # For repeating FBBA at different amplitudes.

    value_dictionary = defaultdict(list)
    error_dictionary = defaultdict(list)

    for amplitude in quad_amplitude_list:
        amp_values, amp_errors = repeat_test(
            algorithm,
            element,
            method,
            axis,
            repeats,
            apply,
            quadrupole_scalar_=amplitude,
        )
        value_dictionary[amplitude] = amp_values
        error_dictionary[amplitude] = amp_errors

    matrix = np.zeros(shape=(len(quad_amplitude_list) * 2, repeats))
    for index, amplitude in enumerate(quad_amplitude_list):
        matrix[(index * 2), :] = value_dictionary[amplitude]
        matrix[(index * 2) + 1, :] = error_dictionary[amplitude]
    np.savetxt(
        f"quad_amp_scan_repeats_{repeats}_len_{len(quad_amplitude_list)}.csv",
        matrix,
        delimiter=",",
    )


def honing_simple(
    algorithm,
    element,
    method,
    axis,
    repeats,
    quadrupole_scalar=0.01,
    corrector_scalar=1,
    cycles=1,
    frequency=8,
):
    # Applying the first calculated value. Repeats refers to the # of times run.
    apply = True

    _fft = False
    offset = 0

    value_list = []
    error_list = []

    value_list, error_list = repeat_test(
        algorithm,
        element,
        method,
        axis,
        repeats,
        apply,
        quadrupole_scalar_=quadrupole_scalar,
        corrector_scalar_=corrector_scalar,
        cycles_=cycles,
        frequency_=frequency,
        fft=_fft,
    )  # Can add other args here.
    matrix = np.zeros(shape=(2, repeats))
    matrix[0, :] = value_list
    matrix[1, :] = error_list
    np.savetxt(
        f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
        matrix,
        delimiter=",",
    )


if __name__ == "__main__":
    main()
