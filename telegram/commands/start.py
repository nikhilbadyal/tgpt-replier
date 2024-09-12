"""Handle start command."""

# Import necessary libraries and modules
from loguru import logger
from telethon import TelegramClient, events

# Import some helper functions
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

    Returns
    -------
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

    prefix_len = len(prefix)
    result = reply[prefix_len:]
    await event.respond(result)
