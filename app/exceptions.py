class AppError(Exception):
    """Base class for all domain exceptions. Supports error accumulation."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def capture(self, message: str) -> None:
        """Accumulate an error message."""
        self.messages.append(message)

    def raise_if_any(self) -> None:
        """Raise self if any errors have been captured."""
        if self.messages:
            raise self


class NotFoundError(AppError):
    """Raised when one or more requested resources do not exist."""

    def capture(self, resource: str) -> None:
        self.messages.append(f"{resource} not found")


class DomainValidationError(AppError):
    """Raised when business rules are violated. Used by validate_input and validate steps."""


class ConflictError(AppError):
    """Raised when an operation conflicts with existing state."""