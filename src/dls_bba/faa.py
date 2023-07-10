import logging as log

import cothread
import numpy
from fa.falib import falib

from dls_bba.exceptions import (
    FAAPowerSupplyIOCTimestampError,
    FastAcquisitionArchiverError,
)

TICKS_PER_SECOND = 10072
TICKS_PER_HOUR = TICKS_PER_SECOND * 60 * 60
IOC_REJECTION_TIMESTAMP = 2**32 - TICKS_PER_HOUR
IOC_WARNING_TIMESTAMP = 2**32 - 3 * TICKS_PER_HOUR
MAX_BBA_DURATION = 6 * TICKS_PER_HOUR


def get_timestamp(decimated):
    """Get the current FAA timestamp in ticks.
    Note: If faa timestamp is larger than 2**32 - 1 hour,
    then the power supply IOC will reject the oscillation.
    Args:
        decimated: A boolean to describe if decimated data is wanted.
    Returns:
        The FAA timestamp.
    """
    # TODO: If faa timestamp is larger than 2**32 - 1 hour,
    # then the power supply IOC will reject the oscillation.
    s = falib.subscription([0], decimated=decimated)
    x = s.read(1)
    s.close()
    timestamp = int(x[0][0][0])

    if timestamp + MAX_BBA_DURATION > IOC_REJECTION_TIMESTAMP:
        msg = "FAA timestamp is too large. Please Resync BPMs."
        log.critical(msg)
        raise FAAPowerSupplyIOCTimestampError(msg)

    elif timestamp + MAX_BBA_DURATION > IOC_WARNING_TIMESTAMP:
        msg = "FAA timestamp approaching IOC limit. Please Resync BPMs."
        log.warning(msg)

    return timestamp


class Buffer(object):
    """The buffer class allows extraction of the data from the FA archiver."""

    SIZE = 1000
    """The number of datapoints to read at once."""
    EXTRA = 1000
    """The number of extra datapoints to ensure desired data is fetched."""

    def __init__(self, ids, start_time, length, decimated):
        """Create buffer.

        Note that length is in FA archiver timestamps, even if the data
        is decimated, so if decimated is true the dimension of the data
        will be 1/10 the value of length.

        Args:
            ids: The BPM id list.
            start_time: The starting FAA tick of the oscillation.
            length: The length of the oscillations.
            decimated: A boolean for if the data is decimated,
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
        """This function returns the FAA data.
        Raises:
            FastAcquisitionArchiverError: If insufficient data is gathered.
        Returns:
            The data.
        """
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
            raise FastAcquisitionArchiverError(
                "Insufficient data received from FA archiver."
            )
        return data
