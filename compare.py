from os import listdir, path
from scipy.io import loadmat
import matplotlib.pyplot as plt
import numpy


filepath = "/dls/physics/jzs47954/BBA_logs/SlowBBA-20240917T121828"
python_lines = []
for filename in listdir(filepath):
    if filename.endswith("results.mat"):
        data = loadmat(path.join(filepath, filename), simplify_cells=True)
        bpm = data["metadata"]["bpm_name"]
        bpm_cell = int(bpm[2:4])
        bpm_number = int(bpm[-2:])
        for quad, values in data["results"].items():
            quad_cell = int(quad[2:4])
            quad_number = int(quad[-4:-2])
            plane = quad[-1].upper()
            center = values[0] * 1e3
            std_dev = values[1] * 1e3
            python_lines.append([f"QUAD({quad_cell},{quad_number}) BPM({bpm_cell},{bpm_number}) {plane}-axis: {center:+.5f} +/-{std_dev:.5f}", center, std_dev])


filepath = "/dls/physics/jzs47954/BBA_logs/BBA_backup_20240917T123919"
matlab_lines = []
for filename in listdir(filepath):
    if filename.endswith(".mat"):
        data = loadmat(path.join(filepath, filename), simplify_cells=True)["QMS"]
        quad_cell, quad_number = data["QuadDev"]
        bpm_cell, bpm_number = data["BPMDev"]
        plane = data["BPMFamily"][-1].upper()
        center = data["Center"] * 1e6
        std_dev = data["CenterSTD"] * 1e6
        matlab_lines.append([f"QUAD({quad_cell},{quad_number}) BPM({bpm_cell},{bpm_number}) {plane}-axis: {center:+.5f} +/-{std_dev:.5f}", center, std_dev])


python_lines.sort()
matlab_lines.sort()
differences = []
for python_line, matlab_line in zip(python_lines, matlab_lines):
    print(python_line[0] + " Python")
    print(matlab_line[0] + " Matlab")
    differences.append([python_line[0].split("-")[0][:-2], abs(python_line[1]-matlab_line[1]), abs(python_line[2]-matlab_line[2])])
    print(f"Diff: {abs(python_line[1]-matlab_line[1]):.5f} {abs(python_line[2]-matlab_line[2]):.5f}")
    print("---------------------------------------------------------")


differences = numpy.array(differences)
fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.errorbar(
    differences[:, 0][0::2],
    numpy.array(differences[:, 1][0::2], dtype=float),
    yerr=numpy.array(differences[:, 2][0::2], dtype=float),
    color="black",
    ecolor="blue",
    capsize=2.5,
)
ax2.errorbar(
    differences[:, 0][1::2],
    numpy.array(differences[:, 1][1::2], dtype=float),
    yerr=numpy.array(differences[:, 2][1::2], dtype=float),
    color="black",
    ecolor="blue",
    capsize=2.5,
)
ax1.title.set_text('X-axis')
ax2.title.set_text('Y-axis')
plt.setp(ax1.get_xticklabels() + ax2.get_xticklabels(), rotation=50, ha='right')
plt.show()

#25.5 vs 7
