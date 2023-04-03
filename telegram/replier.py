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
        self.no_input = "Please provide valid input."
        self.cleanup_success = "Gone🧹"
        self.cleanup_failure = "Something bad happened.☠️"
        self.block_list = ["start", "image", "resetmessages", "resetimages", "reset"]
        logger.info("Auto-replying...")
        if env.str("BOT_TOKEN", None):
            bot = True
            logger.debug("Trying to connect using bot token")
            self.client.start(bot_token=env.str("BOT_TOKEN"))
        else:
            bot = False
            logger.debug("Trying to connect using phone & 2FA")
            self.client.start(env.int("PHONE"), env.str("TWOFA_PASSWORD"))
        if self.client.is_connected():
            logger.info("Connected to Telegram")
            if bot:
                logger.info(
                    "Using bot authentication. Only bot messages are recognized."
                )
        else:
            logger.info("Unable to connect with Telegram exiting.")
            exit(1)

    def get_regex(self) -> str:
        """Generate regex."""
        pattern = r"^(?!/(%s))[^/].*" % "|".join(self.block_list)
        return pattern

    async def send_file(self, file: Union[bytes, IO[bytes]], caption: str) -> None:
        """Sends a file to the user.

        :param file: The file to send.
        :param caption: The caption for the file.
        """

        file_handle = io.BytesIO(file) if isinstance(file, bytes) else file
        await self.client.send_file("me", file_handle, caption=caption)

    async def send_image_from_url(self, user: User, url: str, caption: str) -> None:
        """Downloads an image from a URL and sends it to the user in Telegram.

        :param user:
        :type user: User Entity
        :param url: The URL of the image to download.
        :param caption: The caption for the image.
        """

        response = requests.get(url)
        file_bytes = response.content
        await self.client.send_file(entity=user, file=file_bytes, caption=caption)

    async def get_user(self, event: events.NewMessage.Event) -> User:
        """Get the user from Telegram."""
        try:
            user: User = await event.client.get_entity(event.peer_id)
        except ValueError:
            user = await event.get_sender()
        return user

    def private_listen(self, gpt: ChatGPT) -> None:
        """Listen for messages."""

        @self.client.on(events.NewMessage(incoming=True))  # type: ignore
        async def handle_new_message(event: events.NewMessage.Event) -> None:
            """Handle Incoming Message."""
            logger.debug("Received new event {}".format(event))
            if event.is_private:  # only auto-reply to private chats
                user: User = await self.get_user(event)
                if user and not user.bot:
                    image_prefix = "/image"
                    if image_prefix in event.message.text:
                        result = event.message.text[len(image_prefix) :]
                        await self.send_image_from_url(
                            user, gpt.image_gen(user, result), result
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

    def bot_listener(self, gpt: ChatGPT) -> None:
        """Listen for incoming bot messages."""

        @self.client.on(events.NewMessage(pattern="/start"))  # type: ignore
        async def handle_new_message(event: events.NewMessage.Event) -> None:
            """Handle Start Message."""
            prefix = "🫡"
            start_message = f"""
                Give a funny pun. Add {prefix} before starting the pun. Dont add anything else to
                result. Just {prefix} and pun
            """
            reply = gpt.reply_start(start_message)
            result = reply[len(prefix) :]
            await event.respond(result)

        @self.client.on(events.NewMessage(pattern="/image"))  # type: ignore
        async def handle_image_command(event: events.NewMessage.Event) -> None:
            """Handle Start Message."""
            prefix = "/image "
            user: User = await self.get_user(event)
            result = event.message.text[len(prefix) :]
            if result:
                await self.send_image_from_url(
                    user, gpt.image_gen(user, result), result
                )
            else:
                await event.respond(self.no_input)

        @self.client.on(events.NewMessage(pattern="/resetmessages"))  # type: ignore
        async def handle_reset_messages_command(event: events.NewMessage.Event) -> None:
            """Delete all message history for a user."""
            user: User = await self.get_user(event)
            if gpt.clean_up_user_messages(user):
                await event.respond(self.cleanup_success)
            else:
                await event.respond(self.cleanup_failure)

        @self.client.on(events.NewMessage(pattern="/resetimages"))  # type: ignore
        async def handle_reset_images_command(event: events.NewMessage.Event) -> None:
            """Delete all message history for a user."""
            user: User = await self.get_user(event)
            if gpt.clean_up_user_images(user):
                await event.respond(self.cleanup_success)
            else:
                await event.respond(self.cleanup_failure)

        @self.client.on(events.NewMessage(pattern="/reset"))  # type: ignore
        async def handle_reset_command(event: events.NewMessage.Event) -> None:
            """Delete all message history for a user."""
            user: User = await self.get_user(event)
            if gpt.clean_up_user_data(user):
                await event.respond(self.cleanup_success)
            else:
                await event.respond(self.cleanup_failure)

        @self.client.on(events.NewMessage(pattern=self.get_regex()))  # type: ignore
        async def handle_any_message(event: events.NewMessage.Event) -> None:
            """Handle Start Message."""
            if event.is_private:  # only auto-reply to private chats
                user: User = await self.get_user(event)
                if user and not user.bot:
                    if event.message.text:
                        await event.respond(gpt.chat(user, event.message.text))
                    else:
                        await event.respond(self.cleanup_failure)
                else:
                    logger.error("Cannot get Entity or a bot")
            else:
                logger.info("Not a private message")

        self.client.run_until_disconnected()
        logger.info("Stopped!")
