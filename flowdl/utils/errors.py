class FlowDLError(Exception):
    """Base exception for FlowDL."""


class PresetNotFoundError(FlowDLError):
    """Raised when requested preset is missing."""


class InvalidURLError(FlowDLError):
    """Raised when URL is clearly malformed."""


class DependencyMissingError(FlowDLError):
    """Raised when a required external dependency is missing."""

