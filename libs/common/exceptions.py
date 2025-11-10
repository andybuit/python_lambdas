"""Custom exceptions for the PSN Emulator service."""


class PSNEmulatorException(Exception):
    """Base exception for PSN Emulator service."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        """
        Initialize exception with message and status code.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(PSNEmulatorException):
    """Raised when request validation fails."""

    def __init__(self, message: str) -> None:
        """
        Initialize validation exception.

        Args:
            message: Validation error message
        """
        super().__init__(message, status_code=400)


class AuthenticationException(PSNEmulatorException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        """
        Initialize authentication exception.

        Args:
            message: Authentication error message
        """
        super().__init__(message, status_code=401)


class NotFoundException(PSNEmulatorException):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        """
        Initialize not found exception.

        Args:
            message: Not found error message
        """
        super().__init__(message, status_code=404)


class ConflictException(PSNEmulatorException):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str = "Resource conflict") -> None:
        """
        Initialize conflict exception.

        Args:
            message: Conflict error message
        """
        super().__init__(message, status_code=409)
