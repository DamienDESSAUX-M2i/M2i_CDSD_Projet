import logging
from datetime import datetime, timezone

from config import mongo_config
from pymongo import ASCENDING, DESCENDING, TEXT, MongoClient
from pymongo.errors import PyMongoError

from src.utils import LOGGER_NAME


class MongoStorage:
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.client = self._get_client()
        self.db = self.client[mongo_config.dbname]
        self.collection = self.db["collection"]
        # self._create_indexes()

    def _get_client(self) -> MongoClient:
        self.logger.info("Attempting to connect to the Mongo service.")
        client = MongoClient(mongo_config.connection_string)
        self.logger.info("Connecting to the Mongo service.")
        return client

    def _create_indexes(self) -> None:
        """Create indexes to optimize queries."""
        self.collection.create_index([("uuid", ASCENDING)], unique=True)
        self.collection.create_index([("string", TEXT)])
        self.collection.create_index([("int_or_float", ASCENDING)])
        self.collection.create_index([("datetime", DESCENDING)])
        self.logger.info("Mongodb indexes created")

    # CRUD

    def insert_document(self, document: dict) -> str | None:
        """Insert or update a document.

        Args:
            document (dict): Dictionary representing the document.

        Returns:
            str | None: "inserted", "updated" or None
        """
        try:
            document["inserted_at"] = datetime.now(timezone.utc)

            # Upsert based on _id
            result = self.collection.update_one(
                {"_id": document["_id"]},
                {"$set": document},
                upsert=True,
            )

            if result.did_upsert:
                self.logger.debug(f"Document inserted: {document['_id']}")
                return "inserted"

            self.logger.debug(f"Document updated: {document['_id']}")
            return "updated"

        except PyMongoError as e:
            self.logger.error(f"Document insert failed: {e}")
            return None

    def insert_documents(self, documents: list[dict]) -> dict:
        """Insert or update many documents.

        Args:
            documents (list[dict]): List of dictionaries representing documents.

        Returns:
            dict: Numbers of inserted documents, updated documents and erros.
            {
                "inserted": (int) Number of documents inserted,
                "updated": (int) Number of documents updated,
                "errors": (int) Number of errors
            }
        """
        results = {"inserted": 0, "updated": 0, "errors": 0}

        for document in documents:
            result = self.insert_document(document)
            match result:
                case "updated":
                    results["updated"] += 1
                case "inserted":
                    results["inserted"] += 1
                case _:
                    results["errors"] += 1

        return results

    def find_documents(
        self,
        filter: dict = {},
        projection: dict = None,
        sort: list = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict]:
        """Query the collection.

        Args:
            filter (dict, optional): Query. Defaults to {}.
            projection (dict, optional): Projection. Defaults to None.
            sort (list, optional): Sorting documents. Defaults to None.
            limit (int, optional): Limit number of documents. Defaults to 100.
            skip (int, optional): Skip documents. Defaults to 0.

        Returns:
            list[dict]: List of documents.
        """
        cursor = self.collection.find(filter=filter, projection=projection)

        if sort:
            cursor = cursor.sort(sort)

        return list(cursor.skip(skip).limit(limit))

    def aggregate_documents(self, pipeline: list[dict]) -> list[dict]:
        """Perform an aggregation on the collection.

        Args:
            pipeline (list[dict]): List of aggregation pipeline stage.

        Returns:
            list[dict]: List of documents.
        """
        return list(self.collection.aggregate(pipeline))

    def count_documents(self, filter: dict = {}) -> int:
        """Count the number of documents that match the filter.

        Args:
            filter (dict, optional): Query. Defaults to {}.

        Returns:
            int: Number of documents matching the filter.
        """
        return self.collection.count_documents(filter)

    def delete_documents(self, filter: dict = {}) -> int:
        """Delete documents that match the filter.

        Args:
            filter (dict, optional): Query. Defaults to {}.

        Returns:
            int: Number of documents deleted.
        """
        deleted_result = self.collection.delete_many(filter=filter)

        self.logger.warning(f"Documents deleted: {deleted_result.deleted_count}")

        return deleted_result.deleted_count

    def close(self) -> None:
        """Close the connection"""
        self.client.close()
        self.logger.info("Mongo connection closed.")
