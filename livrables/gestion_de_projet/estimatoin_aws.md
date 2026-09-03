<h1>Estimation AWS - Plateforme de transcription audio → MIDI</h1>

**Périmètre :** Première mise en production

**Région cible :** AWS `eu-west-3` - Paris

**Volume cible :** 1 000 audios par jour

**GPU :** Exclu de cette première estimation

**Spark :** Exclu de cette première estimation

# 1. Table des matières

- [1. Table des matières](#1-table-des-matières)
- [2. Synthèse des besoins et solution AWS](#2-synthèse-des-besoins-et-solution-aws)
- [3. Capacité de stockage](#3-capacité-de-stockage)
- [4. Capacité de calcul nécessaire](#4-capacité-de-calcul-nécessaire)
- [5. Data Platform](#5-data-platform)
- [6. MongoDB](#6-mongodb)
- [7. PostgreSQL](#7-postgresql)
- [8. MLflow](#8-mlflow)
- [9. Couche applicative](#9-couche-applicative)
- [10. API](#10-api)
- [11. ETL Python](#11-etl-python)
- [12. Estimation des coûts](#12-estimation-des-coûts)
- [13. Politique de stockage S3](#13-politique-de-stockage-s3)
- [14. Hors périmètre](#14-hors-périmètre)
- [15. Conclusion](#15-conclusion)

# 2. Synthèse des besoins et solution AWS

La solution est constituée de deux blocs :

1. **Data Platform** : stockage des données sources, annotations, métadonnées, traitements et suivi des expériences ML.
2. **Couche applicative** : réception des fichiers audio, transcription, génération des fichiers MIDI et des représentations graphiques.

Un déploiement AWS remplace les services d'infrastructure du `docker-compose` par des services cloud :

| Besoin | Solution AWS proposée |
| :-: | :-: |
| Stockage fichiers | Amazon S3 |
| API / application | Amazon ECS + Fargate |
| ETL Python | ECS Fargate, à la demande |
| Base PostgreSQL | Amazon RDS PostgreSQL |
| MongoDB | MongoDB Atlas sur AWS |
| MLflow | ECS Fargate |
| Images Docker | Amazon ECR |
| Logs | Amazon CloudWatch |
| Secrets | AWS Secrets Manager |
| Exposition HTTP/HTTPS | Application Load Balancer |
| Spark | Hors périmètre |

# 3. Capacité de stockage

**Hypothèses :**

| Paramètre | Valeur |
| :-: | -: |
| Audios traités | 1 000 / jour |
| Durée moyenne | 1 min |
| Taille moyenne | 10 Mo |
| Temps actuel | 90 s / audio |
| CPU actuel | 2 vCPU |
| RAM actuelle | 16 Go |
| GPU | Non |
| Région | `eu-west-3` |

Pour les fichiers audio entrants, le volume serait de 1 000 audios × 10 Mo = **10 Go/jour**, soit environ **300 Go/mois** et **3,6 To/an**.

Ce chiffre ne comprend pas les données d'entraînement, les fichiers prétraités, les échantillons frame-wise, ni les modèles.

Il est donc important de mettre en place une **politique de rétention** plutôt que de conserver indéfiniment toutes les données dans la classe S3 Standard.

Amazon S3 facture principalement le stockage, les requêtes et le transfert de données selon l'usage.

Au prix mensuel de **0,025 €/Go**, on peut estimer le budget du stockage S3 à environ **50-150 €/mois**.

# 4. Capacité de calcul nécessaire

Actuellement, 1 audio nécessite 90 secondes de calcul sur 2 vCPU / 16 Go RAM.

Pour 1 000 audios, cela représente **1 000 × 90 s = 90 000 secondes**, soit **25 heures de calcul CPU par jour**.

Il est nécessaire d'augmenter la capacité de calcul pour traiter le volume de données quotidien.

On pourra tester plusieurs configurations en gardant à l'esprit que la facturation dépend du vCPU, de la mémoire et de la durée d'exécution :
```text
Configuration A
2 vCPU / 16 Go
→ benchmark actuel : ~90 s

Configuration B
4 vCPU / 16 Go
→ objectif expérimental : ~45-60 s

Configuration C
8 vCPU / 16-32 Go
→ objectif expérimental : ~30-45 s
```

Pour une première estimation, on dimensionne l'API sur **4 vCPU / 16 Go**.

# 5. Data Platform

La Data Platform conserve la structure logique actuelle.

S3 devient le remplacement direct de MinIO et contiendra notamment :

```text
s3://audio-midi/
├── raw/            <- Données d'entrainement + audio entrants
├── preprocessed/   <- Echantillons Frame-Wise
├── output/         <- Artéfacts API
└── mlflow/         <- Backend MLflow
```

# 6. MongoDB

MongoDB contient les annotations, les métadonnées des traitements et les informations associées aux données d'entraînement

On utilisera **MongoDB Atlas** pour un budget d'environ **50-80 €/mois**.

# 7. PostgreSQL

Une seule instance RDS PostgreSQL hébergera trois bases de données :

- pour les métadonnées des datasets d'entrainement,
- pour la couche applicative,
- comme backend pour mlflow.

Cela évite de payer trois instances PostgreSQL indépendantes.

Pour une première production, on utilisara **RDS PostgreSQL Single-AZ** avec un coût d'environ **40-70 €/mois**.

# 8. MLflow

MLflow sera conservé sous forme de conteneur et déployé dans ECS Fargate.

Il aura pour backend S3 et RDS Postgres.

Le coût estimé est d'environ **20-40 €/mois**.

# 9. Couche applicative

La couche applicative produit :

- MIDI
- piano-roll PNG
- piano-roll SVG
- partition PNG
- partition SVG

Ces fichiers seront stockés dans le bucket output du S3.

PostgreSQL conservera uniquement des métadonnées.

# 10. API

L'API devient une tâche ECS Fargate avec pour configuration **4vCPU 16GB RAM**.

Elle réalise directement la transcription. Une requête HTTP reste ouverte pendant le temps de transcription.

L'API représente le coût le plus important en raison de la charge de calculs. Une première estimation des coût serait environ **150-200 €/mois**.

Dans l'idéal, l'API ne devrait pas réaliser les calculs lourds, cette tâche devrait être dédiée à des workers de transcription.

# 11. ETL Python

Un conteneur ETL remplace l'exécution locale.

Il pourrait être exécuté sous forme de tâche ECS.

Il n'est pas nécessaire de faire tourner le conteneur 24/7.

Le coût restera faible, environ **5-20 €/mois**.

# 12. Estimation des coûts

| Poste | Solution | Estimation |
| :-: | :-: | -: |
| API | ECS Fargate | 150-200 € |
| MLflow | ECS Fargate | 20-40 € |
| ETL | Fargate ponctuel | 5-20 € |
| PostgreSQL | RDS | 40-70 € |
| MongoDB | Atlas | 50-80 € |
| S3 | données + artefacts | 50-150 € |
| ALB | exposition API | 20-30 € |
| CloudWatch | logs / monitoring | 10-30 € |
| ECR | images Docker | 1-5 € |
| Secrets Manager | secrets | 2-5 € |
| réseau / IPv4 / divers | VPC | 20-50 € |
| **TOTAL** | | **350-700 €/mois** |

On retiendra environ **600 €/mois** pour le budget du projet avec une enveloppe maximale de **1 000 €/mois**.

# 13. Politique de stockage S3

Le volume d'entrée est déjà de 10 Go/jour soit 300 Go/mois ou 3,6 To/an.

Si les audios sont conservés indéfiniment en S3 Standard, le coût de stockage va progressivement augmenter.

Une politique de cycle de vie devra être instaurée :

```text
0-3 mois -> S3 Standard

3-12 mois -> S3 Infrequent Access

>12 mois -> Glacier / Deep Archive
```

Les données d'entraînement importantes peuvent avoir une politique différente.

S3 propose plusieurs classes de stockage précisément pour adapter le coût à la fréquence d'accès.

# 14. Hors périmètre

L'estimation actuelle ne comprend pas :

- l'inférence via GPU,
- le calcul distribué avec Spark,
- un environnement de développement permanent,
- le coûts de développement et d'exploitation,
- les besoins de haute disponibilité,
- le coût de backups,
- l'entraînement de modèles à grande échelle.

Ces coût devront être estimés séparément.

# 15. Conclusion

Pour une première mise en production AWS de la solution de transcription audio vers MIDI, une architecture **ECS Fargate + S3 + RDS PostgreSQL + MongoDB Atlas** est adaptée au niveau de maturité actuel du projet.

Le dimensionnement recommandé est :

```text
API              -> 4 vCPU / 16 Go
MLflow           -> 0,5 vCPU / 1-2 Go
ETL              -> 2 vCPU / 16 Go (exécution ponctuelle)
PostgreSQL       -> RDS Single-AZ
MongoDB          -> MongoDB Atlas
Object storage   -> S3
```

> Chiffre à retenir :
> - **Budget AWS de référence : 600 €/mois.**
> - **Fourchette de prévision : 350-700 €/mois.**
>
> Les principaux facteurs de coût sont **le calcul de transcription** et le stockage.
