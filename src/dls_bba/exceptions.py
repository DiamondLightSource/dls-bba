class BBAComponentException(Exception):
    """Raised when an invalid PV is given."""

    pass


class InvalidRingmodeException(Exception):
    """Raised when a pytac tries to load an invalid ringmode."""

    pass


class InvalidConfigException(Exception):
    """Raised when an expected key does not exist in the config file."""

    pass


class BeamPositionMonitorCAException(Exception):
    """Raised when a CA error occurs upon connecting to a BPM."""

    pass


class CheckBeamCurrentException(Exception):
    """Raised when check_beam_current is used incorrectly."""

    pass


class LowCurrentError(Exception):
    """Raised when the current drops below the critical threshold."""

    pass


class FeedbacksActiveException(Exception):
    """Raised with one or more feedback systems are active unexpectedly."""

    pass
