import logging
from datetime import datetime, timezone

from config import mongo_config
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from src.models import BeatPositionDict, ChordDict, NoteMidiDict, PitchContourDict
from src.utils import LOGGER_NAME


class MongoStorage:
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.client = self._get_client()
        self.db = self.client[mongo_config.dbname]
        self.pitch_contour = self.db[mongo_config.collection_pitch_contour]
        self.note_midi = self.db[mongo_config.collection_note_midi]
        self.beat_position = self.db[mongo_config.collection_beat_position]
        self.chord = self.db[mongo_config.collection_chord]
        self.collections = {
            "pitch_contour": self.pitch_contour,
            "note_midi": self.note_midi,
            "beat_position": self.beat_position,
            "chord": self.chord,
        }

    def _get_client(self) -> MongoClient:
        self.logger.info("Connexion to the Mongo service...")
        client = MongoClient(mongo_config.connection_string)
        self.logger.info("Connecting to the Mongo service")
        return client

    def _insert_document(self, collection_name: str, document: dict) -> str | None:
        """Insert or update a document. The update is based on 'dataset_name' and 'title'.

        Args:
            collection_name (str): Name of the collection in which to insert the document.
            document (dict): Dictionary representing document.

        Returns:
            str | None: "inserted", "updated" or None
        """
        try:
            if document.get("dataset_name", None) is None:
                raise RuntimeError("'dataset_name' key does not exist")

            if document.get("title", None) is None:
                raise RuntimeError("'title' key does not exist")

            document["inserted_at"] = datetime.now(timezone.utc)

            # Upsert based on dataset_name and title
            result = self.collections[collection_name].update_one(
                {"dataset_name": document["dataset_name"], "title": document["title"]},
                {"$set": document},
                upsert=True,
            )

            if result.did_upsert:
                self.logger.debug(
                    f"Document inserted: dataset_name={document['dataset_name']}, title={document['title']}"
                )
                return "inserted"

            self.logger.debug(
                f"Document updated: dataset_name={document['dataset_name']}, title={document['title']}"
            )
            return "updated"

        except PyMongoError as exception:
            self.logger.error(f"Document insert failed: {exception}")
            return None

    def insert_pitch_contour(
        self, pitch_contour: dict[str, str | list[PitchContourDict]]
    ) -> str | None:
        """Insert or update a pitch contour. The update is based on 'dataset_name' and 'title'.

        Args:
            pitch_contour (PitchContourDict): Dictionary representing pitch contour. {dataset_name: str, title: str, pitch_contour: list[PitchContourDict]}

        Returns:
            str | None: "inserted", "updated" or None
        """
        return self._insert_document(
            collection_name=mongo_config.collection_pitch_contour,
            document=pitch_contour,
        )

    def insert_note_midi(
        self, note_midi: dict[str, str | list[NoteMidiDict]]
    ) -> str | None:
        """Insert or update a note midi. The update is based on 'dataset_name' and 'title'.

        Args:
            note_midi (NoteMidiDict): Dictionary representing note midi. {dataset_name: str, title: str, note_midi: list[NoteMidiDict]}

        Returns:
            str | None: "inserted", "updated" or None
        """
        return self._insert_document(
            collection_name=mongo_config.collection_note_midi,
            document=note_midi,
        )

    def insert_beat_position(
        self, beat_position: dict[str, str | list[BeatPositionDict]]
    ) -> str | None:
        """Insert or update a beat position. The update is based on 'dataset_name' and 'title'.

        Args:
            beat_position (BeatPositionDict): Dictionary representing beat position. {dataset_name: str, title: str, beat_position: list[BeatPositionDict]}

        Returns:
            str | None: "inserted", "updated" or None
        """
        return self._insert_document(
            collection_name=mongo_config.collection_beat_position,
            document=beat_position,
        )

    def insert_chord(self, chord: dict[str, str | list[ChordDict]]) -> str | None:
        """Insert or update a chord. The update is based on 'dataset_name' and 'title'.

        Args:
            chord (ChordDict): Dictionary representing chord. {dataset_name: str, title: str, chord: list[ChordDict]}

        Returns:
            str | None: "inserted", "updated" or None
        """
        return self._insert_document(
            collection_name=mongo_config.collection_chord,
            document=chord,
        )

    def _insert_many_documents(
        self, collection_name: str, documents: list[dict]
    ) -> dict:
        """Insert or update many documents. The update is based on 'dataset_name' and 'title'.

        Args:
            collection_name (str): Name of the collection in which to insert the document.
            documents (list[dict]): List of dictionaries representing documents.

        Returns:
            dict: Numbers of inserted pitch_contours, updated pitch_contours and errors.
            {
                "inserted": (int) Number of documents inserted,
                "updated": (int) Number of documents updated,
                "errors": (int) Number of errors
            }
        """
        results = {"inserted": 0, "updated": 0, "errors": 0}

        for document in documents:
            result = self._insert_document(
                collection_name=collection_name, document=document
            )
            match result:
                case "updated":
                    results["updated"] += 1
                case "inserted":
                    results["inserted"] += 1
                case _:
                    results["errors"] += 1

        return results

    def find_document(
        self,
        collection_name: str,
        filter: dict = {},
        projection: dict = None,
        sort: list = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict]:
        """Query the collection.

        Args:
            collection_name (str): Name of the collection in which to find the document.
            filter (dict, optional): Query. Defaults to {}.
            projection (dict, optional): Projection. Defaults to None.
            sort (list, optional): Sorting documents. Defaults to None.
            limit (int, optional): Limit number of documents. Defaults to 100.
            skip (int, optional): Skip documents. Defaults to 0.

        Returns:
            list[dict]: List of documents.
        """
        cursor = self.collections[collection_name].find(
            filter=filter, projection=projection
        )

        if sort:
            cursor = cursor.sort(sort)

        return list(cursor.skip(skip).limit(limit))

    def aggregate_documents(
        self, collection_name: str, pipeline: list[dict]
    ) -> list[dict]:
        """Perform an aggregation on the collection.

        Args:
            collection_name (str): Name of the collection in which to aggregate documents.
            pipeline (list[dict]): List of aggregation pipeline stage.

        Returns:
            list[dict]: List of documents.
        """
        return list(self.collections[collection_name].aggregate(pipeline))

    def count_documents(self, collection_name: str, filter: dict = {}) -> int:
        """Count the number of documents that match the filter.

        Args:
            collection_name (str): Name of the collection in which to count documents.
            filter (dict, optional): Query. Defaults to {}.

        Returns:
            int: Number of documents matching the filter.
        """
        return self.collections[collection_name].count_documents(filter)

    def delete_document(self, collection_name: str, filter: dict = {}) -> int:
        """Delete documents that match the filter.

        Args:
            collection_name (str): Name of the collection in which to delete documents.
            filter (dict, optional): Query. Defaults to {}.

        Returns:
            int: Number of documents deleted.
        """
        deleted_result = self.collections[collection_name].delete_many(filter=filter)

        self.logger.warning(f"Documents deleted: {deleted_result.deleted_count}")

        return deleted_result.deleted_count

    def close(self) -> None:
        """Close the connection"""
        self.client.close()
        self.logger.info("Mongo connection closed")
