<h1>IDMT-SMT-Guitar ingestion pipeline documentation</h1>

This documentation talk about the IDMT-SMT-Guitar ingestion pipeline used in the Audio MIDI project.

# 1. Table of contents
- [1. Table of contents](#1-table-of-contents)
- [2. Pipeline Responsibilities](#2-pipeline-responsibilities)
- [3. Pipeline Construction](#3-pipeline-construction)
  - [3.1. Parameters](#31-parameters)
- [4. Execution Flow](#4-execution-flow)
- [5. XML Ingestion Pipeline](#5-xml-ingestion-pipeline)
  - [5.1. Input](#51-input)
  - [5.2. Processing Steps](#52-processing-steps)
- [6. WAV Ingestion Pipeline](#6-wav-ingestion-pipeline)
  - [6.1. Input](#61-input)
  - [6.2. Processing Steps](#62-processing-steps)
- [Dataset-Specific Logic](#dataset-specific-logic)
  - [Dataset1](#dataset1)
  - [Dataset2](#dataset2)
- [7. Running the Pipeline from CLI](#7-running-the-pipeline-from-cli)
  - [7.1. Ingest dataset](#71-ingest-dataset)
  - [7.2. Limits number of files processed](#72-limits-number-of-files-processed)
  - [7.3. Avoid ingesting subsets of data](#73-avoid-ingesting-subsets-of-data)
- [8. Relevant CLI Arguments](#8-relevant-cli-arguments)
- [9. Statistics](#9-statistics)
  - [9.1. XML Metrics](#91-xml-metrics)
    - [9.1.1. MinIO](#911-minio)
    - [9.1.2. PostgreSQL](#912-postgresql)
    - [9.1.3. MongoDB](#913-mongodb)
  - [9.2. WAV Metrics](#92-wav-metrics)
    - [9.2.1. MinIO](#921-minio)
    - [9.2.2. PostgrSQL](#922-postgrsql)

# 2. Pipeline Responsibilities

The `IDMTSMTGuitarIngestionPipeline` is responsible for ingesting and normalizing the **IDMT-SMT-Guitar dataset**, which is split into multiple subsets (1 to 4).

It performs ETL processing across a distributed storage stack:
- **MinIO**: raw XML and WAV files
- **PostgreSQL**: structured metadata (recordings, IDMT-SMT-Guitar metadata, audio file references, annotation file references)
- **MongoDB**: musical annotations (MIDI-like note events extracted from XML)

The pipeline processes two main data types:
- **XML annotation files** (annotation + metadata)
- **WAV audio files** (recorded guitar signals)

# 3. Pipeline Construction

The pipeline is initialized from `./audio_midi/main.py`.
```python
ingestion_pipeline = IDMTSMTGuitarIngestionPipeline(
    logger=logger,
    ingestion_limit=args.limit,
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
| `ingestion_limit` | Limits number of files processed |
| `dataset1` | Allow sub-dataset ingestion |
| `dataset2` | Allow sub-dataset ingestion |
| `dataset3` | Allow sub-dataset ingestion |
| `dataset4` | Allow sub-dataset ingestion |

# 4. Execution Flow

The pipeline execution flow is:
```text
main.py
    └── IDMTSMTGuitarIngestionPipeline.run()
        ├── dataset1 ingestion (optional)
        │    └── _dataset1_ingestion()
        │         ├── _add_pickup_prefix_to_filenames()
        │         ├── _xml_ingestion()
        │         │    └── _xml_processing(file)
        │         │         ├── XMLExtractor.read()
        │         │         ├── MinIO.put_xml()
        │         │         ├── XMLExtractor.extract()
        │         │         ├── XML metadata enrichment
        │         │         ├── PostgreSQL recording upsert
        │         │         ├── PostgreSQL annotation_file upsert
        │         │         ├── PostgreSQL idmt_smt_guitar_metadata upsert
        │         │         └── MongoDB insert_note_midi()
        │         ├── _wav_ingestion()
        │         │    └── _wav_processing(file)
        │         │         ├── WAVExtractor.extract()
        │         │         ├── PostgreSQL.select_recording()
        │         │         ├── MinIO.put_audio()
        │         │         ├── PostgreSQL audio_file upsert
        │         │         └── statistics update
        │
        ├── dataset2 ingestion (optional)
        │    ├── _rename_audio_files_to_match_xml()
        │    └── _dataset_ingestion()
        │         ├── _xml_ingestion()
        │         └── _wav_ingestion()
        │
        ├── dataset3 ingestion (optional)
        │    └── _dataset_ingestion()
        │         ├── _xml_ingestion()
        │         └── _wav_ingestion()
        │
        ├── dataset4 ingestion (optional, not implemented)
        │    └── _dataset4_ingestion()
        │
        └── statistics reporting
```

The pipeline enforces a strict ingestion order: XML ingestion then WAV ingestion. This is required because WAV files depend on recordings created during XML ingestion.

# 5. XML Ingestion Pipeline

## 5.1. Input

The pipeline processes three directories:
- `dataset1/annotation`
- `dataset2/annotation`
- `dataset3/annotation`

Each directory contains `.xml` files.

## 5.2. Processing Steps

1. Load and parse XML file.
2. Upload raw XML to MinIO. Stored under `{bucket_raw}/{dataset_name}_{dataset_number}/{xml_stem}/annotation.xml`
3. Extract metadata and annotations. Metadata is enriched with directory information.
4. Recording upsert (PostgreSQL). Table affected: `recordings`.
5. Annotation file upsert (PostgreSQL). Table affected: `annotation_files`.
6. IDMT-SMT-Guitar metadata upsert (PostgreSQL). Table affected: `idmt_smt_guitar_metadata`.
7. MIDI annotation insertion (MongoDB). Collection affected: `note_midi`.

Any exception during processing increments `xml_error`, logs the failure, does not stop pipeline execution.

# 6. WAV Ingestion Pipeline

## 6.1. Input

The pipeline processes four directories:
- `dataset1/audio`
- `dataset2/audio`
- `dataset3/audio`

Each directory contains `.wav` files.

## 6.2. Processing Steps

1. Load WAV file.
2. Retrieve associated recording (PostgreSQL). If not found, an error is raised (WAV depends on XML ingestion).
3. Upload audio to MinIO. Storage path is `{dataset_name}_{dataset_number}/{wav_stem}/audio.wav`.
4. Audio file upsert (PostgreSQL). Table affected: `audio_file`.

Any failure during processing increments `wav_error`, logs error, continues processing remaining files.

# Dataset-Specific Logic

## Dataset1

Before ingestion, a preprocessing step is necessary. To avoid name conflicts, the SC/HU prefixes are added to the filenames. The `_add_pickup_prefix_to_filenames()` method performs this preprocessing step.

## Dataset2

Ingestion requires consistency between XML and WAV naming conventions. Nine audio files have different names than their associated XML files. The `_rename_audio_files_to_match_xml` method renames these audio files.

# 7. Running the Pipeline from CLI

## 7.1. Ingest dataset

```bash
uv run ./audio_midi/main.py --ingest_idmt_smt_guitar
```

## 7.2. Limits number of files processed

```bash
uv run ./audio_midi/main.py --ingest_idmt_smt_guitar --limit 10
```

## 7.3. Avoid ingesting subsets of data

```bash
uv run ./audio_midi/main.py --ingest_idmt_smt_guitar --no_dataset2 --no_dataset4
```

# 8. Relevant CLI Arguments

| Argument | Description |
|---|---|
| `--ingest_idmt_smt_guitar` | Run IDMT-SMT-Guitar ingestion pipeline |
| `--limit` | Limits number of files processed |
| `--no_dataset1` | Disables subset 1 ingestion |
| `--no_dataset2` | Disables subset 2 ingestion |
| `--no_dataset3` | Disables subset 3 ingestion |
| `--no_dataset4` | Disables subset 4 ingestion |

# 9. Statistics

The pipeline maintains a detailed metrics object: `IDMTSMTGuitarIngestionPipelineStatistics`.
Statistics are reported at the end of the execution.

## 9.1. XML Metrics

| Metric | Description |
| :- | :- |
| `xml_loaded` | Number of XML files successfully parsed |
| `xml_error` | Number of failed XML processing operations |

### 9.1.1. MinIO

| Metric | Description |
| :- | :- |
| `xml_uploaded` | Number of XML files uploaded to MinIO |

### 9.1.2. PostgreSQL

| Metric | Description |
| :- | :- |
| `recordings_inserted` | New recordings created |
| `recordings_updated` | Existing recordings updated |
| `idmt_smt_guitar_metadata_inserted` | New IDMT-SMT-Guitar metadata rows |
| `idmt_smt_guitar_metadata_updated` | Updated metadata rows |
| `annotation_file_inserted` | New annotation file records |
| `annotation_file_updated` | Updated annotation file records |

### 9.1.3. MongoDB

| Metric | Description |
| :- | :- |
| `xml_annotation_inserted` | New MIDI annotations inserted |
| `xml_annotation_updated` | Existing MIDI annotations updated |

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
