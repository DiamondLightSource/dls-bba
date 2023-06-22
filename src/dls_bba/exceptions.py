class BBAComponentException(Exception):
    """Raised when an invalid PV is given."""

    pass


class BeamPositionMonitorCAException(Exception):
    """Raised when a CA error occurs upon connecting to a BPM."""

    pass


class CheckBeamCurrentException(Exception):
    """Raised when check_beam_current is used incorrectly."""

    pass


class DisabledBPMException(Exception):
    """Raised when a disabled BPM is selected."""

    pass


class FeedbacksActiveException(Exception):
    """Raised with one or more feedback systems are active unexpectedly."""

    pass


class InvalidConfigException(Exception):
    """Raised when an expected key does not exist in the config file."""

    pass


class InvalidRingmodeException(Exception):
    """Raised when a pytac tries to load an invalid ringmode."""

    pass


class InvalidNameError(Exception):
    """Raised when a non existant element name is used."""

    pass


class LowCurrentError(Exception):
    """Raised when the current drops below the critical threshold."""

    pass
