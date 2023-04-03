"""SQLite database to store messages."""
import sqlite3
from typing import Any, List, Tuple, Union

from chatgpt.utils import UserType


class SQLiteDatabase(object):
    """SQLite database Object."""

    def __init__(self, db_name: str) -> None:
        self.connection = sqlite3.connect(f"{db_name}.db")
        self.create_table()

    def create_table(self) -> None:
        """Create a new table to store messages."""
        cursor = self.connection.cursor()
        cursor.executescript(
            """
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          message TEXT,
          role text,
          is_bot_message BOOLEAN,
          message_date DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE if not exists images (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          image_caption TEXT,
          image_url TEXT,
          is_bot_image BOOLEAN,
          message_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        )
        self.connection.commit()

    def execute_query(
        self, query: str, params: Union[Tuple[Any, ...], List[Tuple[Any, ...]]] = ()
    ) -> List[Tuple[Any, ...]]:
        """Execute an SQL query and return the results as a list of tuples."""

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        self.connection.commit()
        return results

    def get_messages_by_user(self, user_id: int) -> List[Tuple[Any, ...]]:
        """Get all messages for a given user."""
        query = """
            SELECT role, message
            FROM messages
            WHERE user_id = ?
        """
        params = (user_id,)
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

    def insert_images_from_gpt(
        self, message: str, image_url: str, user_id: int
    ) -> None:
        """Insert an image generated by the GPT model."""
        query = """
            INSERT INTO images (user_id, image_caption, image_url, is_bot_image)
            VALUES (?, ?, ?, ?)
        """
        params = (user_id, message, image_url, True)
        self.execute_query(query, params)

    def delete_all_user_messages(self, user_id: int) -> bool:
        """Delete all the messages associated with the user."""
        query = "delete from messages where user_id = ?"
        params = (user_id,)
        try:
            self.execute_query(query, params)
            return True
        except sqlite3.Error:
            return False

    def delete_all_user_images(self, user_id: int) -> bool:
        """Delete all the messages associated with the user."""
        query = "delete from images where user_id = ?"
        params = (user_id,)
        try:
            self.execute_query(query, params)
            return True
        except sqlite3.Error:
            return False

    def delete_all_user_data(self, user_id: int) -> bool:
        """Delete all the messages associated with the user."""
        try:
            # TODO: Do this in a transaction
            self.delete_all_user_images(user_id)
            self.delete_all_user_messages(user_id)
            return True
        except sqlite3.Error:
            return False
