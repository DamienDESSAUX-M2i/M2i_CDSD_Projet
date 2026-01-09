# Sujet de Soutenance pour le titre RNCP35288 - Concepteur Developpeur en Science des Donnees

## Blocs de competences du titre RNCP35288

| Bloc | Descriptif |
| :- | :- |
| BC01 | Construction et alimentation d'une infrastructure de gestion de donnees |
| BC02 | Analyse exploratoire, descriptive et inferentielle de donnees |
| BC03 | Analyse predictive de donnees structurees par IA (Machine Learning) |
| BC04 | Analyse predictive de donnees non-structurees par IA (Deep Learning) |
| BC05 | Industrialisation d'un algorithme et automatisation des processus de decision |
| BC06 | Direction de projets de gestion de donnees |

## Livrables

### BC01 - Infrastructure de donnees

- Schema d'architecture technique
- Scripts ETL documentes
- Base de donnees operationnelle

### BC02 - Analyse exploratoire

- Notebook d'analyse exploratoire
- Rapport statistique
- Visualisations commentees

### BC03 - Machine Learning

- Pipeline de preprocessing
- Modeles entraines et evalues
- Rapport de performance comparative

### BC04 - Deep Learning

- Architecture du reseau de neurones
- Modele entraine
- Analyse des resultats et explicabilite

### BC05 - Industrialisation

- API fonctionnelle
- Conteneur Docker
- Documentation de deploiement
- Monitoring en place

### BC06 - Gestion de projet

- Planning et suivi de projet
- Documentation technique complete
- Presentation de soutenance
- Analyse des risques et ROI

## Sujet

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

## Packages Python

Liste de packages Python pouvant être utiles pour le projet. Une liste non exhaustive de pakages pour le traitement du son en Python est disponible ici : https://github.com/andreimatveyeu/awesome-python-audio/blob/main/README.md

| Package | Documentation | Description|
| :- | :- | :- |
| **JAMS** | https://jams.readthedocs.io/en/stable/index.html | Annotation musicale en JSON pour la recherche MIR (music information retrieval) |
| **lxml** | https://lxml.de/ | Traitement de fichier au format XML |
| **Pydub** | https://github.com/jiaaro/pydub | Manipulation de fichier audio |
| **Librosa** | https://librosa.org/doc/latest/index.html | Analyse audio et musique |
| **Essentia** | https://essentia.upf.edu/ | Aanalyse, description et synthèse audio et musicale |
| **Madmom** | https://madmom.readthedocs.io/en/latest/ | Récupération d'information musicale (beat, tempo, ...) |
| **Soundfile** | https://python-soundfile.readthedocs.io/en/0.13.1/ | Lecture, écriture de fichier audio |
| **Pedalboard** | https://spotify.github.io/pedalboard/ | Traitement audio : lecture, écriture, rendu et ajout d'effet (supporte VST3) |
| **Music21** | https://www.music21.org/music21docs/ | Théorie musicale |
| **pretty_midi** | https://craffel.github.io/pretty-midi/ | Ecriture MIDI |
| **Jupyterlab** | https://jupyterlab.readthedocs.io/en/latest/ | Notebook |
| **Numpy** | https://numpy.org/ | Representation d'un signal audio |
| **Scipy** | https://scipy.org/ | Traitement de signal avec filtre, convolution, ... |
| **pandas** | https://pandas.pydata.org/docs/ | Manipulation DataFrame |
| **matplotlib** | https://matplotlib.org/stable/index.html | Data visualisation |
| **seaborn** | https://seaborn.pydata.org/ | Data visualisation |
| **Pypianoroll** | https://hermandong.com/pypianoroll/ | Piano-rolls |
| **TensorFlow** | https://www.tensorflow.org/?hl=fr | ML : Tâches traitement audio avancées |
| **PyTorch** | https://pytorch.org/ | ML : Tâches traitement audio avancées |
| **mirdata** | https://mirdata.readthedocs.io/en/stable/ | Accès standardisé aux datasets |
| **mir_eval** | https://mir-eval.readthedocs.io/latest/ | Métriques MIR |
| ... | ... | ... |

## Sources de donnees

### GuitarSet :

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

### IDMT-SMT-Guitar

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
