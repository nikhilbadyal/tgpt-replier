"""Auth Open API."""
from typing import Dict, List, Tuple

import openai
from loguru import logger
from telethon.tl.types import User

from chatgpt.utils import UserType


class ChatGPT(object):
    """Base Open API."""

    def __init__(self) -> None:
        self.message_history: Dict[str, List[Dict[str, str]]] = {}
        self._auth()

    def _auth(self) -> None:
        """Auth Open API."""
        from main import env

        openai.api_key = env.str("GPT_KEY")

    def build_message(self, result: Dict[Dict[str, str], str]) -> List[Dict[str, str]]:
        """Build Open API message."""
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages += [
            {
                "role": UserType.ASSISTANT.value
                if row["from_bot"]
                else UserType.USER.value,
                "content": row["message"],
            }
            for row in result
        ]

        return messages

    def reply_start(self, message: str) -> str:
        """Reply to start message."""

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ]
        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo",
            messages=messages,
            timeout=10,
        )
        logger.debug("Got response fromm open AI")
        reply = str(response["choices"][0]["message"]["content"])
        return reply

    def chat(self, user: User, message: str) -> str:
        """Chat Open API."""
        from main import db

        db.insert_message_from_user(message, user.id)
        messages = db.get_messages_by_user(user.id)
        self.message_history[user.username] = self.build_message(messages)
        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo",
            messages=self.message_history[user.username],
            timeout=10,
        )
        logger.debug("Got response fromm open AI")
        reply = str(response["choices"][0]["message"]["content"])
        db.insert_message_from_gpt(reply, user.id)
        self.message_history[user.username].append(
            {"role": UserType.ASSISTANT.value, "content": reply}
        )
        return reply

    def image_gen(self, telegram_user: User, message: str) -> str:
        """Generate an image from the text."""
        response = openai.Image.create(prompt=message, n=1, size="512x512")  # type: ignore
        image_url = str(response["data"][0]["url"])
        from main import db

        db.insert_images_from_gpt(message, image_url, telegram_user.id)
        return image_url

    def clean_up_user_messages(self, telegram_user: User) -> int:
        """Delete all user's message data."""
        from main import db

        return db.delete_all_user_messages(telegram_user.id)

    def clean_up_user_images(self, user: User) -> int:
        """Delete all user's image data."""
        from main import db

        return db.delete_all_user_messages(user.id)

    def clean_up_user_data(self, telegram_user: User) -> Tuple[int, int]:
        """Delete all for a user data."""
        from main import db

        return db.delete_all_user_data(telegram_user.id)
