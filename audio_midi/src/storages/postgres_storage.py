import logging
from typing import Any, TypedDict

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from settings import GUITAR_SET_SETTINGS, IDMT_SMT_GUITAR_SETTINGS, POSTGRES_SETTINGS

from src.models import AnnotationType, AudioType, JAMSMetadata, XMLMetadata

from .abstract_storage import AbstractStorage


class Row(TypedDict, total=False):
    """Generic database row representation."""

    pass


class PostgresStorage(AbstractStorage):
    """PostgreSQL storage backend for recordings and dataset metadata.

    This class provides a low-level persistence layer over PostgreSQL using psycopg.
    It handles CRUD operations for:
    - recordings (core entity)
    - dataset-specific metadata (GuitarSet, IDMT-SMT-Guitar)
    - audio files stored in MinIO (URI references)
    - annotation files stored in MinIO (URI references)
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize storage and database connection.

        Args:
            logger: Application logger instance.
        """

        super().__init__(logger)
        self._connection: Connection[Row] = self._get_connection()

    def _get_connection(self) -> Connection[Row]:
        """Create PostgreSQL connection.

        Returns:
            Active PostgreSQL connection.
        """

        self.logger.info("Connecting to PostgreSQL")

        return psycopg.connect(
            POSTGRES_SETTINGS.connection_string,
            row_factory=dict_row,
        )

    def close(self) -> None:
        """Close database connection."""

        if not self._connection.closed:
            self._connection.close()
            self.logger.info("PostgreSQL connection closed")

    def _execute_one(
        self,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> Row | None:
        """Execute a SQL query with fetchone strategy.

        Args:
            query: SQL query.
            params: Query parameters.

        Returns:
            Query result.
        """

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                self._connection.commit()
                return result

        except Exception:
            self._connection.rollback()
            self.logger.exception("SQL execution failed")
            return None

    def _execute_many(
        self,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> list[Row]:
        """Execute a SQL query with fetchmany strategy.

        Args:
            query: SQL query.
            params: Query parameters.

        Returns:
            Query result.
        """

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                self._connection.commit()
                return result

        except Exception:
            self._connection.rollback()
            self.logger.exception("SQL execution failed")
            return None

    # ===
    # RECORDINGS
    # ===

    def insert_recording(
        self,
        dataset_name: str,
        title: str,
    ) -> Row | None:
        """Insert a recording.

        Args:
            dataset_name: Dataset identifier.
            title: Recording title.

        Returns:
            Inserted recording row or None if failed.
        """

        return self._execute_one(
            query="""
            INSERT INTO recordings (dataset_name, title)
            VALUES (%s, %s)
            RETURNING *;
            """,
            params=(dataset_name, title),
        )

    def select_recording(
        self,
        dataset_name: str,
        title: str,
    ) -> Row | None:
        """Fetch a recording by dataset name and title.

        Args:
            dataset_name: Dataset identifier.
            title: Recording title.

        Returns:
            Recording row if found, otherwise None.
        """

        return self._execute_one(
            query="""
            SELECT *
            FROM recordings
            WHERE dataset_name = %s
            AND title = %s;
            """,
            params=(dataset_name, title),
        )

    def update_recording(
        self,
        id_recording: str,
        dataset_name: str,
        title: str,
    ) -> Row | None:
        """Update a recording.

        Args:
            dataset_name: Dataset identifier.
            title: Recording title.

        Returns:
            Updated recording row or None if failed.
        """

        return self._execute_one(
            query="""
            UPDATE recordings
            SET dataset_name = %s,
                title = %s
            WHERE id_recording = %s
            RETURNING *;
            """,
            params=(dataset_name, title, id_recording),
        )

    def delete_recording(self, id_recording: str) -> Row | None:
        """Delete a recording.

        Args:
            id_recording: Recording ID.
        """

        return self._execute_one(
            query="DELETE FROM recordings WHERE id_recording = %s RETURNING *;",
            params=(id_recording,),
        )

    # ===
    # GUITARSET METADATA
    # ===

    def insert_guitarset_metadata(
        self,
        id_recording: str,
        metadata: JAMSMetadata,
    ) -> Row | None:
        """Insert GuitarSet metadata.

        Args:
            id_recording: Recording ID.
            metadata: GuitarSet metadata object.

        Returns:
            Inserted metadata row or None.
        """

        return self._execute_one(
            query="""
            INSERT INTO guitarset_metadata (
                id_recording,
                duration,
                guitarist_id,
                style,
                tempo,
                scale,
                mode,
                playing_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
            """,
            params=(
                id_recording,
                metadata.duration,
                metadata.guitarist_id,
                metadata.style,
                metadata.tempo,
                metadata.scale,
                metadata.mode,
                metadata.playing_version,
            ),
        )

    def select_guitarset_metadata(self, id_recording: str) -> Row | None:
        """Fetch GuitarSet metadata.

        Args:
            id_recording: Recording ID.

        Returns:
            GuitarSet metadata row if found, otherwise None.
        """

        return self._execute_one(
            query="SELECT * FROM guitarset_metadata WHERE id_recording = %s;",
            params=(id_recording,),
        )

    def select_all_guitarset_metadata(self) -> list[Row]:
        """Fetch all GuitarSet metadata.

        Returns:
            List of GuitarSet metadata rows.
        """

        return self._execute_many(
            query="""
            SELECT
                r.id_recording,
                r.dataset_name,
                r.title,
                g.duration,
                g.guitarist_id,
                g.style,
                g.tempo,
                g.scale,
                g.mode,
                g.playing_version
            FROM recordings AS r
            INNER JOIN guitarset_metadata AS g
                ON r.id_recording = g.id_recording
            WHERE r.dataset_name = %s;
            """,
            params=(GUITAR_SET_SETTINGS.name,),
        )

    def update_guitarset_metadata(
        self,
        id_recording: str,
        metadata: JAMSMetadata,
    ) -> Row | None:
        """Update GuitarSet metadata.

        Args:
            id_recording: Recording ID.
            metadata: GuitarSet metadata object.

        Returns:
            Updated metadata row or None.
        """

        return self._execute_one(
            query="""
            UPDATE guitarset_metadata
            SET duration = %s,
                guitarist_id = %s,
                style = %s,
                tempo = %s,
                scale = %s,
                mode = %s,
                playing_version = %s
            WHERE id_recording = %s
            RETURNING *;
            """,
            params=(
                metadata.duration,
                metadata.guitarist_id,
                metadata.style,
                metadata.tempo,
                metadata.scale,
                metadata.mode,
                metadata.playing_version,
                id_recording,
            ),
        )

    def delete_guitarset_metadata(
        self,
        id_recording: str,
    ) -> Row | None:
        """Delete GuitarSet metadata.

        Args:
            id_recording: Recording ID.
        """

        return self._execute_one(
            query="DELETE FROM guitarset_metadata WHERE id_recording = %s RETURNING *;",
            params=(id_recording,),
        )

    # ===
    # IDMT-SMT-GUITAR METADATA
    # ===

    def insert_idmt_smt_guitar_metadata(
        self,
        id_recording: str,
        metadata: XMLMetadata,
    ) -> Row | None:
        """Insert IDMT-SMT-Guitar metadata.

        Args:
            id_recording: Recording ID.
            metadata: IDMT metadata object.

        Returns:
            Inserted metadata row or None.
        """

        return self._execute_one(
            query="""
            INSERT INTO idmt_smt_guitar_metadata (
                id_recording,
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
            """,
            params=(
                id_recording,
                metadata.instrument,
                metadata.instrument_model,
                metadata.pick_up_setting,
                metadata.instrument_tuning,
                metadata.audio_effects,
                metadata.recording_date,
                metadata.recording_artist,
                metadata.instrument_body_material,
                metadata.instrument_string_material,
                metadata.composer,
                metadata.recording_source,
            ),
        )

    def select_idmt_smt_guitar_metadata(self, id_recording: str) -> Row | None:
        """Fetch IDMT-SMT-Guitar metadata.

        Args:
            id_recording: Recording ID.

        Returns:
            IDMT-SMT-Guitar metadata row if found, otherwise None.
        """

        return self._execute_one(
            query="SELECT * FROM idmt_smt_guitar_metadata WHERE id_recording = %s;",
            params=(id_recording,),
        )

    def select_all_idmt_smt_guitar_metadata(self, dataset_number: int) -> list[Row]:
        """Fetch all IDMT-SMT-Guitar metadata.

        Returns:
            List of IDMT-SMT-Guitar metadata rows.
        """

        return self._execute_many(
            query="""
            SELECT
                r.id_recording,
                r.dataset_name,
                r.title,
                i.instrument,
                i.instrument_model,
                i.pick_up_setting,
                i.instrument_tuning,
                i.audio_effects,
                i.recording_date,
                i.recording_artist,
                i.instrument_body_material,
                i.instrument_string_material,
                i.composer,
                i.recording_source
            FROM recordings AS r
            INNER JOIN idmt_smt_guitar_metadata AS i
                ON r.id_recording = i.id_recording
            WHERE r.dataset_name = %s;
            """,
            params=(f"{IDMT_SMT_GUITAR_SETTINGS.name}_{dataset_number}",),
        )

    def update_idmt_smt_guitar_metadata(
        self,
        id_recording: str,
        metadata: XMLMetadata,
    ) -> Row | None:
        """Update IDMT metadata.

        Args:
            id_recording: Recording ID.
            metadata: IDMT metadata object.

        Returns:
            Updated metadata row or None.
        """

        return self._execute_one(
            query="""
            UPDATE idmt_smt_guitar_metadata
            SET instrument = %s,
                instrument_model = %s,
                pick_up_setting = %s,
                instrument_tuning = %s,
                audio_effects = %s,
                recording_date = %s,
                recording_artist = %s,
                instrument_body_material = %s,
                instrument_string_material = %s,
                composer = %s,
                recording_source = %s
            WHERE id_recording = %s
            RETURNING *;
            """,
            params=(
                metadata.instrument,
                metadata.instrument_model,
                metadata.pick_up_setting,
                metadata.instrument_tuning,
                metadata.audio_effects,
                metadata.recording_date,
                metadata.recording_artist,
                metadata.instrument_body_material,
                metadata.instrument_string_material,
                metadata.composer,
                metadata.recording_source,
                id_recording,
            ),
        )

    def delete_idmt_smt_guitar_metadata(
        self,
        id_recording: str,
    ) -> Row | None:
        """Delete IDMT metadata.

        Args:
            id_recording: Recording ID.
        """

        return self._execute_one(
            query="""
                DELETE FROM idmt_smt_guitar_metadata
                WHERE id_recording = %s
                RETURNING *;
            """,
            params=(id_recording,),
        )

    # ===
    # AUDIO FILES (MINIO)
    # ===

    def insert_audio_file(
        self,
        id_recording: str,
        audio_type: AudioType,
        uri: str,
        sample_rate: int | None,
        channels: int | None,
    ) -> Row | None:
        """Insert audio file reference.

        Args:
            id_recording: Recording ID.
            audio_type: Type of audio.
            uri: MinIO object URI.
            sample_rate: Sample rate in Hz.
            channels: Number of channels.

        Returns:
            Inserted audio file row or None.
        """

        return self._execute_one(
            query="""
            INSERT INTO audio_files (
                id_recording,
                audio_type,
                uri,
                sample_rate,
                channels
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *;
            """,
            params=(id_recording, audio_type, uri, sample_rate, channels),
        )

    def select_audio_file(self, id_recording: str, audio_type: str) -> Row | None:
        """Fetch audio file metadata.

        Args:
            id_recording: Recording ID.
            audio_type: Audio type.

        Returns:
            Audio file metadata row if found, otherwise None.
        """

        return self._execute_one(
            query="""
                SELECT * FROM audio_files
                WHERE id_recording = %s AND audio_type = %s;
            """,
            params=(id_recording, audio_type),
        )

    def update_audio_file(
        self,
        id_audio: str,
        audio_type: AudioType,
        uri: str,
        sample_rate: int | None,
        channels: int | None,
    ) -> Row | None:
        """Update audio file.

        Args:
            id_audio: Audio ID.
            audio_type: Type of audio.
            uri: MinIO object URI.
            sample_rate: Sample rate in Hz.
            channels: Number of channels.

        Returns:
            Updated audio file row or None.
        """

        return self._execute_one(
            query="""
            UPDATE audio_files
            SET audio_type = %s,
                uri = %s,
                sample_rate = %s,
                channels = %s
            WHERE id_audio = %s
            RETURNING *;
            """,
            params=(audio_type, uri, sample_rate, channels, id_audio),
        )

    def delete_audio_file(self, id_audio: str) -> Row | None:
        """Delete audio file.

        Args:
            id_audio: Audio ID.
        """

        return self._execute_one(
            query="DELETE FROM audio_files WHERE id_audio = %s RETURNING *;",
            params=(id_audio,),
        )

    # ===
    # ANNOTATIONS (MINIO)
    # ===

    def insert_annotation_file(
        self,
        id_recording: str,
        annotation_type: AnnotationType,
        uri: str,
    ) -> Row | None:
        """Insert annotation file reference.

        Args:
            id_recording: Recording ID.
            annotation_type: Annotation type (jams, xml).
            uri: MinIO object URI.

        Returns:
            Inserted annotation row or None.
        """

        return self._execute_one(
            query="""
            INSERT INTO annotation_files (
                id_recording,
                annotation_type,
                uri
            )
            VALUES (%s, %s, %s)
            RETURNING *;
            """,
            params=(id_recording, annotation_type, uri),
        )

    def select_annotation_file(
        self, id_recording: str, annotation_type: AnnotationType
    ) -> Row | None:
        """Fetch annotation file metadata.

        Args:
            id_recording: Recording ID.
            annotation_type: Annotation type (jams, xml).

        Returns:
            Annotation file metadata row if found, otherwise None.
        """

        return self._execute_one(
            query="""
                SELECT * FROM annotation_files
                WHERE id_recording = %s AND annotation_type = %s;
            """,
            params=(id_recording, annotation_type),
        )

    def update_annotation_file(
        self,
        id_annotation: str,
        annotation_type: AnnotationType,
        uri: str,
    ) -> Row | None:
        """Update annotation file.

        Args:
            id_annotation: Annotation ID.
            annotation_type: Annotation type (jams, xml).
            uri: MinIO object URI.

        Returns:
            Inserted annotation row or None.
        """

        return self._execute_one(
            query="""
            UPDATE annotation_files
            SET annotation_type = %s,
                uri = %s
            WHERE id_annotation = %s
            RETURNING *;
            """,
            params=(annotation_type, uri, id_annotation),
        )

    def delete_annotation_file(
        self,
        id_annotation: str,
    ) -> Row | None:
        """Delete annotation file.

        Args:
            id_annotation: Annotation ID.
        """

        return self._execute_one(
            query="DELETE FROM annotation_files WHERE id_annotation = %s RETURNING *;",
            params=(id_annotation,),
        )
