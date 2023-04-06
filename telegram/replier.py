"""Reply to messages."""
import io
import re
from typing import IO, Union

import requests
from asgiref.sync import sync_to_async
from loguru import logger
from telethon import TelegramClient, events
from telethon.tl.types import User

from chatgpt.chatgpt import ChatGPT
from sqlitedb.utils import ErrorCodes


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
                        response = gpt.image_gen(user, result)
                        if isinstance(response, int):
                            await event.respond(self.cleanup_failure)
                        else:
                            await self.send_image_from_url(user, response, result)
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
            logger.debug("Received pun request")
            reply = gpt.reply_start(start_message)
            result = reply[len(prefix) :]
            await event.respond(result)

        @self.client.on(events.NewMessage(pattern="/image"))  # type: ignore
        async def handle_image_command(event: events.NewMessage.Event) -> None:
            """Handle Start Message."""
            logger.debug("Received image request")
            prefix = "/image "
            telegram_user: User = await self.get_user(event)
            result = event.message.text[len(prefix) :]
            if result:
                url = await sync_to_async(gpt.image_gen)(telegram_user, result)
                if isinstance(url, int):
                    await event.respond(self.cleanup_failure)
                await self.send_image_from_url(telegram_user, url, result)
            else:
                await event.respond(self.no_input)

        @self.client.on(events.NewMessage(pattern="^/reset(messages|images)$"))  # type: ignore
        async def handle_reset_images_command(event: events.NewMessage.Event) -> None:
            """Delete all message history for a user."""
            telegram_user: User = await self.get_user(event)
            original_message = event.message.text
            match = re.search(r"^/reset(.+)$", original_message)
            if match:
                request = match.group(1)
                logger.debug(f"Received request to delete all {request}")
                result = await sync_to_async(gpt.clean_up_user_data)(
                    original_message, telegram_user
                )
                logger.debug(f"Removed {result} {request}")
                if result >= ErrorCodes.exceptions.value:
                    await event.respond(self.cleanup_success)
                else:
                    await event.respond(self.cleanup_failure)

        @self.client.on(events.NewMessage(pattern="^/reset$"))  # type: ignore
        async def handle_reset_command(event: events.NewMessage.Event) -> None:
            """Delete all message history for a user."""
            logger.debug("Received request to delete all user data")
            telegram_user: User = await self.get_user(event)
            num_conv_deleted, num_img_deleted = await sync_to_async(
                gpt.clean_up_user_data
            )("/reset", telegram_user)
            logger.debug(
                f"Removed {num_conv_deleted} convo and {num_img_deleted} images"
            )
            if (
                num_conv_deleted <= ErrorCodes.exceptions.value
                or num_img_deleted <= ErrorCodes.exceptions.value
            ):
                await event.respond(self.cleanup_failure)
            await event.respond(self.cleanup_success)

        @self.client.on(events.NewMessage(pattern=self.get_regex()))  # type: ignore
        async def handle_any_message(event: events.NewMessage.Event) -> None:
            """Handle Start Message."""
            logger.debug("Received request in general handler")
            if event.is_private:  # only auto-reply to private chats
                user: User = await self.get_user(event)
                if user and not user.bot:
                    if event.message.text:
                        logger.debug("Sent request to OPENAI")
                        message = await sync_to_async(gpt.chat)(
                            user, event.message.text
                        )
                        if isinstance(message, int):
                            await event.respond(self.cleanup_failure)
                        else:
                            await event.respond(message)
                    else:
                        await event.respond(self.cleanup_failure)
                else:
                    logger.error("Cannot get Entity or a bot")
            else:
                logger.info("Not a private message")

        self.client.run_until_disconnected()
        logger.info("Stopped!")
