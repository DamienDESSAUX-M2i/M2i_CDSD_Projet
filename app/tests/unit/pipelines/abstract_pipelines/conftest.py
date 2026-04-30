from unittest.mock import MagicMock

import pytest
from src.pipelines.abstract_pipeline import AbstractPipeline


class ConcretePipeline(AbstractPipeline):
    def run(self):
        pass


@pytest.fixture
def mock_storages(mocker):
    mock_minio = MagicMock()
    mock_mongo = MagicMock()
    mock_postgres = MagicMock()

    mocker.patch(
        "src.pipelines.abstract_pipeline.MinIOStorage", return_value=mock_minio
    )
    mocker.patch(
        "src.pipelines.abstract_pipeline.MongoStorage", return_value=mock_mongo
    )
    mocker.patch(
        "src.pipelines.abstract_pipeline.PostgresStorage", return_value=mock_postgres
    )

    return {
        "minio": mock_minio,
        "mongo": mock_mongo,
        "postgres": mock_postgres,
    }


@pytest.fixture
def pipeline(mock_storages):
    return ConcretePipeline()
