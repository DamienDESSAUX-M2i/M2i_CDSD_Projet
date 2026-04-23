from dataclasses import dataclass
from typing import Literal

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
    # PIPELINE / OUTPUT
    # ===
    preprocessing_limit: int | None = None
    save_clean_audio: bool = True
    save_features: bool = True

    # ===
    # METADATA / VERSIONING
    # ===
    pipeline_version: str = "v1"


preprocessing_pipeline_config = PreprocessingPipelineSettings()
