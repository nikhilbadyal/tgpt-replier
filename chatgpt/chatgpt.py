"""Auth Open API."""
from typing import Dict, List

import openai
from loguru import logger


class ChatGPT(object):
    """Base Open API."""

    def __init__(self) -> None:
        self.message_history: Dict[str, List[Dict[str, str]]] = {}
        self._auth()

    def _auth(self) -> None:
        """Auth Open API."""
        from main import env

        openai.api_key = env.str("GPT_KEY")

    def chat(self, username: str, message: str) -> str:
        """Chat Open API."""
        if username not in self.message_history:
            logger.info("No message history found for the user {}".format(username))
            self.message_history[username] = [
                {"role": "system", "content": "You are a helpful assistant."}
            ]
        self.message_history[username].append({"role": "user", "content": message})
        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo", messages=self.message_history[username], timeout=10
        )
        logger.debug("Got response fromm open AI")
        reply = str(response["choices"][0]["message"]["content"])
        self.message_history[username].append({"role": "assistant", "content": reply})
        return reply
