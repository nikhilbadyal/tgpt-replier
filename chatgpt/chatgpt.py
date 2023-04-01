"""Auth Open API."""
from typing import Any, Dict, List, Tuple

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

    def build_message(self, result: List[Tuple[Any, ...]]) -> List[Dict[str, str]]:
        """Build Open API message."""
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages += [{"role": row[0], "content": row[1]} for row in result]

        return messages

    def chat(self, user: User, message: str) -> str:
        """Chat Open API."""
        from main import db

        db.insert_message_from_user(message, user.id)
        messages = db.get_messages_by_user(user)
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
