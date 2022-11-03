"""A file that contains all constants and filepaths."""
from bba import faa
# Default constants.
CYCLES = 1
FREQUENCY = 8

# Plane constants.
HORIZONTAL_PLANE = 0  # Fundamental definition of plane orientation
VERTICAL_PLANE = 1
X = HORIZONTAL_PLANE
Y = VERTICAL_PLANE
AXIS_NAMES = {HORIZONTAL_PLANE: "X", VERTICAL_PLANE: "Y"}
CORRECTOR_FAMILIES = {HORIZONTAL_PLANE: "HSTR", VERTICAL_PLANE: "VSTR"}

# Formatting constants
LOG_FORMAT = "%(levelname)-7s: %(message)s"
#TICKS_PER_SECOND = 10072
NETWORK_LAG_S = 0.5
SAFETY_NET_S = 0.1
QUAD_SLEW_RATE = 0.5  # A/s
NETWORK_LAG = int(NETWORK_LAG_S * faa.TICKS_PER_SECOND)
SAFETY_NET = int(SAFETY_NET_S * faa.TICKS_PER_SECOND)

BPM_IDS = range(174)
IOCS = ["SR%02dA-CS-FOFB-01" % i for i in range(1, 25)]

# Config filepaths

H_AMPS_FILE = "config/horizontal_bba.csv"
V_AMPS_FILE = "config/vertical_bba.csv"
CORRECTORS_FILE = "config/correctors.csv"

# Other filepaths
# GoldenBPMResp.mat Root
DATAROOT = "/dls_sw/work/common/matlab/mml/machine/diamondopsdata/"
