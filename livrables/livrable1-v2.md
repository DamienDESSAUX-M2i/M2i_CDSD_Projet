<h1>Livrable 1 - Infrastructure conceptualisée</h1>

> **Consigne :** Une étude de 1 page décrivant schématiquement l'infrastructure conceptualisée et le code source permettant de construire l'infrastructure.

# 1. Table des matières
- [1. Table des matières](#1-table-des-matières)
- [2. Contexte](#2-contexte)
- [3. Analyse des besoins et contraintes](#3-analyse-des-besoins-et-contraintes)
  - [3.1. Collecte et centralisation des données](#31-collecte-et-centralisation-des-données)
  - [3.2. Préparation des données](#32-préparation-des-données)
  - [3.3. Traçabilité des traitements](#33-traçabilité-des-traitements)
    - [3.3.1. Déploiement reproductible](#331-déploiement-reproductible)
- [4. Principes d'architecture retenus](#4-principes-darchitecture-retenus)
  - [4.1. Couche de stockage](#41-couche-de-stockage)
  - [4.2. Couche de métadonnées](#42-couche-de-métadonnées)
  - [4.3. Couche de traitement](#43-couche-de-traitement)
  - [4.4. Couche Data Science](#44-couche-data-science)
  - [4.5. Couche applicative](#45-couche-applicative)
- [5. Mise en œuvre du Data Lake et des processus ETL](#5-mise-en-œuvre-du-data-lake-et-des-processus-etl)
  - [5.1. Collecte et intégration des données (C1.3)](#51-collecte-et-intégration-des-données-c13)
  - [5.2. Organisation du Data Lake (C1.1)](#52-organisation-du-data-lake-c11)
  - [5.3. Construction des données d'entraînement (C1.4)](#53-construction-des-données-dentraînement-c14)
  - [5.4. Gestion des métadonnées](#54-gestion-des-métadonnées)
    - [5.4.1. PostgreSQL](#541-postgresql)
    - [5.4.2. MongoDB](#542-mongodb)
- [6. Préparation à la montée en charge (C1.2)](#6-préparation-à-la-montée-en-charge-c12)
- [7. Infrastructure as Code et reproductibilité](#7-infrastructure-as-code-et-reproductibilité)
- [8. Industrialisation et qualité logicielle](#8-industrialisation-et-qualité-logicielle)
  - [8.1. Validation du code](#81-validation-du-code)
  - [8.2. Construction et publication de l'application](#82-construction-et-publication-de-lapplication)
- [9. Évolutivité de la plateforme](#9-évolutivité-de-la-plateforme)
  - [9.1. Calcul distribué](#91-calcul-distribué)
  - [9.2. MLOps](#92-mlops)
  - [9.3. Valorisation des résultats](#93-valorisation-des-résultats)
- [10. Conclusion](#10-conclusion)


# 2. Contexte

Le projet consiste à développer une plateforme de **transcription automatique de fichiers audio de guitare en fichiers MIDI et partitions musicales** en s'appyant sur des techniques de traitement du signal et de Machine Learning. L'objectif est de construire une infrastructure capable de collecter, stocker, transformer et tracer les données utilisées pour l'entraînement de modèles de Machine Learning, tout en garantissant la reproductibilité des expérimentations et en assurant le déploiement d'une application web permettant d'exploiter ces modèles.

La [note de cadrage](./gestion_de_projet/note_de_cadrage.pdf) et le [cahier des charges](./gestion_de_projet/cahier_des_charger.pdf) présentent plus en détail le projet.

La plateforme s'appuie sur deux jeux de données publics :

- **GuitarSet**, contenant des enregistrements audio au format **WAV** accompagnés d'annotations **JAMS** ;
- **IDMT-SMT-Guitar**, contenant des enregistrements **WAV** accompagnés d'annotations **XML**.

Ces données doivent être collectées, stockées, nettoyées, transformées puis exploitées afin de produire des jeux d'entraînement de qualité pour les modèles de Machine Learning.

Le document [inventaire_des_sources_de_donnees](./gestion_de_projet/inventaire_des_sources_de_donnees.pdf) présente des informations complémentaires sur les jeux de données collectés.

L'infrastructure devait répondre à plusieurs contraintes :

- séparer les données brutes des données transformées ;
- assurer la traçabilité complète des traitements appliqués aux données ;
- permettre la reproductibilité des expérimentations ;
- préparer l'évolution vers des traitements distribués ;
- faciliter le déploiement de l'application finale.

L'architecture retenue répond à ces objectifs en distinguant clairement les différentes couches fonctionnelles de la plateforme.

# 3. Analyse des besoins et contraintes

L'analyse des besoins a conduit à identifier quatre fonctions principales.

## 3.1. Collecte et centralisation des données

Les données proviennent de plusieurs sources hétérogènes possédant des formats différents (WAV, JAMS et XML). L'infrastructure doit permettre leur téléchargement automatique puis leur intégration dans un espace de stockage unique afin de constituer un **Data Lake**.

## 3.2. Préparation des données

Les fichiers audio doivent subir plusieurs traitements avant d'être exploitables :

* nettoyage du signal ;
* normalisation ;
* extraction des caractéristiques musicales (features) ;
* alignement avec les annotations ;
* génération d'échantillons destinés à l'apprentissage.

Ces traitements sont réalisés au travers de pipelines ETL développés en Python.

## 3.3. Traçabilité des traitements

Chaque transformation appliquée aux données doit être historisée afin de garantir la reproductibilité des expérimentations.

Les métadonnées enregistrées comprennent notamment :

* les pipelines exécutés ;
* les paramètres utilisés ;
* les fichiers produits ;
* les échantillons générés ;
* les jeux de données construits.

Cette traçabilité est assurée par **MongoDB**, tandis que les expérimentations de Machine Learning sont suivies par **MLflow**.

### 3.3.1. Déploiement reproductible

L'ensemble des services nécessaires au projet doit pouvoir être reconstruit automatiquement sur un nouvel environnement.

L'infrastructure est donc entièrement décrite sous forme de code à l'aide de **Docker Compose**, tandis que le déploiement applicatif est automatisé par une chaîne **CI/CD GitHub Actions**.

# 4. Principes d'architecture retenus

L'architecture a été conçue selon une approche en couches, chaque composant remplissant une responsabilité clairement identifiée.

## 4.1. Couche de stockage

Le stockage repose sur un **Data Lake MinIO** organisé en plusieurs buckets :

| Bucket    | Rôle                                                     |
| --------- | -------------------------------------------------------- |
| raw       | stockage des données sources                             |
| processed | stockage des données nettoyées, features et échantillons |
| mlflow    | stockage des artefacts des expérimentations              |
| output    | réservé aux productions futures de l'API                 |

Cette organisation permet de séparer les différents états de transformation des données tout en conservant les fichiers originaux.

## 4.2. Couche de métadonnées

Les métadonnées sont volontairement séparées des fichiers.

Deux bases sont utilisées :

* **MongoDB** conserve les métadonnées techniques liées aux pipelines, aux jeux de données et aux traitements réalisés ;
* **PostgreSQL** centralise les informations relationnelles sur les fichiers audio et leurs annotations.

Cette séparation facilite les recherches, le suivi des traitements et les futures évolutions de la plateforme.

## 4.3. Couche de traitement

Les traitements de données sont organisés sous forme de pipelines ETL indépendants :

* téléchargement des jeux de données ;
* ingestion dans le Data Lake ;
* prétraitement audio ;
* extraction des caractéristiques ;
* construction des échantillons d'apprentissage.

Cette organisation permet d'exécuter chaque étape indépendamment et facilite leur maintenance.

L'ensemble des pipelines est actuellement développé en Python. L'architecture prévoit néanmoins leur migration vers **Apache Spark** afin de prendre en charge des volumes de données plus importants sans remettre en cause l'organisation générale de la plateforme.

## 4.4. Couche Data Science

Les notebooks Jupyter permettent :

* d'explorer les données ;
* de construire différents jeux d'entraînement ;
* d'entraîner plusieurs modèles ;
* de comparer leurs performances.

Toutes les expérimentations sont suivies automatiquement par **MLflow**, qui enregistre paramètres, métriques et artefacts afin de garantir leur reproductibilité.

## 4.5. Couche applicative

Le meilleur modèle sélectionné est exporté manuellement depuis MLflow au format **TensorFlow `.keras`**, puis intégré à une API **FastAPI**.

Une interface **Streamlit** permet aux utilisateurs de déposer un fichier audio et de récupérer les fichiers générés (MIDI, partition PDF et représentations graphiques).

Le déploiement de cette couche applicative est entièrement automatisé par une pipeline **GitHub Actions**, qui exécute :

* les tests automatisés ;
* les contrôles qualité (Ruff et MyPy) ;
* la vérification de la couverture de tests ;
* la construction de l'image Docker ;
* sa publication sur **GitHub Container Registry** ;
* le déploiement automatique sur **Hugging Face Spaces**.

Cette séparation entre plateforme Data et couche applicative permet de faire évoluer indépendamment les pipelines de préparation des données, les expérimentations de Machine Learning et l'application destinée aux utilisateurs.

# 5. Mise en œuvre du Data Lake et des processus ETL

## 5.1. Collecte et intégration des données (C1.3)

Les données utilisées pour entraîner le modèle proviennent de deux corpus publics complémentaires :

| Source          | Audio | Annotations |
| --------------- | ----- | ----------- |
| GuitarSet       | WAV   | JAMS        |
| IDMT-SMT-Guitar | WAV   | XML         |

Afin de garantir la reproductibilité des traitements, les données ne sont jamais manipulées directement depuis Internet.

La collecte est réalisée en deux étapes :

1. **Pipeline de téléchargement**

   Les jeux de données sont téléchargés localement puis vérifiés avant leur intégration.

2. **Pipeline d'ingestion**

   Cette seconde étape alimente l'infrastructure de données en répartissant les informations selon leur nature :

   * les fichiers audio et annotations originales sont déposés dans le bucket **raw** du Data Lake MinIO ;
   * les métadonnées descriptives des fichiers sont enregistrées dans PostgreSQL ;
   * les annotations musicales sont extraites et indexées dans MongoDB afin de faciliter leur exploitation par les traitements ultérieurs.

Cette séparation entre données binaires et métadonnées permet d'éviter les redondances tout en simplifiant les recherches et la traçabilité.

L'ensemble des données utilisées est constitué de jeux de données publics ; aucune donnée personnelle n'est collectée ni traitée. Les exigences du RGPD sont donc respectées par conception.

## 5.2. Organisation du Data Lake (C1.1)

Le stockage repose sur MinIO, utilisé comme implémentation d'un Data Lake compatible avec l'API S3.

Les données sont réparties dans plusieurs buckets spécialisés.

| Bucket    | Contenu                                                                     |
| --------- | --------------------------------------------------------------------------- |
| raw       | fichiers audio et annotations d'origine                                     |
| processed | audios nettoyés, caractéristiques extraites et échantillons d'apprentissage |
| mlflow    | artefacts produits lors des expérimentations                                |
| output    | réservé aux futurs résultats produits par l'API                             |

Cette organisation présente plusieurs avantages :

* conservation permanente des données sources ;
* séparation claire entre données brutes et données transformées ;
* possibilité de reconstruire intégralement les jeux d'entraînement ;
* simplification de la maintenance et des sauvegardes.

Le Data Lake constitue ainsi le référentiel unique de stockage des objets volumineux manipulés par la plateforme.

## 5.3. Construction des données d'entraînement (C1.4)

Après leur ingestion, les fichiers audio traversent une chaîne de prétraitement entièrement automatisée.

Chaque pipeline réalise successivement :

* le nettoyage du signal audio ;
* la normalisation des amplitudes ;
* l'extraction des représentations fréquentielles (CQT notamment) ;
* l'alignement temporel avec les annotations musicales ;
* la génération d'échantillons destinés au Machine Learning.

Les nouveaux objets produits sont enregistrés dans le bucket **processed**.

Parallèlement, MongoDB conserve les métadonnées permettant de reconstituer précisément les traitements réalisés :

* pipeline exécuté ;
* paramètres utilisés ;
* fichiers d'entrée ;
* fichiers produits ;
* échantillons générés.

Cette approche garantit la reproductibilité complète des jeux de données d'entraînement.

## 5.4. Gestion des métadonnées

L'architecture distingue volontairement les données métier des métadonnées techniques.

### 5.4.1. PostgreSQL

PostgreSQL centralise les informations relationnelles sur les ressources manipulées par la plateforme :

* références des fichiers audio ;
* références des annotations ;
* informations descriptives associées.

Cette base facilite les recherches structurées et garantit la cohérence des données.

### 5.4.2. MongoDB

MongoDB conserve les informations évolutives produites par les différents pipelines :

* historique des traitements ;
* paramètres d'exécution ;
* composition des datasets ;
* relations entre fichiers, échantillons et pipelines.

Ce choix est particulièrement adapté à des documents dont la structure évolue au fil du projet.

La combinaison de PostgreSQL et MongoDB permet ainsi d'associer la robustesse d'un modèle relationnel à la flexibilité d'une base documentaire.

# 6. Préparation à la montée en charge (C1.2)

Le volume actuel des données permet l'exécution des pipelines sur une seule machine en Python.

Toutefois, l'architecture a été pensée dès sa conception pour permettre une évolution vers des traitements distribués.

Une infrastructure Apache Spark est déjà intégrée au projet via Docker Compose et comprend :

* un nœud Spark Master ;
* deux Spark Workers.

Cette infrastructure n'est pas encore utilisée en production. Elle constitue néanmoins le socle technique de la prochaine évolution du projet.

L'objectif est de remplacer progressivement les pipelines Python de prétraitement par des traitements distribués exécutés par Spark afin de :

* paralléliser le nettoyage des fichiers audio ;
* accélérer l'extraction des caractéristiques ;
* réduire les temps de traitement lors de l'augmentation du volume de données ;
* conserver la même organisation générale du Data Lake.

Le choix d'intégrer dès maintenant cette infrastructure permet d'anticiper les besoins futurs sans remettre en cause l'architecture existante.

# 7. Infrastructure as Code et reproductibilité

L'ensemble de l'environnement de développement est défini sous forme de code à l'aide de **Docker Compose**. Cette approche permet de reconstruire automatiquement une plateforme identique sur toute machine disposant de Docker.

L'infrastructure comprend l'ensemble des composants nécessaires au cycle de vie du projet :

* MinIO servant de Data Lake ;
* MongoDB pour le stockage documentaire des métadonnées ;
* PostgreSQL pour les données relationnelles ;
* PostgreSQL dédié au suivi des expérimentations MLflow ;
* MLflow pour le suivi des expériences de Machine Learning ;
* Apache Spark (Master et Workers) destiné aux futurs traitements distribués ;
* FastAPI et Streamlit constituant la couche applicative ;
* Mongo Express et pgAdmin facilitant l'administration des bases de données.

La configuration des services est centralisée dans un fichier `.env`, permettant de séparer les paramètres d'exécution (identifiants, ports, buckets, URI) du code source.

Les dépendances Python sont gérées avec **uv**, garantissant une installation reproductible grâce au verrouillage des versions (`uv.lock`).

Cette approche présente plusieurs avantages :

* environnement identique pour tous les développeurs ;
* installation rapide de la plateforme ;
* réduction des erreurs liées aux différences de configuration ;
* simplification des démonstrations et de la maintenance.

Le jury peut ainsi reconstruire l'intégralité de l'environnement en exécutant simplement :

```bash
docker compose up -d
```

L'ensemble des services est alors automatiquement déployé et interconnecté.

# 8. Industrialisation et qualité logicielle

La couche applicative fait l'objet d'une industrialisation complète grâce à une chaîne d'intégration et de déploiement continus (**CI/CD**) implémentée avec **GitHub Actions**.

À chaque modification de la branche principale ou lors de l'ouverture d'une Pull Request, plusieurs contrôles sont exécutés automatiquement.

## 8.1. Validation du code

La pipeline réalise successivement :

* installation reproductible de l'environnement Python avec **uv** ;
* exécution des tests unitaires et d'intégration ;
* calcul de la couverture de tests avec seuil minimal imposé ;
* analyse statique du code avec **Ruff** ;
* vérification du typage avec **MyPy**.

Cette étape garantit que chaque évolution respecte les exigences de qualité définies pour le projet.

## 8.2. Construction et publication de l'application

Lorsque les validations sont satisfaites :

* une image Docker est construite automatiquement ;
* l'image est publiée sur **GitHub Container Registry (GHCR)** ;
* le dépôt **Hugging Face Spaces** est mis à jour automatiquement afin de redéployer l'application.

Le déploiement de l'application ne nécessite ainsi aucune intervention manuelle.

Cette automatisation garantit la cohérence entre le code source, l'image distribuée et l'application accessible aux utilisateurs.

# 9. Évolutivité de la plateforme

L'architecture a été conçue pour permettre des évolutions sans remise en cause de son organisation générale.

Plusieurs axes d'amélioration sont déjà identifiés.

## 9.1. Calcul distribué

Les pipelines ETL sont actuellement exécutés en Python.

L'infrastructure Spark déjà présente permettra, dans une version ultérieure, de distribuer les traitements de prétraitement audio afin d'améliorer les performances sur des volumes de données plus importants.

## 9.2. MLOps

Les expérimentations sont déjà suivies avec MLflow.

L'évolution naturelle de la plateforme consiste à automatiser davantage le cycle de vie des modèles, notamment :

* sélection automatique du meilleur modèle ;
* validation avant mise en production ;
* déploiement automatisé vers l'API.

## 9.3. Valorisation des résultats

Le bucket **output**, déjà prévu dans le Data Lake, pourra être utilisé pour archiver les productions générées par l'API (MIDI, partitions, représentations graphiques), facilitant ainsi leur partage ou leur réutilisation.

Ces évolutions pourront être réalisées sans modifier les fondements de l'architecture actuelle.

# 10. Conclusion

L'architecture conçue répond aux exigences fonctionnelles et techniques du projet tout en préparant ses évolutions futures.

Elle repose sur une séparation claire entre les différentes responsabilités :

* stockage des données dans un Data Lake ;
* gestion des métadonnées ;
* pipelines ETL de préparation des données ;
* expérimentation des modèles avec MLflow ;
* déploiement d'une application web de transcription musicale.

Cette organisation garantit la reproductibilité des traitements, la traçabilité des données, la maintenabilité du projet et son évolutivité.

Au regard du référentiel RNCP 35288, ce travail démontre la maîtrise des compétences du bloc 1 :

* **C1.1** : conception d'une architecture de données intégrant un Data Lake et des bases spécialisées ;
* **C1.2** : prise en compte du calcul distribué grâce à l'intégration d'une infrastructure Apache Spark ;
* **C1.3** : collecte et intégration de données issues de plusieurs sources dans un processus maîtrisé ;
* **C1.4** : conception et mise en œuvre de pipelines ETL permettant de nettoyer, transformer et organiser les données en vue de leur exploitation par les modèles de Machine Learning.

L'ensemble de cette infrastructure est intégralement décrit sous forme de code, reproductible via Docker Compose et constitue le socle technique de la plateforme de transcription automatique développée dans le cadre de ce projet.
