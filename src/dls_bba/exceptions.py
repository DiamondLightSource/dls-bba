class ActiveFeedbacksError(Exception):
    """Raised when any feedback system is active. Disable to continue."""

    pass


class ChannelAccessError(Exception):
    """Raised when a Channel Access error occurs."""

    pass


class CheckBeamCurrentError(Exception):
    """Raised when check_beam_current is used incorrectly."""

    pass


class ComponentConstructionError(Exception):
    """Raised when an invalid element name is given for component construction."""

    pass


class FAATimestampError(Exception):
    """Raised when the FAA timestamp is too large to be used."""

    pass


class FeedbacksActiveException(Exception):
    """Raised with one or more feedback systems are active unexpectedly."""

    pass


class ElementDisabledError(Exception):
    """Raised when a disabled element is selected."""

    pass


class InvalidElementError(Exception):
    """Raised when a non existant element name is used."""

    pass


class InvalidRingmodeError(Exception):
    """Raised when a pytac tries to load an invalid ringmode."""

    pass


class LowCurrentError(Exception):
    """Raised when the current drops below the critical threshold."""

    pass
