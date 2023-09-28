"""User Settings modifications."""
from __future__ import annotations

from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async

from telegram.commands.utils import UserSettings

if TYPE_CHECKING:
    from telethon import events

    from sqlitedb.models import User


async def modify_page_size(
    event: events.NewMessage.Event,
    user: User,
    user_settings: dict[str, str],
    new_value: str,
) -> None:
    """Modify the page_size setting for a user.

    Args:
        event (events.NewMessage.Event): The new message event.
        user (User): The user instance to modify the settings for.
        user_settings (dict): The user's settings dictionary.
        new_value (str): The new value for the page_size setting.
    """
    try:
        page_size = int(new_value)
        if page_size < 1:
            raise ValueError

        user_settings[UserSettings.PAGE_SIZE.value] = str(page_size)
        user.settings = user_settings
        await sync_to_async(user.save)()

        await event.reply(f"Page size successfully updated to {page_size}.")
    except ValueError:
        await event.reply(
            "Invalid value for page size. Please provide a positive integer.",
        )
