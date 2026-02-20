import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pandas as pd

from src.extractors import AbstractExtractor
from src.models import (
    Event,
    ExcitationStyle,
    ExpressionStyle,
    Loudness,
    XMLAnnotation,
    XMLMetadata,
)
from src.transformers import ElementTreeWrapper

DIRECTORY_NAME_REGEX = re.compile(
    r"(?P<instrument_model>(Fender\ Strat|Ibanez\ Power\ Strat))\ (?P<amp_channel>Clean)\ (?P<pick_up_setting>Neck|Bridge|Bridge\+Neck)\ (?P<pick_up_type>SC|HU)\ ?(?P<polyphony>(?:Chords)?)",
    re.VERBOSE,
)


class XMLExtractor(AbstractExtractor):
    """
    XML file extractor.
    Extract data from a XML file using the xml backend.
    """

    def read(self, file_path: Path, **kwargs: Any) -> ET.ElementTree:
        """Load data from a XML file.

        Args:
            file_path (Path): Path to the XML file. Must end with '.xml'.
            **kwargs: Additional keyword arguments forwarded to 'xml.etree.ElementTree.ElementTree.parse'.

        Raises:
            FileNotFoundError: If the XML file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the XML file fails.

        Returns:
            ET.Element: ElementTree loaded from the XML file.
        """
        self._validate_file_path(file_path=file_path, suffix=".xml")

        try:
            self.logger.debug(f"Reading XML file: path={file_path.as_posix()}")
            tree = ET.parse(file_path, **kwargs)
            self.logger.debug("XML extraction completed")
            return tree
        except Exception as exception:
            self.logger.error(f"Failed to load XML file: {exception}")
            raise RuntimeError("XML extraction failed") from exception

    def enrich_with_directory_name(
        self, xml_metadata: XMLMetadata, xml_file_path: Path
    ) -> XMLMetadata:
        """Enrich a XMLMetadata with information content into directory name.

        Args:
            xml_metadata (XMLMetadata): XMLMetadata to enriched.
            xml_file_path (Path): Path of the XML file.

        Returns:
            XMLMetadata: XMLMetadata enriched.
        """
        self.logger.debug(f"Enrich XMLMedata: title={xml_metadata.title}")

        if "dataset1" in xml_file_path.as_posix():
            directory_name_search = DIRECTORY_NAME_REGEX.search(
                xml_file_path.as_posix()
            )
            if not directory_name_search:
                self.logger.error(
                    f"Directory name format does not match: {xml_file_path.as_posix()}"
                )
                raise RuntimeError("Directory name format does not match")

            xml_metadata.instrument_model = directory_name_search.group(
                "instrument_model"
            )
            # xml_metadata.amp_channel = directory_name_search.group("amp_channel")
            xml_metadata.pick_up_setting = directory_name_search.group(
                "pick_up_setting"
            )
            # xml_metadata.pick_up_type = directory_name_search.group("pick_up_type")
            # xml_metadata.polyphony = directory_name_search.group("polyphony")

        self.logger.debug("XMLMetadata enriched")
        return xml_metadata

    def _get_title(self, tree_wrapper: ElementTreeWrapper) -> str:
        """Extract and formate title from XML file.

        Args:
            tree_wrapper (ElementTreeWrapper): XML file loaded.

        Returns:
            str: title.
        """
        title = tree_wrapper.get_value(path="globalParameter/audioFileName")
        if not title:
            raise RuntimeError("XML title is missing")

        title = title.replace(".wav", "").replace("\\", "")

        return title

    def extract_metadata(
        self,
        tree: ET.ElementTree,
        title: str,
        dataset_name: str = "IDMT_SMT_Guitar",
    ) -> XMLMetadata:
        """Extract metadata from an ET.ElementTree.

        Args:
            tree (ET.ElementTree): An ET.ElementTree.
            title (str): File name.
            dataset_name (str): Name of the dataset. Default "IDMT_SMT_Guitar".

        Raises:
            RunTimeError: If XML metadata extraction fails.

        Returns:
            XMLMetadata: Metadata extracted from a ET.ElementTree.
        """
        try:
            self.logger.debug("Extracting XML metadata...")

            title = title.replace(".wav", "").replace("\\", "")

            tree_wrapper = ElementTreeWrapper(tree=tree)

            instrument = tree_wrapper.get_value(path="globalParameter/instrument")
            instrument_model = tree_wrapper.get_value(
                path="globalParameter/instrumentModel"
            )
            pick_up_setting = tree_wrapper.get_value(
                path="globalParameter/pickUpSetting"
            )
            instrument_tuning = tree_wrapper.get_value(
                path="globalParameter/instrumentTuning"
            )
            audio_effects = tree_wrapper.get_value(path="globalParameter/audioFX")
            recording_date = tree_wrapper.get_value(
                path="globalParameter/recordingDate"
            )
            recording_artist = tree_wrapper.get_value(
                path="globalParameter/recordingArtist"
            )
            instrument_body_material = tree_wrapper.get_value(
                path="globalParameter/instrumentBodyMaterial"
            )
            instrument_string_material = tree_wrapper.get_value(
                path="globalParameter/instrumentStringMaterial"
            )
            composer = tree_wrapper.get_value(path="globalParameter/composer")
            recording_source = tree_wrapper.get_value(
                path="globalParameter/recordingSource"
            )
            # pick_up_type = None
            # amp_channel = None
            # polyphony = None

            # cast
            try:
                pass
            except ValueError as exception:
                raise RuntimeError("enum cast has failed") from exception

            self.logger.debug(f"XML metadata extracted: title={title}")
            return XMLMetadata(
                dataset_name=dataset_name,
                title=title,
                instrument=instrument,
                instrument_model=instrument_model,
                pick_up_setting=pick_up_setting,
                # pick_up_type=pick_up_type,
                instrument_tuning=instrument_tuning,
                # amp_channel=amp_channel,
                audio_effects=audio_effects,
                recording_date=recording_date,
                recording_artist=recording_artist,
                instrument_body_material=instrument_body_material,
                instrument_string_material=instrument_string_material,
                composer=composer,
                recording_source=recording_source,
                # polyphony=bool(polyphony),
            )
        except Exception as exception:
            self.logger.error(f"XML metadata extraction has failed: {exception}")
            raise RuntimeError("XML metadata extraction has failed") from exception

    def extract_annotation(
        self, tree: ET.ElementTree, title: str, dataset_name: str = "IDMT_SMT_Guitar"
    ) -> XMLAnnotation:
        """Extract annotation from a ET.ElementTree.

        Args:
            tree (ET.ElementTree): An ET.ElementTree.
            title (str): File name.
            dataset_name (str): Name of the dataset. Default "IDMT_SMT_Guitar".

        Raises:
            RunTimeError: If XML annotation extraction fails.

        Returns:
            XMLAnnotation: Annotations extracted from a ET.ElementTree.
        """
        try:
            self.logger.debug("Extracting XML annotation...")

            title = title.replace(".wav", "").replace("\\", "")

            tree_wrapper = ElementTreeWrapper(tree)

            events_raw = tree_wrapper.to_list(
                element=tree_wrapper.get_element("transcription")
            )
            if events_raw == []:
                raise RuntimeError("XML annotations is missing")

            events_processed: list[Event] = []
            for event in events_raw:
                try:
                    pitch_str = event.get("pitch", None)
                    onset_str = event.get("onsetSec", None)
                    offset_str = event.get("offsetSec", None)
                    fret_number_str = event.get("fretNumber", None)
                    string_number_str = event.get("stringNumber", None)
                    excitation_style_str = event.get("excitationStyle", None)
                    expression_style_str = event.get("expressionStyle", None)
                    loudness_str = event.get("loudness", None)
                    modulation_frequency_range_str = event.get(
                        "modulationFrequencyRange", None
                    )
                    modulation_frequency_str = event.get("modulationFrequency", None)

                    events_processed.append(
                        Event(
                            pitch=int(pitch_str) if pitch_str else None,
                            onset=float(onset_str) if onset_str else None,
                            offset=float(offset_str) if offset_str else None,
                            fret_number=int(fret_number_str)
                            if fret_number_str
                            else None,
                            string_number=int(string_number_str)
                            if string_number_str
                            else None,
                            excitation_style=ExcitationStyle(excitation_style_str)
                            if excitation_style_str
                            else None,
                            expression_style=ExpressionStyle(expression_style_str)
                            if expression_style_str
                            and (expression_style_str in ExpressionStyle)
                            else None,
                            loudness=Loudness(loudness_str) if loudness_str else None,
                            modulation_frequency_range=float(
                                modulation_frequency_range_str
                            )
                            if modulation_frequency_range_str
                            else None,
                            modulation_frequency=float(modulation_frequency_str)
                            if modulation_frequency_str
                            else None,
                        )
                    )
                except ValueError as exception:
                    self.logger.error(f"Event cast has failed: {exception}")
                    raise RuntimeError("Event cast has failed") from exception

            self.logger.debug(
                f"XML annotation extracted: transcription={len(events_processed)}"
            )
            return XMLAnnotation(
                dataset_name=dataset_name,
                title=title,
                transcription=pd.DataFrame(
                    [event.to_dict() for event in events_processed],
                    columns=[
                        "pitch",
                        "onset",
                        "offset",
                        "fret_number",
                        "string_number",
                        "excitation_style",
                        "expression_style",
                        "loudness",
                        "modulation_frequency_range",
                        "modulation_frequency",
                    ],
                ),
            )
        except Exception as exception:
            self.logger.error(f"XML annotation extraction has failed: {exception}")
            raise RuntimeError("XML annotation extraction has failed") from exception
