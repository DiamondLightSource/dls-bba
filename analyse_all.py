#!/usr/bin/env dls-python

import pkg_resources
pkg_resources.require('scipy')
pkg_resources.require('numpy')
import simple_analysis
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

print('Analysing {} files.'.format(len(files)))

results = []
for f in files:
    data = scipy.io.loadmat(f, squeeze_me=True)
    results.append(simple_analysis.analyse(data))

a = numpy.array(results)

print a[:,0].mean()
print a[:,0].std()
