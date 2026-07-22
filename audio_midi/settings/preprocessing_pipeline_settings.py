from dataclasses import dataclass
from typing import Any

import librosa
from src.transformers import DenoiseMethod, NormalizationType

from .abstract_pipeline_settings import AbstractPipelineSettings, PipelineType


@dataclass
class PreprocessingPipelineSettings(AbstractPipelineSettings):
    """
    Configuration for the full audio transformation pipeline.

    This includes:
        - Normalization parameters
        - Cleaning parameters
        - Feature extraction parameters

    The goal is to ensure reproducibility and centralize all DSP-related settings.
    """

    pipeline_name: str = "preprocessor_standard"
    pipeline_type: PipelineType = PipelineType.PREPROCESSOR
    pipeline_version: str = "1.0.0"

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
    cqt_fmin: float = float(librosa.note_to_hz("E2"))
    n_cqt_bins: int = 84
    bins_per_octave: int = 12

    use_chroma: bool = False
    chroma_cqt_norm: int | float | None = 2

    use_mfcc: bool = False
    n_mfcc: int = 20

    # ===
    # PIANO ROLL
    # ===
    midi_pitch_min = 40
    midi_pitch_max = 88

    # ===
    # PIPELINE PARAMETERS
    # ===
    preprocessing_limit: int | None = None
    save_clean_audio: bool = True
    save_sample: bool = True

    def _to_metadata_dict(self) -> dict[str, Any]:
        return {
            "cleaning": {
                "use_highpass": self.use_highpass,
                "highpass_cutoff": self.highpass_cutoff,
                "use_lowpass": self.use_lowpass,
                "lowpass_cutoff": self.lowpass_cutoff,
                "denoise_method": self.denoise_method.value,
                "wiener_strength": self.wiener_strength,
                "use_trim": self.use_trim,
                "trim_db": self.trim_db,
            },
            "normalization": {
                "use_remove_dc_offset": self.use_remove_dc_offset,
                "target_sample_rate": self.target_sample_rate,
                "normalization_type": self.normalization_type.value,
                "target_peak": self.target_peak,
                "target_rms": self.target_rms,
                "clip": self.clip,
                "use_to_float32": self.use_to_float32,
            },
            "features_extraction": {
                "use_stft": self.use_stft,
                "n_fft": self.n_fft,
                "hop_length": self.hop_length,
                "use_mel": self.use_mel,
                "n_mels": self.n_mels,
                "use_cqt": self.use_cqt,
                "cqt_fmin": self.cqt_fmin,
                "n_cqt_bins": self.n_cqt_bins,
                "bins_per_octave": self.bins_per_octave,
                "use_chroma": self.use_chroma,
                "chroma_cqt_norm": self.chroma_cqt_norm,
                "use_mfcc": self.use_mfcc,
                "n_mfcc": self.n_mfcc,
            },
            "piano_roll": {
                "midi_min": self.midi_pitch_min,
                "midi_max": self.midi_pitch_max,
            },
        }


PREPROCESSING_PIPELINE_SETTINGS = PreprocessingPipelineSettings()
