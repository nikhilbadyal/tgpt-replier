"""Auth Open API."""
from typing import Dict, List, Tuple

import openai
from loguru import logger
from openai.openai_object import OpenAIObject
from telethon.tl.types import User

from chatgpt.utils import DataType, UserType
from sqlitedb.utils import ErrorCodes


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

    def send_request(self, messages: List[Dict[str, str]]) -> int | OpenAIObject:
        """Send a request to OpenAI."""
        try:
            response: OpenAIObject = openai.ChatCompletion.create(  # type: ignore
                model="gpt-3.5-turbo",
                messages=messages,
                timeout=10,
            )
            logger.debug("Got response fromm open AI")
            return response
        except Exception as e:
            logger.error(f"Unable to get response from OpenAI {e}")
            return ErrorCodes.exceptions.value

    def reply_start(self, message: str) -> str | int:
        """Reply to start message."""

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ]
        openapi_response = self.send_request(messages)
        if isinstance(openapi_response, int):
            return openapi_response
        return str(openapi_response["choices"][0]["message"]["content"])

    def chat(self, user: User, message: str) -> str | int:
        """Chat Open API."""
        from main import db

        response = db.insert_message_from_user(message, user.id)
        if response <= ErrorCodes.exceptions.value:
            return response
        messages = db.get_messages_by_user(user.id)
        if response <= ErrorCodes.exceptions.value:
            return response
        self.message_history[user.username] = self.build_message(messages)
        logger.debug("Sent request to OPENAI")
        openapi_response = self.send_request(self.message_history[user.username])
        if isinstance(openapi_response, int):
            return openapi_response
        reply = str(openapi_response["choices"][0]["message"]["content"])
        response = db.insert_message_from_gpt(reply, user.id)
        if response <= ErrorCodes.exceptions.value:
            return response
        self.message_history[user.username].append(
            {"role": UserType.ASSISTANT.value, "content": reply}
        )
        return reply

    def image_gen(self, telegram_user: User, message: str) -> str | int:
        """Generate an image from the text."""
        response = openai.Image.create(prompt=message, n=1, size="512x512")  # type: ignore
        image_url = str(response["data"][0]["url"])
        from main import db

        response = db.insert_images_from_gpt(message, image_url, telegram_user.id)
        if response <= ErrorCodes.exceptions.value:
            return int(response)
        return image_url

    def _clean_up_user_messages(self, telegram_user: User) -> int:
        """Delete all user's message data."""
        from main import db

        return db.delete_all_user_messages(telegram_user.id)

    def _clean_up_user_images(self, user: User) -> int:
        """Delete all user's image data."""
        from main import db

        return db.delete_all_user_images(user.id)

    def clean_up_user_data(
        self, data: str, telegram_user: User
    ) -> Tuple[int, int] | int:
        """Delete all for a user data."""
        from main import db

        if data == DataType.MESSAGES.value:
            return self._clean_up_user_messages(telegram_user)
        elif data == DataType.IMAGES.value:
            return self._clean_up_user_images(telegram_user)
        elif data == DataType.ALL.value:
            return db.delete_all_user_data(telegram_user.id)
        else:
            logger.error("Not a valid choice")
            return -1, -1

    def initiate_new_conversation(self, telegram_user: User) -> int:
        """Initiate a new conversation."""
        from main import db

        return db.initiate_new_conversation(telegram_user.id)
