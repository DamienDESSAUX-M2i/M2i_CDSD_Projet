import logging

import psycopg
from config import postgres_config

from src.extractors.jams_extractor import JAMSMetadata
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

    # CRUD Metadata

    def select_metadata(self, id_item: int) -> dict | None:
        try:
            self.cursor.execute(
                "SELECT id_item FROM table WHERE id_item=%s;",
                (id_item,),
            )
            return self.cursor.fetchone()
        except Exception as e:
            self.logger.error(f"select_author_failed: {e}")
            return None

    def insert_into_metadata(self, metadata: JAMSMetadata) -> dict | None:
        try:
            self.cursor.execute(
                """
                INSERT INTO metadata (dataset_name, guitarist_id, title, style, tempo, scale, mode, playing_version, duration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (
                    metadata.dataset_name,
                    metadata.guitarist_id,
                    metadata.title,
                    metadata.style,
                    metadata.tempo,
                    metadata.scale,
                    metadata.mode,
                    metadata.version,
                    metadata.duration,
                ),
            )
            self.connection.commit()
            result = self.cursor.fetchone()
            self.logger.info(f"Insertion: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Insertion has failed: {e}")
            return None

    def update_metadata(self, id_item: int, item: str) -> dict | None:
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

    def delete_metadata(self, id_item: int) -> dict | None:
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
