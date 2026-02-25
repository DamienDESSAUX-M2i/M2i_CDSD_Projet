<h1>Transcription audio de guitare en MIDI</h1>

Transcription automatique d'un signal audio de guitare en fichier MIDI à l’aide de techniques de traitement du signal et de deep learning.

## 1. Table des matières

- [1. Table des matières](#1-table-des-matières)
- [2. Context](#2-context)
- [3. Objectifs](#3-objectifs)
  - [3.1. Limitations du format MIDI](#31-limitations-du-format-midi)
  - [3.2. Données d'entrée](#32-données-dentrée)
  - [3.3. Données de sortie](#33-données-de-sortie)
- [4. État de l’art](#4-état-de-lart)
- [5. Application par bloc](#5-application-par-bloc)
  - [5.1. BC01 : Construction et alimentation d'une infrastructure de gestion de donnees](#51-bc01--construction-et-alimentation-dune-infrastructure-de-gestion-de-donnees)
  - [5.2. BC02 : Analyse exploratoire, descriptive et inferentielle de donnees](#52-bc02--analyse-exploratoire-descriptive-et-inferentielle-de-donnees)
  - [5.3. BC03 : Analyse predictive de donnees structurees par IA (Machine Learning)](#53-bc03--analyse-predictive-de-donnees-structurees-par-ia-machine-learning)
  - [5.4. BC04 : Analyse predictive de donnees non-structurees par IA (Deep Learning)](#54-bc04--analyse-predictive-de-donnees-non-structurees-par-ia-deep-learning)
  - [5.5. BC05 : Industrialisation d'un algorithme et automatisation des processus de decision](#55-bc05--industrialisation-dun-algorithme-et-automatisation-des-processus-de-decision)
  - [5.6. BC06 : Direction de projets de gestion de donnees](#56-bc06--direction-de-projets-de-gestion-de-donnees)
- [6. Sources de données](#6-sources-de-données)
  - [6.1. GuitarSet](#61-guitarset)
  - [6.2. IDMT-SMT-Guitar](#62-idmt-smt-guitar)
- [7. Architecture](#7-architecture)
- [8. Structure du projet](#8-structure-du-projet)
- [9. Prérequis](#9-prérequis)
- [10. Installation](#10-installation)
  - [10.1. Repository](#101-repository)
  - [10.2. Environnement virtuel](#102-environnement-virtuel)
  - [10.3. Variables d'environnement](#103-variables-denvironnement)
  - [10.4. Démarrer l'infrastructure](#104-démarrer-linfrastructure)
  - [10.5. Structure des données](#105-structure-des-données)
- [11. Utilisation](#11-utilisation)
  - [11.1. Accès aux interfaces](#111-accès-aux-interfaces)
  - [11.2. Exécution des pipelines](#112-exécution-des-pipelines)
  - [11.3. Options disponibles](#113-options-disponibles)
  - [11.4. Exemples d'utilisations des options](#114-exemples-dutilisations-des-options)
  - [11.5. Commandes utiles](#115-commandes-utiles)
- [12. Auteur](#12-auteur)

## 2. Context

La transcription automatique de musique (Automatic Music Transcription) consiste à convertir un signal audio en représentation symbolique (notes, temps, durées, vélocité).

Dans le cas de la guitare, le problème est complexe en raison :
- de la richesse harmonique de l'instrument : Une note de guitare ne produit pas une seule fréquence, mais une fréquence fondamentale accompagnée de plusieurs harmoniques, des résonances de la caisse... Dans un spectrogramme, les harmoniques peuvent avoir une amplitude plus élevée que la fondamentale, ce qui peut conduire à une mauvaise estimation du pitch.
- de la polyphonie : La guitare peut jouer plusieurs notes simultanément provoquant un chevauchement spectral des harmoniques, un masquage fréquentiel ou une superposition d’enveloppes temporelles. Contrairement à un instrument monophonique, la détection multi-pitch nécessite une classification multi-label et une séparation implicite des sources.
- du sustain : Une note de guitare a une enveloppe ADSR complexe (attaque rapide, décroissance, sustain variable, release dépendant de l’interprétation) entrainant des difficultés à la détection précise des onsets, à l'estimation correcte de la fin de note et un risque de fragmentation d’une note longue en plusieurs notes courtes.
- des techniques expressives : La guitare introduit des phénomènes non linéaires comme les dends (variation continue de pitch), vibrato (modulation périodique de fréquence), hammer-on / pull-off, slides ou palm mute. Ces effets produisent des variations continues de fréquence, des signaux non stationnaires, des ambiguïtés dans la quantification MIDI (qui est discret). Le MIDI impose des hauteurs discrètes, alors que la guitare peut produire des transitions continues.
- des bruits et artefacts : Les enregistrements réels contiennent des bruits de fond, bruits de frottement des cordes, de la réverbération, de la saturation (guitare électrique). Ces éléments perturbent les représentations spectrales et les modèles entraînés sur données propres.

Ce projet vise à développer un pipeline complet permettant de générer un fichier MIDI exploitable à partir d’un enregistrement audio brut.

## 3. Objectifs

Les objectifs visés sont :
- Détecter les hauteurs (pitch detection)
- Identifier les instants d’attaque (onset detection)
- Estimer les durées des notes
- Générer un fichier MIDI structuré
- Évaluer les performances avec des métriques standards

### 3.1. Limitations du format MIDI

- Les annotations MIDI peuvent présenter de légers décalages temporels, des erreurs humaines, une quantification différente du jeu réel. Cela complique l’apprentissage supervisé et l’évaluation des performances.
- Mathématiquement, la transcription est un problème inverse, on cherche une représentation symbolique discrète à partir d’un signal continu complexe. Il n’existe pas de solution unique, plusieurs combinaisons de notes peuvent produire un spectre similaire et l’information harmonique peut être ambiguë. Le problème est donc non linéaire, multi-label et fortement dépendant du contexte temporel.
- Le MIDI standard représente Note number (entier), Velocity, Start time et Duration. Mais ne capture pas naturellement les micro-intervalles, les bends continus précis les subtilités timbrales. Il existe donc une perte d’information intrinsèque lors du passage audio → MIDI.

### 3.2. Données d'entrée

- Fichier audio WAV
- Guitare monophonique et polyphonique
- Guitare acoustique et électrique
- Accordage standard EADGBE

### 3.3. Données de sortie

- Fichier MIDI représentant les notes jouées

## 4. État de l’art

Les principales approches existantes :
- Méthodes DSP classiques : STFT, autocorrélation, YIN
- Approches Deep Learning : CNN, CRNN, Transformers
- Outils commerciaux comme Melodyne
- Modèle open-source Spotify Basic Pitch

Ce projet combine une représentation spectrale (CQT) avec un modèle CRNN.

## 5. Application par bloc

### 5.1. BC01 : Construction et alimentation d'une infrastructure de gestion de donnees

Stockage objet (MinIO S3) des enregistrements sonores (.wav), annotations (.xml, .jams) et features (spectrogrammes, CQT, MFCC, ...), Stockage document (MongoDB) des annotations Stockage SQL (PostgreSQL) des métadonnées entrées et sorties, Pipeline preprocessing (Resampling (22.05 kHz), Conversion mono, Normalisation, Découpage en frames), Pipeline preprocessing (Extraction features: spectrogrammes, CQT et MFCC ...)

### 5.2. BC02 : Analyse exploratoire, descriptive et inferentielle de donnees

Analyse exploratoire des données, visualisation spectrogrammes et pianorolls, Comparaison STFT vs CQT

### 5.3. BC03 : Analyse predictive de donnees structurees par IA (Machine Learning)

### 5.4. BC04 : Analyse predictive de donnees non-structurees par IA (Deep Learning)

### 5.5. BC05 : Industrialisation d'un algorithme et automatisation des processus de decision

### 5.6. BC06 : Direction de projets de gestion de donnees

## 6. Sources de données

### 6.1. GuitarSet

**Lien du site associé au dataset** : https://guitarset.weebly.com/

**Contenu audio** :
- 360 extraits audio d'environ 30 secondes chacun :
  - 6 musiciens interprètent chacun 30 grilles d'accords.
  - 2 versions par grilles d'accords : accompagnement et solo qui est une improvisation sur l'accompagnement.
- 30 grilles d'accords générées à partir de combinaisons de :
  - 5 styles : rock, auteur-compositeur-interprète, bossa nova, jazz et funk.
  - 3 progressions : blues à 12 mesures, Autumn Leaves et Canon de Pachelbel.
  - Deux tempi : lent et rapide.

**Configuration de la collection audio** :
- L'audio est enregistré à l'aide d'un capteur hexaphonique qui génère un signal pour chaque corde séparément et un microphone à condensateur Neumann U-87.
- Les musiciens disposent de partitions et de pistes d'accompagnement conformes au style approprié, incluant une batterie et une ligne de basse.
- 3 enregistrements audio accompagnent chaque extrait, avec le suffixe suivant :
  - hex : fichier WAV original 6 canaux du capteur hexaphonique
  - hex_cln : fichiers WAV hexaphoniques après suppression des interférences
  - mic : enregistrement monophonique du microphone de référence

**Contenu d'annotation** :
- Chacun des 360 extraits est accompagné d'un fichier .jams contenant 16 annotations :
  - **Hauteur :**
    - 6 annotations *pitch_contour* (1 par corde)
    - 6 annotations *midi_note* (1 par corde)
  - **Temps et tempo :**
    - 1 annotation *beat_position*
    - 1 annotation *tempo*
  - **Accords :**
    - 2 annotations d'accords : *instructed* (version numérique de la partition founie aux musiciens) et *performed* (annatation d'accords déduite des annotations de notes en utilisabt la segmentation et la fondamentale de la partition numérique). 

### 6.2. IDMT-SMT-Guitar

**Lien du site associé au dataset** : https://www.idmt.fraunhofer.de/en/publications/datasets/guitar.html

**Vue d'ensemble :**
- 7 guitares (accordage standard)
- Plusieurs réglages micros
- Plusieurs épaisseurs de cordes
- Dispositif d'enregistrement : interfaces audio appropriées connectées directement à la sortie de la guitare ou microphone à condensateur
- Format : RIFF WAVE mono
- Fréquence d'échantillonnage : 44 100 Hz

**4 sous-ensembles :**
- **1er sous-ensemble :**
  - Différentes techniques de jeu :
    - styles de jeu aux doigts : *finger-style*, *muted*, *picked*
    - styles d'expression : *normal*, *bending*, *slide*, *vibrato*, *harmonics*, *dead-notes*
  - Profondeur de bits : 24 bits
  - Enregistré à l'aide de 3 guitares différentes
  - Environ 4 700 événements de notes, avec une structure monophonique et polyphonique
  - Annotation au format XML

- **2e sous-ensemble :**
  - 400 notes monophoniques et polyphoniques
  - Chacune jouée avec deux guitares différentes
  - Aucun style d'expression n'a été appliqué
  - Profondeur de bits : 16 bits
  - Annotation au format XML

- **3e sous-ensemble :**
  - 5 courts enregistrements de guitare monophoniques et polyphoniques
  - Enregistrés avec le même instrument, sans style ni expression particulier
  - Fichiers sont au format XML
  - Profondeur de bits : 16 bits
  - Annotation au format XML

- **4e sous-ensemble :**
  - À des fins d'évaluation pour la reconnaissance d'accords et l'estimation de styles rythmiques
  - 64 courts morceaux musicaux regroupés par genre
  - Pour chaque morceau :
    - 2 tempos différents
    - 3 guitares différentes
    - Format XML
  - Profondeur de bits : 16 bits
  - Annotations concernant les positions d'attaque, les accords, la longueur du motif rythmique et la texture (monophonie/polyphonie) sont incluses dans différents formats de fichiers

## 7. Architecture

L'architecture du projet est décrite par le schéma ci-dessous.

```
                                  ┌───────────────────────────────┐
                                  │ SOURCES                       │
                                  │                               │
                                  │ • GuitarSET                   │
                                  │ • IDMT-SMT-Guitar             │
                                  └───────────────┬───────────────┘
                                                  │
                                  ┌───────────────┴───────────────┐
                                  │ Ingestion Pipeline (Python)   │
                                  └───────────────┬───────────────┘
                                                  │
                ┌─────────────────────────────────┼──────────────────────────────────┐
                │                                 │                                  │
                ▼                                 ▼                                  ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
│ MinIO                         │ │ MongoDB                       │ │ PostgreSQL                    │
│ (Object Storage)              │ │ (Document Storage)            │ │ (SGBD)                        │
│                               │ │                               │ │                               │
│ Bucket: raw                   │ │ Collections:                  │ │ • Métadonnées input           │
│ • Annotations (.jams / .xml)  │ │ • chords                      │ │                               │
│ • Audios (.wav)               │ │ • note_midi                   │ │                               │
│                               │ │ • beat_position               │ │                               │
│                               │ │ • pitch_contour               │ │                               │
└───────────────────────────────┘ └───────────────┬───────────────┘ └───────────────────────────────┘
                │                                 │
                └─────────────────────────────────┤
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │ Preprocessor Pipeline (Python)│
                                  │ Feature Extraction            │
                                  └───────────────┬───────────────┘
                                                  │
               ┌──────────────────────────────────┤
               │                                  │ 
               ▼                                  ▼ 
┌───────────────────────────────┐ ┌───────────────────────────────┐
│ MinIO                         │ │ MongoDB                       │
│ (Object Storage)              │ │ (Document Storage)            │
│                               │ │                               │
│ Bucket: processing            │ │ Collections:                  │
│ • Audios (22 kHz / Mono)      │ │ • QTC                         │
│                               │ │ • MFCC                        │
│                               │ │ • Spectrogramme               │
└───────────────────────────────┘ └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │ ML Pipeline (Python)          │
                                  └───────────────┬───────────────┘
                                                  │
               ┌──────────────────────────────────┼─────────────────────────────────┐
               │                                  │                                 │
               ▼                                  ▼                                 ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
│ MinIO                         │ │ MongoDB                       │ │ PostgreSQL                    │
│ (Object Storage)              │ │ (Document Storage)            │ │ (SGBD)                        │
│                               │ │                               │ │                               │
│ Bucket: output                │ │ Collections:                  │ │ • Métadonnées output          │
│ • MIDI                        │ │ • ML output                   │ │ • Métriques                   │
└───────────────────────────────┘ └───────────────────────────────┘ └───────────────────────────────┘
```

## 8. Structure du projet

La structure du projet est décrite par le schéma ci-dessous.


```
M2i_CDSD_Projet/
├── .env                          # Variables d’environnement (non versionnées)
├── .gitignore                    # Fichiers/dossiers ignorés par Git
├── docker-compose.yml            # Orchestration des services (PostgreSQL, MongoDB, MinIO)
├── pyproject.toml                # Configuration du projet Python (PEP 621)
├── README.md                     # Documentation principale du projet
│
├── app/                          # Code applicatif principal
│   ├── .dockerignore             # Fichiers ignorés lors du build Docker
│   ├── Dockerfile                # Image Docker de l’application
│   ├── main.py                   # Point d’entrée de l’application
│   ├── requirements.txt          # Dépendances Python
│   │
│   ├── config/                   # Fichiers de configuration centralisés
│   │   ├── etl_settings.py
│   │   ├── ingestion_pipelines_settings.py
│   │   ├── minio_settings.py
│   │   ├── mongodb_settings.py
│   │   ├── postgresql_settings.py
│   │   └── __init__.py
│   │
│   ├── notebooks/                # Notebooks d’exploration et d’analyse
│   │   └── 01_analyse_exploratoire.ipynb
│   │
│   ├── src/                      # Code source structuré par responsabilités
│   │   ├── __init__.py
│   │   │
│   │   ├── extractors/           # Extraction des données (audio et annotation)
│   │   │   ├── abstract_extractor.py
│   │   │   ├── api_extractor.py
│   │   │   ├── csv_extractor.py
│   │   │   ├── excel_extractor.py
│   │   │   ├── jams_extractor.py
│   │   │   ├── json_extractor.py
│   │   │   ├── wav_extractor.py
│   │   │   ├── xml_extractor.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── loaders/              # Chargement des données vers différentes cibles
│   │   │   ├── abstract_loader.py
│   │   │   ├── csv_loader.py
│   │   │   ├── excel_loader.py
│   │   │   ├── jams_loader.py
│   │   │   ├── json_loader.py
│   │   │   ├── wav_loader.py
│   │   │   ├── xml_loader.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── models/               # Modèles de données (structures métiers)
│   │   │   ├── jams_models.py
│   │   │   ├── xml_models.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── pipelines/            # Orchestration des flux ETL
│   │   │   ├── abstract_pipeline.py
│   │   │   ├── guitar_set_ingestion_pipeline.py
│   │   │   ├── idmt_smt_guitar_ingestion_pipeline.py
│   │   │   ├── preprocessing_pipeline.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── storages/             # Connecteurs vers systèmes de stockage
│   │   │   ├── minio_storage.py
│   │   │   ├── mongo_storage.py
│   │   │   ├── postgresql_storage.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── transformers/         # Transformation et enrichissement des données
│   │   │   ├── element_tree_wrapper.py
│   │   │   └── __init__.py
│   │   │
│   │   └── utils/                # Outils transverses (logging)
│   │       ├── logger.py
│   │       └── __init__.py
│   │
│   └── tests/                    # Tests unitaires et fonctionnels
│
├── docs/                         # Documentation complémentaire
│   └── rncp35288.md
│
├── logs/                         # Fichiers de logs générés par l’application
│
├── minio/                        # Service MinIO
│   └── volume/                   # Données persistées
│
├── mongo/                        # Service MongoDB
│   ├── initdb/                   # Scripts d’initialisation de la base
│   │   └── 01_collections.js
│   └── volume/                   # Données persistées
│
├── pgadmin/                      # Interface d’administration PostgreSQL
│   ├── storage/
│   └── volume/
│
└── postgres/                     # Service PostgreSQL
    ├── initdb/                   # Scripts d’initialisation de la base
    │   └── 01_tables.sql
    └── volume/                   # Données persistées

```

## 9. Prérequis

- Git
- Docker et Docker Compose
- Python 3.13+ (pour exécution locale)

## 10. Installation

### 10.1. Repository

Cloner le projet depuis GitHub.

```bash
git clone https://github.com/DamienDESSAUX-M2i/M2i_CDSD_Projet.git
```

### 10.2. Environnement virtuel

Créer un environement virtuel et installer les dépendances.

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
## Linux/Mac:
source venv/bin/activate
## Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

Si vous utilisez uv, initialisez le projet avec `uv sync`.

### 10.3. Variables d'environnement

Créer, à la racine du projet, un fichier environement `./env` comprenant les variables d'environnement suivantes :

```bash
# ===
# Global
# ===

LOG_NAME="app"
GUITARSET_PATH="C:/Users/Administrateur/Documents/M2i_CDSD_Projet_Data/guitarset"
IDMT_SMT_GUITAR_PATH="C:/Users/Administrateur/Documents/M2i_CDSD_Projet_Data/idmt-smt-guitar"

# ===
# MinIO
# ===

MINIO_ENDPOINT="minio:9000"
MINIO_USER="admin"
MINIO_PASSWORD="admin0000"
MINIO_SECURE="False"
# bucket names
BUCKET_RAW="raw"
BUCKET_PROCESSED="processed"
BUCKET_OUTPUT="output"

# ===
# Mongo
# ===

MONGO_USER="admin"
MONGO_PASSWORD="admin0000"
MONGO_HOST="mongo"
MONGO_PORT="27017"
MONGO_DBNAME="audio_midi"
# mongo-express
ME_USER="admin"
ME_PASSWORD="admin0000"

# ===
# Postgres
# ===

POSTGRES_USER="admin"
POSTGRES_PASSWORD="admin0000"
POSTGRES_HOST="postgres"
POSTGRES_PORT="5432"
POSTGRES_DBNAME="audio_midi"
# pgadmin
PGADMIN_EMAIL="admin@admin.com"
PGADMIN_PASSWORD="admin0000"

```

### 10.4. Démarrer l'infrastructure

Démarrer l'infrastructure Docker.

| Service | Image |
| :- | :- |
| `minio` | `quay.io/minio/minio` |
| `minio-init` | `minio/mc` |
| `mongo` | `mongo` |
| `mongo-express` | `mongo-express` |
| `postgres` | `postgres` |
| `pgadmin` | `dpage/pgadmin4` |

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier l'état des services
docker-compose ps
```

Le service `minio-init` s'arrête après l'initialisation du service `minio`.

### 10.5. Structure des données

Les données doivent absolument respecter la structure suivante :

```txt
M2i_CDSD_Projet_Data\
├───guitarset
│   ├───annotation
│   ├───audio_hex-pickup_debleeded
│   ├───audio_hex-pickup_original
│   ├───audio_mono-mic
│   └───audio_mono-pickup_mix
└───idmt-smt-guitar
    ├───dataset1
    ├───dataset2
    ├───dataset3
    └───dataset4
```

## 11. Utilisation

### 11.1. Accès aux interfaces

| Service | URL | Identifiants |
|---------|-----|--------------|
| **MinIO Console** | http://localhost:9001 | admin / admin0000 |
| **Mongo Express** | http://localhost:8081 | admin / admin0000 |
| **pgAdmin** | http://localhost:8080 | admin@admin.com / admin0000 |

### 11.2. Exécution des pipelines

```bash
# Ingestion pipeline
python app/main.py --guitarset --idmtsmtguitar

# Preprocessor pipeline
python app/main.py --preprocessor

# ML pipeline
python app/main.py --ml
```

### 11.3. Options disponibles

| Option | Description |
|--------|-------------|
| `--guitar_set` | Lance la pipeline d'ingestion pour le dataset `GuitarSet` |
| `--idmt_smt_guitar` | Lance la pipeline d'ingestion pour le dataset `IDMT-SMT-Guitar` |
| `--limit` | Type: int | None, Défaut: None, Limite le nombre données ingérées |
| `--no-dataset1` | Désactive l'ingestion du sous ensemble numéro 1 du dataset `IDMT-SMT-Guitar` |
| `--no-dataset2` | Désactive l'ingestion du sous ensemble numéro 2 du dataset `IDMT-SMT-Guitar` |
| `--no-dataset3` | Désactive l'ingestion du sous ensemble numéro 3 du dataset `IDMT-SMT-Guitar` |
| `--no-dataset4` | Désactive l'ingestion du sous ensemble numéro 4 du dataset `IDMT-SMT-Guitar` |
| `--preprocessor` | Lance la pipeline de prétraitement |
| `--ml` | Lance la pipeline de machine learning |

### 11.4. Exemples d'utilisations des options

```bash
# Ingestion des 10 premières données du dataset GuitarSet
python app/main.py --guitar_set --limit 10

# Ingestion des 10 premières données des sous ensembles de données numéros 1 et 3 du dataset IDMT-SMT-Guitar
python app/main.py --idmt_smt_guitar --limit 10 --no-dataset2 --no-dataset4
```

### 11.5. Commandes utiles

```bash
# Création alias MinIO
docker-compose exec minio mc alias set local http://localhost:9000 admin admin000
# Liste des objets du bucket raw
docker-compose exec minio mc ls local/raw

# Accès MongoDB
docker-compose exec mongo mongosh -u admin -p admin0000

# Accès PostgreSQL
docker-compose exec postgres psql -U admin -d audio_midi

# Arrêter l'infrastructure
docker-compose down
```

## 12. Auteur

DESSAUX Damien

---

Projet de soutenance du titre professionnel *Concepteur Développeur en Science des Données* (Jedha - RNCP35288).