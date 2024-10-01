import numpy
from scipy.io import loadmat
import matplotlib.pyplot as plt


enabled_bpms = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
valid_bpms = len(numpy.flatnonzero(enabled_bpms))

python_data = dict()
data = loadmat("/dls/physics/jzs47954/BBA_logs/SlowBBA-20240917T121828/SlowBBA-20240917T122214-SR01C-DI-EBPM-03-rawdata.mat", simplify_cells=True)["rawdata"]
for key, value in data.items():
    parts = key.split("_")
    python_data[f"Quad {parts[2]} {parts[1]} Corr {int(parts[3])-3:+}"] = numpy.delete(value, numpy.logical_not(enabled_bpms))

# Load mat SBBA data
matlab_data = dict()
for axis in ["x", "y"]:
    if axis == "x":
        dct = loadmat("/dls/physics/jzs47954/BBA_logs/BBA_backup_20240917T123919/s1Q2AD4h1_2024-09-17_12-41-23.mat", simplify_cells=True)
    else:
        dct = loadmat("/dls/physics/jzs47954/BBA_logs/BBA_backup_20240917T123919/s1Q2AD4v1_2024-09-17_12-41-44.mat", simplify_cells=True)
    qms = dct["QMS"]
    # x0 = start
    for i in range(5):
        matlab_data[f"Quad High {axis} Corr {i-2:+}"] = qms[f"{axis}1"][:, 4-i] * 1000
        matlab_data[f"Quad Low {axis} Corr {i-2:+}"] = qms[f"{axis}2"][:, 4-i] * 1000

#print(set(python_data.keys()) - set(matlab_data.keys()))
for key in python_data.keys():
    assert key in matlab_data.keys()
for key in matlab_data.keys():
    assert key in python_data.keys()

fig, axs = plt.subplots(4, 5)
keys = list(python_data.keys())
#keys.sort()
axs = axs.ravel()
#numpy.set_printoptions(suppress=True)
for key, ax in zip(keys, axs):
    #print(python_data[key])
    #print(matlab_data[key])
    #raise Exception()
    ax.plot(range(valid_bpms), python_data[key], color="blue", linestyle="-", linewidth=0.1, marker="x", markersize=0.1)
    ax.plot(range(valid_bpms), matlab_data[key], color="red", linestyle="-", linewidth=0.1, marker="x", markersize=0.1)
    ax.title.set_text(key)
plt.show()
"""
plt.subplots_adjust(hspace=0.4, wspace=0.3)
plt.gcf().set_size_inches(15, 10)
plt.savefig("SlowBBA_raw.png", bbox_inches="tight", dpi=1000)
"""
