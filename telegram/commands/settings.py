"""Settings command."""

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import Button, TelegramClient, events

from telegram.commands.user_settings import modify_page_size
from telegram.commands.utils import SupportedCommands, UserSettings


def add_settings_handlers(client: TelegramClient) -> None:
    """Add /settings command Event Handler."""
    client.add_event_handler(handle_settings_command)
    client.add_event_handler(handle_settings_list_settings)
    client.add_event_handler(handle_settings_current_settings)


@events.register(events.CallbackQuery(pattern="list_settings"))  # type: ignore
async def handle_settings_list_settings(
    event: events.callbackquery.CallbackQuery.Event,
) -> None:
    """Event handler for listing available settings.

    Args:
        event (CallbackQuery.Event): The callback query event.
    """
    await event.answer()

    response = "**Available settings**:\n\n"
    for setting in UserSettings:
        response += f"- `{setting.name}`: {setting.description}\n"

    await event.edit(response, parse_mode="markdown")


@events.register(events.CallbackQuery(pattern="current_settings"))  # type: ignore
async def handle_settings_current_settings(
    event: events.callbackquery.CallbackQuery.Event,
) -> None:
    """Event handler for listing current settings.

    Args:
        event (CallbackQuery.Event): The callback query event.
    """
    await event.answer()
    from main import db  # noqa: PLC0415

    response = "**Current settings**:\n\n"
    telegram_id = event.query.user_id
    user = await sync_to_async(db.get_user)(telegram_id)
    settings = user.settings
    for setting in settings:
        setting_enum = UserSettings(setting)
        description = setting_enum.description
        response += f"- `{setting_enum} {settings[setting]}`: __{description}__\n"

    await event.edit(response, parse_mode="markdown")


@events.register(events.NewMessage(pattern=f"^{SupportedCommands.SETTINGS.value}"))  # type: ignore
async def handle_settings_command(event: events.NewMessage.Event) -> None:
    """Event handler for the /settings command.

    Args:
        event (NewMessage.Event): The new message event.
    """
    from main import db  # noqa: PLC0415

    # Extract the setting name and new value from the input message
    parts = event.message.text.split()
    if len(parts) < 3:
        response = "To update a setting, use the following command format:\n``/settings <setting_name> <value>`\n\n"
        response += "**For example**:\n`/settings page_size 5`\n\n"
        response += "Click the **List Settings** button below to see available settings."

        buttons = [
            Button.inline("List Settings", data="list_settings"),
            Button.inline("Current Settings", data="current_settings"),
        ]

        await event.reply(response, buttons=buttons, parse_mode="markdown")
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
        setting_name.lower(),
    )
    if setting_modification_function:
        await setting_modification_function(event, user, user_settings, new_value)
    else:
        await event.reply(
            f"Invalid setting name `{setting_name}`. Please provide a valid setting name.",
            parse_mode="markdown",
        )
