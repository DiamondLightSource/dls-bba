"""
Various ways of testing BBA.

    - change frequency of corrector oscillations
    - change number of corrector cycles
    - scan whole cell
"""
import argparse
import logging as log

from bba.constants import LOG_FORMAT, H_AMPS_FILE, V_AMPS_FILE, FREQUENCY, CYCLES, PLANE_VALUES
from bba.accelerator import Accelerator as acc
from bba.excite import Oscillation
from bba.faa import TICKS_PER_SECOND
from bba.jump_bba import get_filename_prefix, jump_bba, DECIMATED

def get_new_logger():
    logger = log.getLogger()
    filename = "data/{}.log".format(get_filename_prefix())
    file_handler = log.FileHandler(filename)
    file_handler.setLevel(log.DEBUG)
    formatter = log.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(log.StreamHandler())
    logger.setLevel(log.DEBUG)


def load_amps_file(filename, quad_scale=1.0, corr_scale=1.0):
    amps = {}
    with open(filename) as f:
        for line in f:
            if line.strip():
                bpm_pv, quad_pv, quad_amps, _, corr_pv, corr_amps, _ = line.split(",")
                amps[quad_pv.split(":")[0]] = (
                    quad_scale * float(quad_amps),
                    corr_scale * float(corr_amps),
                )
    return amps


def load_amps(quad_scale=1.0, corr_scale=1.0):
    h_amps = load_amps_file(H_AMPS_FILE, quad_scale, corr_scale)
    v_amps = load_amps_file(V_AMPS_FILE, quad_scale, corr_scale)
    return h_amps, v_amps


def one_bba(accelerator, quad, plane):
    """Needs accelerator, quad element and plane dictionary."""
    quad_prefix = accelerator.prefix_from_element(quad, "b1")
    log.warning("BBA on quad {} in plane {}".format(quad_prefix, plane.axis))
    new_quad_step = accelerator.measure_quad(quad) * constants.QUADRUPOLE_SCALAR
    corrector_index, corr_element = accelerator.effective_corrector(quad, plane)
    corr_pv = accelerator.element_to_pv(corr_element, plane)
    new_corr_amp = accelerator.microrads(corr_pv)
    osc = excite.Oscillation(new_corr_amp, plane, constants.FREQUENCY, constants.CYCLES)
    jump_bba.jump_bba(quad, new_quad_step, osc, accelerator)

