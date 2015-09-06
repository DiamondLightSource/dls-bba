#!/usr/bin/env dls-python

import analysis
import scipy.io
import numpy
import os

DATADIR = 'data'

files = os.listdir(DATADIR)

results = []
for f in files:
    if f.endswith('mat'):
        f = os.path.join(DATADIR, f)
        data = scipy.io.loadmat(f, squeeze_me=True)
        results.append(analysis.analyse(data, False))

a = numpy.array(results)

print a[:,0].mean()
print a[:,0].std()
