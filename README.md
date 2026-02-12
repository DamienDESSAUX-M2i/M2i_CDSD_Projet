<h1>Transcription Audio - Midi</h1>

Projet de soutenance du titre *Concepteur Développeur en Science des Données* (Jedha - RNCP 35288)

<h2>Table des matières</h2>

- [1. Description du projet](#1-description-du-projet)
- [Contexte](#contexte)
- [Application par bloc](#application-par-bloc)
- [2. Architecture](#2-architecture)
- [3. Structure du projet](#3-structure-du-projet)
- [4. Prérequis](#4-prérequis)
- [5. Installation](#5-installation)
  - [5.1. Démarrer l'infrastructure](#51-démarrer-linfrastructure)
  - [5.2. Accès aux interfaces](#52-accès-aux-interfaces)
  - [5.3. Exécuter le pipeline](#53-exécuter-le-pipeline)
- [6. Sources de données](#6-sources-de-données)
  - [6.1. Web Scraping](#61-web-scraping)
  - [6.2. API](#62-api)
  - [6.3. Fichier Excel](#63-fichier-excel)
- [7. Conformité RGPD](#7-conformité-rgpd)
- [8. Requêtes analytiques](#8-requêtes-analytiques)
- [9. Technologies utilisées](#9-technologies-utilisées)
- [10. Commandes utiles](#10-commandes-utiles)
- [11. Auteur](#11-auteur)


## 1. Description du projet

Transcription d'un enregistrement audio de guitare en fichier MIDI.

## Contexte

**Entrée** :
- Fichier audio WAV
- Guitare monophonique et polyphonique
- Guitare acoustique et électrique
- Accordage standard EADGBE

**Sortie** :
- Fichier MIDI représentant les notes jouées

## Application par bloc

| Bloc | Application concrete |
| :- | :- |
| BC01 | Stockage objet (MinIO S3) des enregistrements sonores (.wav), annotations (.xml, .jams) et features (spectrogrammes, CQT, MFCC, ...), Stockage document (MongoDB) des annotations Stockage SQL (PostgreSQL) des métadonnées entrées et sorties, Pipeline preprocessing (Resampling (22.05 kHz), Conversion mono, Normalisation, Découpage en frames), Pipeline processing (Extraction features: spectrogrammes, CQT et MFCC ...) |
| BC02 | Analyse exploratoire des données, visualisation spectrogrammes et pianorolls, Comparaison STFT vs CQT |
| BC03 | |
| BC04 | |
| BC05 | |
| BC06 | |

## 2. Architecture

```
                                  ┌───────────────────────────────┐
                                  │ SOURCES                       │
                                  │                               │
                                  │ • GuitarSET                   │
                                  │ • IDMT-SMT-Guitar             │
                                  └───────────────┬───────────────┘
                                                  │
                                  ┌───────────────┴───────────────┐
                                  │ Ingestion Pipeline            │
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
                                  │ Preprocessing Pipeline        │
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
                                  │ ML Pipeline                   │
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
│ • MIDI                        │ │ • ML output                   │ │                               │
└───────────────────────────────┘ └───────────────────────────────┘ └───────────────────────────────┘
```

## 3. Structure du projet

```
M2i_CDSD_Projet/
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── README.md
│
├── docs/
│   ├── DAT.md                   # Dossier d'Architecture Technique
│   └── RGPD_CONFORMITE.md       # Documentation RGPD
│
├── src/
│   ├── scrapers/
│   │   ├── books_scraper.py     # Scraper Books to Scrape
│   │   └── quotes_scraper.py    # Scraper Quotes to Scrape
│   ├── api/
│   │   └── geocoding_client.py  # Client API Adresse
│   ├── import/
│   │   └── excel_importer.py    # Import fichier Excel
│   └── pipeline/
│       └── etl_pipeline.py      # Pipeline ETL complet
│
├── sql/
│   └── analyses.sql             # 5 requêtes analytiques
│
├── init/
│   ├── mongo-init.js            # Initialisation MongoDB
│   └── postgres-init.sql        # Initialisation PostgreSQL
│
├── data/
│   └── partenaire_librairies.xlsx  # Fichier fourni
│
└── logs/                        # Logs d'exécution
```

## 4. Prérequis

- Docker et Docker Compose
- Python 3.11+ (pour exécution locale)

## 5. Installation

### 5.1. Démarrer l'infrastructure

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier l'état des services
docker-compose ps
```

### 5.2. Accès aux interfaces

| Service | URL | Identifiants |
|---------|-----|--------------|
| **Mongo Express** | http://localhost:8081 | admin / admin2026 |
| **pgAdmin** | http://localhost:5050 | admin@datapulse.local / admin2026 |
| **MinIO Console** | http://localhost:9001 | datapulse / datapulse2026 |

### 5.3. Exécuter le pipeline

```bash
# Pipeline complet
docker-compose exec pipeline python -m pipeline.etl_pipeline --step all --excel /app/data/partenaire_librairies.xlsx

# Mode test (données limitées)
docker-compose exec pipeline python -m pipeline.etl_pipeline --step all --test --excel /app/data/partenaire_librairies.xlsx

# Étapes séparées
docker-compose exec pipeline python -m pipeline.etl_pipeline --step extract
docker-compose exec pipeline python -m pipeline.etl_pipeline --step transform
docker-compose exec pipeline python -m pipeline.etl_pipeline --step load
```

## 6. Sources de données

### 6.1. Web Scraping

| Site | URL | Données |
|------|-----|---------|
| Books to Scrape | https://books.toscrape.com | ~1000 livres |
| Quotes to Scrape | https://quotes.toscrape.com | ~100 citations |

### 6.2. API

| API | URL | Usage |
|-----|-----|-------|
| API Adresse | https://api-adresse.data.gouv.fr | Géocodage des librairies |

### 6.3. Fichier Excel

Le fichier `partenaire_librairies.xlsx` contient 20 librairies partenaires avec des données personnelles nécessitant un traitement RGPD.

## 7. Conformité RGPD

Les données personnelles (nom, email, téléphone des contacts) sont :

1. **Pseudonymisées** : Hashage SHA-256 avec sel
2. **Minimisées** : Seul le hash est conservé en couche Gold
3. **Supprimables** : Script de suppression sur demande disponible

Voir `docs/RGPD_CONFORMITE.md` pour plus de détails.

## 8. Requêtes analytiques

Le fichier `sql/analyses.sql` contient 5 requêtes démontrant la valeur de la plateforme :

1. **Agrégation simple** : Statistiques par catégorie de livres
2. **Jointure** : Citations avec auteurs et tags
3. **Window function** : Classement des livres par prix dans leur catégorie
4. **Top N** : Top 10 des auteurs les plus prolifiques
5. **Croisement sources** : Opportunités commerciales librairies/livres

## 9. Technologies utilisées

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Données brutes | MongoDB | Flexibilité schéma, JSON natif |
| Données finales | PostgreSQL | SQL standard, window functions |
| Stockage fichiers | MinIO | Compatible S3, versioning |
| Pipeline | Python | Écosystème riche, lisibilité |
| Infrastructure | Docker | Reproductibilité, isolation |

## 10. Commandes utiles

```bash
# Logs du pipeline
docker-compose logs -f pipeline

# Accès MongoDB
docker-compose exec mongodb mongosh -u admin -p datapulse2026

# Accès PostgreSQL
docker-compose exec postgres psql -U datapulse -d datapulse

# Arrêter l'infrastructure
docker-compose down

# Supprimer les données (volumes)
docker-compose down -v
```

## 11. Auteur

Data Engineer - DataPulse Analytics
ECF Titre Professionnel Data Engineer

---

*Projet réalisé dans le cadre du Titre Professionnel Data Engineer (RNCP35288)*
