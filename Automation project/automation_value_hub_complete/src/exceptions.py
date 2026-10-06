class AutomationHubError(Exception):
    """Base exception raised by the Automation Value Hub pipeline."""


class DataLoadError(AutomationHubError):
    """Raised when an input file cannot be loaded or mapped."""


class BlockingDataQualityError(AutomationHubError):
    """Raised when blocking data-quality issues prevent publication."""
