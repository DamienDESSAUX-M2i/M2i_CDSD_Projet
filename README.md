<h1>Transcription audio de guitare en MIDI</h1>

Transcription automatique d'un signal audio de guitare en fichier MIDI à l’aide de techniques de traitement du signal et de deep learning.

Projet de soutenance du titre professionnel *Concepteur Développeur en Science des Données* (Jedha - RNCP35288).

## 1. Table des matières

- [1. Table des matières](#1-table-des-matières)
- [2. Context](#2-context)
- [3. État de l’art](#3-état-de-lart)
- [4. Application par bloc](#4-application-par-bloc)
  - [4.1. BC01 : Construction et alimentation d'une infrastructure de gestion de donnees](#41-bc01--construction-et-alimentation-dune-infrastructure-de-gestion-de-donnees)
  - [4.2. BC02 : Analyse exploratoire, descriptive et inferentielle de donnees](#42-bc02--analyse-exploratoire-descriptive-et-inferentielle-de-donnees)
  - [4.3. BC03 : Analyse predictive de donnees structurees par IA (Machine Learning)](#43-bc03--analyse-predictive-de-donnees-structurees-par-ia-machine-learning)
  - [4.4. BC04 : Analyse predictive de donnees non-structurees par IA (Deep Learning)](#44-bc04--analyse-predictive-de-donnees-non-structurees-par-ia-deep-learning)
  - [4.5. BC05 : Industrialisation d'un algorithme et automatisation des processus de decision](#45-bc05--industrialisation-dun-algorithme-et-automatisation-des-processus-de-decision)
  - [4.6. BC06 : Direction de projets de gestion de donnees](#46-bc06--direction-de-projets-de-gestion-de-donnees)
- [5. Sources de données](#5-sources-de-données)
  - [5.1. GuitarSet](#51-guitarset)
  - [5.2. IDMT-SMT-Guitar](#52-idmt-smt-guitar)
- [6. Architecture](#6-architecture)
- [7. Structure du projet](#7-structure-du-projet)
- [8. Prérequis](#8-prérequis)
- [9. Installation](#9-installation)
  - [9.1. Démarrer l'infrastructure](#91-démarrer-linfrastructure)
  - [9.2. Accès aux interfaces](#92-accès-aux-interfaces)
  - [9.3. Exécuter le pipeline](#93-exécuter-le-pipeline)
- [12. Technologies utilisées](#12-technologies-utilisées)
- [13. Commandes utiles](#13-commandes-utiles)
- [14. Auteur](#14-auteur)

## 2. Context

La transcription automatique de musique (Automatic Music Transcription) consiste à convertir un signal audio en représentation symbolique (notes, temps, durées, vélocité).

Dans le cas de la guitare, le problème est complexe en raison :
- de la richesse harmonique de l'instrument : Une note de guitare ne produit pas une seule fréquence, mais une fréquence fondamentale accompagnée de plusieurs harmoniques, des résonances de la caisse... Dans un spectrogramme, les harmoniques peuvent avoir une amplitude plus élevée que la fondamentale, ce qui peut conduire à une mauvaise estimation du pitch.
- de la polyphonie : La guitare peut jouer plusieurs notes simultanément provoquant un chevauchement spectral des harmoniques, un masquage fréquentiel ou une superposition d’enveloppes temporelles. Contrairement à un instrument monophonique, la détection multi-pitch nécessite une classification multi-label et une séparation implicite des sources.
- du sustain : Une note de guitare a une enveloppe ADSR complexe (attaque rapide, décroissance, sustain variable, release dépendant de l’interprétation) entrainant des difficultés à la détection précise des onsets, à l'estimation correcte de la fin de note et un risque de fragmentation d’une note longue en plusieurs notes courtes.
- des techniques expressives : La guitare introduit des phénomènes non linéaires comme les dends (variation continue de pitch), vibrato (modulation périodique de fréquence), hammer-on / pull-off, slides ou palm mute. Ces effets produisent des variations continues de fréquence, des signaux non stationnaires, des ambiguïtés dans la quantification MIDI (qui est discret). Le MIDI impose des hauteurs discrètes, alors que la guitare peut produire des transitions continues.
- des bruits et artefacts : Les enregistrements réels contiennent des bruits de fond, bruits de frottement des cordes, de la réverbération, de la saturation (guitare électrique). Ces éléments perturbent les représentations spectrales et les modèles entraînés sur données propres.

Ce projet vise à développer un pipeline complet permettant de générer un fichier MIDI exploitable à partir d’un enregistrement audio brut.

**Objectifs visést :**
- Détecter les hauteurs (pitch detection)
- Identifier les instants d’attaque (onset detection)
- Estimer les durées des notes
- Générer un fichier MIDI structuré
- Évaluer les performances avec des métriques standards

**Limitations du format MIDI :**
- Les annotations MIDI peuvent présenter de légers décalages temporels, des erreurs humaines, une quantification différente du jeu réel. Cela complique l’apprentissage supervisé et l’évaluation des performances.
- Mathématiquement, la transcription est un problème inverse, on cherche une représentation symbolique discrète à partir d’un signal continu complexe. Il n’existe pas de solution unique, plusieurs combinaisons de notes peuvent produire un spectre similaire et l’information harmonique peut être ambiguë. Le problème est donc non linéaire, multi-label et fortement dépendant du contexte temporel.
- Le MIDI standard représente Note number (entier), Velocity, Start time et Duration. Mais ne capture pas naturellement les micro-intervalles, les bends continus précis les subtilités timbrales. Il existe donc une perte d’information intrinsèque lors du passage audio → MIDI.

**Données d'entrée :**
- Fichier audio WAV
- Guitare monophonique et polyphonique
- Guitare acoustique et électrique
- Accordage standard EADGBE

**Données de sortie** :
- Fichier MIDI représentant les notes jouées

## 3. État de l’art

Les principales approches existantes :
- Méthodes DSP classiques : STFT, autocorrélation, YIN
- Approches Deep Learning : CNN, CRNN, Transformers
- Outils commerciaux comme Melodyne
- Modèle open-source Spotify Basic Pitch

Ce projet combine une représentation spectrale (CQT) avec un modèle CRNN.

## 4. Application par bloc

### 4.1. BC01 : Construction et alimentation d'une infrastructure de gestion de donnees

Stockage objet (MinIO S3) des enregistrements sonores (.wav), annotations (.xml, .jams) et features (spectrogrammes, CQT, MFCC, ...), Stockage document (MongoDB) des annotations Stockage SQL (PostgreSQL) des métadonnées entrées et sorties, Pipeline preprocessing (Resampling (22.05 kHz), Conversion mono, Normalisation, Découpage en frames), Pipeline processing (Extraction features: spectrogrammes, CQT et MFCC ...) |

### 4.2. BC02 : Analyse exploratoire, descriptive et inferentielle de donnees

Analyse exploratoire des données, visualisation spectrogrammes et pianorolls, Comparaison STFT vs CQT |

### 4.3. BC03 : Analyse predictive de donnees structurees par IA (Machine Learning)

### 4.4. BC04 : Analyse predictive de donnees non-structurees par IA (Deep Learning)

### 4.5. BC05 : Industrialisation d'un algorithme et automatisation des processus de decision

### 4.6. BC06 : Direction de projets de gestion de donnees

## 5. Sources de données

### 5.1. GuitarSet

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
  - **Hauteur** :
    - 6 annotations *pitch_contour* (1 par corde)
    - 6 annotations *midi_note* (1 par corde)
  - Temps et tempo :
    - 1 annotation *beat_position*
    - 1 annotation *tempo*
  - Accords
    - 2 annotations d'accords : *instructed* (version numérique de la partition founie aux musiciens) et *performed* (annatation d'accords déduite des annotations de notes en utilisabt la segmentation et la fondamentale de la partition numérique). 

### 5.2. IDMT-SMT-Guitar

**Lien du site associé au dataset** : https://www.idmt.fraunhofer.de/en/publications/datasets/guitar.html

**Vue d'ensemble** :
- 7 guitares (accordage standard)
- Plusieurs réglages micros
- Plusieurs épaisseurs de cordes
- Dispositif d'enregistrement : interfaces audio appropriées connectées directement à la sortie de la guitare ou microphone à condensateur
- Format : RIFF WAVE mono
- Fréquence d'échantillonnage : 44 100 Hz

**4 sous-ensembles** :
- 1er sous-ensemble
  - Différentes techniques de jeu :
    - styles de jeu aux doigts : *finger-style*, *muted*, *picked*
    - styles d'expression : *normal*, *bending*, *slide*, *vibrato*, *harmonics*, *dead-notes*
  - Profondeur de bits : 24 bits
  - Enregistré à l'aide de 3 guitares différentes
  - Environ 4 700 événements de notes, avec une structure monophonique et polyphonique
  - Annotation au format XML

- 2e sous-ensemble : 
  - 400 notes monophoniques et polyphoniques
  - Chacune jouée avec deux guitares différentes
  - Aucun style d'expression n'a été appliqué
  - Profondeur de bits : 16 bits
  - Annotation au format XML

- 3e sous-ensemble :
  - 5 courts enregistrements de guitare monophoniques et polyphoniques
  - Enregistrés avec le même instrument, sans style ni expression particulier
  - Fichiers sont au format XML
  - Profondeur de bits : 16 bits
  - Annotation au format XML

- 4e sous-ensemble :
  - À des fins d'évaluation pour la reconnaissance d'accords et l'estimation de styles rythmiques
  - 64 courts morceaux musicaux regroupés par genre
  - Pour chaque morceau :
    - 2 tempos différents
    - 3 guitares différentes
    - Format XML
  - Profondeur de bits : 16 bits
  - Annotations concernant les positions d'attaque, les accords, la longueur du motif rythmique et la texture (monophonie/polyphonie) sont incluses dans différents formats de fichiers

## 6. Architecture

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

## 7. Structure du projet

```
M2i_CDSD_Projet/
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── README.md
│
├── docs/
│   ├── DAT.md                   # Dossier d'Architecture Technique
│   ├── rncp35288.md             # Description titre RNCP35288
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

## 8. Prérequis

- Docker et Docker Compose
- Python 3.11+ (pour exécution locale)
- Git

## 9. Installation

### 9.1. Démarrer l'infrastructure

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier l'état des services
docker-compose ps
```

### 9.2. Accès aux interfaces

| Service | URL | Identifiants |
|---------|-----|--------------|
| **Mongo Express** | http://localhost:8081 | admin / admin0000 |
| **pgAdmin** | http://localhost:5050 | admin@admin.com / admin0000 |
| **MinIO Console** | http://localhost:9001 | admin / admin0000 |

### 9.3. Exécuter le pipeline

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

## 12. Technologies utilisées

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Données brutes | MongoDB | Flexibilité schéma, JSON natif |
| Données finales | PostgreSQL | SQL standard, window functions |
| Stockage fichiers | MinIO | Compatible S3, versioning |
| Pipeline | Python | Écosystème riche, lisibilité |
| Infrastructure | Docker | Reproductibilité, isolation |

## 13. Commandes utiles

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

## 14. Auteur

Data Engineer - DataPulse Analytics
ECF Titre Professionnel Data Engineer

---

*Projet réalisé dans le cadre du Titre Professionnel Data Engineer (RNCP35288)*
