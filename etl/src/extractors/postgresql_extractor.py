import psycopg
from config import postgres_config

from src.extractors.abstract_extractor import AbstractExtractor


class PostgreSQLExtractor(AbstractExtractor):
    """Extractor for PostgreSQL."""

    def extract(self, table_name: str) -> list[dict]:
        """Extract data from PostgreSQL.

        Args:
            table_name (str): Name of the table.
        """
        try:
            self.logger.info("Attempting to connect to the PostgreSQL service.")
            with psycopg.connect(
                postgres_config.connection_string, row_factory=psycopg.rows.dict_row
            ) as connection:
                self.logger.info("Connecting to the PostgreSQL service.")
                with connection.cursor() as cursor:
                    self.logger.info(f"Attempting extraction from : {table_name}.")
                    cursor.execute(
                        "SELECT * FROM %s;",
                        (table_name,),
                    )
                rows = cursor.fetchall()
                self.logger.info(f"Number of rows extracted : {len(rows)}.")
                return rows
        except Exception as e:
            self.logger.error(f"Error PostgreSQL extractor: {e}.")
            raise