"""
def frequency_scan(accelerator, quad, plane):
    log.warning("Beginning test of different corrector oscillation frequencies.")
    amps = load_amps()[plane.index]
    quad_step, corr_amp = amps[accelerator.prefix_from_element(quad, "b1")]
    for i in range(1, 8):
        period = TICKS_PER_SECOND // i
        log.info("The calculated period is {}.".format(period))
        osc = Oscillation(corr_amp, plane, i, CYCLES)
        # TODO: Cannot work: Passing plane in quad_step arg and missing accelerator arg
        jump_bba(quad, plane, quad_step, osc)


def cycle_scan(accelerator, quad, plane):
    log.warning("Beginning test of different numbers of corrector cycles.")
    amps = load_amps()[plane.index]
    quad_step, corr_amp = amps[accelerator.prefix_from_element(quad, "b1")]
    for cycles in range(1, 5):
        log.info("Trying {} cycles.".format(cycles))
        osc = Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
        # TODO: Cannot work: Passing plane in quad_step arg and missing accelerator arg
        jump_bba(quad, plane, quad_step, osc)


def repeatability_scan(accelerator, quad, plane, counts):
    log.warning("Beginning test of different numbers of corrector cycles.")
    amps = load_amps()[plane.index]
    quad_step, corr_amp = amps[accelerator.prefix_from_element(quad, "b1")]
    log.info("Quad_step %s, corr_amp %s", quad_step, corr_amp)
    for count in counts:  # Just run ten times at 8 Hz
        log.info("Trying scan {} of {}.".format(count, counts))
        osc = Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
        # TODO: Cannot work: Missing accelerator arg
        jump_bba(quad, quad_step, osc)


def compare_decimated_data(accelerator, quad, plane):
    log.warning("Beginning test between raw and decimated data.")
    amps = load_amps()[plane.index]
    quad_step, corr_amp = amps[accelerator.prefix_from_element(quad, "b1")]

    osc = Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
    # TODO: Cannot work: Passing plane in quad_step arg and missing accelerator arg
    jump_bba(quad, plane, quad_step, osc)
    # Now do the full one.  Change a constant!
    DECIMATED = False
    try:
        # TODO: Cannot work: Passing plane in quad_step arg and missing accelerator arg
        jump_bba(quad, plane, quad_step, osc)
    except Exception as e:
        log.warn("BBA failed: {} ({}).".format(e, e.__class__))
    # And back!
    DECIMATED = True


def scan_cell(accelerator, cell):
    log.warning("Beginning scan of cell {}.".format(cell))
    quads = accelerator.quads_from_cell(cell)
    amps = load_amps()
    for quad in quads:
        for plane in (PLANE_VALUES["HORIZONTAL"]["axis"], PLANE_VALUES["VERTICAL"]["axis"]):
            quad_step, corr_amp = amps[plane][accelerator.prefix_from_element(quad, "b1")]
            osc = Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
            # TODO: Cannot work: Passing plane in quad_step arg and missing accelerator arg
            jump_bba(quad, plane, quad_step, osc)


def scan_amplitudes(accelerator, quad, plane, scale_quad=True, scale_corr=True):
    log.warning(
        "Beginning scaling test: quad? {}; corr? {}.".format(scale_quad, scale_corr)
    )
    amps = load_amps()[plane.index]
    quad_step, corr_amp = amps[accelerator.prefix_from_element(quad, "b1")]
    osc = Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
    scales = [0.5, 1.0, 2.0, 5.0]
    for s in scales:
        if scale_quad:
            qs = quad_step * s
        if scale_corr:
            ca = corr_amp * s
            osc = Oscillation(ca, plane, FREQUENCY, CYCLES)
        # TODO: Cannot work: Passing plane in quad_step arg and missing accelerator arg
        jump_bba.jump_bba(quad, plane, qs, osc)
"""

def parse_args():
    parser = argparse.ArgumentParser(description="Take BBA measurements")
    parser.add_argument(
        "-p",
        "--plane",
        dest="plane",
        action="store_const",
        default="HORIZONTAL",
        const="VERTICAL",
        help="Which plane to measure",
    )
    parser.add_argument(
        "-q",
        "--quad-scale",
        dest="quad_scale",
        action="store",
        default=1.0,
        help="Quadrupole amplitude scaler",
    )
    parser.add_argument(
        "-c",
        "--corrector-scale",
        dest="corr_scale",
        action="store",
        default=1.0,
        help="Corrector amplitude scaler",
    )
    return parser.parse_args()


def main():
    print("running")
    args = parse_args()
    plane = str(args.plane)
    quad_scale = float(args.quad_scale)
    corr_scale = float(args.corr_scale)

    # TODO: System that will accept a cell or selection of quads that need correcting, then will adjust which function is required.
    # TODO: Doesnt remove all inactive elements, only bpms.
    pv = "SR01A-PC-Q2B-09"
    get_new_logger()
    log.warning(
        "Plane: {}, Quad scale: {}, Corr scale: {}\n".format(
            plane, quad_scale, corr_scale
        )
    )
    ringmode = None
    # TODO: Tie in axis into lattice? Or run for both axes as default (same as SBBA)?
    accelerator = acc.Accelerator(ringmode)
    quad = accelerator.pv_to_quad(pv)
    one_bba(accelerator, quad, constants.PLANE_VALUES[plane])

    """
    one_bba(accelerator, quad, plane)
    # None of these work
    frequency_scan(accelerator, quad, plane)
    cycle_scan(accelerator, quad, plane)
    repeatability_scan(accelerator, quad, plane, counts)
    compare_decimated_data(accelerator, quad, plane)
    scan_cell(accelerator, cell)
    scan_amplitudes(accelerator, quad, plane, scale_quad=True, scale_corr=True)
    """


if __name__ == "__main__":
    main()
