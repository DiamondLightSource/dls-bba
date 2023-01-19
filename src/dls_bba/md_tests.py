"""MD Tests."""
# frequency_scan(accelerator, quad, plane)
# cycle_scan(accelerator, quad, plane)
# repeatability_scan(accelerator, quad, plane, counts)
# compare_decimated_data(accelerator, quad, plane)
# scan_cell(accelerator, cell)
# scan_amplitudes(accelerator, quad, plane, scale_quad=True, scale_corr=True)

import argparse
import logging as log
import os.path as osp
from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt  # noqa
import numpy as np

from dls_bba import accelerator as acc
from dls_bba.common import PLANE_VALUES, Algorithm
from dls_bba.fbba import FBBA
from dls_bba.sbba import SBBA

CONSOLE_LOG_FORMAT = "%(levelname)-7s: [%(filename)s:%(lineno)d] — %(message)s"
FILE_LOG_FORMAT = (
    "%(levelname)-7s: %(asctime)s — [%(filename)s:%(lineno)d] — %(message)s"
)

TEMP_FILEPATH_ROOT = osp.join("/dls", "physics", "owr68555", "13Jan2023")


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
        "-s",
        "--special",
        dest="combi",
        action="store_true",
        default=False,
        help="combination test",
    )
    return parser.parse_args()


def main():
    # Sort arguments
    args = parse_args()
    method = str(args.method)

    cycle_test = args.cycle
    freq_test = args.freq
    corr_test = args.corr_amp_test
    quad_test = args.quads_amp_test
    honing_test = args.honing_test
    combination_test = args.combi

    get_new_logger(method)

    # TODO: System that will accept a number of quads (or cell).
    # TODO: System that will accept bpm selection.

    # pv_list = ['SR01C-DI-EBPM-01'] # First BPM
    # pv_list = ["SR24C-DI-EBPM-07"] # Last BPM
    pv_list = ["SR01A-PC-Q2AB-07"]  # Single BPM

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

    log.info("Starting Test")
    # Note: All tests occur in the x-axis only.
    axis = "HORIZONTAL"

    if cycle_test:
        repeats = 20
        cycle_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        cycle_scan(algorithm, element_list[0], method, axis, repeats, False, cycle_list)

    if freq_test:
        repeats = 10
        frequency_list = [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
        ]
        frequency_scan(
            algorithm, element_list[0], method, axis, repeats, False, frequency_list
        )

    if corr_test:
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
            4,
            4.5,
            5,
        ]
        corrector_amplitude_scan(
            algorithm, element_list[0], method, axis, repeats, False, corr_amp_list
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
        # Simple honing test.
        repeats = 5
        cycles = 1
        frequency = 8
        quad_scalar = 0.01
        corr_scalar = 1
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

    if combination_test:
        # cycles and corr_amp test
        repeats = 5
        corr_amps = [
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
            4,
            4.5,
            5,
        ]
        cycles_list = [1, 10, 20]
        combination(
            algorithm,
            element_list[0],
            method,
            axis,
            repeats,
            False,
            cycles_list,
            corr_amps,
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
):
    """For repeating BBA a number of times with the same arguments."""
    log.info(f"Starting repeats: {repeats}, with apply: {apply}.")
    plot = False
    max_orbit = 15
    offsets = []
    errors = []

    for i in range(repeats):
        filename_prefix = get_filename_prefix(method)
        algorithm.configure(
            quadrupole_scalar=quadrupole_scalar_,
            corrector_scalar=corrector_scalar_,
            cycles=cycles_,
            frequency=frequency_,
            decimated=decimated_,
        )
        raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
        raw_data.save(filename_prefix)
        results = algorithm.analyse_data(raw_data, plot)
        results.save(filename_prefix)
        if apply:
            algorithm.apply_results(results)
        for quad, answers in results.results.items():
            offsets += [answers[0]]
            errors += [answers[1]]
    return offsets, errors


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

    for frequency in frequency_list:
        frequency_values, frequency_errors = repeat_test(
            algorithm, element, method, axis, repeats, apply, frequency_=frequency
        )
        value_dictionary[frequency] = frequency_values
        error_dictionary[frequency] = frequency_errors

    matrix = np.zeros(shape=(len(frequency_list) * 2, repeats))
    for index, frequency in enumerate(frequency_list):
        matrix[(index * 2), :] = value_dictionary[frequency]
        matrix[(index * 2) + 1, :] = error_dictionary[frequency]
    np.savetxt(
        f"frequency_scan_repeats_{repeats}_len_{len(frequency_list)}.csv",
        matrix,
        delimiter=",",
    )


def corrector_amplitude_scan(
    algorithm, element, method, axis, repeats, apply, corr_amplitude_list
):
    # For repeating FBBA at different amplitudes.

    value_dictionary = defaultdict(list)
    error_dictionary = defaultdict(list)

    for amplitude in corr_amplitude_list:
        amp_values, amp_errors = repeat_test(
            algorithm,
            element,
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
        f"corr_amp_scan_repeats_{repeats}_len_{len(corr_amplitude_list)}.csv",
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


def decimated_scan():
    # For comparing decimated FBBA against non decimated FBBA.
    pass


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
    )  # Can add other args here.
    matrix = np.zeros(shape=(2, repeats))
    matrix[0, :] = value_list
    matrix[1, :] = error_list
    np.savetxt(
        f"honing_simple_repeats_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}.csv",
        matrix,
        delimiter=",",
    )


def honing_average():
    apply = True
    # Showing the honing ability of BBA if each step is repeated before being applied.
    pass


def combination(
    algorithm, element, method, axis, repeats, apply, cycle_list, corr_amplitude_list
):
    # Something that can do multiple tests at once. eg. corrector_amp and cycles.
    # Saved in terms of the cycle list for all amplitudes.

    value_dictionary = defaultdict(list)
    error_dictionary = defaultdict(list)
    for cycle in cycle_list:
        for corr_amp in corr_amplitude_list:
            value_list, error_list = repeat_test(
                algorithm,
                element,
                method,
                axis,
                repeats,
                apply,
                corrector_scalar_=corr_amp,
                cycles_=cycle,
            )
            value_dictionary[f"c_{cycle},a_{corr_amp}"] = value_list
            error_dictionary[f"c_{cycle},a_{corr_amp}"] = error_list

    for cycle in cycle_list:
        matrix = np.zeros(shape=(len(corr_amplitude_list) * 2, repeats))
        for index, corr_amp in enumerate(corr_amplitude_list):
            matrix[(index * 2), :] = value_dictionary[f"c_{cycle},a_{corr_amp}"]
            matrix[(index * 2) + 1, :] = error_dictionary[f"c_{cycle},a_{corr_amp}"]
        np.savetxt(
            f"combination_scan_repeats_{repeats}_cycle_{cycle}.csv",
            matrix,
            delimiter=",",
        )


if __name__ == "__main__":
    main()
