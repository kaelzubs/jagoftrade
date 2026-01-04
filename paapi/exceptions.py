class PaapiError(Exception):
    """Base PAAPI error."""

class PaapiAuthError(PaapiError):
    """Authentication/signature error."""

class PaapiRateLimitError(PaapiError):
    """Throttling or quota issues."""

class PaapiRequestError(PaapiError):
    """Network or request formatting issues."""

class PaapiResponseError(PaapiError):
    """Non-2xx response from API."""

class PaapiDataError(PaapiError):
    """Unexpected/missing data format."""