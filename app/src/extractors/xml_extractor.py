import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.extractors import AbstractExtractor
from src.models import (
    AmpChannel,
    Event,
    ExcitationStyle,
    ExpressionStyle,
    GuitarBrand,
    GuitarModel,
    GuitarType,
    Loudness,
    MicroPosition,
    MicroType,
    XMLAnnotation,
    XMLMetadata,
)
from src.transformers import ElementTreeWrapper

DIRECTORY_NAME_REGEX = re.compile(
    r"^(?P<instrument_model>(Fender\ Strat|Ibanez\ Power\ Strat))\ (?P<amp_channel>Clean)\ (?P<pick_up_setting>Neck|Bridge|Bridge\+Neck)\ (?P<pick_up_type>SC|HU)\ ?(?P<polyphony>(?:Chords)?)$",
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
            self.logger.info(
                "Reading XML file",
                extra={
                    "path": str(file_path),
                },
            )
            tree = ET.parse(file_path, **kwargs)
            self.logger.info(
                "XML extraction completed",
                extra={
                    "path": str(file_path),
                },
            )
            return tree
        except Exception as exc:
            self.logger.exception(
                "Failed to load XML file.",
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("XML extraction failed") from exc

    def extract_metadata(
        self,
        tree: ET.ElementTree,
        dataset_name: str = "IDMT_SMT_Guitar",
        directory_name: str | None = None,
    ) -> XMLMetadata:
        """Extract metadata from an ET.ElementTree.

        Args:
            tree (ET.ElementTree): An ET.ElementTree.
            dataset_name (str) : Name of the dataset. Default "IDMT_SMT_Guitar".
            directory_name (str) : Name of the directory. Used for "dataset1".

        Raises:
            RunTimeError: If XML metadata extraction fails.

        Returns:
            XMLMetadata: Metadata extracted from a ET.ElementTree.
        """
        try:
            self.logger.info("Extracting XML metadata...")

            tree_wrapper = ElementTreeWrapper(tree=tree)
            audio_file_name = tree_wrapper.get_value(
                path="globalParameter/audioFileName"
            )
            if not audio_file_name:
                raise RuntimeError("XML title is missing")

            audio_file_name = audio_file_name.replace(".wav", "").replace("\\", "")

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

            # Parse directory_name
            if directory_name:
                directory_name_match = DIRECTORY_NAME_REGEX.match(directory_name)
                if not directory_name_match:
                    raise RuntimeError(
                        f"Directory name format does not match: {directory_name}"
                    )

                instrument_model = directory_name_match.group("instrument_model")
                # amp_channel = directory_name_match.group("amp_channel")
                pick_up_setting = directory_name_match.group("pick_up_setting")
                # pick_up_type = directory_name_match.group("pick_up_type")
                # polyphony = directory_name_match.group("polyphony")

            # cast
            try:
                pass
            except ValueError as exception:
                raise RuntimeError(f"enum cast has failed") from exception

            self.logger.info(
                f"XML metadata extracted: {audio_file_name}",
                extra={"audio_file_name": audio_file_name},
            )
            return XMLMetadata(
                dataset_name=dataset_name,
                audio_file_name=audio_file_name,
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
            self.logger.error("XML metadata extraction has failed", exc_info=True)
            raise RuntimeError("XML metadata extraction has failed.") from exception

    def extract_annotation(
        self, tree: ET.ElementTree, dataset_name: str = "IDMT_SMT_Guitar"
    ) -> XMLAnnotation:
        """Extract annotation from a ET.ElementTree.

        Args:
            tree (ET.ElementTree): An ET.ElementTree.
            dataset_name (str) : Name of the dataset. Default "IDMT_SMT_Guitar".

        Raises:
            RunTimeError: If XML annotation extraction fails.

        Returns:
            XMLAnnotation: Annotations extracted from a ET.ElementTree.
        """
        try:
            self.logger.info("Extracting XML annotation...")

            tree_wrapper = ElementTreeWrapper(tree)
            title = tree_wrapper.get_value(path="globalParameter/audioFileName")
            if not title:
                raise RuntimeError("XML title is missing")

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
                    raise RuntimeError(
                        f"Event cast has failed: {event.__dir__}"
                    ) from exception

            self.logger.info(
                "XML annotation extracted",
                extra={
                    "transcription": len(events_processed),
                },
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
            self.logger.error("XML annotation extraction has failed", exc_info=True)
            raise RuntimeError("XML annotation extraction has failed") from exception
