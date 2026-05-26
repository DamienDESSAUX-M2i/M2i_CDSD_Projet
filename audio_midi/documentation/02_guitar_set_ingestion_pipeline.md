<h1>GuitarSet ingestion pipeline documentation</h1>

This documentation talk about the GuitarSet ingestion pipeline used in the Audio MIDI project.

# 1. Table of contents
- [1. Table of contents](#1-table-of-contents)
- [2. Pipeline Responsibilities](#2-pipeline-responsibilities)
- [3. Pipeline Construction](#3-pipeline-construction)
  - [3.1. Parameters](#31-parameters)
- [4. Execution Flow](#4-execution-flow)
- [5. JAMS Ingestion Pipeline](#5-jams-ingestion-pipeline)
  - [5.1. Input](#51-input)
  - [5.2. Processing Steps](#52-processing-steps)
- [6. WAV Ingestion Pipeline](#6-wav-ingestion-pipeline)
  - [6.1. Input](#61-input)
  - [6.2. Processing Steps](#62-processing-steps)
- [7. Running the Pipeline from CLI](#7-running-the-pipeline-from-cli)
  - [7.1. Ingest dataset](#71-ingest-dataset)
  - [7.2. Limits number of files processed](#72-limits-number-of-files-processed)
- [8. Relevant CLI Arguments](#8-relevant-cli-arguments)
- [9. Statistics](#9-statistics)
  - [9.1. JAMS Metrics](#91-jams-metrics)
    - [9.1.1. MinIO](#911-minio)
    - [9.1.2. PostgreSQL](#912-postgresql)
    - [9.1.3. MongoDB](#913-mongodb)
  - [9.2. WAV Metrics](#92-wav-metrics)
    - [9.2.1. MinIO](#921-minio)
    - [9.2.2. PostgrSQL](#922-postgrsql)

# 2. Pipeline Responsibilities

The `src.pipelines.GuitarSetIngestionPipeline` is responsible for ingesting the GuitarSet dataset into a multi-storage architecture:
- **MinIO**: raw storage for `.jams` files and `.wav` audio
- **PostgreSQL**: relational metadata (recordings, audio files, GuitarSet metadata, annotation file references)
- **MongoDB**: musical annotations (MIDI note events extracted from JAMS)

The pipeline processes two main data types:
1. **JAMS files** (annotation + metadata)
2. **WAV audio files** (multiple recording modalities)

# 3. Pipeline Construction

The pipeline is initialized from `./audio_midi/main.py`.
```python
ingestion_pipeline = GuitarSetIngestionPipeline(
    logger=logger,
    ingestion_limit=args.limit,
)
```

## 3.1. Parameters

| Parameter | Description |
| :- | :- |
| `logger` | Shared application logger |
| `ingestion_limit` | Limits number of files processed |

# 4. Execution Flow

The pipeline execution flow is:
```text
main.py
 └── GuitarSetIngestionPipeline.run()
        ├── _jams_ingestion(annotation_path)
        │    └── iterate .jams files (tqdm loop)
        │         └── _jam_processing(file)
        │              ├── JAMSExtractor.read()
        │              ├── MinIOStorage.put_jams()
        │              ├── JAMSExtractor.extract()
        │              ├── PostgreSQL recording upsert
        │              ├── PostgreSQL annotation_file upsert
        │              ├── PostgreSQL guitarset_metadata upsert
        │              ├── MongoStorage.insert_note_midi()
        │              └── statistics update
        │
        ├── _wav_ingestion(audio_hex-pickup_debleeded)
        │    └── iterate .wav files
        │         └── _wav_processing(file)
        │              ├── WAVExtractor.extract()
        │              ├── TITLE_REGEX parsing
        │              ├── PostgreStorage.select_recording()
        │              ├── MinIO.put_audio()
        │              ├── PostgreSQL audio_file upsert
        │              └── statistics update
        │
        ├── _wav_ingestion(audio_hex-pickup_original)
        │    └── _wav_processing(...)
        │
        ├── _wav_ingestion(audio_mono-mic)
        │    └── _wav_processing(...)
        │
        ├── _wav_ingestion(audio_mono-pickup_mix)
        │   └── _wav_processing(...)
        └── statistics reporting
```

The pipeline enforces a strict ingestion order: JAMS ingestion then WAV ingestion. This is required because WAV files depend on recordings created during JAMS ingestion.

# 5. JAMS Ingestion Pipeline

## 5.1. Input

Directory containing `.jams` files: `settings.GUITAR_SET_INGESTION_PIPELINE_SETTINGS.annotation_path`.

## 5.2. Processing Steps

1. Load JAMS file.
2. Upload raw JAMS to MinIO. Stored under `{bucket_raw}/{dataset_name}/{jam_stem}/annotation.jams`
3. Extract metadata and annotations.
4. Recording upsert (PostgreSQL). Table affected: `recordings`.
5. Annotation file upsert (PostgreSQL). Table affected: `annotation_files`.
6. GuitarSet metadata upsert (PostgreSQL). Table affected: `guitarset_metadata`.
7. MIDI annotation insertion (MongoDB). Collection affected: `note_midi`.

Any exception during processing increments `jams_error`, logs the failure, does not stop pipeline execution.

# 6. WAV Ingestion Pipeline

## 6.1. Input

The pipeline processes four directories:
- `audio_hex-pickup_debleeded`
- `audio_hex-pickup_original`
- `audio_mono-mic`
- `audio_mono-pickup_mix`

Each directory contains `.wav` files.

## 6.2. Processing Steps

1. Load WAV file.
2. Extract recording title. The filename must match `TITLE_REGEX` for which pattern is `\d{2}_[A-Za-z0-9]+-\d+-[A-G](b|#)?_[A-Za-z]+`. If parsing fails then file is rejected.
3. Retrieve associated recording (PostgreSQL). If not found, an error is raised (WAV depends on JAMS ingestion).
4. Upload audio to MinIO. Storage path is `{dataset_name}/{title}/{audio_type}.wav`, where `audio_type` is derived from the parent directory name.
5. Audio file upsert (PostgreSQL). Table affected: `audio_file`.

Any failure during processing increments `wav_error`, logs error, continues processing remaining files.

# 7. Running the Pipeline from CLI

## 7.1. Ingest dataset

```bash
uv run ./audio_midi/main.py --ingest_guitar_set
```

## 7.2. Limits number of files processed

```bash
uv run ./audio_midi/main.py --ingest_guitar_set --limit 10
```

# 8. Relevant CLI Arguments

| Argument | Description |
|---|---|
| `--ingest_guitar_set` | Run GuitarSet ingestion pipeline |
| `--limit` | Limits number of files processed |

# 9. Statistics

The pipeline maintains a detailed metrics object: `GuitarSetIngestionPipelineStatistics`.
Statistics are reported at the end of the execution.

## 9.1. JAMS Metrics

| Metric | Description |
| :- | :- |
| `jams_loaded` | Number of JAMS files successfully parsed |
| `jams_error` | Number of failed JAMS processing operations |

### 9.1.1. MinIO

| Metric | Description |
| :- | :- |
| `jams_uploaded` | Number of JAMS files uploaded to MinIO |

### 9.1.2. PostgreSQL

| Metric | Description |
| :- | :- |
| `recordings_inserted` | New recordings created |
| `recordings_updated` | Existing recordings updated |
| `guitarset_metadata_inserted` | New GuitarSet metadata rows |
| `guitarset_metadata_updated` | Updated metadata rows |
| `annotation_file_inserted` | New annotation file records |
| `annotation_file_updated` | Updated annotation file records |

### 9.1.3. MongoDB

| Metric | Description |
| :- | :- |
| `jams_annotation_inserted` | New MIDI annotations inserted |
| `jams_annotation_updated` | Existing MIDI annotations updated |

## 9.2. WAV Metrics

| Metric | Description |
| :- | :- |
| `wav_loaded` | Number of WAV files loaded |
| `wav_error` | Number of failed WAV processing operations |

### 9.2.1. MinIO

| Metric | Description |
| :- | :- |
| `wav_uploaded` | Number of WAV files uploaded to MinIO |

### 9.2.2. PostgrSQL

| Metric | Description |
| :- | :- |
| `audio_file_inserted` | New audio file records inserted |
| `audio_file_updated` | Updated audio file records |
