"""Reply to messages."""

from loguru import logger
from telethon import TelegramClient, events

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
        self.client.start(env.int("PHONE"), env.str("2FA_PASSWORD"))

    def listen(self, gpt: ChatGPT) -> None:
        """Listen for messages."""

        @self.client.on(events.NewMessage(incoming=True))  # type: ignore
        async def handle_new_message(event: events.NewMessage.Event) -> None:
            """Handle Incoming Message."""
            if event.is_private:  # only auto-reply to private chats
                try:
                    from_ = await event.client.get_entity(event.from_id)
                except ValueError:
                    from_ = await event.get_sender()
                if from_ and not from_.bot:
                    await event.respond(gpt.chat(event.message.text))
                else:
                    logger.error("Cannot get Entity or a bot")
            else:
                logger.info("Not a private message")

        self.client.run_until_disconnected()
        logger.info("Stopped!")
