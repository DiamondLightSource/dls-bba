from datetime import datetime

ISO_TIME_FORMAT_STRING: str = "%Y%m%dT%H%M%S"
"""ISO 8601 in the format YYYYMMDDThhmmss. Note. T seperates date and time."""


def get_isotime():
    """"""
    now = datetime.now()
    isotime = now.strftime(ISO_TIME_FORMAT_STRING)
    return isotime
