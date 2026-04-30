import pytest


def test_validate_file_path_with_non_path(extractor):
    with pytest.raises(ValueError, match="file_path must be a pathlib.Path"):
        extractor._validate_file_path("not_a_path")


def test_validate_file_path_file_not_found(extractor, non_existing_file):
    with pytest.raises(FileNotFoundError, match="File not found"):
        extractor._validate_file_path(non_existing_file)


def test_validate_file_path_invalid_suffix(extractor, existing_file):
    with pytest.raises(ValueError, match="Invalid file extension"):
        extractor._validate_file_path(existing_file, suffix=".csv")


def test_validate_file_path_valid_without_suffix(extractor, existing_file):
    # Should not raise
    extractor._validate_file_path(existing_file)


def test_validate_file_path_valid_with_correct_suffix(extractor, existing_file):
    extractor._validate_file_path(existing_file, suffix=".txt")
