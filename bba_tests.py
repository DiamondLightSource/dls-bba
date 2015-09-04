'''
Various ways of testing BBA:

    - change frequency of corrector oscillations
    - change number of corrector cycles
    - scan whole cell
'''
from __future__ import division
from pkg_resources import require
require('cothread')
require('fa-archiver')
require('scipy')
require('aphla')
import logging as log

import pml
import jump_bba
import fa

###############
# Global config
H_AMPS_FILE = 'config/horizontal_bba.txt'
V_AMPS_FILE = 'config/vertical_bba.txt'
# Defaults
CYCLES = 1
FREQ = 8
PERIOD = 1259
###############


LOG_FORMAT = '%(levelname)-7s: %(message)s'


def get_new_logger():
    logger = log.getLogger()
    filename = 'data/{}.log'.format(jump_bba.get_filename_prefix())
    file_handler = log.FileHandler(filename)
    file_handler.setLevel(log.DEBUG)
    formatter = log.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(log.StreamHandler())
    logger.setLevel(log.DEBUG)


def load_amps_file(filename):
    amps = {}
    with open(filename) as f:
        for line in f:
            bpm_pv, quad_pv, quad_amps, _, corr_pv, corr_amps, _ = line.split()
            amps[pml.prefix_from_pv(quad_pv)] = (float(quad_amps),
                                                 float(corr_amps))
    return amps


def load_amps():
    h_amps = load_amps_file(H_AMPS_FILE)
    v_amps = load_amps_file(V_AMPS_FILE)
    return h_amps, v_amps


def one_bba(quad, plane):
    quad_prefix = pml.prefix_from_element(quad)
    log.warn('BBA on quad {} in plane {}'.format(quad_prefix,
                                                 pml.AXIS_NAMES[plane]))
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[quad_prefix]
    osc = jump_bba.Oscillation(corr_amp, PERIOD, CYCLES)
    jump_bba.jump_bba(quad, plane, quad_step, osc)


def frequency_scan(quad, plane):
    log.warn('Beginning test of different corrector oscillation frequencies.')
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    for i in range(1, 8):
        period = fa.TICKS_PER_SECOND // i
        log.info('The calculated period is {}.'.format(period))
        osc = jump_bba.Oscillation(corr_amp, period, CYCLES)
        jump_bba.jump_bba(quad, plane, quad_step, osc)


def cycle_scan(quad, plane):
    log.warn('Beginning test of different numbers of corrector cycles.')
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    for cycles in range(1, 5):
        log.info('Trying {} cycles.'.format(cycles))
        osc = jump_bba.Oscillation(corr_amp, PERIOD, cycles)
        jump_bba.jump_bba(quad, plane, quad_step, osc)


def repeatability_scan(quad, plane, counts):
    log.warn('Beginning test of different numbers of corrector cycles.')
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    for count in counts:  # Just run ten times at 8 Hz
        log.info('Trying scan {} of {}.'.format(count, counts))
        osc = jump_bba.Oscillation(corr_amp, PERIOD, CYCLES)
        jump_bba.jump_bba(quad, plane, quad_step, osc)


def compare_decimated_data(quad, plane):
    log.warn('Beginning test between raw and decimated data.')
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    osc = jump_bba.Oscillation(corr_amp, PERIOD, CYCLES)
    jump_bba.jump_bba(quad, plane, quad_step, osc)
    # Now do the full one.  Change a constant!
    jump_bba.DECIMATED = False
    try:
        jump_bba.jump_bba(quad, plane, quad_step, osc)
    except Exception as e:
        log.warn('BBA failed: {} ({}).'.format(e, e.__class__))
    # And back!
    jump_bba.DECIMATED = True


def scan_cell(cell):
    log.warn('Beginning scan of cell {}.'.format(cell))
    quads = pml.quads_from_cell(cell)
    amps = load_amps()
    for quad in quads:
        for plane in (pml.X, pml.Y):
            quad_step, corr_amp = amps[plane][pml.prefix_from_element(quad)]
            osc = jump_bba.Oscillation(corr_amp, PERIOD, CYCLES)
            jump_bba.jump_bba(quad, plane, quad_step, osc)


def scan_amplitudes(quad, plane, scale_quad=True, scale_corr=True):
    log.warn('Beginning scaling test: quad? {}; corr? {}.'.format(scale_quad,
                                                                  scale_corr))
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    osc = jump_bba.Oscillation(corr_amp, PERIOD, CYCLES)
    scales = [0.5, 1.0, 2.0, 5.0]
    for s in scales:
        if scale_quad:
            qs = quad_step * s
        if scale_corr:
            ca = corr_amp * s
            osc = jump_bba.Oscillation(ca, PERIOD, CYCLES)
        jump_bba.jump_bba(quad, plane, qs, osc)


if __name__ == '__main__':
    h, v = load_amps()
    pv = 'SR01A-PC-Q1D-01'
    get_new_logger()
    quad = pml.quad_from_pv(pv)
    one_bba(quad, pml.X)
    repeatability_scan(quad, pml.X, 10)
    frequency_scan(quad, pml.X)
    compare_decimated_data(quad, pml.X)
    scan_cell(1)
    cycle_scan(quad, pml.X)
