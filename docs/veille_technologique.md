<h1>Veille technologique</h1>
<h2>Projet de transcription audio vers MIDI - GuitarFlow</h2>

# 1. Table des matières

- [1. Table des matières](#1-table-des-matières)
- [2. Veille sur les représentations audio](#2-veille-sur-les-représentations-audio)
  - [2.1. Comparatif des features audio](#21-comparatif-des-features-audio)
    - [2.1.1. STFT (Short-Time Fourier Transform)](#211-stft-short-time-fourier-transform)
    - [2.1.2. Mel Spectrogram](#212-mel-spectrogram)
    - [2.1.3. MFCC (Mel-Frequency Cepstral Coefficients)](#213-mfcc-mel-frequency-cepstral-coefficients)
    - [2.1.4. CQT (Constant-Q Transform) — représentation clé](#214-cqt-constant-q-transform--représentation-clé)
    - [2.1.5. Chromagram (Chroma / STFT-CQT chroma)](#215-chromagram-chroma--stft-cqt-chroma)
  - [2.2. Matrice de décision](#22-matrice-de-décision)
  - [2.3. Décision retenue](#23-décision-retenue)
- [Veille sur les architectures de modélisation](#veille-sur-les-architectures-de-modélisation)
  - [Comparatif architectures ML](#comparatif-architectures-ml)
  - [2.2. Matrice de décision](#22-matrice-de-décision-1)
  - [2.3. Décision retenue](#23-décision-retenue-1)

# 2. Veille sur les représentations audio

## 2.1. Comparatif des features audio

| Critère | STFT | Mel Spectrogram | MFCC | CQT | Chromagram |
| :- | :- | :- | :- | :- | :- |
| Domaine | Temps–fréquence | Temps–Mel fréquence | Cepstral (Mel compressé) | Temps–fréquence log (pitch-based) | Temps–pitch class (12 notes) |
| Axe fréquentiel | Linéaire (Hz) | Log perceptif Mel | Compressé (DCT du Mel) | Logarithmique musical | 12 classes chromatiques |
| Résolution basse fréquence (cordes graves guitare) | Faible | Moyenne | Perte d’info | Très élevée | Moyenne à élevée (selon CQT) |
| Résolution haute fréquence | Bonne | Moyenne | Très réduite | Bonne | Très réduite (car octave-folding) |
| Conservation des harmoniques | Oui | Oui | Partielle | Très bonne | Non (fusion par classe de note) |
| Robustesse bruit | Moyenne | Bonne | Bonne (très compacte) | Bonne | Moyenne |
| Information temporelle | Excellente | Bonne | Réduite | Excellente | Excellente |
| Information pitch exacte | Oui | Indirecte | Non | Oui (MIDI-aligned) | Non (classe de pitch seulement) |
| Adaptation guitare → MIDI | Moyenne | Moyenne | Faible | Très élevée (standard de facto) | Moyenne (utile pour accords) |
| Séparation notes simultanées (polyphonie) | Bonne | Bonne | Faible | Très bonne | Moyenne (fusion harmonique) |
| Inversion vers signal audio | Oui | Non (perte phase) | Non | Oui (approximatif) | Non |
| Usage typique en transcription musicale | Baseline CNN | Feature deep learning | Compression ML classique | Modèle SOTA transcription | Détection accords / tonalité |

### 2.1.1. STFT (Short-Time Fourier Transform)

- Représentation brute temps-fréquence.
- Bonne fidélité physique du signal.
- Limite majeure : résolution uniforme en Hz
  - insuffisante pour distinguer correctement les notes graves (cordes Mi, La de guitare).
- Génère des bins non alignés sur la structure musicale.

Utilisation : baseline CNN, mais sous-optimal pour transcription précise.

### 2.1.2. Mel Spectrogram

- Compression perceptive (échelle Mel).
- Réduit dimension et bruit.

Limite critique :
- Non linéaire mais non aligné avec les demi-tons musicaux
- Perte de précision pour pitch exact

Bon pour classification globale, moins pour MIDI précis.

### 2.1.3. MFCC (Mel-Frequency Cepstral Coefficients)

- Compression supplémentaire via DCT du spectre Mel.
- Capture l’enveloppe spectrale (timbre), pas les notes.

Conséquence :
- Très faible utilité directe pour transcription musicale.
- Excellent pour reconnaissance de timbre, pas de hauteur.

Mauvais choix pour guitare → MIDI.

### 2.1.4. CQT (Constant-Q Transform) — représentation clé

- Axe fréquentiel logarithmique aligné sur les demi-tons.
- Chaque bin correspond directement à une note musicale.

Points forts :
- Très forte résolution dans les basses fréquences (cordes graves guitare).
- Correspondance naturelle avec MIDI (A4 = 440 Hz → mapping direct).
- Très utilisé en transcription automatique moderne.

Limite :
- Coût computationnel plus élevé.

Meilleure représentation globale pour transcription polyphonique guitare → MIDI.

### 2.1.5. Chromagram (Chroma / STFT-CQT chroma)

- Réduction de toutes les fréquences à 12 classes (C, C#, D… B).
- Ignore les octaves.

Points forts :
- Très bon pour :
  - reconnaissance d’accords
  - tonalité
- Stable musicalement.

Limites critiques :
- Impossible de reconstruire les hauteurs exactes
- Perte totale d’information d’octave → incompatible MIDI précis

Bon pour harmonique global, pas pour transcription note-à-note.

## 2.2. Matrice de décision

![Matrice de décision features](./veille_technologique.pdf)

## 2.3. Décision retenue

Pour la tâche spécifique guitare → MIDI, on cherche :
- résolution logarithmique en fréquence,
- séparation des notes simultanées,
- alignement sur la grille MIDI (12-TET),
- conservation des harmoniques.

Hiérarchie de pertinence (du meilleur au pire)
- CQT → meilleur choix global (alignement MIDI natif)
- STFT → acceptable mais sous-optimal (résolution non musicale)
- Mel spectrogram → bon pour deep learning général, pas pitch précis
- Chromagram → utile pour accords, pas notes
- MFCC → inutilisable pour transcription musicale fine

# Veille sur les architectures de modélisation

## Comparatif architectures ML

| Architecture | Avantages | Limites |
| :- | :- | :- |
| Multiclass + LogisticRegression | Léger | Faible précision |
| MLP | Simple à implémenter | Peu performant sur séquences |
| CNN | Bonnes performances fréquentielles | Faible mémoire temporelle |
| RCNN | Bon compromis temps/fréquence | Plus complexe |
| Transformer audio | Très performant | Coût GPU élevé |

## 2.2. Matrice de décision

![Matrice de décision features](./veille_technologique.pdf)

## 2.3. Décision retenue

L’architecture RCNN (Recurrent Convolutional Neural Network) est retenue comme architecture principale.

Le RCNN présente le meilleur compromis entre :
- performances de transcription,
- robustesse polyphonique,
- coût d’inférence,
- simplicité de déploiement.