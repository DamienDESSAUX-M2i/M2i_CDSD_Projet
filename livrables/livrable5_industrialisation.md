<h1>Livrable 5 : Industrialisation d'un algorithme d'apprentissage automatique et automatisation des processus de décision</h1>

> Un code source contenant la création de l'environnement standardisé, le déploiement de l'algorithme et l'application web ainsi qu'un URL vers l'application déployée.

# 1. Table des matières
- [1. Table des matières](#1-table-des-matières)
- [2. Objectif du livrable](#2-objectif-du-livrable)
- [3. Architecture générale](#3-architecture-générale)
- [4. Environnement standardisé](#4-environnement-standardisé)
- [5. Déploiement de l'algorithme](#5-déploiement-de-lalgorithme)
- [6. API de production](#6-api-de-production)
- [7. Interface utilisateur](#7-interface-utilisateur)
- [8. Conteneurisation](#8-conteneurisation)
- [9. Déploiement local](#9-déploiement-local)
- [10. Intégration continue (CI)](#10-intégration-continue-ci)
- [11. Livraison continue (CD)](#11-livraison-continue-cd)
- [12. Gestion des dépendances](#12-gestion-des-dépendances)
- [13. Ressources du projet](#13-ressources-du-projet)
- [14. Conclusion](#14-conclusion)

# 2. Objectif du livrable

Ce document présente les éléments permettant de démontrer l'industrialisation et le déploiement de l'application.

Le projet est composé :

- d'une API REST `FastAPI`,
- d'une interface utilisateur `Streamlit`,
- d'un modèle `TensorFlow` chargé au démarrage de l'API,
- d'une chaîne CI/CD `GitHub Actions`,
- d'un déploiement automatisé sur `Hugging Face Spaces`,
- d'un environnement `Docker` entièrement reproductible.

# 3. Architecture générale

![Figure d'architecture](./soutenance/figures/BC05/cicd_deployment_architecture.png)

# 4. Environnement standardisé

L'ensemble du projet est conteneurisé avec `Docker`.

Les dépendances Python sont gérées par `uv` afin de garantir :

- la reproductibilité de l'environnement,
- le verrouillage des versions ([uv.lock](../uv.lock)),
- une installation identique entre le développement, la CI et la production.

Les dépendances sont décrites dans :

- [pyproject.toml](../pyproject.toml)
- [uv.lock](../uv.lock)

Le conteneur principal embarque :

- Python 3.13
- `FastAPI`
- `Streamlit`
- `TensorFlow`
- `music21`
- `Verovio`
- `CairoSVG`

Le script `start.sh` démarre simultanément :

- l'API `FastAPI` ;
- l'interface `Streamlit`.

# 5. Déploiement de l'algorithme

Le modèle d'apprentissage est développé indépendamment de l'API.

Le cycle du modèle est le suivant :

1. entraînement de plusieurs modèles,
2. suivi des expérimentations avec MLflow,
3. export du meilleur modèle et du scaler associé s'il existe,
4. intégration manuelle dans l'API,
5. chargement unique du modèle au démarrage.

L'API ne réalise aucun entraînement.

Elle ne réalise que :

- le chargement du modèle,
- le prétraitement audio,
- l'extraction des features de machine-learning,
- l'inférence,
- le post-traitement,
- la génération des fichiers MIDI et partition.

# 6. API de production

L'API est développée avec **FastAPI**.

Elle expose les routes :

- `/health`
- `/model`
- `/predict`
- `/artifact/{id}/midi`
- `/artifact/{id}/piano_roll/svg`
- `/artifact/{id}/piano_roll/png`
- `/artifact/{id}/score/svg`
- `/artifact/{id}/score/pdf`

Les réponses sont standardisées au travers d'un modèle générique :

- `ApiResponse<T>`

Les erreurs sont centralisées via des gestionnaires d'exceptions dédiés.

Le modèle TensorFlow est partagé entre toutes les requêtes grâce au cycle de vie (`lifespan`) de FastAPI.

# 7. Interface utilisateur

L'application utilisateur est développée avec `Streamlit`.

Elle communique exclusivement avec l'API REST.

Elle permet :

- le dépôt d'un fichier WAV,
- le lancement de la transcription,
- l'affichage des résultats,
- le téléchargement des artefacts générés.

# 8. Conteneurisation

Le projet est distribué sous forme d'image `Docker`.

```yaml
# ===
# Builder
# ===

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./

RUN uv sync \
    --frozen \
    --no-dev \
    --group api

COPY api/backend ./backend
COPY api/frontend ./frontend
COPY api/.streamlit ./.streamlit
COPY api/start.sh ./start.sh

# ===
# Runtime
# ===

FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsndfile1 \
        libcairo2 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:${PATH}"

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/backend ./backend
COPY --from=builder /app/frontend ./frontend
COPY --from=builder /app/.streamlit ./.streamlit
COPY --from=builder /app/start.sh ./start.sh

RUN chmod +x start.sh

RUN mkdir -p /tmp

RUN useradd \
        --create-home \
        --shell /usr/sbin/nologin \
        appuser \
    && chown -R appuser:appuser /app \
    && chmod 777 /tmp

USER appuser

EXPOSE 7860
EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=20s \
    --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["./start.sh"]
```

Le conteneur contient :

- `FastAPI`
- `Streamlit`
- le modèle `TensorFlow`
- les dépendances Python
- les bibliothèques système nécessaires.

Le même conteneur est utilisé :

- en développement,
- dans `GitHub Actions`,
- sur `Hugging Face Spaces`.

Cette approche garantit un comportement identique sur tous les environnements.

L'image docker multi-stage pour alléger l'image, ce qui accélère le build.

Pour sécuriser l'image, un utilisateur est crée avec des droits spécifiques.

# 9. Déploiement local

Le projet peut être lancé intégralement avec :

```bash
docker compose up -d
```

Le fichier `docker-compose.yml` déploie :

- API `FastAPI`
- `Streamlit`
- `MinIO`
- `MongoDB`
- `Mongo Express`
- `PostgreSQL`
- `pgAdmin`
- `PostgreSQL` MLflow
- `MLflow`
- `Apache Spark` Master
- `Apache Spark` Workers

L'ensemble des paramètres est externalisé dans un fichier `.env`.

Un fichier [`env.example`](../.env.example) est fourni afin de reproduire facilement l'environnement.

# 10. Intégration continue (CI)

Chaque Push ou Pull Request déclenche automatiquement `GitHub Actions`.

La chaîne CI réalise :

**Validation du code**

- `Ruff`
- `MyPy`

**Validation fonctionnelle**

- exécution des tests `Pytest`

**Mesure de qualité**

- génération du rapport Coverage
- vérification d'un seuil minimal de couverture

Les rapports de couverture sont publiés comme artefacts `GitHub Actions`.

# 11. Livraison continue (CD)

Après validation de la qualité du code :

1. construction de l'image `Docker`,
2. publication dans `GitHub Container Registry` (GHCR),
3. mise à jour automatique du Dockerfile du Space `Hugging Face`,
4. déploiement automatique de la nouvelle version.

Le Space `Hugging Face` exécute directement la dernière image Docker publiée.

# 12. Gestion des dépendances

Le projet utilise :

- `uv`
- `pyproject.toml`
- `uv.lock`

afin d'assurer :

- la reproductibilité,
- le verrouillage des versions,
- une installation déterministe.

# 13. Ressources du projet

- [Dépôt GitHub](https://github.com/DamienDESSAUX-M2i/M2i_CDSD_Projet) du projet.
- [Space Hugging Face](https://huggingface.co/spaces/DamienDESSAUX/M2i_CDSD_Projet_Deployment) du projet.

# 14. Conclusion

Le projet met en œuvre une chaîne complète d'industrialisation.

L'environnement est entièrement reproductible, les contrôles qualité sont automatisés, le déploiement est continu et l'application est disponible publiquement via Hugging Face Spaces.