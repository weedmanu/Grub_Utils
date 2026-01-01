"""Professional exception hierarchy for GRUB Manager."""


class GrubError(Exception):
    """Base exception for all GRUB-related errors.

    All custom exceptions inherit from this base class, allowing
    catch-all handling when needed while maintaining specificity.
    """

    def __init__(self, message: str, details: str = "") -> None:
        """Initialize exception with message and optional details.

        Args:
            message: Human-readable error message
            details: Technical details for debugging

        """
        super().__init__(message)
        self.message = message
        self.details = details


class GrubConfigError(GrubError):
    """Raised when configuration file has errors or cannot be accessed."""


class GrubValidationError(GrubError):
    """Raised when configuration values fail validation."""


class GrubBackupError(GrubError):
    """Raised when backup operations fail."""


class GrubApplyError(GrubError):
    """Raised when applying configuration to system fails."""


class GrubServiceError(GrubError):
    """Raised when service-level operations fail."""


class GrubThemeError(GrubError):
    """Raised when theme operations fail."""


class GrubFileError(GrubError):
    """Raised when file I/O operations fail."""


class GrubParseError(GrubError):
    """Raised when parsing configuration fails."""
