"""Utility class."""

import secrets
import string
from enum import Enum

from telegram.commands.utils import SupportedCommands


class UserType(Enum):
    """User type."""

    ASSISTANT = "assistant"
    USER = "user"


class DataType(Enum):
    """Data type."""

    MESSAGES = SupportedCommands.RESET_MESSAGES.value
    IMAGES = SupportedCommands.RESET_IMAGES.value
    ALL = SupportedCommands.RESET.value


def generate_random_string(length: int = 10) -> str:
    """Generate a random string of lowercase letters with the given length.

    Args:
        length (int): Length of the desired random string.

    Returns
    -------
        str: Random string of lowercase letters with the given length.
    """
    # Create a string of all lowercase letters
    letters = string.ascii_lowercase

    # Use a loop to randomly select characters from the string to build the result string
    return "".join(secrets.choice(letters) for _ in range(length))

    # Return the result string
