"""Auth Open API."""
from typing import Dict, List

import openai


class ChatGPT(object):
    """Base Open API."""

    def __init__(self) -> None:
        self.message_history: List[Dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]
        self._auth()

    def _auth(self) -> None:
        """Auth Open API."""
        from main import env

        openai.api_key = env.str("GPT_KEY")

    def chat(self, message: str) -> str:
        """Chat Open API."""
        self.message_history.append({"role": "user", "content": message})
        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo",
            messages=self.message_history,
        )
        reply = str(response["choices"][0]["message"]["content"])
        self.message_history.append({"role": "assistant", "content": reply})
        return reply
