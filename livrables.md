# Liste des livrables par bloc de compétences

Cliquer sur les liens pour naviguer vers les livrables.

## BC01 - Construction et alimentation d'une infrastructure de gestion de données

> Une étude de 1 page décrivant schématiquement l'infrastructure conceptualisée et le code source permettant de construire l'infrastructure.

| Lien | Description |
| :- | :- |
| [Livrable 1](./livrables/livrable1_infrastructure_conceptualisee.pdf) | Infrastructure conceptualisée. |

Aucun scrapper n'a été utilisé dans ce projet. Afin de valider la compétence **C1.3**, vous pouvez consulter mon [ECF1](https://github.com/DamienDESSAUX-M2i/DESSAUX_Damien_ECF1/blob/main/src/extractors/books_scrapper.py) pour une implémentation de la bibliothèque **Beautiful Soup**.

Spark n'a pas été utilisé dans ce projet. Afin de valider les compétences **C1.2** et **C2.3**, vous pouvez consulter mon [ECF3](https://github.com/DamienDESSAUX-M2i/DESSAUX_Damien_ECF3/blob/main/notebooks/05_spark_mllib.py) pour une implémentation de **Spark MLlib**.

## BC02 - Analyse exploratoire, descriptive et inférentielle de données

> Deux codes sources décrivant l'analyse de chacune des bases de données, incluant la construction de graphiques.

| Lien | Description |
| :- | :- |
| [Livrable 2.1](./audio_midi/notebooks/21_eda_guitarset.ipynb) | EDA GuitarSet. |
| [Livrable 2.2](./audio_midi/notebooks/22_eda_idmt_smt_guitar.ipynb) | EDA IDMT-SMT-GUITAR. |
| [Livrable 2.3](./audio_midi/notebooks/23_eda_dataset_frame_wise.ipynb) | EDA Dataset frame-wise. |

## BC03 - Analyse prédictive de données structurées par l'intelligence artificielle

> Trois codes sources incluant la conception et l'optimisation de trois algorithmes adaptés à la problématiques ainsi que des recommandations sur les prédictions obtenues.

| Lien | Description |
| :- | :- |
| [Livrable 3.1](./audio_midi/notebooks/31_cqt_baseline_trainer.ipynb) | Conception et évaluation de 4 modèles : OVR LogisticRegression, OVR LinearSVC, OVR HistGradientBoosting, OVR SGDClassifier. Optimisation du modèle OVR HistGradientBoosting. Etude de l'ajout d'une PCA. |

Le projet est intrinsèquement supervisé. Cependant un algorithme non supervisé pourrait avoir plusieurs intérêts, comme l'explorer la structure des données ou encore détecter des anomalies. Par manque de temps je n'ai réalisée qu'un réduction de dimension dans le [livrable 3.1](./audio_midi/notebooks/31_cqt_baseline_trainer.ipynb). Afin de valider la compétence **C3.3**, vous pouvez consulter le notebook [C33-analyse_non_supervisee](./livrables/C33-analyse_non_supervisee.ipynb).

## BC04 - Analyse prédictive de données non-structurées par l'intelligence artificielle

> Un code source incluant la conception de l'algorithme et les métriques de performances sur des données de validation.

| Lien | Description |
| :- | :- |
| [Livrable 4.1](./audio_midi/notebooks/41_cqt_mlp_trainer.ipynb) | MLP sur dataset frame-wise. |
| [Livrable 4.2](./audio_midi/notebooks/42_cqt_rcnn_trainer.ipynb) | CNN + MLP et RCNN sur dataset frame-wise avec context window. |

## BC05 - Industrialisation d'un algorithme d'apprentissage automatique et automatisation des processus de décision

> Un code source contenant la création de l'environnement standardisé, le déploiement de l'algorithme et l'application web ainsi qu'un URL vers l'application déployée.

| Lien | Description |
| :- | :- |
| [Livrable 5](./livrables/livrable5_industrialisation.md) | Déploiement de l'application sur HuggingFace. |

## BC06 - Direction de projets de gestion de données

> Le code source correspond au projet data développé et une soutenance orale de 10 minutes suivie de 5 minutes de questions et éventuellement de 5 minutes d'entretien.

| Lien | Description |
| :- | :- |
| [Livrable 6](./livrables/soutenance/main.pdf) | Support pour la soutenance. |
