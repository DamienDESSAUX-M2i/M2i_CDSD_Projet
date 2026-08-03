<h1>Descriptif des données</h1>

> Ce document présente les datasets utilisés dans ce projet.

# 1. Table des matières

- [1. Table des matières](#1-table-des-matières)
- [2. GuitarSet](#2-guitarset)
- [3. IDMT-SMT-Guitar](#3-idmt-smt-guitar)

# 2. GuitarSet

**Lien du site associé au dataset** : <https://guitarset.weebly.com/>

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

# 3. IDMT-SMT-Guitar

**Lien du site associé au dataset** : <https://www.idmt.fraunhofer.de/en/publications/datasets/guitar.html>

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
