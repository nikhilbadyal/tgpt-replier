"""Handle start command."""
# Import necessary libraries and modules
from loguru import logger
from telethon import TelegramClient, events

from sqlitedb.utils import ErrorCodes

# Import some helper functions
from telegram.commands.strings import something_bad_occurred
from telegram.commands.utils import SupportedCommands


def add_start_handlers(client: TelegramClient) -> None:
    """Add /start command Event Handler."""
    client.add_event_handler(handle_start_message)


# Register the function to handle the /start command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.START.value}$"))  # type: ignore
async def handle_start_message(event: events.NewMessage.Event) -> None:
    """Handle /start command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Define a prefix for the pun
    prefix = "🫡"

    # Define a message to ask the user for a pun
    start_message = f"""
        Give a funny pun. Add {prefix} before starting the pun. Dont add anything else to
        result. Just {prefix} and pun
    """

    # Log that a pun request has been received
    logger.debug("Received pun request")

    # Import the main function for generating responses
    from main import gpt

    # Generate a response based on the start message
    reply = gpt.reply_start(start_message)

    # If the response is an integer, send a cleanup message instead
    if isinstance(reply, ErrorCodes):
        await event.respond(something_bad_occurred)
    # Otherwise, extract the pun from the response and send it back to the user
    else:
        result = reply[len(prefix) :]
        await event.respond(result)
