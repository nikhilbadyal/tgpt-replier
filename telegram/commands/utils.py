"""Utility functions."""
from telethon import events
from telethon.tl.types import User

# Define a list of supported commands
supported_commands = [
    "start",
    "image",
    "resetmessages",
    "resetimages",
    "reset",
    "new",
]


async def get_user(event: events.NewMessage.Event) -> User:
    """Get the user associated with a message event in Telegram.

    Args:
        event (events.NewMessage.Event): The message event.

    Returns:
        User: The User entity associated with the message event.
    """
    try:
        # Get the user entity from the peer ID of the message event, Uses cache
        user: User = await event.client.get_entity(event.peer_id)
    except ValueError:
        # If the peer ID is invalid, get the sender entity from the message event
        user = await event.get_sender()
    return user


def get_regex() -> str:
    """Generate a regex pattern that matches any message that is not a
    supported command.

    Returns:
        str: A regex pattern as a string.
    """
    # Exclude any message that starts with one of the supported commands using negative lookahead
    pattern = r"^(?!/(%s))[^/].*" % "|".join(supported_commands)
    return pattern
