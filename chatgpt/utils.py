"""Utility class."""
from enum import Enum


class UserType(Enum):
    """User type."""

    ASSISTANT = "assistant"
    USER = "user"


class DataType(Enum):
    """Data type."""

    MESSAGES = "/resetmessages"
    IMAGES = "/resetimages"
    ALL = "/reset"
