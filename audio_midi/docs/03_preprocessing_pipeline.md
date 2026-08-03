<h1>Audio Preprocessing Pipeline</h1>

# 1. Table of Contents

- [1. Table of Contents](#1-table-of-contents)
- [2. Pipeline Responsibilities](#2-pipeline-responsibilities)
- [3. Pipeline Construction](#3-pipeline-construction)
  - [Initialization](#initialization)
  - [3.1. Parameters](#31-parameters)
  - [3.1. Settings](#31-settings)
  - [3.2. Components](#32-components)
- [4. Execution Flow](#4-execution-flow)
- [5. Audio Preparation](#5-audio-preparation)
  - [5.1. Mono Conversion](#51-mono-conversion)
  - [5.2. DC Offset Removal](#52-dc-offset-removal)
  - [5.3. Resampling](#53-resampling)
- [6. Audio Cleaning](#6-audio-cleaning)
  - [6.1. High-Pass Filtering](#61-high-pass-filtering)
  - [6.2. Low-Pass Filtering](#62-low-pass-filtering)
  - [6.3. Noise Reduction](#63-noise-reduction)
  - [6.4. Silence Trimming](#64-silence-trimming)
- [7. Audio Normalization](#7-audio-normalization)
  - [7.1. Peak Normalization](#71-peak-normalization)
  - [7.2. RMS Normalization](#72-rms-normalization)
  - [7.3. Float32 Conversion](#73-float32-conversion)
- [8. Feature Extraction](#8-feature-extraction)
  - [8.1. STFT Spectrogram](#81-stft-spectrogram)
  - [8.2. Mel Spectrogram](#82-mel-spectrogram)
  - [8.3. Constant-Q Transform (CQT)](#83-constant-q-transform-cqt)
  - [8.4. Chromagram](#84-chromagram)
  - [8.5. MFCC](#85-mfcc)
- [9. Annotation Alignment](#9-annotation-alignment)
  - [9.1. MIDI Pitch Mapping](#91-midi-pitch-mapping)
  - [9.2. Time-to-Frame Mapping](#92-time-to-frame-mapping)
  - [9.3. Piano-Roll Construction](#93-piano-roll-construction)
- [10. Output sample](#10-output-sample)
  - [10.1. Feature Matrix](#101-feature-matrix)
  - [10.2. Piano-Roll Labels](#102-piano-roll-labels)
- [12. Running the Pipeline from CLI](#12-running-the-pipeline-from-cli)
  - [8.1. Preprocess dataset](#81-preprocess-dataset)
  - [8.2. Limits number of files processed](#82-limits-number-of-files-processed)
  - [8.3. Avoid ingesting sets or subsets of data](#83-avoid-ingesting-sets-or-subsets-of-data)
- [9. Relevant CLI Arguments](#9-relevant-cli-arguments)
- [10. Statistics](#10-statistics)
  - [Pipeline Metrics](#pipeline-metrics)
  - [10.1. Audio Metrics](#101-audio-metrics)
    - [10.1.1. MinIO](#1011-minio)
    - [10.1.3. MongoDB](#1013-mongodb)
  - [10.2. Sample Metrics](#102-sample-metrics)
    - [10.2.1. MinIO](#1021-minio)
    - [10.2.2. MongoDB](#1022-mongodb)
- [14. Design Decisions](#14-design-decisions)

# 2. Pipeline Responsibilities

The `src.pipelines.PreprocessingPipeline` transforms raw audio recordings and note annotations into a frame-wise machine learning dataset.

Its responsibilities are:

- Prepare raw audio signals.
- Normalize signal amplitude.
- Remove unwanted artifacts and noise.
- Extract time-aligned audio features.
- Align annotations with extracted features.
- Build frame-level piano-roll labels.
- Produce reproducible samples for training and evaluation datasets.

# 3. Pipeline Construction

## Initialization

The pipeline is initialized from `./audio_midi/main.py`.
```python
preprocessing_pipeline = PreprocessingPipeline(
    logger=logger,
    preprocessing_limit=args.limit,
    guitar_set=args.guitar_set,
    idmt_smt_guitar=args.idmt_smt_guitar,
    dataset1=args.dataset1,
    dataset2=args.dataset2,
    dataset3=args.dataset3,
    dataset4=args.dataset4,
)
```

## 3.1. Parameters

| Parameter | Description |
| :- | :- |
| `logger` | Shared application logger |
| `preprocessing_limit` | Limits number of audio processed |
| `guitar_set` | Enable GuitarSet preprocessing |
| `idmt_smt_guitar` | Enable IDMT-SMT-Guitar preprocessing |
| `dataset1` | Allow sub-dataset ingestion |
| `dataset2` | Allow sub-dataset ingestion |
| `dataset3` | Allow sub-dataset ingestion |
| `dataset4` | Allow sub-dataset ingestion |

The `preprocessing_limit` parameter corresponds to the maximum number of preprocessed audio files for each dataset. For example, if `preprocessing_limit`=10, then a maximum of 10 audio files will be preprocessed for each dataset (GuitarSet, IDMT-SMT-Guitar/dataset1, IDMT-SMT-Guitar/dataset2, IDMT-SMT-Guitar/dataset3 and IDMT-SMT-Guitar/dataset4).

## 3.1. Settings

The pipeline behavior is fully controlled through a `PreprocessingPipelineSettings` object.

The settings define:

- Audio cleaning parameters.
- Normalization parameters.
- Feature extraction parameters.
- Piano-roll construction parameters.
- Dataset export options.

All settings are serialized and stored as metadata to ensure reproducibility.

## 3.2. Components

The pipeline is composed of the following transformers:

| Component | Responsibility |
|------------|---------------|
| `AudioNormalizer` | Signal preparation and normalization |
| `AudioCleaner` | Filtering and denoising |
| `AudioFeatureExtractor` | Feature extraction |
| `MIDIPitchMapper` | MIDI pitch mapping |
| `TimeMapper` | Time-to-frame conversion |
| `PianoRollBuilder` | Piano-roll generation |

# 4. Execution Flow

The preprocessing workflow follows the sequence below:

```text
Raw Audio
    ↓
To Mono
    ↓
Remove DC Offset
    ↓
Resample
    ↓
Clean Audio
    ↓
Normalize Audio
    ↓
Convert to Float32
    ↓
Extract Features
    ↓
Build Piano Roll
    ↓
Frame-wise sample
```

The order is intentional and ensures feature-label consistency.

# 5. Audio Preparation

## 5.1. Mono Conversion

Multi-channel recordings are converted to mono before any DSP operation.

This guarantees consistent processing across datasets.

## 5.2. DC Offset Removal

The mean value of the waveform is removed.

This prevents bias during filtering and normalization.

## 5.3. Resampling

All recordings are resampled to a common sampling rate.

Default:

```python
target_sample_rate = 22050
```

Using a fixed sampling rate guarantees consistent feature extraction.

# 6. Audio Cleaning

## 6.1. High-Pass Filtering

A Butterworth high-pass filter removes low-frequency rumble and handling noise.

Default:

```python
highpass_cutoff = 60.0
```

## 6.2. Low-Pass Filtering

An optional Butterworth low-pass filter removes high-frequency noise.

Default:

```python
highpass_cutoff = 10_000.0
```
## 6.3. Noise Reduction

Supported denoising methods:

- Spectral gating
- Wiener filtering

The selected method is controlled through:

```python
denoise_method
```

Default is spectral gating.

## 6.4. Silence Trimming

Leading and trailing silence can optionally be removed.

Disabled by default because trimming modifies temporal alignment and may invalidate annotations.

# 7. Audio Normalization

## 7.1. Peak Normalization

Scales the waveform so that the maximum absolute amplitude matches the target peak value.

Default:

```python
target_peak = 0.99
```

## 7.2. RMS Normalization

Scales the waveform to a target RMS energy level.

Default:

```python
target_rms = 0.1
```

## 7.3. Float32 Conversion

The processed waveform is converted to `float32`.

Benefits:

- Reduced memory footprint.
- Faster computation.
- Compatibility with machine learning frameworks.

# 8. Feature Extraction

All features share the same temporal resolution.

The frame duration is determined by:

```python
n_fft
hop_length
```

## 8.1. STFT Spectrogram

Short-Time Fourier Transform magnitude spectrogram expressed in decibels.

## 8.2. Mel Spectrogram

Mel-scaled spectrogram expressed in decibels.

Default:

```python
n_mels = 128
```

## 8.3. Constant-Q Transform (CQT)

Musically meaningful frequency representation.

Default:

```python
n_cqt_bins = 84
bins_per_octave = 12
```

## 8.4. Chromagram

Pitch-class representation derived from the CQT.

Output dimension:

```text
12 pitch classes
```

## 8.5. MFCC

Mel-Frequency Cepstral Coefficients.

Default:

```python
n_mfcc = 20
```

# 9. Annotation Alignment

## 9.1. MIDI Pitch Mapping

MIDI notes are projected into a reduced pitch space.

Default range:

```python
40 ≤ MIDI ≤ 88
```

## 9.2. Time-to-Frame Mapping

Annotation timestamps are converted to frame indices using:

```python
sample_rate
hop_length
```

Frame boundaries follow:

```text
start_frame = floor(onset)
end_frame = ceil(offset)
```

This prevents off-by-one errors.

## 9.3. Piano-Roll Construction

Annotations are converted into a binary piano-roll matrix:

```text
(n_frames, n_pitches)
```

Each cell indicates whether a note is active during a frame.

# 10. Output sample

## 10.1. Feature Matrix

All extracted features are concatenated into a single DataFrame:

```text
(n_frames, n_features)
```

Each row corresponds to a time frame.

## 10.2. Piano-Roll Labels

The target labels are represented as:

```text
(n_frames, n_pitches)
```

This enables frame-wise supervised learning.

# 12. Running the Pipeline from CLI

## 8.1. Preprocess dataset

```bash
uv run ./audio_midi/main.py --preprocess_datasets
```

## 8.2. Limits number of files processed

```bash
uv run ./audio_midi/main.py --preprocess_datasets --limit 10
```

By setting the --limit parameter to 10, a maximum of 10 audio will be preprocessed for each dataset (GuitarSet, IDMT-SMT-Guitar/dataset1, IDMT-SMT-Guitar/dataset2, IDMT-SMT-Guitar/dataset3, IDMT-SMT-Guitar/dataset4).

All datasets 

## 8.3. Avoid ingesting sets or subsets of data

```bash
uv run ./audio_midi/main.py --preprocess_datasets --no_idmt_smt_guitar
```

# 9. Relevant CLI Arguments

| Argument | Description |
|---|---|
| `--preprocess_datasets` | Run preprocessing pipeline |
| `--limit` | Limits number of audio processed |
| `--no_dataset1` | Disables subset 1 ingestion |
| `--no_dataset2` | Disables subset 2 ingestion |
| `--no_dataset3` | Disables subset 3 ingestion |
| `--no_dataset4` | Disables subset 4 ingestion |

# 10. Statistics

The pipeline maintains a detailed metrics object: `PreprocessingPipelineStatistics`.
Statistics are reported at the end of the execution.

## Pipeline Metrics

| Metric | Description |
| :- | :- |
| `pipeline_metadata_inserted` | Pipeline metadata insertion status into MongoDB |
| `pipeline_metadata_inserted` | Pipeline metadata updating status in MongoDB |

## 10.1. Audio Metrics

| Metric | Description |
| :- | :- |
| `audio_error` | Number of audio processing or upload failures |
| `audio_loaded` | Number of successfully loaded raw audio files |
| `audio_normalized` | Number of successfully normalized audio files |
| `audio_cleaned` | Number of successfully cleaned audio files |
| `feature_extracted` | Number of successful feature extraction operations |
| `piano_roll_builded` | Number of successfully generated piano-roll targets |

### 10.1.1. MinIO

| Metric | Description |
| :- | :- |
| `audio_uploaded` | Number of cleaned audio files uploaded to MinIO |

### 10.1.3. MongoDB

| Metric | Description |
| :- | :- |
| `audio_metadata_inserted` | Number of audio metadata inserted into MongoDB |
| `audio_metadata_updated` | Number of audio metadata updated into MongoDB |

## 10.2. Sample Metrics

| Metric | Description |
| :- | :- |
| `sample_error` | Number of sample saving failures |

### 10.2.1. MinIO

| Metric | Description |
| :- | :- |
| `sample_uploaded` | Number of final samples successfully uploaded |

### 10.2.2. MongoDB

| Metric | Description |
| :- | :- |
| `sample_metadata_inserted` | Number of sample metadata inserted into MongoDB |
| `sample_metadata_updated` | Number of sample metadata updated in MongoDB |

# 14. Design Decisions

Several design choices were made to ensure reproducibility and alignment correctness:

- Mono conversion before all DSP operations.
- Resampling before cleaning and feature extraction.
- Cleaning before normalization.
- Consistent frame resolution across all features.
- Explicit handling of piano-roll frame boundaries.
- Float32 representation before feature extraction.
- Disabled silence trimming by default to preserve annotation alignment.

These choices guarantee deterministic preprocessing and reproducible datasets.