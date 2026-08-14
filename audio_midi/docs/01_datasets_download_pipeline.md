<h1>Datasets download pipeline documentation</h1>

This documentation talk about the datasets download pipeline used in the Audio MIDI project.

# 1. Table of contents
- [1. Table of contents](#1-table-of-contents)
- [2. Pipeline Responsibilities](#2-pipeline-responsibilities)
- [3. Pipeline Construction](#3-pipeline-construction)
  - [3.1. Parameters](#31-parameters)
- [4. Execution Flow](#4-execution-flow)
- [5. Download Workflow](#5-download-workflow)
- [6. Extraction Workflow](#6-extraction-workflow)
- [7. Running the Pipeline from CLI](#7-running-the-pipeline-from-cli)
  - [7.1. Download all datasets](#71-download-all-datasets)
  - [7.2. Download only GuitarSet](#72-download-only-guitarset)
  - [7.3. Download only IDMT-SMT-Guitar](#73-download-only-idmt-smt-guitar)
- [8. Relevant CLI Arguments](#8-relevant-cli-arguments)
- [9. Expected Directory Structure](#9-expected-directory-structure)
- [10. Error Handling](#10-error-handling)
- [11. Statistics](#11-statistics)

# 2. Pipeline Responsibilities

The `src.pipelines.DatasetsDownloadPipeline` is responsible for:
1. Downloading dataset archives
2. Extracting ZIP archives
3. Collecting execution statistics

The pipeline currently supports:
- GuitarSet
- IDMT-SMT-Guitar

# 3. Pipeline Construction

The pipeline is initialized from `./audio_midi/main.py`.
```python
download_datasets_pipeline = DatasetsDownloadPipeline(
    logger=logger,
    guitar_set=args.guitar_set,
    idmt_smt_guitar=args.idmt_smt_guitar,
)
```

## 3.1. Parameters

| Parameter | Description |
| :- | :- |
| `logger` | Shared application logger |
| `guitar_set` | Enable GuitarSet download |
| `idmt_smt_guitar` | Enable IDMT-SMT-Guitar download |

# 4. Execution Flow

The pipeline execution flow is:
```text
main.py
 └── DatasetsDownloadPipeline.run()
      ├── _process_dataset(config)
      │    ├── _download(...)
      │    ├── _extract(...)
      │    └── statistics update
      └── statistics reporting
```

# 5. Download Workflow

The download step uses `src.downloaders.DatasetDownloader`.

Features:
- configurable HTTP retry strategy
- resumable downloads using HTTP Range headers
- temporary .part files for partial downloads
- automatic retry with exponential backoff
- configurable HTTP session and headers
- progress tracking with tqdm

Downloads are skipped when the target archive already exists.

If a partial .part file exists, the downloader attempts to resume the transfer instead of restarting from scratch.

# 6. Extraction Workflow

The extraction step uses `src.extractors.ZipExtractor`.

Features:
- safe extraction into a temporary directory
- Zip Slip protection
- idempotent extraction
- automatic cleanup of temporary directories

Extraction is skipped when the target directory already exists.

# 7. Running the Pipeline from CLI

## 7.1. Download all datasets

```bash
uv run ./audio_midi/main.py --download_datasets
```

## 7.2. Download only GuitarSet

```bash
uv run ./audio_midi/main.py --download_datasets --no_idmt_smt_guitar
```

## 7.3. Download only IDMT-SMT-Guitar

```bash
uv run ./audio_midi/main.py --download_datasets --no_guitar_set
```

# 8. Relevant CLI Arguments

| Argument | Description |
|---|---|
| `--download_datasets` | Run dataset download pipeline |
| `--no_guitar_set` | Disable GuitarSet download |
| `--no_idmt_smt_guitar` | Disable IDMT-SMT-Guitar download |

# 9. Expected Directory Structure

Downloaded archives and extracted datasets are stored under:
```text
./audio_midi/data/
```

Typical structure:
```text
audio_midi/
└── data/
    ├── archive.zip
    └── extracted_dataset/
```

# 10. Error Handling

The pipeline logs and propagates failures occurring during:
- dataset download
- archive extraction
- filesystem operations

Statistics counters are updated accordingly.

# 11. Statistics

The pipeline tracks:
- successful downloads
- failed downloads
- successful extractions
- failed extractions

Statistics are reported at the end of the execution.