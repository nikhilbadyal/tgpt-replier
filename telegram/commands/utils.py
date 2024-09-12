"""Utility functions."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from typing import Self

    from telethon import events
    from telethon.tl.types import User

PAGE_SIZE = 10  # Number of conversations per page


# Define a list of supported commands
class SupportedCommands(Enum):
    """Enum for supported commands."""

    START: str = "/start"
    IMAGE: str = "/image"
    RESET_MESSAGES: str = "/resetmessages"
    RESET_IMAGES: str = "/resetimages"
    RESET: str = "/reset"
    NEW: str = "/new"
    LIST: str = "/list"
    SETTINGS: str = "/settings"
    SWITCH: str = "/switch"
    CHAT: str = "/chat"
    PRINT: str = "/print"

    @classmethod
    def get_values(cls) -> list[str]:
        """Returns a list of all the values of the SupportedCommands enum.

        Returns
        -------
            list: A list of all the values of the SupportedCommands enum.
        """
        return [command.value for command in cls]

    def __str__(self: Self) -> str:
        """Returns the string representation of the enum value.

        Returns
        -------
            str: The string representation of the enum value.
        """
        return str(self.value)


async def get_user(event: events.NewMessage.Event) -> User:
    """Get the user associated with a message event in Telegram.

    Args:
        event (events.NewMessage.Event): The message event.

    Returns
    -------
        User: The User entity associated with the message event.
    """
    try:
        # Get the user entity from the peer ID of the message event, Uses cache
        user: User = await event.client.get_entity(event.peer_id)
    except (ValueError, AttributeError):
        logger.debug("Invalid Peer ID")
        user = await event.get_sender()
    return user


def get_regex() -> str:
    """Generate a regex pattern that matches any message that is not a supported command.

    Returns
    -------
        str: A regex pattern as a string.
    """
    # Exclude any message that starts with one of the supported commands using negative lookahead
    return r"^(?!({}))[^/].*".format("|".join(SupportedCommands.get_values()))


class UserSettings(Enum):
    """User Settings."""

    PAGE_SIZE = "page_size", "The number of conversations displayed per page."

    def __new__(cls, *args: Any, **kwargs: Any) -> UserSettings:  # noqa: ARG003
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    # ignore the first param since it's already set by __new__
    def __init__(self: Self, _: str, description: str | None = None) -> None:
        self._description_ = description

    def __str__(self: Self) -> str:
        """String representation."""
        return str(self.value)

    @property
    def description(self: Self) -> str | None:
        """Returns the description of the setting.

        Returns
        -------
            Optional[str]: The description of the setting.
        """
        return self._description_
