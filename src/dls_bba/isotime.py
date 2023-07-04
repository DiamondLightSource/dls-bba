from datetime import datetime

ISO_TIME_FORMAT_STRING: str = "%Y%m%dT%H%M%S"
"""ISO 8601 in the format YYYYMMDDThhmmss. Note. T seperates date and time."""


def get_isotime():
    """This function gets the current time and returns in isotime format.

    Returns:
        The datetime in ISO 8601 format.
    """
    now = datetime.now()
    isotime = now.strftime(ISO_TIME_FORMAT_STRING)
    return isotime
