from __future__ import division
import numpy
import cothread
from falib import falib


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
        sub = self.server.subscription(self.ids, decimated=self.dec)
        while count < self.datapoints:
            self.cache.append(sub.read(Buffer.SIZE))
            count += Buffer.SIZE
        self.complete = True
        sub.close()

    def get_data(self):
        while not self.complete:
            cothread.Sleep(0.1)
        data = numpy.concatenate(self.cache)
        data = data[:self.datapoints,:,:]
        return data
