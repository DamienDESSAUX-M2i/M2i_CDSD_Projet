import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

import librosa


@dataclass(frozen=True)
class PreprocessingPipelineSettings:
    """
    Configuration for the full audio transformation pipeline.

    This includes:
        - Normalization parameters
        - Cleaning parameters
        - Feature extraction parameters

    The goal is to ensure reproducibility and centralize all DSP-related settings.
    """

    # ===
    # NORMALIZATION
    # ===
    norm_type: Literal["peak", "rms", "peak+rms", "none"] = "peak+rms"
    target_rms: float = 0.1
    target_peak: float = 1.0
    target_sample_rate: int = 22050

    # ===
    # CLEANING
    # ===
    use_highpass: bool = False
    highpass_cutoff: float = 80.0

    use_lowpass: bool = False
    lowpass_cutoff: float = 8000.0

    use_wiener: bool = False
    wiener_strength: float = 1.0

    use_spectral_denoise: bool = False
    wiener_strength: float = 1.0

    use_trim: bool = False
    trim_db: float = 40.0

    # ===
    # FEATURE SELECTION
    # ===
    use_stft: bool = True
    use_mel: bool = True
    use_cqt: bool = True
    use_chroma: bool = True
    use_mfcc: bool = True

    # ===
    # FEATURE PARAMETERS
    # ===
    n_fft: int = 2048
    hop_length: int = 512

    # Mel
    n_mels: int = 128

    # MFCC
    n_mfcc: int = 13

    # CQT
    fmin: float = librosa.note_to_hz("E2")  # C2 | E2
    n_cqt_bins: int = 84  # C2: 88 | E2: 84
    bins_per_octave: int = 12

    # ===
    # PIANO ROLL
    # ===
    midi_min = 36
    midi_max = 99

    # ===
    # PIPELINE PARAMETERS
    # ===
    preprocessing_limit: int | None = None
    save_clean_audio: bool = True
    save_sample: bool = True

    # ===
    # METADATA / VERSIONING
    # ===
    pipeline_name: str = "preprocessing"
    pipeline_version: str = "1.0.0"

    def to_mongo_dict(self) -> dict[str, dict[str, Any]]:
        """
        Convert the configuration into a structured MongoDB-ready dictionary.

        The output groups parameters by logical sections to improve readability
        and metadata organization in MongoDB documents.

        The following fields are intentionally excluded:
            - pipeline_version
            - preprocessing_limit

        Returns:
            dict[str, dict[str, Any]]:
                A nested dictionary organized by configuration sections.
        """
        metadata = {
            "pipeline_name": self.pipeline_name,
            "pipeline_version": self.pipeline_version,
            "metadata": {
                "normalization": {
                    "norm_type": self.norm_type,
                    "target_rms": self.target_rms,
                    "target_peak": self.target_peak,
                    "target_sample_rate": self.target_sample_rate,
                },
                "cleaning": {
                    "use_highpass": self.use_highpass,
                    "highpass_cutoff": self.highpass_cutoff,
                    "use_lowpass": self.use_lowpass,
                    "lowpass_cutoff": self.lowpass_cutoff,
                    "use_wiener": self.use_wiener,
                    "wiener_strength": self.wiener_strength,
                    "use_spectral_denoise": self.use_spectral_denoise,
                    "use_trim": self.use_trim,
                    "trim_db": self.trim_db,
                },
                "feature_selection": {
                    "use_stft": self.use_stft,
                    "use_mel": self.use_mel,
                    "use_cqt": self.use_cqt,
                    "use_chroma": self.use_chroma,
                    "use_mfcc": self.use_mfcc,
                },
                "feature_parameters": {
                    "n_fft": self.n_fft,
                    "hop_length": self.hop_length,
                    "n_mels": self.n_mels,
                    "n_mfcc": self.n_mfcc,
                    "fmin": self.fmin,
                    "n_cqt_bins": self.n_cqt_bins,
                    "bins_per_octave": self.bins_per_octave,
                },
                "piano_roll": {
                    "midi_min": self.midi_min,
                    "midi_max": self.midi_max,
                },
            },
        }

        metadata["_id"] = self.get_functional_key(metadata)

        return metadata

    def get_functional_key(self, metadata) -> str:
        """
        Generates a stable functional key from a potentially nested dictionary.
        """
        canonical = json.dumps(
            metadata,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        )

        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


preprocessing_pipeline_config = PreprocessingPipelineSettings()
