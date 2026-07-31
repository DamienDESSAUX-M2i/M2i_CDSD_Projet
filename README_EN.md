# Automatic Music Transcription

> End-to-end Automatic Music Transcription platform based on Deep Learning, featuring a complete Data Engineering pipeline, experiment tracking with MLflow, production-ready FastAPI API, Streamlit web interface and automated CI/CD deployment.

![global_architecture](./livrables/soutenance/figures/BC01/global_architecture.png)

## Table of contents

- [Automatic Music Transcription](#automatic-music-transcription)
  - [Table of contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
    - [Data Engineering](#data-engineering)
    - [Machine Learning](#machine-learning)
    - [Production API](#production-api)
    - [Web Interface](#web-interface)
    - [Software Engineering](#software-engineering)
  - [Project Architecture](#project-architecture)
  - [Technology Stack](#technology-stack)
  - [Repository Structure](#repository-structure)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Clone the repository](#clone-the-repository)
    - [Configure the environment](#configure-the-environment)
    - [Start the platform](#start-the-platform)
  - [Development](#development)
  - [Install dependencies](#install-dependencies)
  - [Running the Application without Docker](#running-the-application-without-docker)
    - [Start the FastAPI server](#start-the-fastapi-server)
  - [Start the Streamlit interface](#start-the-streamlit-interface)
  - [Testing](#testing)
  - [Code Quality](#code-quality)
    - [Ruff](#ruff)
    - [MyPy](#mypy)
  - [Docker](#docker)
  - [Continuous Integration \& Deployment](#continuous-integration--deployment)
    - [Continuous Integration](#continuous-integration)
    - [Continuous Delivery](#continuous-delivery)
  - [Production Architecture](#production-architecture)
  - [REST API](#rest-api)
  - [Model Lifecycle](#model-lifecycle)

## Overview

This project was developed as part of the **RNCP 35288 – Concepteur Développeur en Science des Données** professional certification.

The objective is to build a complete machine learning platform capable of automatically transcribing a monophonic or polyphonic guitar recording into symbolic musical notation.

This project covers the complete lifecycle of an AI application:

- data ingestion,
- ETL pipelines,
- feature engineering,
- dataset generation,
- experiment tracking,
- model selection,
- production API,
- web application,
- Docker deployment,
- automated CI/CD.

The repository therefore combines **Data Engineering**, **Machine Learning**, **MLOps** and **Software Engineering** best practices.

## Features

### Data Engineering

- Audio dataset ingestion
- Annotation extraction
- ETL pipelines
- Feature extraction
- Dataset generation
- Metadata management
- MinIO object storage
- MongoDB metadata storage
- PostgreSQL relational storage

### Machine Learning

- Deep Learning model for Automatic Music Transcription
- TensorFlow inference
- MLflow experiment tracking
- Model comparison
- Reproducible training environment

### Production API

- FastAPI REST API
- OpenAPI documentation
- Dependency Injection
- Typed models (Pydantic)
- Structured logging
- Exception handling
- Health monitoring

### Web Interface

- Streamlit frontend
- Audio upload
- Prediction visualization
- MIDI download
- Piano-roll visualization
- Music score generation

### Software Engineering

- Docker
- Docker Compose
- GitHub Actions CI/CD
- Ruff
- MyPy
- Pytest
- Coverage
- uv dependency management

## Project Architecture

The platform is organised into several independent layers.

```text
Data Sources
    ▼
Download Pipelines
    ▼
Ingestion Pipelines
    ▼
Data Lake MinIO bucket raw
    ▼
Preprocessing Pipelines
    ▼
Data Lake MinIO bucket processed
    ▼
Dataset Generation
    ▼
MLflow Training
    ▼
Best TensorFlow Model
    ▼
FastAPI Production
    ▼
Streamlit Frontend
```

The entire infrastructure can be started locally using a single Docker Compose file.

## Technology Stack

| Category | Technologies |
| :- | :- |
| Language | Python 3.13 |
| Dependency management | uv |
| API | FastAPI |
| Frontend | Streamlit |
| Machine Learning | TensorFlow / Scikit-learn |
| Experiment tracking | MLflow |
| Object Storage | MinIO |
| Metadata | MongoDB |
| Relational Database | PostgreSQL |
| Containerization | Docker |
| Orchestration | Docker Compose |
| CI/CD | GitHub Actions |
| Registry | GitHub Container Registry |
| Deployment | Hugging Face Spaces |
| Quality | Ruff / MyPy / Pytest |

## Repository Structure

```text
.
├── api/
│   ├── backend/           # FastAPI REST API
│   ├── frontend/          # Streamlit web interface
│   ├── tests/             # Unit and integration tests
│   └── start.sh           # Starts FastAPI and Streamlit
│
├── audio_midi/
│   ├── documentation/     # Technical documentation of ETL pipelines
│   ├── notebooks/         # EDA, feature engineering and ML experiments
│   ├── output/            # Generated datasets, reports and experiment outputs
│   ├── settings/          # Pipeline and processing configuration files
│   ├── src/
│   │   ├── downloaders/   # Download datasets from external sources
│   │   ├── extractors/    # Extract annotations and audio metadata
│   │   ├── loaders/       # Load data into storage backends
│   │   ├── models/        # Data models and domain objects
│   │   ├── pipelines/     # ETL pipeline orchestration
│   │   ├── storages/      # Storage abstraction (MinIO, MongoDB, PostgreSQL)
│   │   ├── transformers/  # Audio preprocessing and feature extraction
│   │   └── utils/         # Shared utility functions
│   └── main.py            # Command-line entry point for the data platform
│
├── minio/
│   └── init/              # MinIO initialization scripts
│
├── mongo/
│   └── initdb/            # MongoDB initialization scripts
│
├── postgres/
│   └── initdb/            # PostgreSQL initialization scripts
│
├── spark/
│   ├── apps/              # Spark applications (future distributed ETL)
│   ├── data/              # Shared datasets for Spark
│   └── events/            # Spark event logs
│
├── livrables/             # Deliverables for the RNCP 35288 certification
│
├── .env.example           # Environment variables template
├── .python-version        # Python version used by uv
├── docker-compose.yml     # Complete local data platform
├── Dockerfile             # Production image (FastAPI + Streamlit)
├── livrables.md           # Certification deliverables index
├── livrables.pdf          # Final certification report
├── pyproject.toml         # Project metadata and dependencies
└── uv.lock                # Locked dependency versions for reproducible builds
```

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Git
- Python 3.13

### Clone the repository

```bash
git clone https://github.com/DamienDESSAUX-M2i/M2i_CDSD_Projet.git

cd M2i_CDSD_Projet
```

### Configure the environment

```bash
cp .env.example .env
```

The default configuration launches the complete platform locally:

- MinIO
- MongoDB
- PostgreSQL
- MLflow
- FastAPI
- Streamlit
- Spark (experimental)

No additional configuration is required for a first execution.

### Start the platform

```bash
docker compose up -d
```

Once the containers are ready:

| Service | URL |
| :- | :- |
| Streamlit | <http://localhost:7860> |
| FastAPI | <http://localhost:8000> |
| Swagger | <http://localhost:8000/docs> |
| MLflow | <http://localhost:5000> |
| MinIO Console | <http://localhost:9001> |
| Mongo Express | <http://localhost:8081> |
| pgAdmin | <http://localhost:8080> |

## Development

The project uses **uv** as its Python package manager to ensure a fast, deterministic and reproducible development environment.

## Install dependencies

```bash
uv sync --group api --group dev
```

The project dependencies are fully defined by:

- `pyproject.toml`
- `uv.lock`

Using `uv.lock` guarantees that every developer, the CI pipeline and the production environment execute exactly the same dependency versions.

## Running the Application without Docker

The backend and frontend can also be started independently.

```bash
cd api
```

### Start the FastAPI server

```bash
uv run uvicorn backend.main:app --reload
```

## Start the Streamlit interface

```bash
uv run streamlit run frontend/streamlit_app.py
```

## Testing

The project includes unit and integration tests for the production API.

Run all tests:

```bash
uv run pytest
```

Generate a coverage report:

```bash
uv run pytest --cov
```

Coverage reports are automatically generated during Continuous Integration.

## Code Quality

Several static analysis tools are integrated into the development workflow.

### Ruff

```bash
uv run ruff check api/backend api/frontend
```

Ruff performs:

- linting
- formatting validation
- code quality analysis

### MyPy

```bash
uv run mypy api/backend api/frontend
```

MyPy validates the project's type annotations and helps detect programming errors before execution.

## Docker

The application is distributed as a Docker image.

The image contains:

- Python 3.13
- TensorFlow
- FastAPI
- Streamlit
- Music21
- Verovio
- CairoSVG
- all Python dependencies
- the trained TensorFlow model

The startup script launches both FastAPI and Streamlit simultaneously.

Build locally:

```bash
docker build -t automatic-music-transcription .
```

Run the container:

```bash
docker run -p 8000:8000 -p 7860:7860 automatic-music-transcription
```

## Continuous Integration & Deployment

Every push to the `main` branch automatically triggers a complete CI/CD pipeline powered by GitHub Actions.

```text
Push / Pull Request
    ▼
Pytest
    ▼
Coverage Report
    ▼
Ruff + MyPy
    ▼
Docker Build
    ▼
Push to GHCR
    ▼
Update Hugging Face Space
    ▼
Automatic Deployment
```

### Continuous Integration

Each commit is automatically validated through:

- unit tests
- integration tests
- Ruff linting
- MyPy static typing
- coverage threshold validation

Coverage reports are published as GitHub Actions artifacts.

### Continuous Delivery

Once the validation pipeline succeeds:

1. a Docker image is built,
2. the image is published to GitHub Container Registry (GHCR),
3. the Hugging Face Space is automatically updated,
4. the new application version is deployed.

No manual deployment step is required.

## Production Architecture

The production application follows a layered architecture.

```text
Streamlit
    ▼
FastAPI Routes
    ▼
Business Services
    ▼
TensorFlow Model
    ▼
Generated Artifacts
```

The FastAPI application separates responsibilities into:

- routes;
- dependency injection;
- services;
- business models;
- infrastructure components;
- exception handlers.

This architecture improves maintainability, testability and scalability.

## REST API

The production API exposes the following endpoints.

| Method | Endpoint | Description |
| :- | :- | :- |
| GET | `/health` | Application health check |
| GET | `/model` | Loaded model information |
| POST | `/predict` | Audio transcription |
| GET | `/artifact/{id}/midi` | Download generated MIDI |
| GET | `/artifact/{id}/piano_roll/png` | Download piano roll (PNG) |
| GET | `/artifact/{id}/piano_roll/svg` | Download piano roll (SVG) |
| GET | `/artifact/{id}/score/pdf` | Download musical score (PDF) |
| GET | `/artifact/{id}/score/svg` | Download musical score (SVG) |

Interactive documentation is available through Swagger: <http://localhost:8000/docs>.

## Model Lifecycle

The production API is dedicated exclusively to inference.

The model lifecycle is intentionally separated from the application.

```text
Dataset generation
    ▼
Model training
    ▼
MLflow experiment tracking
    ▼
Best model selection
    ▼
Manual export (.keras)
    ▼
Integration into the API
    ▼
Production inference
```

This separation guarantees:

- reproducible experiments;
- controlled model promotion;
- lightweight production deployments.

The TensorFlow model is loaded only once during the FastAPI application startup using the application lifespan mechanism.

This avoids unnecessary loading overhead for each prediction request.
