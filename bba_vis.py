
from pkg_resources import require
require('cothread')
require('numpy')

from cothread.catools import *
import numpy

BBA_FILE = '/home/ops/burt/requestFiles/BBA.req'
GOLDEN_FILE = '/home/ops/burt/requestFiles/goldenorbit.req'

def get_pvs(filename):

    pvs = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line.startswith('%') and not line == '':
                pvs.append(line.strip())
    return pvs

def summarise(offsets):
    print('Max offset: %s' % max(offsets))
    print('Min offset: %s' % min(offsets))
    print('Mean offset: %s' % numpy.mean(offsets))
    print('Std dev offset: %s' % numpy.std(offsets))

bba_pvs = get_pvs(BBA_FILE)

dim = caget(bba_pvs[0] + '.EGU')
print('The dimension of each PV is %s' % dim)

bba_offsets = caget(bba_pvs)
summarise(bba_offsets)

golden_pvs = get_pvs(GOLDEN_FILE)
golden_offsets = caget(golden_pvs)
summarise(golden_offsets)

print('Summarising golden offsets:')
for pv, offset in zip(golden_pvs, golden_offsets):
    if offset != 0:
        print('Non-zero offset: %s %s' %(pv, offset))

