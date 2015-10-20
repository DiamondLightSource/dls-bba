#!/usr/bin/env dls-python

import pkg_resources
pkg_resources.require('scipy')
pkg_resources.require('numpy')
import simple_analysis
import analysis
import scipy.io
import numpy
import os
import sys
import glob


try:
    datadir = sys.argv[1]
except IndexError:
    print('Usage: {} <datadir>'.format(sys.argv[0]))
    sys.exit()


files = glob.glob(os.path.join(datadir, '*.mat'))

print('Analysing {}: {} files.'.format(datadir, len(files)))

for module in (simple_analysis, analysis):
    print('Analysing with {}'.format(module.__name__))
    results = []
    for f in files:
        data = scipy.io.loadmat(f, squeeze_me=True)
        results.append(module.analyse(data))

    a = numpy.array(results)

    print a.mean()
    print a.std()
    print('')

