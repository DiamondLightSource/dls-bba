
import dls_packages

import sys
import time
import struct
import numpy
import matplotlib.pyplot as pp
from cothread.catools import *
import cothread

def get_stop_flag():
    nan_string = struct.pack('HHHH', 65535, 65535, 65535, 65535)
    psc_nan = struct.unpack('d', nan_string)
    return psc_nan[0]


def get_stop_flag2():
    flag_file = "/dls_sw/work/common/matlab/mml/machine/diamond/stopflag"
    with open(flag_file) as f:
        stop_flag = f.read()
    print stop_flag
    stop_flag = struct.unpack('d', stop_flag)
    return stop_flag[0]

def get_sine_wave(length):
    a = numpy.arange(length)
    s = numpy.sin(2 * numpy.pi * a / length)
    return s


def print_nan(double):
    n = struct.pack('d', double)
    print [hex(ord(x)) for x in n]

IOC = "SR25A-PC-TEST-03"

DLLEN = "%s:SETDLLEN" % IOC
DLDEST = "%s:SETDLDEST" % IOC

ULLEN = "%s:SETULLEN" % IOC
ULDEST = "%s:SETULDEST" % IOC
STARTUL = "%s:STARTUL" % IOC
STARTDL = "%s:STARTDL" % IOC
DLSTATE = "%s:DLSTATE" % IOC

CONTROL = ['%s:DATA%s.PROC' % (IOC, i) for i in range(8)]
SETDATA = ['%s:SETDATA%s' % (IOC, i) for i in range(8)]


def set_up(bank=14):
    caput(DLDEST, bank)
    caput(ULDEST, bank)
    caput(STARTUL, 1)

    caput(CONTROL, 1)
    cothread.Sleep(2)


def plot(data):
    pp.plot(data)
    pp.show()


def download():
    length = caget(DLLEN)
    print("Length is %s" % length)
    bank = caget(DLDEST)
    print("Bank is %s" % bank)


    data = []
    pvs = ['%s:DATA%s' % (IOC, i) for i in range(8)]

    for pv in pvs:
        data.extend(caget(pv))

    print(data[1490:1510])

    for i, item in enumerate(data):
        if numpy.isnan(item):
            n = item
            print_nan(item)
            print "NAN! at ", i
            break

    plot(data)
    return n

def upload(pscnan):
    caput(DLLEN, 2000)

    print 'waiting to start upload'
    cothread.Sleep(2)
    s = get_sine_wave(1500)
    data = numpy.concatenate((s, numpy.zeros(500)))
    data[1500] = pscnan
    data[1501] = pscnan
    print get_stop_flag()
    print_nan(struct.pack('f', get_stop_flag2()))
    assert len(data) == 2000
    print(data[1490:1510])
    caput(SETDATA[0], s)
    caput(STARTDL, 1)
    while True:
        state = caget(DLSTATE)
        print "Waiting for download to complete.", state
        if state == 0:
            break
        cothread.Sleep(1)


if sys.argv[1] == 'u':
    set_up(14)
    n = download()
    set_up(13)
    upload(n)
else:
    set_up(14)
    download()
print "Done"

