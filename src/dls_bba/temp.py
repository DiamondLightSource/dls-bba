import os
from collections import defaultdict  # noqa
from statistics import mean, stdev  # noqa

import matplotlib.pyplot as plt
import numpy as np

TEMP_FILEPATH_ROOT = os.path.join("/dls", "physics", "owr68555", "24Jan2023")


# repeats = 8
# cycles = 16
# frequency = 8
# quadrupole_scalar = 0.02
# corrector_scalar = 2
# _fft = False
# offset = 0
# method = "FBBA"

offset_0_original = 0.789
spread_index = 1
x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8]

index = 0
data1 = np.genfromtxt(
    f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_FBBA_8_c1_f8_q0.01_cs1_fftFalse_offset0_300ma1.csv",
    delimiter=",",
)
label1 = "honing_simple_repeats_FBBA_8_c1_f8_q0.01_cs1_fftFalse_offset0_300ma1"
y_1 = data1[index, :]
cumy = np.cumsum(y_1)
ydata = [offset_0_original] + [value + offset_0_original for value in cumy]
y_err_1 = [0]
y_err_1.extend(data1[index + 1, :])
spread_mean = mean(ydata[spread_index:])
spread_list = [(y_err_1[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
spread_error = spread_mean * np.sqrt(sum(spread_list))
# print(len(x_axis), len(ydata), len(y_err_1))
# print(x_axis)
# print(ydata)
# print(y_err_1)
plt.errorbar(
    x_axis,
    ydata,
    y_err_1,
    marker=".",
    capsize=5,
    color="b",
    linestyle="--",
    label=f"FBBA: 8r 1c 8f 0.01q 1c, 300mA, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
)  # honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",

data2 = np.genfromtxt(
    f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_FBBA_8_c1_f8_q0.01_cs1_fftFalse_offset0_300ma2.csv",
    delimiter=",",
)
label2 = "honing_simple_repeats_FBBA_8_c1_f8_q0.01_cs1_fftFalse_offset0_300ma2"
y_2 = data2[index, :]
cumy = np.cumsum(y_2)
ydata = [offset_0_original] + [value + offset_0_original for value in cumy]
y_err_2 = [0]
y_err_2.extend(data2[index + 1, :])
spread_mean = mean(ydata[spread_index:])
spread_list = [(y_err_2[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
spread_error = spread_mean * np.sqrt(sum(spread_list))
plt.errorbar(
    x_axis,
    ydata,
    y_err_2,
    marker=".",
    capsize=5,
    color="c",
    linestyle="--",
    label=f"FBBA: 8r 1c 8f 0.01q 1c, 300mA, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
)

data3 = np.genfromtxt(
    f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_FBBA_8_c16_f8_q0.02_cs2_fftFalse_offset0_low1.csv",
    delimiter=",",
)
label3 = "honing_simple_repeats_FBBA_8_c16_f8_q0.02_cs2_fftFalse_offset0_low1.csv"
y_3 = data3[index, :]
cumy = np.cumsum(y_3)
ydata = [offset_0_original] + [value + offset_0_original for value in cumy]
y_err_3 = [0]
y_err_3.extend(data3[index + 1, :])
spread_mean = mean(ydata[spread_index:])
spread_list = [(y_err_3[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
spread_error = spread_mean * np.sqrt(sum(spread_list))
plt.errorbar(
    x_axis,
    ydata,
    y_err_3,
    marker=".",
    capsize=5,
    color="r",
    linestyle="-",
    label=f"FBBA: 8r 16c 8f 0.02q 2c, 10mA, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
)

data4 = np.genfromtxt(
    f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_FBBA_8_c16_f8_q0.02_cs2_fftFalse_offset0_low2.csv",
    delimiter=",",
)
label4 = "honing_simple_repeats_FBBA_8_c16_f8_q0.02_cs2_fftFalse_offset0_low2.csv"
y_4 = data4[index, :]
cumy = np.cumsum(y_4)
ydata = [offset_0_original] + [value + offset_0_original for value in cumy]
y_err_4 = [0]
y_err_4.extend(data4[index + 1, :])
spread_mean = mean(ydata[spread_index:])
spread_list = [(y_err_4[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
spread_error = spread_mean * np.sqrt(sum(spread_list))
plt.errorbar(
    x_axis,
    ydata,
    y_err_4,
    marker=".",
    capsize=5,
    color="g",
    linestyle="-",
    label=f"FBBA: 8r 16c 8f 0.02q 2c, 10mA, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
)

plt.title("0 Offset, No FFT")
plt.xlim(0, 8.1)
plt.xlabel("Number run.")
plt.ylabel("Value (mm)")
plt.grid(which="both", axis="both")
plt.legend()
plt.savefig(
    f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_high_low_fbba_plot_spread.png",
    bbox_inches="tight",
    dpi=1200,
)
plt.close()


# _________________________________________

value_dictionary = defaultdict(list)
error_dictionary = defaultdict(list)

for i in range(0, 8):

    repeats = 8
    cycles = 16
    frequency = 8
    quadrupole_scalar = 0.02
    corrector_scalar = 2
    x_axis = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    index = 0
    spread_index = i

    offset_0_original = 0.7890
    plt.hlines(y=offset_0_original, xmin=0, xmax=8.1, color="r", linestyle="--")

    offset_100_original = 0.8890
    plt.hlines(y=offset_100_original, xmin=0, xmax=8.1, color="r", linestyle="--")

    # BBA matlab 0 offset:
    method = "Matlab BBA"
    offset = 0
    y = [0.789, 0.7160, 0.7110, 0.7180, 0.7140, 0.7200, 0.7170, 0.7160, 0.7200]
    plt.plot(
        x_axis,
        y,
        marker="x",
        color="k",
        linestyle="--",
        label=f"{method}, Offset:{offset}, Spread: {str(mean(y[spread_index:]))[:6]} +- {str(stdev(y[spread_index:]))[:6]}",
    )
    value_dictionary["BBA_0"].append(mean(y[spread_index:]))
    error_dictionary["BBA_0"].append(stdev(y[spread_index:]))

    # BBA matlab 100 offset:
    method = "Matlab BBA"
    offset = 100
    y = [0.889, 0.7340, 0.7130, 0.713, 0.7190, 0.7150, 0.713, 0.7080, 0.7170]
    plt.plot(
        x_axis,
        y,
        marker="x",
        color="k",
        label=f"{method}, Offset:{offset}, Spread: {str(mean(y[spread_index:]))[:6]} +- {str(stdev(y[spread_index:]))[:6]}",
    )
    value_dictionary["BBA_100"].append(mean(y[spread_index:]))
    error_dictionary["BBA_100"].append(stdev(y[spread_index:]))

    _fft = False
    offset = 0
    method = "FBBA"
    data = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
        delimiter=",",
    )
    y = data[index, :]  # type: ignore
    cumy = np.cumsum(y)
    ydata = [offset_0_original] + [value + offset_0_original for value in cumy]
    y_err = [0]
    y_err.extend(data[index + 1, :])
    spread_mean = mean(ydata[spread_index:])
    spread_list = [(y_err[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
    spread_error = spread_mean * np.sqrt(sum(spread_list))
    plt.errorbar(
        x_axis,
        ydata,
        y_err,
        marker=".",
        capsize=5,
        color="b",
        linestyle="--",
        label=f"{method}, Offset:{offset}, fft:{_fft}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
    )
    value_dictionary["FBBA_0_fftF"].append(spread_mean)
    error_dictionary["FBBA_0_fftF"].append(spread_error)

    _fft = True
    offset = 0
    method = "FBBA"
    data = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
        delimiter=",",
    )
    y = data[index, :]  # type: ignore
    cumy = np.cumsum(y)
    ydata = [offset_0_original] + [value + offset_0_original for value in cumy]
    y_err = [0]
    y_err.extend(data[index + 1, :])
    spread_mean = mean(ydata[spread_index:])
    spread_list = [(y_err[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
    spread_error = spread_mean * np.sqrt(sum(spread_list))
    plt.errorbar(
        x_axis,
        ydata,
        y_err,
        marker=".",
        capsize=5,
        color="g",
        linestyle="--",
        label=f"{method}, Offset:{offset}, fft:{_fft}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
    )
    value_dictionary["FBBA_0_fftT"].append(spread_mean)
    error_dictionary["FBBA_0_fftT"].append(spread_error)

    _fft = False
    offset = 100
    method = "FBBA"
    data = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
        delimiter=",",
    )
    y = data[index, :]  # type: ignore
    cumy = np.cumsum(y)
    ydata = [offset_100_original] + [value + offset_100_original for value in cumy]
    y_err = [0]
    y_err.extend(data[index + 1, :])
    spread_mean = mean(ydata[spread_index:])
    spread_list = [(y_err[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
    spread_error = spread_mean * np.sqrt(sum(spread_list))
    plt.errorbar(
        x_axis,
        ydata,
        y_err,
        marker=".",
        capsize=5,
        color="c",
        label=f"{method}, Offset:{offset}, fft:{_fft}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
    )
    value_dictionary["FBBA_100_fftF"].append(spread_mean)
    error_dictionary["FBBA_100_fftF"].append(spread_error)

    _fft = True
    offset = 100
    method = "FBBA"
    data = np.genfromtxt(
        f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{method}_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_fft{_fft}_offset{offset}.csv",
        delimiter=",",
    )
    y = data[index, :]  # type: ignore
    cumy = np.cumsum(y)
    ydata = [offset_100_original] + [value + offset_100_original for value in cumy]
    y_err = [0]
    y_err.extend(data[index + 1, :])
    spread_mean = mean(ydata[spread_index:])
    spread_list = [(y_err[n] / ydata[n]) ** 2 for n in range(spread_index, 9)]
    spread_error = spread_mean * np.sqrt(sum(spread_list))
    plt.errorbar(
        x_axis,
        ydata,
        y_err,
        marker=".",
        capsize=5,
        color="y",
        label=f"{method}, Offset:{offset}, fft:{_fft}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
    )
    value_dictionary["FBBA_100_fftT"].append(spread_mean)
    error_dictionary["FBBA_100_fftT"].append(spread_error)

    plt.title(f"Honing Test of BPM 1-5, Spread is from point {spread_index}")
    plt.xlim(0, 8.1)
    plt.xlabel("Run number")
    plt.ylabel("Offset Value (mm)")
    plt.grid(which="both", axis="both")
    plt.legend()
    plt.savefig(
        f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_plot_stats{i}.png",
        bbox_inches="tight",
        dpi=1200,
    )
    plt.close()


marker_colour_line_dict = {
    "BBA_0": ["x", "k", "--"],
    "BBA_100": ["x", "k", "-"],
    "FBBA_0_fftF": [".", "b", "--"],
    "FBBA_0_fftT": [".", "g", "--"],
    "FBBA_100_fftF": [".", "c", "-"],
    "FBBA_100_fftT": [".", "y", "-"],
}

x_axis = [1, 2, 3, 4, 5, 6, 7, 8]
for key in value_dictionary.keys():
    value = value_dictionary[key]
    error = error_dictionary[key]
    value_mean = value_dictionary[key][0:]
    error_mean = error_dictionary[key][0:]
    spread_mean = mean(value_mean)
    spread_list = [
        (error_mean[n] / value_mean[n]) ** 2 for n, v in enumerate(value_mean)
    ]
    spread_error = spread_mean * np.sqrt(sum(spread_list))
    plt.errorbar(
        x_axis,
        value,
        error,
        marker=marker_colour_line_dict[key][0],
        color=marker_colour_line_dict[key][1],
        linestyle=marker_colour_line_dict[key][2],
        capsize=5,
        label=f"Key:{key}, Spread: {str(spread_mean)[:6]} +- {str(spread_error)[:6]}",
    )
plt.title("Change in spread dependant on startpoint: BPM 1-5, excl. 1st point")
plt.xlim(0.9, 8.1)
plt.xlabel("Start averaging from nth run.")
plt.ylabel("Spread Value (mm)")
plt.grid(which="both", axis="both")
plt.legend()
plt.savefig(
    f"{TEMP_FILEPATH_ROOT}/honing_simple_repeats_{repeats}_c{cycles}_f{frequency}_q{quadrupole_scalar}_cs{corrector_scalar}_plot_spread.png",
    bbox_inches="tight",
    dpi=1200,
)
plt.close()
