from pathlib import Path

import pytest
from src.extractors.abstract_extractor import AbstractExtractor


class ConcreteExtractor(AbstractExtractor):
    pass


@pytest.fixture
def extractor():
    return ConcreteExtractor()


@pytest.fixture
def existing_file(tmp_path: Path):
    file = tmp_path / "test.txt"
    file.write_text("content")
    return file


@pytest.fixture
def non_existing_file(tmp_path: Path):
    return tmp_path / "missing.txt"
