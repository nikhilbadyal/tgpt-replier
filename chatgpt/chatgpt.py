"""Auth Open API."""
from __future__ import annotations

from typing import TYPE_CHECKING

import openai
from loguru import logger

from chatgpt.utils import DataType, UserType, generate_random_string
from sqlitedb.utils import ErrorCodes

if TYPE_CHECKING:
    from openai.openai_object import OpenAIObject
    from telethon.tl.types import User
    from typing_extensions import Self


class ChatGPT(object):
    """Base Open API."""

    def __init__(self: Self) -> None:
        self.message_history: dict[str, list[dict[str, str]]] = {}
        self._auth()

    def _auth(self: Self) -> None:
        """Auth Open API."""
        from main import env

        openai.api_key = env.str("GPT_KEY")

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
    ) -> OpenAIObject | dict[str, list[dict[str, dict[str, str]]]] | ErrorCodes:
        """Send a request to OpenAI."""
        try:
            from main import env

            if env.bool("PROD", False):
                logger.debug("Sent chat completion request to OPENAI")
                response: OpenAIObject = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    timeout=10,
                )
                logger.debug("Got chat completion response fromm open AI")
                return response
            logger.debug("Returned patched chat completion response from open AI")
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"Message: {generate_random_string(length=20)}",
                        },
                    },
                ],
            }

        except Exception as e:
            logger.error(f"Unable to get response from OpenAI {e}")
            return ErrorCodes.exceptions

    @staticmethod
    def send_text_completion_request(
        messages: str,
    ) -> dict[str, list[dict[str, str]]] | ErrorCodes:
        """Send a Text completion request to OpenAI."""
        try:
            from main import env

            if env.bool("PROD", False):
                logger.debug("Sent text completion request to OPENAI")
                response: OpenAIObject = openai.Completion.create(
                    model="text-davinci-003",
                    temperature=0,
                    prompt=messages,
                    timeout=10,
                )
                logger.debug("Got text completion response fromm open AI")
                return response.json()
            logger.debug("Returned patched text completion response from open AI")
            return {
                "choices": [
                    {
                        "text": f"Title: {generate_random_string(length=20)}",
                    },
                ],
            }

        except Exception as e:
            logger.error(f"Unable to get response from OpenAI {e}")
            return ErrorCodes.exceptions

    def reply_start(self: Self, message: str) -> str | ErrorCodes:
        """Reply to start message."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ]
        openapi_response = self.send_request(messages)
        if isinstance(openapi_response, ErrorCodes):
            return openapi_response
        return str(openapi_response["choices"][0]["message"]["content"])

    def chat(self: Self, user: User, message: str) -> str | ErrorCodes:
        """Chat Open API."""
        from main import db

        response = db.insert_message_from_user(message, user.id)
        if isinstance(response, ErrorCodes):
            return response
        messages = db.get_messages_by_user(user.id)
        if isinstance(response, ErrorCodes):
            return response
        self.message_history[user.username] = self.build_message(messages)
        openapi_response = self.send_request(self.message_history[user.username])
        if isinstance(openapi_response, ErrorCodes):
            return openapi_response
        reply = str(openapi_response["choices"][0]["message"]["content"])
        response = db.insert_message_from_gpt(reply, user.id)
        if isinstance(response, ErrorCodes):
            return response
        self.message_history[user.username].append(
            {"role": UserType.ASSISTANT.value, "content": reply},
        )
        return reply

    def image_gen(self: Self, telegram_user: User, message: str) -> str | ErrorCodes:
        """Generate an image from the text."""
        response = openai.Image.create(prompt=message, n=1, size="512x512")
        image_url = str(response["data"][0]["url"])
        from main import db

        response = db.insert_images_from_gpt(message, image_url, telegram_user.id)
        if isinstance(response, ErrorCodes):
            return response
        return image_url

    def _clean_up_user_messages(self: Self, telegram_user: User) -> ErrorCodes | int:
        """Delete all user's message data."""
        from main import db

        return db.delete_all_user_messages(telegram_user.id)

    def _clean_up_user_images(self: Self, user: User) -> ErrorCodes | int:
        """Delete all user's image data."""
        from main import db

        return db.delete_all_user_images(user.id)

    def clean_up_user_data(
        self: Self,
        data: str,
        telegram_user: User,
    ) -> ErrorCodes | int | tuple[int, int] | tuple[ErrorCodes | int, ErrorCodes | int]:
        """Delete all for a user data."""
        from main import db

        if data == DataType.MESSAGES.value:
            return self._clean_up_user_messages(telegram_user)
        elif data == DataType.IMAGES.value:
            return self._clean_up_user_images(telegram_user)
        elif data == DataType.ALL.value:
            return db.delete_all_user_data(telegram_user.id)
        logger.error(f"Not a valid choice {data}")
        return ErrorCodes.exceptions

    def initiate_new_conversation(
        self: Self,
        telegram_user: User,
        title: str,
    ) -> ErrorCodes | None:
        """Initiate a new conversation."""
        from main import db

        if title:
            logger.debug("Initializing new conversation with title")
            return db.initiate_new_conversation(telegram_user.id, title)
        logger.debug("Initializing new conversation without title")
        db.initiate_empty_new_conversation(telegram_user.id)
        return None
