<h1>Note de cadrage</h1>
<h2>Projet de transcription audio vers MIDI - GuitarFlow</h2>

# Table des matières

- [Table des matières](#table-des-matières)
- [1. Contexte et enjeux métier](#1-contexte-et-enjeux-métier)
  - [1.1. Présentation du projet](#11-présentation-du-projet)
  - [1.2. Constat métier](#12-constat-métier)
  - [1.3. Opportunité](#13-opportunité)
- [2. Objectifs du projet](#2-objectifs-du-projet)
  - [2.1. Objectif principal](#21-objectif-principal)
  - [2.2. Objectifs SMART](#22-objectifs-smart)
  - [2.3. Nature du projet](#23-nature-du-projet)
- [3. Cibles et usages prioritaires](#3-cibles-et-usages-prioritaires)
  - [3.1. Utilisateurs visés](#31-utilisateurs-visés)
  - [3.2. Cible prioritaire phase 1](#32-cible-prioritaire-phase-1)
  - [3.3. Cas d’usage principal](#33-cas-dusage-principal)
- [4. Périmètre du projet](#4-périmètre-du-projet)
  - [4.1. Inclus dans le périmètre](#41-inclus-dans-le-périmètre)
  - [4.2. Exclus dans le périmètre](#42-exclus-dans-le-périmètre)
- [5. Hypothèses de faisabilité](#5-hypothèses-de-faisabilité)
  - [5.1. Orientation technique](#51-orientation-technique)
  - [5.2. Technologies envisagées](#52-technologies-envisagées)
    - [5.2.1. Préprocessing audio](#521-préprocessing-audio)
    - [5.2.2. Features extraction](#522-features-extraction)
    - [5.2.3. Modélisation](#523-modélisation)
  - [5.3. Données](#53-données)
- [6. Bénéfices attendus](#6-bénéfices-attendus)
  - [6.1. Gains métier estimés](#61-gains-métier-estimés)
  - [6.2. Valeur attendue](#62-valeur-attendue)
- [7. Organisation projet](#7-organisation-projet)
  - [7.1. Ressources](#71-ressources)
  - [7.2. Infrastructure prévisionnelle](#72-infrastructure-prévisionnelle)
- [8. Risques identifiés](#8-risques-identifiés)
- [9. Planning macro prévisionnel](#9-planning-macro-prévisionnel)
  - [9.1. Jalons de pilotage](#91-jalons-de-pilotage)
  - [9.2. Budget prévisionnel](#92-budget-prévisionnel)
  - [9.3. Valorisation estimative phase 1](#93-valorisation-estimative-phase-1)
  - [9.4. Cout du développement](#94-cout-du-développement)
  - [9.5. Hypothèse financière](#95-hypothèse-financière)
- [10. KPIs de pilotage](#10-kpis-de-pilotage)
- [11. Critères de succès](#11-critères-de-succès)
- [12. Perspectives et roadmap](#12-perspectives-et-roadmap)
  - [12.1. Phase 2 — Industrialisation (hors périmètre)](#121-phase-2--industrialisation-hors-périmètre)
- [13. Décision attendue](#13-décision-attendue)
  - [13.1. Demande de validation](#131-demande-de-validation)

# 1. Contexte et enjeux métier

## 1.1. Présentation du projet

*GuitarFlow* souhaite développer un prototype de service capable de transformer automatiquement un enregistrement audio de guitare en fichier MIDI exploitable dans des logiciels de MAO (Musique Assistée par Ordinateur).

Le projet s’inscrit dans une démarche d’automatisation des tâches de retranscription musicale et d’assistance à la création de contenu pédagogique et créatif.

## 1.2. Constat métier

La retranscription manuelle d’une performance guitare vers un format éditable représente une opération :
- chronophage,
- nécessitant une expertise musicale avancée,
- difficilement scalable pour des usages pédagogiques ou créatifs.

À titre indicatif, la retranscription manuelle d’une minute d’audio peut nécessiter entre 15 et 30 minutes de travail selon la complexité du morceau.

Bien que plusieurs outils de transcription audio vers MIDI existent sur le marché, la transcription fiable de guitare polyphonique dans des conditions réelles demeure un sujet complexe, laissant une marge d’amélioration sur la robustesse, l’accessibilité et l’automatisation des usages pédagogiques et créatifs.

## 1.3. Opportunité

Le projet vise à :
- réduire drastiquement le temps de retranscription,
- simplifier la création de contenus pédagogiques,
- accélérer les workflows de composition musicale,
- proposer un démonstrateur technologique autour de l’IA musicale.

# 2. Objectifs du projet

## 2.1. Objectif principal

Développer un prototype fonctionnel capable de :
- recevoir un fichier audio .wav de guitare,
- générer automatiquement un fichier MIDI exploitable,
- produire une visualisation piano-roll,
- produire une partition ou une tablature (optionnelle).
- exposer le service via une interface web déployée sur Hugging Face.

## 2.2. Objectifs SMART

| Objectif | Cible |
| :- | :- |
| Détection des notes polyphoniques | F1-score ≥ 90 % |
| Temps moyen d’inférence | < 10 secondes pour 1 minute audio |
| Disponibilité du prototype | Démonstration fonctionnelle avant le 31/07/2026 |
| Déploiement | API accessible via interface web |
| Taux de correction manuelle cible | < 10 % |

## 2.3. Nature du projet

Cette phase correspond à un Proof of Concept (POC).

L’objectif est de :
- valider la faisabilité technique,
- mesurer les performances du modèle,
- démontrer la valeur métier du service,
- préparer une éventuelle phase d’industrialisation.

La mise en production industrielle n’entre pas dans le périmètre de cette phase.

# 3. Cibles et usages prioritaires

## 3.1. Utilisateurs visés

Le service cible principalement :
- professeurs de guitare,
- créateurs de contenus pédagogiques,
- musiciens amateurs,
- compositeurs.

## 3.2. Cible prioritaire phase 1

La phase 1 cible prioritairement :
- les professeurs de guitare,
- les créateurs de contenu pédagogique.

Ces profils présentent :
- des besoins fréquents de retranscription,
- des workflows répétitifs,
- un fort gain potentiel en productivité.

## 3.3. Cas d’usage principal

Exemple d’usage cible :
> Un professeur de guitare enregistre un exercice audio, dépose le fichier dans l’application et récupère automatiquement un fichier MIDI afin de produire rapidement un support pédagogique éditable.

# 4. Périmètre du projet

## 4.1. Inclus dans le périmètre

Le périmètre de la phase 1 comprend :
- prise en charge des guitares acoustiques et électriques,
- accordage standard EADGBE,
- traitement de fichiers audio .wav,
- génération de fichiers MIDI,
- visualisation piano-roll,
- génération optionnelle de partition et tablature,
- développement d’une API d’inférence,
- déploiement du prototype sur Hugging Face Spaces.

## 4.2. Exclus dans le périmètre

Les éléments suivants sont exclus de la phase 1 :
- autres instruments,
- open tunings et accordages alternatifs,
- détection des techniques d’expression de jeu :
  - bends,
  - slides,
  - vibrato,
  - hammer-on / pull-off,
- traitement temps réel,
- application mobile,
- industrialisation cloud.

# 5. Hypothèses de faisabilité

## 5.1. Orientation technique

Le prototype reposera sur une approche supervisée de transcription audio utilisant :
- extraction de features fréquentielles,
- classification frame-wise,
- architecture de type RCNN.

## 5.2. Technologies envisagées

### 5.2.1. Préprocessing audio

Le pipeline de préparation des données audio comprendra :
- harmonisation des formats audio,
- conversion mono,
- rééchantillonnage,
- normalisation des signaux,
- réduction du bruit,
- suppression des silences.

Plusieurs techniques de filtrage et de débruitage pourront être évaluées afin d’améliorer la qualité des signaux d’entrée.

### 5.2.2. Features extraction

Plusieurs représentations fréquentielles du signal audio seront étudiées :
- STFT,
- Mel Spectrogram,
- MFCC,
- CQT (Constant-Q Transform),
- chromagrammes.

Ces représentations visent à capturer les caractéristiques temporelles, fréquentielles et harmoniques nécessaires à la transcription polyphonique de la guitare.

### 5.2.3. Modélisation

Plusieurs approches de modélisation seront évaluées :
- modèles de baseline simples,
- réseaux de neurones fully connected (MLP),
- architectures convolutionnelles récurrentes (Recurrent Convolutional Neural Networks).

L’objectif est d’identifier le meilleur compromis entre :
- performances de transcription,
- robustesse,
- temps d’inférence.

## 5.3. Données

Aucune donnée propriétaire n’est disponible.

Le projet s’appuiera sur des datasets publics spécialisés :
- GuitarSet
- IDMT-SMT-Guitar

Une analyse des licences sera réalisée avant utilisation.

# 6. Bénéfices attendus

## 6.1. Gains métier estimés

| Indicateur | Situation actuelle | Cible projet |
| :- | :- | :- |
| Temps moyen de retranscription | 15–30 min | < 1 min |
| Effort manuel | Élevé | Faible |
| Exploitabilité du contenu | Limitée | Immédiate |
| Partage et édition | Complexes | Simplifiés |

## 6.2. Valeur attendue

Le projet vise principalement :
- un gain de productivité,
- une réduction du travail manuel,
- une accélération des workflows pédagogiques et créatifs.

# 7. Organisation projet

## 7.1. Ressources

| Rôle | Ressource |
| :- | :- |
| Développeur concepteur en science des données | Damien DESSAUX |

## 7.2. Infrastructure prévisionnelle

L’infrastructure prévisionnelle repose principalement sur des composants gratuits ou locaux :
| Composant | Solution |
| :- | :- |
| Stockage objet | MinIO local |
| Base documentaire | MongoDB local |
| Base relationnelle | PostgreSQL local |
| Hébergement démonstrateur | Hugging Face Spaces |

# 8. Risques identifiés

| Risque | Impact | Probabilité | Plan de mitigation |
| :- | :- | :- | :- |
| Restrictions de licence sur les datasets | Élevé | Moyen | Validation juridique préalable |
| Volume de données insuffisant | Élevé | Élevé | Data augmentation et transfert learning |
| Performances insuffisantes sur polyphonie | Élevé | Moyen | Benchmark de plusieurs architectures |
| Temps d’inférence trop élevé | Moyen | Moyen | Optimisation modèle et quantization |
| Variabilité de qualité audio | Moyen | Élevé | Préprocessing et normalisation audio |

# 9. Planning macro prévisionnel

| Échéance | Livrable / activité |
| :- | :- |
| J0 | Kick-off projet |
| J+7 | Validation de la note de cadrage |
| J+14 | Ingestion des datasets |
| J+20 | Analyse exploratoire des données |
| J+25 | Préprocessing audio et extraction des features |
| J+28 | Construction des datasets frame-wise |
| J+42 | Benchmark des modèles candidats |
| J+49 | Implémentation du pipeline ML complet |
| J+63 | Développement de l’API d’inférence |
| J+70 | Dockerisation et déploiement sur Hugging Face Spaces |
| 31/07/2026 | Démonstration de restitution phase 1 |

## 9.1. Jalons de pilotage

| Jalon | Critère de validation |
| :- | :- |
| GO Datasets | Données validées et exploitables |
| GO Modèle | Baseline opérationnelle |
| GO Prototype | Pipeline complet exécutable |
| GO Démonstration | API et interface accessibles |

## 9.2. Budget prévisionnel

## 9.3. Valorisation estimative phase 1

| Poste | Charge estimée |
| :- | :- |
| Data preparation | 15 jours |
| Développement ML | 15 jours |
| API / Backend | 10 jours |
| Déploiement / DevOps | 5 jours |

## 9.4. Cout du développement

| Poste | Estimation |
| :- | :- |
| Développement ML / backend | À estimer |
| Hébergement cloud | 0 € (phase prototype) |
| Infrastructure locale | Réutilisation existante |

## 9.5. Hypothèse financière

La phase 1 représente une phase de prototypage avec infrastructure majoritairement gratuite.

La valorisation théorique du projet est estimée entre 18 k€ et 25 k€ selon les charges d’ingénierie mobilisées.

Une phase 2 d’industrialisation fera l’objet d’un chiffrage distinct.

# 10. KPIs de pilotage

| KPI | Objectif cible | Statut |
| :- | :- | :- |
| F1-score transcription | ≥ 90 % | À mesurer |
| Temps moyen d’inférence | < 10 s | À mesurer |
| Taux de correction manuelle | < 10 % | À mesurer |
| Satisfaction utilisateur | > 80 % | À mesurer |
| Disponibilité démonstrateur | 100 % lors de la présentation | À mesurer |

# 11. Critères de succès

La phase 1 sera considérée comme validée si :
- le prototype est accessible via interface web,
- la transcription MIDI est fonctionnelle,
- les performances minimales sont atteintes,
- le démonstrateur permet un usage exploitable en contexte pédagogique.

# 12. Perspectives et roadmap

## 12.1. Phase 2 — Industrialisation (hors périmètre)

Les évolutions potentielles identifiées sont :
- amélioration de la robustesse polyphonique,
- détection avancée des techniques de jeu,
- support d’accordages alternatifs,
- transcription temps réel,
- montée en charge cloud,
- extension multi-instruments.

# 13. Décision attendue

## 13.1. Demande de validation

Le comité de pilotage est sollicité afin de valider le lancement de la phase 1 du projet GuitarFlow.

Cette phase couvre :
- l’étude de faisabilité,
- la construction du pipeline data,
- l’entraînement du modèle,
- le déploiement du prototype de démonstration.

La phase 2, dédiée à l’industrialisation et à la mise en production, fera l’objet d’une décision GO / NO-GO distincte accompagnée d’un budget prévisionnel détaillé.

---

**Auteur:** Damien DESSAUX