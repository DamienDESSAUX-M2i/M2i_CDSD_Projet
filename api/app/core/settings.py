from dataclasses import dataclass

import librosa
from audio import DenoiseMethod, NormalizationType


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Configuration for the full audio preprocessing and postprocessing pipelines.

    This includes:
        - Normalization parameters
        - Cleaning parameters
        - Feature extraction parameters
        - Context window parameters

    The goal is to ensure reproducibility and centralize all DSP-related settings.
    """

    # ===
    # CLEANING
    # ===
    use_highpass: bool = True
    highpass_cutoff: float = 60.0

    use_lowpass: bool = True
    lowpass_cutoff: float = 10_000.0

    denoise_method: DenoiseMethod = DenoiseMethod.SPECTRAL
    wiener_strength: float = 1.0

    use_trim: bool = False
    trim_db: float = 40.0

    # ===
    # NORMALIZATION
    # ===
    use_remove_dc_offset: bool = True

    target_sample_rate: int = 22050

    normalization_type: NormalizationType = NormalizationType.RMS
    target_peak: float = 0.99
    target_rms: float = 0.1
    clip: bool = False

    use_to_float32: bool = True

    # ===
    # FEATURES EXTRACTION
    # ===
    use_stft: bool = False
    n_fft: int = 2048
    hop_length: int = 512

    use_mel: bool = False
    n_mels: int = 128

    use_cqt: bool = True
    cqt_fmin: float = librosa.note_to_hz("E2")
    n_cqt_bins: int = 84
    bins_per_octave: int = 12

    use_chroma: bool = False
    chroma_cqt_norm: int | float | None = 2

    use_mfcc: bool = False
    n_mfcc: int = 20

    # ===
    # CONTEXT WINDOW
    # ===
    use_context_window: bool = False
    context_size: int = 11

    # ===
    # PIANO ROLL
    # ===
    midi_pitch_min = 40
    midi_pitch_max = 88


SETTINGS = Settings()
