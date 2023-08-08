import logging as log
from typing import List

import cothread
import numpy as np
from fa.falib import falib

from dls_bba.exceptions import (
    FAAPowerSupplyIOCTimestampError,
    FastAcquisitionArchiverError,
)

TICKS_PER_SECOND = 10072
"""Number of FA ticks per second."""
TICKS_PER_HOUR = TICKS_PER_SECOND * 60 * 60
"""Number of FA ticks per hour."""
IOC_REJECTION_TIMESTAMP = 2**32 - TICKS_PER_HOUR
"""Timestamp after which the corrector power supply will reject the oscillation."""
IOC_WARNING_TIMESTAMP = 2**32 - 3 * TICKS_PER_HOUR
"""Timestamp after which warnings will be displayed."""
MAX_BBA_DURATION = 6 * TICKS_PER_HOUR
"""Maximum duration of a full BBA run in ticks."""


def get_timestamp(decimated: bool) -> int:
    """Get the FAA timestamp.

    Note: If the timestamp is larger than 2**32 - 1 hour,
    then the power supply IOC will reject the oscillation.

    Args:
        decimated: Whether the data is decimated.

    Returns:
        The timestamp.

    Raises:
        FAAPowerSupplyIOCTimestampError: If the timestamp is too large.
    """
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
    """Buffer for FA data.

    Args:
        SIZE: Number of datapoints to read at once.
        EXTRA: Timestamps of extra data to ensure desired data is fetched.
    """

    SIZE = 1000
    EXTRA = 1000

    def __init__(
        self, ids: List[int], start_time: int, length: int, decimated: bool
    ) -> None:
        """Create buffer.

        Note that length is in FA archiver timestamps, even if the data
        is decimated, so if decimated is true the dimension of the data
        will be 1/10 the value of length.

        Args:
            ids: List of BPM IDs to fetch data for.
            start_time: Timestamp of start of data.
            length: Length of data in FA archiver timestamps.
            decimated: Whether the data is decimated.
        """
        self.length = length
        self.start = start_time
        # We need the timestamps for selecting the correct data
        if not ids[0] == 0:
            ids = [0] + List(ids)
            self.timestamps = False
        else:
            self.timestamps = True
        self.ids = ids
        self.cache: List[np.ndarray] = []
        self.datapoints = int(length // 10) if decimated else length
        log.debug("FA buffer: length %s; datapoints %s", length, self.datapoints)
        self.dec = decimated
        self.server = falib.Server()
        self.complete = False
        cothread.Spawn(self._fetch_data)

    def _fetch_data(self) -> None:
        """Fetch the data from the FA archiver.

        Keep fetching data until the desired data is fetched.
        """
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

    def get_data(self) -> np.ndarray:
        """Get the data from the buffer.

        Returns:
            The data.
        """
        while not self.complete:
            cothread.Sleep(0.1)
        try:
            data = np.concatenate(self.cache)
            data_start = int(np.searchsorted(data[:, 0, 0], self.start))
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
