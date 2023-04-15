"""Utility class."""
from enum import Enum

test_message = "Test message"
test_conversation = "Test Conversation"
test_title = "Test Title"


class ErrorCodes(Enum):
    """List of error codes."""

    success = 0
    exceptions = -1


class UserStatus(Enum):
    """User Status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TEMP_BANNED = "temporarily banned"
