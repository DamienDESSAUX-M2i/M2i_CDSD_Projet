import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from src.loaders import AbstractLoader


class XMLLoader(AbstractLoader):
    """
    XML file loader.
    Load an ElementTree to a XML file using the xml backend.
    """

    def load(self, tree: ET.ElementTree, file_path: Path, **kwargs: Any) -> None:
        """Load an ElementTree to a XML file.

        Args:
            tree (etree.ElementTree): ElementTree to load.
            file_path (Path): Destination path of the XML file. Must end with '.xml'.
            **kwargs: Additional keyword arguments forwarded to 'xml.etree.ElementTree.ElementTree.write'.

        Raises:
            TypeError: If inputs are invalid type.
            ValueError: If the file path is invalid.
            RuntimeError: If writing the XML file fails.
        """
        self._load_validate_inputs(
            tree=tree,
            file_path=file_path,
        )
        self._ensure_parent_directory(parent_directory_path=file_path.parent)

        try:
            self.logger.info(
                "Writing XML file",
                extra={
                    "path": str(file_path),
                },
            )
            tree.write(
                file_or_filename=file_path,
                encoding="utf-8",
                xml_declaration=True,
                **kwargs,
            )
            self.logger.info(
                "XML file successfully written",
                extra={
                    "path": str(file_path),
                },
            )
        except Exception as exc:
            self.logger.exception(
                "Failed to write XML file",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("XML writing failed") from exc

    def _load_validate_inputs(
        self,
        tree: ET.ElementTree,
        file_path: Path,
    ) -> None:
        """Raise an exception if an input is invalid."""
        if not isinstance(tree, ET.ElementTree):
            raise TypeError("tree must be an xml.etree.ElementTree.ElementTree.")
        if not isinstance(file_path, Path):
            raise TypeError("file_path must be a pathlib.Path.")
        if not file_path.suffix.lower() == ".xml":
            raise ValueError("file_path must end with '.xml'.")
