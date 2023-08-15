from datetime import datetime

ISO_TIME_FORMAT_STRING: str = "%Y%m%dT%H%M%S"
"""ISO 8601 in the format YYYYMMDDThhmmss. Note. T seperates date and time."""


def get_isotime() -> str:
    """Get the current time in ISO 8601 format.

    Returns:
        The current time in ISO 8601 format.
    """
    now = datetime.now()
    isotime = now.strftime(ISO_TIME_FORMAT_STRING)
    return isotime
