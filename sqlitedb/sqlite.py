"""SQLite database to store messages."""
import sqlite3
from typing import Any, List, Tuple, Union

from telethon.tl.types import User

from chatgpt.utils import UserType


class SQLiteDatabase(object):
    """SQLite database Object."""

    def __init__(self) -> None:
        self.connection = sqlite3.connect("tgreplier.db")
        self.create_table()

    def create_table(self) -> None:
        """Create a new table to store messages."""
        cursor = self.connection.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY,
          user_id INTEGER,
          message TEXT,
          role text,
          is_bot_message BOOLEAN,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        )

    def execute_query(
        self, query: str, params: Union[Tuple[Any, ...], List[Tuple[Any, ...]]] = ()
    ) -> List[Tuple[Any, ...]]:
        """Execute an SQL query and return the results as a list of tuples."""

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        self.connection.commit()
        return results

    def get_messages_by_user(self, user: User) -> List[Tuple[Any, ...]]:
        """Get all messages for a given user."""
        query = """
            SELECT role, message
            FROM messages
            WHERE user_id = ?
        """
        params = (user.id,)
        return self.execute_query(query, params)

    def insert_message_from_user(self, message: str, user_id: int) -> None:
        """Insert a message sent by a user."""
        query = """
            INSERT INTO messages (user_id, message, role, is_bot_message)
            VALUES (?, ?, ?, ?)
        """
        params = (user_id, message, UserType.USER.value, False)
        self.execute_query(query, params)

    def insert_message_from_gpt(self, message: str, user_id: int) -> None:
        """Insert a message generated by the GPT model."""
        query = """
            INSERT INTO messages (user_id, message, role, is_bot_message)
            VALUES (?, ?, ?, ?)
        """
        params = (user_id, message, UserType.ASSISTANT.value, True)
        self.execute_query(query, params)