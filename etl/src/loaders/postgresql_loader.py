import psycopg

from src.loaders.abstract_loader import AbstractLoader
from src.utils.config import postgresql_config


class PostgreSQLLoader(AbstractLoader):
    """Extractor for PostgreSQL."""

    def load(self, table_name: str, data: str) -> list[dict]:
        """Load data into PostgreSQL.

        Args:
            table_name (str): Name of the table.
            data (str): Data to load.
        """
        try:
            self.logger.info("Attempting to connect to the PostgreSQL service.")
            with psycopg.connect(
                postgresql_config.connection_string, row_factory=psycopg.rows.dict_row
            ) as connection:
                self.logger.info("Connecting to the PostgreSQL service.")
                with connection.cursor() as cursor:
                    self.logger.info(f"Attempting load into: {table_name}.")
                    cursor.execute(
                        "INSERT INTO %s (data) VALUES (%s) RETURNING *;",
                        (table_name, data),
                    )
                result = cursor.fetchone()
                self.logger.info(f"Data successfully inserted: {result}.")
                return result
        except Exception as e:
            self.logger.error(f"Error PostgreSQL loader: {e}.")
            raise
