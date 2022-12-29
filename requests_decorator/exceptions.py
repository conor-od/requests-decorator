from requests import RequestException


class ArgumentError(RequestException):
    """An argument was invalid."""


class SerialisationException(RequestException):
    """Failed to serialise content"""

