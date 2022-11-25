"""MD Tests."""
#frequency_scan(accelerator, quad, plane)
#cycle_scan(accelerator, quad, plane)
#repeatability_scan(accelerator, quad, plane, counts)
#compare_decimated_data(accelerator, quad, plane)
#scan_cell(accelerator, cell)
#scan_amplitudes(accelerator, quad, plane, scale_quad=True, scale_corr=True)

from datetime import datetime
import argparse
import logging as log
from statistics import mean

from bba.common import Algorithm, PLANE_VALUES, Results
from bba.fbba import FBBA
from bba.sbba import SBBA
from bba import accelerator as acc

import matplotlib.pyplot as plt
import numpy as np


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
        const ="SBBA",
        help="Which BBA method to use"
    )
    parser.add_argument(
        "-o",
        "--orbit",
        dest="max_orbit",
        action="store",
        default = 15,
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
    method = str(args.method)
    max_orbit = args.max_orbit
    apply = args.apply
    plot = args.plot
    fft = args.fft

    get_new_logger(method)

    # TODO: System that will accept a number of quads (or cell).
    # TODO: System that will accept bpm selection.

    pv_list = ["SR01A-PC-Q2AB-07"] #single bpm

    accelerator = acc.Accelerator(ringmode = None)

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
    
    print("Starting Test")

    cycle_number_test = False
    if cycle_number_test:
        print("Running cycle test")
        cycle_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        cycle_dict_value = {}
        cycle_dict_error = {}
        for cycle in cycle_numbers:
            cycle_dict_value[cycle] = []
            cycle_dict_error[cycle] = []
            for i in range(20):
                for axis in ["HORIZONTAL"]:
                    for element in element_list:
                        print(cycle)
                        filename_prefix = get_filename_prefix(method)
                        algorithm.configure(cycles=cycle)
                        raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
                        raw_data.save(filename_prefix)
                        results = algorithm.analyse_data(raw_data, plot, fft)
                        results.save(filename_prefix)
                        for quad, answers in results.results.items():
                            cycle_dict_value[cycle] += answers[0]
                            cycle_dict_error[cycle] += answers[1]
        matrix = np.zeros(shape=(len(cycle_numbers)*2, 20))
        for index, cycle in enumerate(cycle_numbers):
            matrix[(index*2), :] = cycle_dict_value[cycle]
            matrix[(index*2) + 1, :] = cycle_dict_error[cycle]
        np.savetxt("cycle_test.csv", matrix, delimiter=",")
    
    # corr_cycles_test 
    corr_cycles_test = False
    if corr_cycles_test:
        print("Running corr cycles test")
        corr_amps = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.20, 1.4, 1.6, 1.8, 2, 2.25, 2.5, 3, 3.5, 4, 4.5, 5]
        corr_amp_cycles = [1, 10, 20]
        corr_dict_value_1 = {}
        corr_dict_error_1 = {}
        corr_dict_value_10 = {}
        corr_dict_error_10 = {}
        corr_dict_value_20 = {}
        corr_dict_error_20 = {}

        for corr in corr_amps:
            corr_dict_value_1[corr] = []
            corr_dict_error_1[corr] = []
            for i in range(10):
                for axis in ["HORIZONTAL"]:
                    for element in element_list:
                        filename_prefix = get_filename_prefix(method)
                        algorithm.configure(cycles=1)
                        raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit, temp_corr_amp=corr)
                        raw_data.save(filename_prefix)
                        results = algorithm.analyse_data(raw_data, plot, fft)
                        results.save(filename_prefix)
                        for quad, answers in results.results.items():
                            corr_dict_value_1[cycle] += answers[0]
                            corr_dict_error_1[cycle] += answers[1]
        matrix = np.zeros(shape=(len(corr_amps)*2, 10))
        for index, cycle in enumerate(corr_amps):
            matrix[(index*2), :] = corr_dict_value_1[cycle]
            matrix[(index*2) + 1, :] = corr_dict_error_1[cycle]
        np.savetxt("corr1_cycle_test.csv", matrix, delimiter=",")

        for corr in corr_amps:
            corr_dict_value_10[corr] = []
            corr_dict_error_10[corr] = []
            for i in range(10):
                for axis in ["HORIZONTAL"]:
                    for element in element_list:
                        filename_prefix = get_filename_prefix(method)
                        algorithm.configure(cycles=10)
                        raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit, temp_corr_amp=corr)
                        raw_data.save(filename_prefix)
                        results = algorithm.analyse_data(raw_data, plot, fft)
                        results.save(filename_prefix)
                        for quad, answers in results.results.items():
                            corr_dict_value_10[cycle] += answers[0]
                            corr_dict_error_10[cycle] += answers[1]
        matrix = np.zeros(shape=(len(corr_amps)*2, 10))
        for index, cycle in enumerate(corr_amps):
            matrix[(index*2), :] = corr_dict_value_10[cycle]
            matrix[(index*2) + 1, :] = corr_dict_error_10[cycle]
        np.savetxt("corr10_cycle_test.csv", matrix, delimiter=",")

        for corr in corr_amps:
            corr_dict_value_20[corr] = []
            corr_dict_error_20[corr] = []
            for i in range(10):
                for axis in ["HORIZONTAL"]:
                    for element in element_list:
                        filename_prefix = get_filename_prefix(method)
                        algorithm.configure(cycles=20)
                        raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit, temp_corr_amp=corr)
                        raw_data.save(filename_prefix)
                        results = algorithm.analyse_data(raw_data, plot, fft)
                        results.save(filename_prefix)
                        for quad, answers in results.results.items():
                            corr_dict_value_20[cycle] += answers[0]
                            corr_dict_error_20[cycle] += answers[1]
        matrix = np.zeros(shape=(len(corr_amps)*2, 10))
        for index, cycle in enumerate(corr_amps):
            matrix[(index*2), :] = corr_dict_value_20[cycle]
            matrix[(index*2) + 1, :] = corr_dict_error_20[cycle]
        np.savetxt("corr20_cycle_test.csv", matrix, delimiter=",")

    # honing_test 
    honing_test = False
    if honing_test:
        print("Running honing test")
        apply = True
        honing_repeats_cycles = [1, 5, 10]
        # set current offset value. to reset to.
        for axis in ["HORIZONTAL"]:
            for cycle in honing_repeats_cycles:
                honing_dict_value = {}
                honing_dict_error = {}
                iterations = [1,2,3,4,5,6,7,8]
                for number_iteration in iterations:
                    for repeat in range(10):
                        for element in element_list:
                            filename_prefix = get_filename_prefix(method)
                            algorithm.configure(cycles=cycle)
                            raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
                            raw_data.save(filename_prefix)
                            results = algorithm.analyse_data(raw_data, plot, fft)
                            results.save(filename_prefix)
                            for quad, answers in results.results.items():
                                honing_dict_value[number_iteration] += answers[0]
                                honing_dict_error[number_iteration] += answers[1]
                            
                            if repeat == 9:
                                matrix = np.zeros(shape=(len(iterations)*2, 10))
                                for index, iterate in enumerate(iterations):
                                    matrix[(index*2), :] = honing_dict_value[iterate]
                                    matrix[(index*2) + 1, :] = honing_dict_error[iterate]
                                np.savetxt(f"honing_cycle_{cycle}_test.csv", matrix, delimiter=",")

                                value_list = honing_dict_value[cycle]
                                error_list = honing_dict_error[cycle]
                                sum_error = []
                                offset = mean(value_list)
                                for place, error in enumerate(error_list):
                                    sum_error += (error/value_list[place])**2
                                sum_error = np.sqrt(sum_error) * offset
                                apply_dict = {"A": [offset, sum_error]}
                                results = Results(apply_dict, results.bpm_pv_prefix, results.metadata)
                                algorithm.apply_results(results)


    simple_honing = False
    if simple_honing:
        print("Running simple honing")
        apply = True
        for axis in ["HORIZONTAL"]:
            for cycles in [1,10]:
                for element in element_list:
                    offset = []
                    error = []
                    honing_simple_value = []
                    honing_simple_error = []
                    for i in range(8):
                        filename_prefix = get_filename_prefix(method)
                        algorithm.configure(cycles=cycles)
                        raw_data = algorithm.run(element, PLANE_VALUES[axis], max_orbit)
                        raw_data.save(filename_prefix)
                        results = algorithm.analyse_data(raw_data, plot, fft)
                        results.save(filename_prefix)
                        for quad, answers in results.results.items():
                            honing_simple_value.append(answers[0])
                            honing_simple_error.append(answers[1])
                        algorithm.apply_results(results)
                    matrix = np.zeros(shape=(2, 10))
                    for index, iterate in enumerate(iterations):
                        matrix[0, :] = honing_simple_value
                        matrix[1, :] = honing_simple_error
                    np.savetxt(f"simple_honing_cycle_{cycles}_test.csv", matrix, delimiter=",")

    print("Finished running")

if __name__ == "__main__":
    main()
