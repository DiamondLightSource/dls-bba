#!/bin/env dls-python

'''
Various ways of testing BBA:

    - change frequency of corrector oscillations
    - change number of corrector cycles
    - scan whole cell
'''
from __future__ import division
from pkg_resources import require
require('fa-archiver')
require('pml')
import logging as log
import argparse

import pml
import jump_bba
import fa

###############
# Global config
H_AMPS_FILE = 'config/horizontal_bba_mmlvals.txt'
V_AMPS_FILE = 'config/vertical_bba_mmlvals.txt'
# Defaults
CYCLES = 1
FREQUENCY = 8
###############


LOG_FORMAT = '%(levelname)-7s: %(message)s'


# Note that it is possible to use full data here by setting
# jump_bba.DECIMATED = False


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


def load_amps_file(filename, quad_scale=1.0, corr_scale=1.0):
    amps = {}
    with open(filename) as f:
        for line in f:
            bpm_pv, quad_pv, quad_amps, _, corr_pv, corr_amps, _ = line.split()
            amps[pml.prefix_from_pv(quad_pv)] = (
                    quad_scale * float(quad_amps),
                    corr_scale * float(corr_amps))
    return amps


def load_amps(quad_scale=1.0, corr_scale=1.0):
    h_amps = load_amps_file(H_AMPS_FILE, quad_scale, corr_scale)
    v_amps = load_amps_file(V_AMPS_FILE, quad_scale, corr_scale)
    return h_amps, v_amps


def one_bba(quad, plane):
    quad_prefix = pml.prefix_from_element(quad)
    log.warn('BBA on quad {} in plane {}'.format(quad_prefix,
                                                 pml.AXIS_NAMES[plane]))
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[quad_prefix]
    osc = pml.excite.Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
    jump_bba.jump_bba(quad, quad_step, osc)


def frequency_scan(quad, plane):
    log.warn('Beginning test of different corrector oscillation frequencies.')
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    for i in range(1, 8):
        period = fa.TICKS_PER_SECOND // i
        log.info('The calculated period is {}.'.format(period))
        osc = pml.excite.Oscillation(corr_amp, plane, i, CYCLES)
        jump_bba.jump_bba(quad, plane, quad_step, osc)


def cycle_scan(quad, plane):
    log.warn('Beginning test of different numbers of corrector cycles.')
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    for cycles in range(1, 5):
        log.info('Trying {} cycles.'.format(cycles))
        osc = pml.excite.Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
        jump_bba.jump_bba(quad, plane, quad_step, osc)


def repeatability_scan(quad, plane, counts):
    log.warn('Beginning test of different numbers of corrector cycles.')
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    log.info('Quad_step %s, corr_amp %s', quad_step, corr_amp)
    for count in counts:  # Just run ten times at 8 Hz
        log.info('Trying scan {} of {}.'.format(count, counts))
        osc = pml.excite.Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
        jump_bba.jump_bba(quad, quad_step, osc)


def compare_decimated_data(quad, plane):
    log.warn('Beginning test between raw and decimated data.')
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]

    osc = pml.excite.Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
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
            osc = pml.excite.Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
            jump_bba.jump_bba(quad, plane, quad_step, osc)


def scan_amplitudes(quad, plane, scale_quad=True, scale_corr=True):
    log.warn('Beginning scaling test: quad? {}; corr? {}.'.format(scale_quad,
                                                                  scale_corr))
    amps = load_amps()[plane]
    quad_step, corr_amp = amps[pml.prefix_from_element(quad)]
    osc = pml.excite.Oscillation(corr_amp, plane, FREQUENCY, CYCLES)
    scales = [0.5, 1.0, 2.0, 5.0]
    for s in scales:
        if scale_quad:
            qs = quad_step * s
        if scale_corr:
            ca = corr_amp * s
            osc = pml.excite.Oscillation(ca, plane, FREQUENCY, CYCLES)
        jump_bba.jump_bba(quad, plane, qs, osc)


def parse_args():
    parser = argparse.ArgumentParser(description='Take BBA measurements')
    parser.add_argument(
            '-p', '--plane', dest='plane', action='store',
            default=0, help='Which plane to measure')
    parser.add_argument(
            '-q', '--quad-scale', dest='quad_scale', action='store',
            default=1.0, help='Quadrupole amplitude scaler')
    parser.add_argument(
            '-c', '--corrector-scale', dest='corr_scale', action='store',
            default=1.0, help='Corrector amplitude scaler')
    return parser.parse_args()


if __name__ == '__main__':
    pml.initialise()
    args = parse_args()
    plane = int(args.plane)
    quad_scale = float(args.quad_scale)
    corr_scale = float(args.corr_scale)

    h, v = load_amps(quad_scale, corr_scale)
    pv = 'SR01A-PC-Q1D-01'
    get_new_logger()
    log.warn('Plane: {}, Quad scale: {}, Corr scale: {}\n'.format(
        plane, quad_scale, corr_scale))

    quad = pml.quad_from_pv(pv)
    one_bba(quad, plane)
    #repeatability_scan(quad, plane, range(10))
    #frequency_scan(quad, plane)
    #compare_decimated_data(quad, plane)
    #scan_cell(1)
    #cycle_scan(quad, plane)
