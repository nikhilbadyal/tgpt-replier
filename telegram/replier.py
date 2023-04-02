"""Reply to messages."""
import io
from typing import IO, Union

import requests
from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.types import User

from chatgpt.chatgpt import ChatGPT


class Telegram(object):
    """Represent Telegram Object."""

    def __init__(self, session_file: str):
        """Build Telegram Connection."""
        from main import env

        self.client: TelegramClient = TelegramClient(
            session_file,
            env.int("API_ID"),
            env.str("API_HASH"),
            sequential_updates=True,
        )
        logger.info("Auto-replying...")
        if env.str("BOT_TOKEN", None):
            logger.debug("Trying to connect using bot token")
            self.client.start(bot_token=env.str("BOT_TOKEN"))
        else:
            logger.debug("Trying to connect using phone & 2FA")
            self.client.start(env.int("PHONE"), env.str("TWOFA_PASSWORD"))
        if self.client.is_connected():
            logger.info("Connected to Telegram")
        else:
            logger.info("Unable to connect with Telegram exiting.")
            exit(1)

    async def send_file(self, file: Union[bytes, IO[bytes]], caption: str) -> None:
        """Sends a file to the 'me' chat in Telegram with the specified
        caption.

        :param file: The file to send.
        :param caption: The caption for the file.
        """

        file_handle = io.BytesIO(file) if isinstance(file, bytes) else file
        await self.client.send_file("me", file_handle, caption=caption)

    async def send_image_from_url(self, user: User, url: str, caption: str) -> None:
        """Downloads an image from a URL and sends it to the user in Telegram
        with the specified caption.

        :param user:
        :type user: User Entity
        :param url: The URL of the image to download.
        :param caption: The caption for the image.
        """

        response = requests.get(url)
        file_bytes = response.content
        await self.client.send_file(entity=user, file=file_bytes, caption=caption)

    def listen(self, gpt: ChatGPT) -> None:
        """Listen for messages."""

        @self.client.on(events.NewMessage(incoming=True))  # type: ignore
        async def handle_new_message(event: events.NewMessage.Event) -> None:
            """Handle Incoming Message."""
            logger.debug("Received new event {}".format(event))
            if event.is_private:  # only auto-reply to private chats
                try:
                    user: User = await event.client.get_entity(event.peer_id)
                except ValueError:
                    user = await event.get_sender()
                if user and not user.bot:
                    image_prefix = "/image"
                    if image_prefix in event.message.text:
                        result = event.message.text[len(image_prefix) :]
                        await self.send_image_from_url(
                            user, gpt.image_gen(result), result
                        )
                    elif event.message.text:
                        await event.respond(gpt.chat(user, event.message.text))
                    else:
                        await event.respond("Only messages supported.")

                else:
                    logger.error("Cannot get Entity or a bot")
            else:
                logger.info("Not a private message")

        self.client.run_until_disconnected()
        logger.info("Stopped!")
