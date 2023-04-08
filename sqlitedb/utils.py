"""Utility class."""
from enum import Enum


class ErrorCodes(Enum):
    """List of error codes."""

    success = 0
    exceptions = -1


class UserStatus(Enum):
    """User Status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TEMP_BANNED = "temporarily banned"
