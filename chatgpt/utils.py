"""Utility class."""
import random
import string
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


def generate_random_string(length: int = 10) -> str:
    """Generate a random string of lowercase letters with the given length.

    Args:
        length (int): Length of the desired random string.

    Returns:
        str: Random string of lowercase letters with the given length.
    """
    # Create a string of all lowercase letters
    letters = string.ascii_lowercase

    # Use a loop to randomly select characters from the string to build the result string
    result_str = "".join(random.choice(letters) for _ in range(length))

    # Return the result string
    return result_str
