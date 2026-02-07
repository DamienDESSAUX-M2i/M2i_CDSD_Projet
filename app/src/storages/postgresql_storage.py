import logging

import psycopg
from config import postgres_config

from src.models import JAMSMetadata, XMLMetadata
from src.utils import LOGGER_NAME


class PostgresStorage:
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.connection = self._get_connection()
        self.cursor = self.connection.cursor()

    def _get_connection(self) -> psycopg.Connection:
        self.logger.info("Connexion to the Postgres service...")
        connection = psycopg.connect(
            postgres_config.connection_string, row_factory=psycopg.rows.dict_row
        )
        self.logger.info("Connecting to the Postgres service")
        return connection

    # CRUD Metadata

    def select_metadata(self, id_metadata: int) -> dict | None:
        try:
            self.logger.debug(f"Executing metadata query: id_metadata={id_metadata}")
            self.cursor.execute(
                "SELECT * FROM metadata WHERE id_metadata=%s;",
                (id_metadata,),
            )
            result = self.cursor.fetchone()
            if result is not None:
                self.logger.debug("Metadata fetched successfully")
                return result
            else:
                self.logger.debug("Metadata fetched nothing")
                return None
        except Exception as exception:
            self.logger.error(f"Metadata selection has failed: {exception}")
            return None

    def select_metadata_title(self, title: str) -> dict | None:
        try:
            self.logger.debug(f"Executing metadata query: title={title}")
            self.cursor.execute(
                "SELECT * FROM metadata WHERE title=%s;",
                (title,),
            )
            result = self.cursor.fetchone()
            if result is not None:
                self.logger.debug("Metadata fetched successfully")
                return result.get("id_metadata", None)
            else:
                self.logger.debug("Metadata fetched nothing")
                return None
        except Exception as exception:
            self.logger.error(f"Metadata selection has failed: {exception}")
            return None

    def insert_into_metadata(self, metadata: JAMSMetadata | XMLMetadata) -> dict | None:
        try:
            self.logger.debug(f"Executing metadata query: title={metadata.title}")
            if isinstance(metadata, JAMSMetadata):
                self.cursor.execute(
                    """
                    INSERT INTO metadata (dataset_name, guitarist_id, title, style, tempo, scale, mode, playing_version, duration, pick_up_setting)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        metadata.playing_version,
                        metadata.duration,
                        metadata.pick_up_setting,
                    ),
                )
            elif isinstance(metadata, XMLMetadata):
                self.cursor.execute(
                    """
                    INSERT INTO metadata (
                        dataset_name,
                        title,
                        instrument,
                        instrument_model,
                        pick_up_setting,
                        instrument_tuning,
                        audio_effects,
                        recording_date,
                        recording_artist,
                        instrument_body_material,
                        instrument_string_material,
                        composer,
                        recording_source
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *;
                    """,
                    (
                        metadata.dataset_name,
                        metadata.title,
                        metadata.instrument,
                        metadata.instrument_model,
                        metadata.pick_up_setting,
                        # metadata.pick_up_type,
                        metadata.instrument_tuning,
                        # metadata.amp_channel,
                        metadata.audio_effects,
                        metadata.recording_date,
                        metadata.recording_artist,
                        metadata.instrument_body_material,
                        metadata.instrument_string_material,
                        metadata.composer,
                        metadata.recording_source,
                        # metadata.polyphony: bool,
                    ),
                )
            else:
                raise TypeError(
                    "metadata must be instance of JAMSMetadata or XMLMetadata"
                )
            self.connection.commit()
            result = self.cursor.fetchone()
            self.logger.debug("Metadata inserted successfully")
            return result
        except Exception as exception:
            self.logger.error(f"Metadata insertion has failed: {exception}")
            return None

    def update_metadata(
        self, id_metadata: int, metadata: JAMSMetadata | XMLMetadata
    ) -> dict | None:
        try:
            self.logger.debug(f"Executing metadata query: title={metadata.title}")
            if isinstance(metadata, JAMSMetadata):
                self.cursor.execute(
                    """
                    UPDATE metadata
                    SET dataset_name=%s, guitarist_id=%s, title=%s, style=%s, tempo=%s, scale=%s, mode=%s, playing_version=%s, duration=%s, pick_up_setting=%s
                    WHERE id_metadata=%s
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
                        metadata.playing_version,
                        metadata.duration,
                        metadata.pick_up_setting,
                        id_metadata,
                    ),
                )
            elif isinstance(metadata, XMLMetadata):
                self.cursor.execute(
                    """
                    UPDATE metadata
                    SET
                        dataset_name=%s,
                        title=%s,
                        instrument=%s,
                        instrument_model=%s,
                        pick_up_setting=%s,
                        instrument_tuning=%s,
                        audio_effects=%s,
                        recording_date=%s,
                        recording_artist=%s,
                        instrument_body_material=%s,
                        instrument_string_material=%s,
                        composer=%s,
                        recording_source=%s
                    WHERE id_metadata=%s
                    RETURNING *;
                    """,
                    (
                        metadata.dataset_name,
                        metadata.title,
                        metadata.instrument,
                        metadata.instrument_model,
                        metadata.pick_up_setting,
                        # metadata.pick_up_type,
                        metadata.instrument_tuning,
                        # metadata.amp_channel,
                        metadata.audio_effects,
                        metadata.recording_date,
                        metadata.recording_artist,
                        metadata.instrument_body_material,
                        metadata.instrument_string_material,
                        metadata.composer,
                        metadata.recording_source,
                        # metadata.polyphony: bool,
                        id_metadata,
                    ),
                )
            else:
                raise TypeError(
                    "metadata must be instance of JAMSMetadata or XMLMetadata"
                )
            self.connection.commit()
            result = self.cursor.fetchone()
            self.logger.debug("Metadata updated successfully")
            return result
        except Exception as exception:
            self.logger.error(f"Metadata updating has failed: {exception}")
            return None

    def delete_metadata(self, id_metadata: int) -> dict | None:
        try:
            self.logger.warning(f"Executing metadata query: id_metadata={id_metadata}")
            self.cursor.execute(
                "DELETE FROM metadata WHERE id_metadata=%s RETURNING *;",
                (id_metadata,),
            )
            self.connection.commit()
            result = self.cursor.fetchone()
            self.logger.warning("Metadata deleted successfully")
            return result
        except Exception as exception:
            self.logger.error(f"Metadata deleting has failed: {exception}")
            return None

    # UTILS

    def close(self) -> None:
        """Close connection"""
        self.cursor.close()
        self.connection.close()
        self.logger.info("Postgres connection closed")
