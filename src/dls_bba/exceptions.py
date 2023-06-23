class ActiveFeedbacksError(Exception):
    """Raised with one or more feedback systems are active unexpectedly."""

    pass


class ChannelAccessError(Exception):
    """Raised when a CA error occurs upon connecting to a BPM."""

    pass


class CheckBeamCurrentError(Exception):
    """Raised when check_beam_current is used incorrectly."""

    pass


class ComponentConstructionError(Exception):
    """Raised when an invalid PV is given."""

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
