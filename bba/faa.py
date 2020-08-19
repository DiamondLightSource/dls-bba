from __future__ import division
import logging as log
import numpy
import cothread
from fa.falib import falib


TICKS_PER_SECOND = 10072


def get_timestamp():
    s = falib.subscription([0], decimated=False)
    x = s.read(1)
    s.close()
    return x[0][0][0]


class FaException(Exception):
    pass


class Buffer(object):
    # Number of datapoints to read at once.
    SIZE = 1000
    # Timestamps of extra data to ensure desired data is fetched.
    EXTRA = 1000

    def __init__(self, ids, start_time, length, decimated):
        """
        Note that length is in FA archiver timestamps, even if the data
        is decimated, so if decimated is true the dimension of the data
        will be 1/10 the value of length.
        """
        self.length = length
        self.start = start_time
        # We need the timestamps for selecting the correct data
        if not ids[0] == 0:
            ids = [0] + list(ids)
            self.timestamps = False
        else:
            self.timestamps = True
        self.ids = ids
        self.cache = []
        self.datapoints = int(length // 10) if decimated else length
        log.debug("FA buffer: length %s; datapoints %s", length, self.datapoints)
        self.dec = decimated
        self.server = falib.Server()
        self.complete = False
        cothread.Spawn(self._fetch_data)

    def _fetch_data(self):
        try:
            sub = self.server.subscription(self.ids, decimated=self.dec)
            self.cache.append(sub.read(Buffer.SIZE))
            while self.cache[-1][-1, 0, 0] < (self.start + self.length + Buffer.EXTRA):
                self.cache.append(sub.read(Buffer.SIZE))
            self.complete = True
            sub.close()
        except Exception as e:  # The EOF exception is hidden from me.
            log.warn("Fetching FA data failed: {}".format(e))
            self.complete = True

    def get_data(self):
        while not self.complete:
            cothread.Sleep(0.1)
        try:
            data = numpy.concatenate(self.cache)
            data_start = numpy.searchsorted(data[:, 0, 0], self.start)
            log.debug("Raw data size: {}".format(data.shape))
            data = data[data_start : data_start + self.datapoints, :, :]
            log.debug("Data timestamps: {}".format(data[:, 0, 0]))
            log.debug("Final data size: {}".format(data.shape))
            if not self.timestamps:
                data = data[:, 1:, :]
        except IndexError:
            raise FaException("Insufficient data received from FA archiver.")
        return data
