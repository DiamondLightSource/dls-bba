"""MD Tests analysis."""

from datetime import datetime
import argparse
import logging as log
from statistics import mean

from bba.common import Algorithm, PLANE_VALUES
from bba.fbba import FBBA
from bba.sbba import SBBA
from bba import accelerator as acc

import matplotlib.pyplot as plt
import numpy as np

def parse_args():
    parser = argparse.ArgumentParser(description="testing")
    parser.add_argument(
        "-c",
        "-cycle",
        dest = "cycle",
        action="store_true",
        default=False,
        help=""
    )
    parser.add_argument(
        "-t",
        "-correctors",
        dest = "corr_cycles_test",
        action="store_true",
        default=False,
        help=""
    )
    parser.add_argument(
        "-j",
        "-honing",
        dest = "honing_test",
        action="store_true",
        default=False,
        help=""
    )
    parser.add_argument(
        "-s",
        "-simple",
        dest = "simple",
        action="store_true",
        default=False,
        help=""
    )
    return parser.parse_args()
    

def main():
    args = parse_args()
    cycle = args.cycle
    corr_cycles_test = args.corr_cycles_test
    honing_test = args.honing_test
    simple = args.simple


    if cycle:
        matrix = np.genfromtxt("cycle_test.csv", delimiter=",")
        cycle_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        y = []
        yerr = []

        for index, cycle in enumerate(cycle_numbers):
            value_list = matrix[(index*2), :]
            error_list = matrix[(index*2) + 1, :]
            y_value = mean(value_list)
            y.append(y_value)
            sum_error = 0
            for place, error in enumerate(error_list):
                sum_error += (error/value_list[place])**2
            sum_error = np.sqrt(sum_error)
            yerr.append(sum_error * y_value)

        plt.errorbar(cycle_numbers, y, yerr, marker = ".")
        plt.title("Number of Cycles test - 20 Repeats")
        plt.xlabel("Cycle number")
        plt.ylabel("Offset Value")
        plt.grid(which = "both", axis = "both")
        plt.savefig("cyclestest.png", bbox_inches="tight", dpi=1200)
        plt.show()


    if corr_cycles_test:
        matrix1 = np.genfromtxt("corr1_cycle_test.csv", delimiter=",")
        matrix10 = np.genfromtxt("corr10_cycle_test.csv", delimiter=",")
        matrix20 = np.genfromtxt("corr20_cycle_test.csv", delimiter=",")
        corr_amps = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.20, 1.4, 1.6, 1.8, 2, 2.25, 2.5, 3, 3.5, 4, 4.5, 5]
        y1 = []
        y1err = []
        y10 = []
        y10err = []
        y20 = []
        y20err = []

        for index, cycle in enumerate(corr_amps):
            value_list = matrix1[(index*2), :]
            error_list = matrix1[(index*2) + 1, :]
            y_value = mean(value_list)
            y1.append(y_value)
            sum_error = 0
            for place, error in enumerate(error_list):
                sum_error += (error/value_list[place])**2
            sum_error = np.sqrt(sum_error)
            y1err.append(sum_error * y_value)

        for index, cycle in enumerate(corr_amps):
            value_list = matrix10[(index*2), :]
            error_list = matrix10[(index*2) + 1, :]
            y_value = mean(value_list)
            y10.append(y_value)
            sum_error = 0
            for place, error in enumerate(error_list):
                sum_error += (error/value_list[place])**2
            sum_error = np.sqrt(sum_error)
            y10err.append(sum_error * y_value)

        for index, cycle in enumerate(corr_amps):
            value_list = matrix20[(index*2), :]
            error_list = matrix20[(index*2) + 1, :]
            y_value = mean(value_list)
            y20.append(y_value)
            sum_error = 0
            for place, error in enumerate(error_list):
                sum_error += (error/value_list[place])**2
            sum_error = np.sqrt(sum_error)
            y20err.append(sum_error * y_value)

        plt.errorbar(corr_amps, y1, y1err, marker = ".", label="Cycles = 1")
        plt.errorbar(corr_amps, y10, y10err, marker = ".", label="Cycles = 10")
        plt.errorbar(corr_amps, y20, y20err, marker = ".", label="Cycles = 20")
        plt.title("Corrector Amplitude test - 10 Repeats")
        plt.xlabel("Corrector Amplitude")
        plt.ylabel("Offset Value")
        plt.legend()
        plt.grid(which = "both", axis = "both")
        plt.savefig("corramptest.png", bbox_inches="tight", dpi=1200)
        plt.show()


    if honing_test:
        matrix1_hon = np.genfromtxt("honing_cycle_1_test.csv", delimiter=",")
        matrix5_hon = np.genfromtxt("honing_cycle_5_test.csv", delimiter=",")
        matrix10_hon = np.genfromtxt("honing_cycle_10_test.csv", delimiter=",")
        iterations = [1,2,3,4,5,6,7,8]
        y1 = []
        y1err = []
        y5 = []
        y5err = []
        y10 = []
        y10err = []

        for index, cycle in enumerate(iterations):
            value_list = matrix1_hon[(index*2), :]
            error_list = matrix1_hon[(index*2) + 1, :]
            y_value = mean(value_list)
            y1.append(y_value)
            sum_error = 0
            for place, error in enumerate(error_list):
                sum_error += (error/value_list[place])**2
            sum_error = np.sqrt(sum_error)
            y1err.append(sum_error * y_value)

        for index, cycle in enumerate(iterations):
            value_list = matrix5_hon[(index*2), :]
            error_list = matrix5_hon[(index*2) + 1, :]
            y_value = mean(value_list)
            y5.append(y_value)
            sum_error = 0
            for place, error in enumerate(error_list):
                sum_error += (error/value_list[place])**2
            sum_error = np.sqrt(sum_error)
            y5err.append(sum_error * y_value)

        for index, cycle in enumerate(iterations):
            value_list = matrix10_hon[(index*2), :]
            error_list = matrix10_hon[(index*2) + 1, :]
            y_value = mean(value_list)
            y10.append(y_value)
            sum_error = 0
            for place, error in enumerate(error_list):
                sum_error += (error/value_list[place])**2
            sum_error = np.sqrt(sum_error)
            y10err.append(sum_error * y_value)

        plt.errorbar(iterations, y1, y1err, marker = ".", label="Cycles = 1")
        plt.errorbar(iterations, y5, y5err, marker = ".", label="Cycles = 5")
        plt.errorbar(iterations, y10, y10err, marker = ".", label="Cycles = 10")
        plt.title("Honing test - 10 Repeats")
        plt.xlabel("Iteration number")
        plt.ylabel("Offset Value")
        plt.legend()
        plt.grid(which = "both", axis = "both")
        plt.savefig("honingtest.png", bbox_inches="tight", dpi=1200)
        plt.show()

    if simple:
        matrix1 = np.genfromtxt("simple_honing_cycle_1_test.csv", delimiter=",")
        matrix10 = np.genfromtxt("simple_honing_cycle_10_test.csv", delimiter=",")
        steps = [1,2,3,4,5,6,7,8]
        plt.errorbar(steps, matrix1[0, :], matrix1[1, :], marker = ".", label="Cycles = 1")
        plt.errorbar(steps, matrix10[0, :], matrix10[1, :], marker = ".", label="Cycles = 10")
        plt.title("Simple Honing test")
        plt.xlabel("Iteration number")
        plt.ylabel("Offset Value")
        plt.legend()
        plt.grid(which = "both", axis = "both")
        plt.savefig("simplehoningtest.png", bbox_inches="tight", dpi=1200)
        plt.show()


if __name__ == "__main__":
    main()
