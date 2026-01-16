import logging

import psycopg
from config import postgres_config

from src.utils import LOGGER_NAME


class PostgresStorage:
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.connection = self._get_connection()
        self.cursor = self.connection.cursor()

    def _get_connection(self) -> psycopg.Connection:
        self.logger.info("Attempting to connect to the Mongo service.")
        connection = psycopg.connect(
            postgres_config.connection_string, row_factory=psycopg.rows.dict_row
        )
        self.logger.info("Connecting to the Mongo service.")
        return connection

    # CRUD

    def select(self, id_item: int) -> dict | None:
        try:
            self.cursor.execute(
                "SELECT id_item FROM table WHERE id_item=%s;",
                (id_item,),
            )
            return self.cursor.fetchone()
        except Exception as e:
            self.logger.error(f"select_author_failed: {e}")
            return None

    def insert_into(self, item: str) -> dict | None:
        try:
            self.cursor.execute(
                "INSERT INTO table (item) VALUES (%s) RETURNING *;",
                (item,),
            )
            self.connection.commit()
            result = self.cursor.fetchone()
            self.logger.debug(f"Insertion: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Insertion failed: {e}")
            return None

    def update(self, id_item: int, item: str) -> dict | None:
        try:
            self.cursor.execute(
                """
                UPDATE table
                SET item=%s
                WHERE id_item=%s
                RETURNING *;
                """,
                (item, id_item),
            )
            self.connection.commit()
            result = self.cursor.fetchone()
            self.logger.debug(f"Updating: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Updating failed: {e}")
            return None

    def delete(self, id_item: int) -> dict | None:
        try:
            self.cursor.execute(
                "DELETE FROM table WHERE id_item=%s RETURNING *;",
                (id_item,),
            )
            self.connection.commit()
            result = self.cursor.fetchone()
            self.logger.warning(f"Deleting: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Deleting failed: {e}")
            return None

    # UTILS

    def close(self) -> None:
        """Close connection"""
        self.cursor.close()
        self.connection.close()
        self.logger.info("Postgres connection closed.")
