def test_close_calls_storage_close_methods(pipeline, mock_storages):
    pipeline.close()

    mock_storages["mongo"].close.assert_called_once()
    mock_storages["postgres"].close.assert_called_once()


def test_close_does_not_call_minio_close(pipeline, mock_storages):
    pipeline.close()

    mock_storages["minio"].close.assert_not_called()


def test_close_is_idempotent(pipeline, mock_storages):
    pipeline.close()
    pipeline.close()

    assert mock_storages["mongo"].close.call_count == 2
    assert mock_storages["postgres"].close.call_count == 2
