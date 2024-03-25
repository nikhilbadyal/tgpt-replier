"""List User Conversation."""

from __future__ import annotations

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import Button, TelegramClient, events

from telegram.commands.utils import PAGE_SIZE, SupportedCommands


def add_list_handlers(client: TelegramClient) -> None:
    """Add /list command Event Handler."""
    client.add_event_handler(handle_list_command)
    client.add_event_handler(navigate_pages)


@events.register(events.CallbackQuery(pattern=r"(next|prev)_page:(\d+)"))  # type: ignore
async def navigate_pages(event: events.callbackquery.CallbackQuery.Event) -> None:
    """Event handler to navigate between pages of conversations.

    Args:
        event (CallbackQuery.Event): The callback query event.
    """
    telegram_id = event.query.user_id
    _, page = event.data.decode("utf-8").split(":")
    page = int(page)

    await event.answer()
    response, buttons = await send_paginated_conversations(telegram_id, page)
    await event.edit(response, buttons=buttons, parse_mode="markdown")


async def send_paginated_conversations(
    telegram_id: int,
    page: int,
) -> tuple[str, list[Button] | None]:
    """Fetch and send paginated conversations for the given user.

    Args:
        telegram_id (int): The Telegram ID of the user.
        page (int): The current page number.

    Returns
    -------
        Tuple[str, List]: A tuple containing the response message and the list of buttons.
    """
    from main import db

    # Fetch user settings
    user = await sync_to_async(db.get_user)(telegram_id)
    user_settings = user.settings

    page_size = user_settings.get("page_size", PAGE_SIZE)

    result = await sync_to_async(db.get_user_conversations)(
        telegram_id,
        page,
        page_size,
    )

    response = "**Conversations:**\n"
    for conversation in result["data"]:
        response += f"- `{conversation.title}` (ID: {conversation.id})\n"

    response += f"\nPage {result['current_page']} of {result['total_pages']}"

    buttons: list[Button] = []
    if result["has_previous"]:
        buttons.append(Button.inline("Previous", data=f"prev_page:{page - 1}"))
    if result["has_next"]:
        buttons.append(Button.inline("Next", data=f"next_page:{page + 1}"))

    if not buttons:
        buttons = None  # type: ignore

    return response, buttons


# Register the function to handle the /list command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.LIST.value}$"))  # type: ignore
async def handle_list_command(event: events.NewMessage.Event) -> None:
    """Event handler for the /list command.

    Args:
        event (NewMessage.Event): The new message event.
    """
    # Log that a request has been received to delete all user data
    logger.debug("Received request to list all conversations")

    telegram_id = event.message.sender_id
    page = 1
    response, buttons = await send_paginated_conversations(telegram_id, page)
    await event.reply(response, buttons=buttons, parse_mode="markdown")
