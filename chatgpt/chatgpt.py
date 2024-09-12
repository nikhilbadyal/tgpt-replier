"""Auth Open API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import openai
from loguru import logger
from openai import OpenAI

from chatgpt.exceptions import InvalidChoiceError
from chatgpt.utils import DataType, UserType, dummy_response

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion
    from telethon.tl.types import User


class ChatGPT(object):
    """Base Open API."""

    def __init__(self: Self) -> None:
        self.message_history: dict[str, list[dict[str, str]]] = {}
        from main import env

        self.model = env.str("BOT_TOKEN", "gpt-4o")
        self.client = OpenAI(
            api_key=env.str("GPT_KEY"),
            base_url=env.str("GPT_URL", "https://api.openai.com/v1"),
        )

    def build_message(self: Self, result: dict[dict[str, str], str]) -> list[dict[str, str]]:
        """Build Open API message."""
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages += [
            {
                "role": UserType.ASSISTANT.value if row["from_bot"] else UserType.USER.value,
                "content": row["message"],
            }
            for row in result
        ]

        return messages

    def send_request(
        self: Self,
        messages: list[dict[str, str]],
    ) -> ChatCompletion:
        """Send a request to OpenAI."""
        try:
            from main import env

            if env.bool("PROD", False):
                logger.debug("Sent chat completion request to OPENAI")
                response: ChatCompletion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    timeout=10,
                )
                logger.debug("Got chat completion response fromm open AI")
                return response
            logger.debug("Returned patched chat completion response from open AI")
            return dummy_response
        except Exception as e:
            logger.error(f"Unable to get response from OpenAI {e}")
            raise

    def send_text_completion_request(
        self,
        message: str,
    ) -> ChatCompletion:
        """Send a Text completion request to OpenAI."""
        try:
            from main import env

            if env.bool("PROD", False):
                logger.debug("Sent text completion request to OPENAI")
                system = [{"role": "system", "content": "You are Summary AI."}]
                user = [
                    {
                        "role": "user",
                        "content": f"If this is answer what will be the question(under 250 words):\n\n{message}",
                    },
                ]
                response: ChatCompletion = self.client.chat.completions.create(
                    model=self.model,
                    messages=system + user,
                    timeout=10,
                )
                logger.debug("Got text completion response fromm open AI")
                return response
            logger.debug("Returned patched text completion response from open AI")
            return dummy_response

        except Exception as e:
            logger.error(f"Unable to get response from OpenAI {e}")
            raise

    def reply_start(self: Self, message: str) -> str:
        """Reply to start message."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ]
        openapi_response = self.send_request(messages)
        return str(openapi_response.choices[0].message.content)

    def chat(self: Self, user: User, message: str) -> str:
        """Chat Open API."""
        from main import db

        db.insert_message_from_user(message, user.id)
        messages = db.get_messages_by_user(user.id)
        self.message_history[user.username] = self.build_message(messages)
        openapi_response = self.send_request(self.message_history[user.username])
        reply = str(openapi_response.choices[0].message.content)
        db.insert_message_from_gpt(reply, user.id)
        self.message_history[user.username].append(
            {"role": UserType.ASSISTANT.value, "content": reply},
        )
        return reply

    def image_gen(self: Self, telegram_user: User, message: str) -> str:
        """Generate an image from the text."""
        response = openai.Image.create(prompt=message, n=1, size="512x512")
        image_url = str(response["data"][0]["url"])
        from main import db

        db.insert_images_from_gpt(message, image_url, telegram_user.id)
        return image_url

    def _clean_up_user_messages(self: Self, telegram_user: User) -> int:
        """Delete all user's message data."""
        from main import db

        return db.delete_all_user_messages(telegram_user.id)

    def _clean_up_user_images(self: Self, user: User) -> int:
        """Delete all user's image data."""
        from main import db

        return db.delete_all_user_images(user.id)

    def clean_up_user_data(
        self: Self,
        data: str,
        telegram_user: User,
    ) -> int | tuple[int, int]:
        """Delete all for a user data."""
        from main import db

        if data == DataType.MESSAGES.value:
            return self._clean_up_user_messages(telegram_user)
        if data == DataType.IMAGES.value:
            return self._clean_up_user_images(telegram_user)
        if data == DataType.ALL.value:
            return db.delete_all_user_data(telegram_user.id)
        raise InvalidChoiceError(data)

    def initiate_new_conversation(
        self: Self,
        telegram_user: User,
        title: str,
    ) -> None:
        """Initiate a new conversation."""
        from main import db

        if title:
            logger.debug("Initializing new conversation with title")
            return db.initiate_new_conversation(telegram_user.id, title)
        logger.debug("Initializing new conversation without title")
        db.initiate_empty_new_conversation(telegram_user.id)
        return None
