import numpy
import scipy.io as io

from dls_bba.plotting import bowtie_plot
from dls_bba.datatypes import RawData
from dls_bba.machine import Machine
from dls_bba.sbba import SlowBBA

# Common init
machine = Machine()
machine._load_element_and_name_lists()
print(machine.get_enabled_bpms())
algorithm = SlowBBA(machine)

# Load py SBBA data
raw_data = RawData.from_file("/dls/physics/owr68555/4July2023/SlowBBA-20230704T182722/SlowBBA-20230704T182744-SR01C-DI-EBPM-05-rawdata.mat")
"""
# Analyse & print py SBBA data
print("\nPython SBBA & Python analysis:")
results = algorithm.analyse(raw_data)
for key, value in results.results.items():
    print(f"Quad: {key.split('_')[0]}, Plane: {key.split('_')[1]}, Mean: {value[0]}, SD: {value[1]}")
print("Offsets:")
for key, value in results.offsets.items():
    print(key, value)
"""

# Load mat SBBA data
rawdata = dict()
expected = dict()
for axis in ["x", "y"]:
    if axis == "x":
        #dct = io.loadmat("/dls/ops-physics/diamonddata/QMS/2023/BBA_backup_20230704T171321/s1Q2AB7h1_2023-07-04_17-12-47.mat", simplify_cells=True)
        dct = io.loadmat("/dls/physics/jzs47954/BBA_logs/BBA_backup_20240917T123919/s1Q2AD4h1_2024-09-17_12-41-23.mat", simplify_cells=True)
    else:
        #dct = io.loadmat("/dls/ops-physics/diamonddata/QMS/2023/BBA_backup_20230704T171321/s1Q2AB7v1_2023-07-04_17-13-10.mat", simplify_cells=True)
        dct = io.loadmat("/dls/physics/jzs47954/BBA_logs/BBA_backup_20240917T123919/s1Q1D1v1_2024-09-17_12-39-40.mat", simplify_cells=True)#s1Q2AD4v1_2024-09-17_12-41-44.mat
    qms = dct["QMS"]
    # Quad name is hard coded for now, but we could try and derive it from qms["QuadDev"] and qms["QuadFamily"], but we'd be making some big assumptions here, nominally: that sector in MML is equivalent to cell in pytac, that the known issues with cells in pytac (#136) don't cause a problem, and that the ring mode is the same
    quad_name = "SR01A_PC_Q2AB_07"
    if qms["QuadPlane"] != 1 and axis == "x":
        raise TypeError("Quadrupole data is not from the x plane.")
    elif qms["QuadPlane"] != 2 and axis == "y":
        raise TypeError("Quadrupole data is not from the y plane.")
    if qms["QuadraticFit"] != 0:
        raise TypeError("Data uses quadratic fit, please use linear fit.")
    expected[f"{quad_name}__{axis}_center_and_stdev"] = [qms["Center"], qms["CenterSTD"]]
    # N.B. disabled BPMs have already been removed from the matlab BBA data so we do some padding to make the dimensions match
    pad = numpy.zeros(len(machine.fofb_disabled[axis]) - len(qms["BPMStatus"]), dtype=int)
    for index in range(5):
        rawdata[f"{quad_name}__{axis}_High_{index + 1}"] = numpy.append(qms[f"{axis}1"][:, index], pad)
        rawdata[f"{quad_name}__{axis}_Low_{index + 1}"] = numpy.append(qms[f"{axis}2"][:, index], pad)
# Outside the loop as we assume that metadata is the same for x and y plane.
metadata = dict()
# Same note as quad_name ~~~~~~~~~ check rows 74 to 80 in BPM device lists ~~~~~~~~~~~ 
metadata["bpm_name"] = "SR01C-DI-EBPM-05"
metadata["enabled_bpms"] = numpy.append(qms["BPMStatus"], pad)
metadata["OUTLIER_FACTOR"] = qms["OutlierFactor"]
metadata["sigma_bpm"] = numpy.append(qms["BPMStd"], pad)
metadata["MIN_SLOPE_FRACTION"] = 0.25  # Hardcoded in quadplot.m, also our default value
metadata["CENTER_OUTLIER_FACTOR"] = 1  # Hardcoded in quadplot.m, also our default value
# N.B. This number is the BPM's position in the list of BPMs, not its index in the ring
bpm_number = numpy.intersect1d(
    numpy.where(qms["BPMDevList"][:, 0] == qms["BPMDev"][0]),
    numpy.where(qms["BPMDevList"][:, 1] == qms["BPMDev"][1])
)
if len(bpm_number) > 1:  # This shouldn't be possible.
    raise IndexError("Device list should only contain 1:1 mappings.")
metadata["bpm_index"] = bpm_number[0]
raw_data = RawData(rawdata, metadata)

print("\nMatlab SBBA & Python analysis:")
results = algorithm.analyse(raw_data)
for key, value in results.results.items():
    print(f"    Quad: {key.split('__')[0]}, Plane: {key.split('__')[1][0]}, Mean: {value[0]: .8e}, SD: {value[1]: .8e}")
#print("Offsets:")
#for key, value in results.offsets.items():
#    print(key, value)

print("\nMatlab SBBA & Matlab analysis:")
for key, value in expected.items():
    print(f"    Quad: {key.split('__')[0]}, Plane: {key.split('__')[1][0]}, Mean: {value[0]: .8e}, SD: {value[1]: .8e}")

#bowtie_plot(results)
