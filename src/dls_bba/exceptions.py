class ActiveFeedbacksError(Exception):
    """Raised when any feedback system is active. Disable to continue."""

    pass


class ChannelAccessError(Exception):
    """Raised when a Channel Access error occurs."""

    pass


class ComponentConstructionError(Exception):
    """Raised when an invalid element name is given for component construction."""

    pass


class ElementDisabledError(Exception):
    """Raised when a disabled element is selected."""

    pass


class FastAcquisitionArchiverError(Exception):
    """Raised when unexpected data shape is recieved from FA Arhciver."""

    pass


class FAAPowerSupplyIOCTimestampError(Exception):
    """Raised when a timestamp that would be rejected by the power supply IOC is selected."""

    pass


class FastOrbitFeedbackError(Exception):
    """Raised when the orbit size is larger than FOFB can handle."""

    pass


class InvalidElementError(Exception):
    """Raised when a non existant element name is used."""

    pass


class InvalidRingmodeError(Exception):
    """Raised when a pytac tries to load an invalid ringmode."""

    pass


class OscillationLengthError(Exception):
    """Raised when the oscillations are not equal in length."""


class LowCurrentError(Exception):
    """Raised when the current drops below the critical threshold."""

    pass
