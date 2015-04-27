from __future__ import division
import logging as log
import numpy
import cothread
from falib import falib


TICKS_PER_SECOND = 10072


class FaException(Exception):
    pass


class Buffer(object):
    SIZE = 1000

    def __init__(self, ids, length, decimated):
        self.ids = ids
        self.cache = []
        if decimated:
            self.datapoints = int(length // 10)
        else:
            self.datapoints = length
        self.dec = decimated
        self.server = falib.Server()
        self.complete = False
        cothread.Spawn(self._fetch_data)

    def _fetch_data(self):
        count = 0
        try:
            sub = self.server.subscription(self.ids, decimated=self.dec)
            while count < self.datapoints:
                self.cache.append(sub.read(Buffer.SIZE))
                count += Buffer.SIZE
            self.complete = True
            sub.close()
        except Exception as e:  # The EOF exception is hidden from me.
            log.warn('Fetching FA data failed: {}'.format(e))
            self.complete = True

    def get_data(self):
        while not self.complete:
            cothread.Sleep(0.1)
        try:
            data = numpy.concatenate(self.cache)
            data = data[:self.datapoints,:,:]
        except IndexError:
            raise FaException('Insufficient data received from FA archiver.')
        return data
