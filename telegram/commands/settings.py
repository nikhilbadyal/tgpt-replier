"""Settings command."""

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import TelegramClient, events

from telegram.commands.user_settings import modify_page_size
from telegram.commands.utils import SupportedCommands, UserSettings


def add_settings_handlers(client: TelegramClient) -> None:
    """Add /settings command Event Handler."""
    client.add_event_handler(handle_settings_command)


# Register the function to handle the /list command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.SETTINGS.value}"))  # type: ignore
async def handle_settings_command(event: events.NewMessage.Event) -> None:
    """Event handler for the /settings command.

    Args:
        event (NewMessage.Event): The new message event.
    """
    from main import db

    # Extract the setting name and new value from the input message
    parts = event.message.text.split()
    if len(parts) < 3:
        await event.reply(
            "Please provide the setting name and the new value, e.g., '/settings page_size 15'"
        )
        return

    setting_name = parts[1]
    new_value = parts[2]
    logger.debug(f"Received request to modify {setting_name} settings to {new_value}")

    telegram_id = event.message.sender_id
    user = await sync_to_async(db.get_user)(telegram_id)
    user_settings = user.settings

    settings_modification_functions = {
        UserSettings.PAGE_SIZE.value: modify_page_size,
    }

    setting_modification_function = settings_modification_functions.get(
        setting_name.lower()
    )
    if setting_modification_function:
        await setting_modification_function(event, user, user_settings, new_value)
    else:
        await event.reply(
            f"Invalid setting name `{setting_name}`. Please provide a valid setting name.",
            parse_mode="markdown",
        )
