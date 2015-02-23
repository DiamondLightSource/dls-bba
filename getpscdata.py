

import dls_packages

import numpy
import matplotlib.pyplot as pp
from cothread.catools import *
import cothread

IOC = "SR25A-PC-TEST-03"

DLLEN = "%s:SETDLLEN" % IOC
DLDEST = "%s:SETDLDEST" % IOC

ULLEN = "%s:SETULLEN" % IOC
ULDEST = "%s:SETULDEST" % IOC
STARTUL = "%s:STARTUL" % IOC

CONTROL = ['%s:DATA%s.PROC' % (IOC, i) for i in range(8)]

bank = 14
caput(DLDEST, bank)
caput(ULDEST, bank)
caput(STARTUL, 1)

caput(CONTROL, 1)
cothread.Sleep(2)


length = caget(DLLEN)
print("Length is %s" % length)
bank = caget(DLDEST)
print("Bank is %s" % bank)


data = []
pvs = ['%s:DATA%s' % (IOC, i) for i in range(8)]

for pv in pvs:
    data.extend(caget(pv))

print(data[1240:1260])

for i, item in enumerate(data):
    if numpy.isnan(item):
        print "NAN! at ", i
        break



pp.plot(data)
pp.show()


