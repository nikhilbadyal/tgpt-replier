"""Print command."""

from __future__ import annotations

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import Button, TelegramClient, events

from telegram.commands.strings import conversation_nf
from telegram.commands.utils import PAGE_SIZE, SupportedCommands


def add_print_handlers(client: TelegramClient) -> None:
    """Add the /print command event handlers."""
    client.add_event_handler(handle_print_command)
    client.add_event_handler(print_navigate_pages)


@events.register(events.CallbackQuery(pattern=r"(next|prev)_page:(\d+):(\d+)"))  # type: ignore
async def print_navigate_pages(event: events.callbackquery.CallbackQuery.Event) -> None:
    """Event handler to navigate between pages of conversation messages.

    Args:
        event (CallbackQuery.Event): The callback query event.
    """
    telegram_id = event.query.user_id
    _, conversation_id, page = event.data.decode("utf-8").split(":")
    conversation_id = int(conversation_id)
    page = int(page)

    await event.answer()
    response, buttons = await display_paginated_messages(
        conversation_id,
        telegram_id,
        page,
    )
    await event.edit(response, buttons=buttons, parse_mode="markdown")


async def display_paginated_messages(
    conversation_id: int,
    telegram_id: int,
    page: int,
) -> tuple[str, list[Button] | None]:
    """Display paginated conversation messages for the given conversation_id.

    Args:
        conversation_id (int): The ID of the conversation.
        telegram_id (int): The user's Telegram ID.
        page (int): The current page number.

    Returns
    -------
        Tuple[str, Union[List[Button], None]]: The formatted conversation messages and navigation buttons.
    """
    # Retrieve UserConversations queryset filtered by the given conversation_id
    # Fetch user settings
    from main import db

    user = await sync_to_async(db.get_user)(telegram_id)
    user_settings = user.settings

    page_size = user_settings.get("page_size", PAGE_SIZE)

    result = await sync_to_async(db.get_conversation_messages)(
        conversation_id,
        telegram_id,
        page,
        page_size,
    )

    response = f"Messages from __Conversation {conversation_id}__\n\n"

    for message in result["data"]:
        sender = "**Bot**" if message.from_bot else "**User**"
        response += f"{sender}: {message.message}\n"

    response += f"\nPage {result['current_page']} of {result['total_pages']}"

    buttons: list[Button] = []
    if result["has_previous"]:
        buttons.append(
            Button.inline("Previous", data=f"prev_page:{conversation_id}:{page - 1}"),
        )
    if result["has_next"]:
        buttons.append(
            Button.inline("Next", data=f"next_page:{conversation_id}:{page + 1}"),
        )

    if not buttons:
        buttons = None  # type: ignore

    return response, buttons


@events.register(events.NewMessage(pattern=f"^{SupportedCommands.PRINT.value}\\s*(\\d*)$"))  # type: ignore
async def handle_print_command(event: events.NewMessage.Event) -> None:
    """Handle the /print command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    # Get the conversation ID from the command

    conversation_id = event.pattern_match.group(1)
    if conversation_id:
        conversation_id = int(conversation_id)
        logger.debug(
            f"Received request to print messages from conversation {conversation_id}",
        )
        telegram_id = event.message.sender_id
        page = 1

        response, buttons = await display_paginated_messages(
            conversation_id,
            telegram_id,
            page,
        )

        if response:
            await event.reply(response, buttons=buttons, parse_mode="markdown")
        else:
            await event.respond(conversation_nf)
    else:
        response = (
            "To print messages of a c conversation, use the following command format:\n`/print "
            "<conversation_id>`\n\n"
        )
        response += "**For example**:\n`/print 42`\n\n"
        await event.reply(response)
