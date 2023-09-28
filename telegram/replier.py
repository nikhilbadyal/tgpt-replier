"""Reply to messages."""

import sys

from loguru import logger
from telethon import TelegramClient
from typing_extensions import Self

from telegram.commands import general, image, new
from telegram.commands.chat import add_chat_handler
from telegram.commands.list import add_list_handlers
from telegram.commands.print import add_print_handlers
from telegram.commands.reset import add_reset_handlers
from telegram.commands.reset_image_message import add_reset_image_message_handlers
from telegram.commands.settings import add_settings_handlers
from telegram.commands.start import add_start_handlers
from telegram.commands.switch import add_switch_handler


class Telegram(object):
    """A class representing a Telegram bot."""

    def __init__(self: Self, session_file: str) -> None:
        """Create a new Telegram object and connect to the Telegram API using the given session file.

        Args:
            session_file (str): The path to the session file to use for connecting to the Telegram API.
        """
        from main import env

        # Create a new TelegramClient instance with the given session file and API credentials
        self.client: TelegramClient = TelegramClient(
            session_file,
            env.int("API_ID"),
            env.str("API_HASH"),
            sequential_updates=True,
        )
        # Connect to the Telegram API using bot authentication
        logger.debug("Trying to connect using bot token")
        self.client.start(bot_token=env.str("BOT_TOKEN"))
        # Check if the connection was successful
        if self.client.is_connected():
            logger.info("Connected to Telegram")
            logger.info("Using bot authentication. Only bot messages are recognized.")
        else:
            logger.info("Unable to connect with Telegram exiting.")
            sys.exit(1)

    def bot_listener(self: Self) -> None:
        """Listen for incoming bot messages and handle them based on the command."""
        # Register event handlers for each command the bot can handle
        add_reset_handlers(self.client)
        add_reset_image_message_handlers(self.client)
        add_start_handlers(self.client)
        add_list_handlers(self.client)
        add_settings_handlers(self.client)
        add_switch_handler(self.client)
        add_chat_handler(self.client)
        add_print_handlers(self.client)
        self.client.add_event_handler(image.handle_image_command)
        self.client.add_event_handler(new.handle_new_command)
        self.client.add_event_handler(general.handle_any_message)

        # Start listening for incoming bot messages
        self.client.run_until_disconnected()

        # Log a message when the bot stops running
        logger.info("Stopped!")
