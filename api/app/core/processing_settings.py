import logging
from dataclasses import dataclass
from pathlib import Path

import librosa

from app.audio import DenoiseMethod, NormalizationType

logger = logging.getLogger(__name__)


API_DIR = Path(__file__).parent.parent.resolve()


@dataclass(frozen=True, slots=True)
class ProcessingSettings:
    """Configuration for audio transcription processing.

    This configuration centralizes all parameters used by preprocessing,
    inference postprocessing and artifact generation.

    Attributes:
        model_path:
            Path to the trained TensorFlow model.

        scaler_path:
            Optional path to the feature scaler.

        metadata_path:
            Optional path to model metadata.

        output_dir:
            Directory where generated artifacts are stored.

        target_sample_rate:
            Audio sampling rate used throughout processing.

        normalization_type:
            Audio normalization strategy.

        use_context_window:
            Whether temporal context windows are generated.

        context_size:
            Number of frames included in temporal context.
    """

    model_path: Path = API_DIR / "artifacts" / "model.keras"
    scaler_path: Path | None = None
    metadata_path: Path | None = API_DIR / "artifacts" / "metadata.json"
    output_dir: Path = API_DIR / "output"

    # Cleaning
    use_highpass: bool = True
    highpass_cutoff: float = 60.0

    use_lowpass: bool = True
    lowpass_cutoff: float = 10_000.0

    denoise_method: DenoiseMethod = DenoiseMethod.SPECTRAL
    wiener_strength: float = 1.0

    use_trim: bool = False
    trim_db: float = 40.0

    # Normalization
    use_remove_dc_offset: bool = True

    target_sample_rate: int = 22_050

    normalization_type: NormalizationType = NormalizationType.RMS
    target_peak: float = 0.99
    target_rms: float = 0.1
    clip: bool = False

    use_to_float32: bool = True

    # Feature extraction
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

    # Context window
    use_context_window: bool = True
    context_size: int = 11

    # Piano roll
    midi_pitch_min: int = 40
    midi_pitch_max: int = 88
    min_piano_roll_note_duration: float = 0.05
    velocity: int = 100

    # Rhythm quantization
    bpm: int = 120
    subdivision: float = 0.25
    min_rhythm_quantizer_note_duration: float = 0.25

    def __post_init__(self) -> None:
        """Validate processing configuration.

        Raises:
            ValueError:
                If one configuration value is invalid.
        """
        if self.target_sample_rate <= 0:
            raise ValueError(
                "target_sample_rate must be greater than zero.",
            )

        if self.n_fft <= 0:
            raise ValueError(
                "n_fft must be greater than zero.",
            )

        if self.hop_length <= 0:
            raise ValueError(
                "hop_length must be greater than zero.",
            )

        if self.hop_length > self.n_fft:
            raise ValueError(
                "hop_length cannot be greater than n_fft.",
            )

        if not 0 < self.target_peak <= 1:
            raise ValueError(
                "target_peak must be between 0 and 1.",
            )

        if self.context_size <= 0:
            raise ValueError(
                "context_size must be greater than zero.",
            )

        if self.midi_pitch_min >= self.midi_pitch_max:
            raise ValueError(
                "midi_pitch_min must be lower than midi_pitch_max.",
            )

        if not 0 <= self.velocity <= 127:
            raise ValueError(
                "velocity must be between 0 and 127.",
            )


PROCESSING_SETTINGS = ProcessingSettings()

logger.debug("Processing settings initialized ")
