import re
from pathlib import Path
from typing import Any

import jams
import pandas as pd

from src.extractors import AbstractExtractor
from src.models import (
    SCALE_MAP,
    BeatPositionDict,
    ChordDict,
    JAMSAnnotation,
    JAMSMetadata,
    Mode,
    NoteMidiDict,
    PitchContourDict,
    PlayingVersion,
    Scale,
    Style,
)

TITLE_REGEX = re.compile(
    r"^(?P<guitarist_id>\d{2})_(?P<style>[A-Za-z0-9]+)-(?P<tempo>\d+)-(?P<scale>[A-G](?:b|\#)?)_(?P<playing_version>[A-Za-z]+)$",
    re.VERBOSE,
)


class JAMSExtractor(AbstractExtractor):
    """
    JAMS file extractor.
    Extract data from a JAMS file using jams backend.
    """

    def read(self, file_path: Path, **kwargs: Any) -> jams.JAMS:
        """Load data from a JAMS file.

        Args:
            file_path (Path): Path of the JAMS file. Must end with '.jams'.
            **kwargs: Additional keyword arguments forwarded to 'jams.load'.

        Raises:
            FileNotFoundError: If the JAMS file does not exist.
            ValueError: If inputs are invalid.
            RuntimeError: If reading the JAMS file fails.

        Returns:
            jams.JAMS: jams.JAMS loaded from the JAMS file.
        """
        self._validate_file_path(file_path=file_path, suffix=".jams")

        try:
            self.logger.info(
                "Reading JAMS file",
                extra={
                    "path": str(file_path),
                },
            )
            jam = jams.load(path_or_file=str(file_path), **kwargs)
            self.logger.info(
                "JAMS extraction completed",
                extra={
                    "path": str(file_path),
                    "metadata": jam.file_metadata,
                },
            )
            return jam
        except Exception as exception:
            self.logger.exception(
                "Failed to load JAMS file.",
                exc_info=exception,
                extra={
                    "path": str(file_path),
                },
            )
            raise RuntimeError("JAMS extraction failed") from exception

    def extract_metadata(
        self, jam: jams.JAMS, dataset_name: str = "GuitarSet"
    ) -> JAMSMetadata:
        """Extract metadata from a jams.JAMS.

        Args:
            jam (jams.JAMS): A jams.JAMS.
            dataset_name (str) : Name of the dataset. Default "GuitarSet".

        Raises:
            RunTimeError: If JAMS metadata extraction fails.

        Returns:
            JAMSMetadata: Metadata extracted from a jams.JAMS.
        """
        try:
            self.logger.info("Extracting JAMS metadata...")

            title = jam.file_metadata.title
            if not title:
                raise RuntimeError("JAMS title is missing")

            title_match = TITLE_REGEX.match(title)
            if not title_match:
                raise RuntimeError(f"Invalid title format: {title}")

            guitarist_id = int(title_match.group("guitarist_id"))
            style_str = title_match.group("style")
            tempo = int(title_match.group("tempo"))
            scale_str = title_match.group("scale")
            playing_version_str = title_match.group("playing_version")

            mode_str = None
            for annotation in jam.annotations:
                if annotation.namespace == "key_mode":
                    try:
                        mode_str = annotation.data[0].value.split(":")[1]
                    except (IndexError, ValueError) as exception:
                        raise RuntimeError("Invalid key_mode annotation") from exception
                    break

            if mode_str is None:
                raise RuntimeError("No key_mode annotation found")

            duration = float(jam.file_metadata.duration)

            # enum cast
            try:
                style = Style(style_str)
                scale = Scale(SCALE_MAP.get(scale_str, scale_str))
                mode = Mode(mode_str)
                playing_version = PlayingVersion(playing_version_str)
            except ValueError as exception:
                raise RuntimeError(
                    f"enum cast has failed: style={style_str}, scale={scale_str}, mode={mode_str}, playing_version={playing_version_str}"
                ) from exception

            self.logger.info("JAMS metadata extracted", extra={"title": title})
            return JAMSMetadata(
                dataset_name=dataset_name,
                guitarist_id=guitarist_id,
                title=title,
                style=style,
                tempo=tempo,
                scale=scale,
                mode=mode,
                playing_version=playing_version,
                duration=duration,
            )
        except Exception as exception:
            self.logger.error("JAMS metadata extraction has failed", exc_info=True)
            raise RuntimeError("JAMS metadata extraction has failed.") from exception

    def _extract_pitch_contour(
        self,
        annotation: jams.core.Annotation,
        data_source: str,
    ) -> list[PitchContourDict]:
        """Extract pitch contour annotation from a jams.core.Annotation

        Args:
            annotation (jams.core.Annotation): Pitch contour annotation.
            data_source (str): Source of annotation data.

        Returns:
            list[PitchContourDict]: Pitch contour annotation extracted.
        """
        return [
            {
                "data_source": data_source,
                "time": data.time,
                "frequency": data.value.get("frequency", 0.0),
            }
            for data in annotation.data
        ]

    def _extract_note_midi(
        self,
        annotation: jams.core.Annotation,
        data_source: str,
    ) -> list[NoteMidiDict]:
        """Extract note midi annotation from a jams.core.Annotation

        Args:
            annotation (jams.core.Annotation): Note midi annotation.
            data_source (str): Source of annotation data.

        Returns:
            list[NoteMidiDict]: Note midi annotation extracted.
        """
        return [
            {
                "data_source": data_source,
                "time": data.time,
                "duration": data.duration,
                "value": data.value,
            }
            for data in annotation.data
        ]

    def _extract_beat_position(
        self, annotation: jams.core.Annotation
    ) -> list[BeatPositionDict]:
        """Extract beat position annotation from a jams.core.Annotation

        Args:
            dataset_name (str): Name of the data set.
            title(str): Title extract from jams.JAMS.file_metadata.
            annotation (jams.core.Annotation): Beat position annotation.

        Returns:
            list[BeatPositionDict]: Beat position annotation extracted.
        """
        return [
            {
                "time": data.time,
                "position": data.value["position"],
                "beat_units": data.value["beat_units"],
                "measure": data.value["measure"],
                "num_beats": data.value["num_beats"],
            }
            for data in annotation.data
        ]

    def _extract_chord(self, annotation: jams.core.Annotation) -> list[ChordDict]:
        """Extract chord annotation from a jams.core.Annotation

        Args:
            annotation (jams.core.Annotation): Chord annotation.

        Returns:
            list[ChordDict]: Chord annotation extracted.
        """
        return [
            {
                "time": data.time,
                "duration": data.duration,
                "value": data.value,
            }
            for data in annotation.data
        ]

    def extract_annotation(
        self, jam: jams.JAMS, dataset_name: str = "GuitarSet"
    ) -> JAMSAnnotation:
        """Extract annotation from a jams.JAMS.

        Args:
            jam (jams.JAMS): A jams.JAMS.

        Raises:
            RunTimeError: If JAMS annotation extraction fails.

        Returns:
            JAMSAnnotation: Annotations extracted from a jams.JAMS.
        """
        try:
            self.logger.info("Extracting JAMS annotation...")

            pitch_contour: list[PitchContourDict] = []
            note_midi: list[NoteMidiDict] = []
            beat_position: list[BeatPositionDict] = []
            chord: list[ChordDict] = []

            title = jam.file_metadata.title
            if not title:
                raise RuntimeError("JAMS title is missing")

            annotations = jam.annotations
            if not annotations:
                raise RuntimeError("JAMS annotations is missing")

            for annotation in annotations:
                data_source = annotation.annotation_metadata.data_source
                namespace = annotation.namespace
                if namespace == "pitch_contour":
                    pitch_contour.extend(
                        self._extract_pitch_contour(
                            annotation=annotation,
                            data_source=data_source,
                        )
                    )
                elif namespace == "note_midi":
                    note_midi.extend(
                        self._extract_note_midi(
                            annotation=annotation,
                            data_source=data_source,
                        )
                    )
                elif namespace == "beat_position":
                    beat_position.extend(
                        self._extract_beat_position(annotation=annotation)
                    )
                elif (namespace == "chord") and (data_source == ""):
                    chord.extend(self._extract_chord(annotation=annotation))

            self.logger.info(
                "JAMS annotation extracted",
                extra={
                    "pitch_contour": len(pitch_contour),
                    "note_midi": len(note_midi),
                    "beat_position": len(beat_position),
                    "chord": len(chord),
                },
            )
            return JAMSAnnotation(
                dataset_name=dataset_name,
                title=title,
                pitch_contour=pd.DataFrame(
                    pitch_contour,
                    columns=[
                        "data_source",
                        "time",
                        "frequency",
                    ],
                ),
                note_midi=pd.DataFrame(
                    note_midi,
                    columns=[
                        "data_source",
                        "time",
                        "duration",
                        "value",
                    ],
                ),
                beat_position=pd.DataFrame(
                    beat_position,
                    columns=[
                        "time",
                        "position",
                        "beat_units",
                        "measure",
                        "num_beats",
                    ],
                ),
                chord=pd.DataFrame(
                    chord,
                    columns=[
                        "time",
                        "duration",
                        "value",
                    ],
                ),
            )
        except Exception as exception:
            self.logger.error("JAMS annotation extraction has failed", exc_info=True)
            raise RuntimeError("JAMS annotation extraction has failed") from exception
