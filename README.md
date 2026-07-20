# GoPro Cinema Camera Tracker

Version actuelle : **1.7.0** — voir [CHANGELOG.md](CHANGELOG.md) pour l'historique des versions.

## Vision du projet

Ce projet vise à développer un outil Python de camera tracking destiné aux workflows VFX cinéma.

L'objectif est de reconstruire la trajectoire d'une caméra cinéma à partir d'une ou plusieurs GoPro fixées rigidement sur celle-ci.

Le résultat attendu est une trajectoire caméra de haute précision, exploitable directement dans des logiciels de production VFX et 3D tels que Nuke, Blender ou Unreal Engine.

---

## Première approche : Postproduction

La première version du projet fonctionne entièrement en postproduction.

Toutes les données vidéo sont disponibles avant le traitement, ce qui permet de privilégier la précision du calcul plutôt que la vitesse d'exécution.

L'objectif est d'obtenir la meilleure qualité de tracking possible dans un contexte professionnel VFX.

---

## Workflow de tournage

Une ou plusieurs GoPro sont fixées rigidement sur la caméra cinéma.

Au début de chaque prise, une cible ArUco est placée au sol et visible pendant une courte durée.

Cette cible permet uniquement de :

- définir un repère monde stable ;
- calculer la transformation rigide entre la GoPro et la caméra cinéma.

Après cette phase d'initialisation, la cible ArUco n'est plus utilisée.

La caméra peut ensuite évoluer librement pendant la prise, sans contrainte de conserver une référence visuelle.

Cette approche est pensée pour respecter les contraintes réelles d'un tournage cinéma.

---

## Résultat attendu

À partir des vidéos capturées par la ou les GoPro, l'outil reconstruit la trajectoire complète de la caméra cinéma dans le repère défini lors de l'initialisation.

Le résultat contient :

- la position de la caméra ;
- son orientation ;
- une pose complète pour chaque image de la séquence.

La trajectoire générée doit pouvoir être exportée et utilisée directement dans des logiciels VFX et 3D.

---

## Niveau de qualité recherché

L'objectif est d'obtenir une précision maximale, proche du niveau requis pour un workflow VFX cinéma.

La priorité est donnée à :

- la précision du tracking ;
- la stabilité de la trajectoire ;
- la cohérence spatiale ;
- la qualité d'export.

Le temps de calcul n'est pas une contrainte prioritaire dans cette première approche.

---

## Contraintes techniques

Le projet est développé en Python.

Il peut utiliser des bibliothèques et outils open source existants, tels que COLMAP, à condition que leurs licences permettent un usage commercial.

Les outils externes doivent être intégrés au pipeline interne et ne doivent pas nécessiter de manipulation directe par l'utilisateur final.

L'objectif est de fournir une application autonome capable de gérer l'ensemble du workflow :

- calibration ;
- reconstruction de trajectoire ;
- optimisation ;
- vérification ;
- export.

---

## Installation

Python 3.10 ou plus récent est requis (contrainte de `pycolmap`).

### Avec conda (recommandé — environnement isolé, versions figées)

```bash
conda env create -f environment.yml
conda activate gopro-tracking
python main.py
```

Pour mettre à jour un environnement déjà créé après un changement du fichier `environment.yml` :

```bash
conda env update -f environment.yml --prune
```

### Avec pip

```bash
pip install -r requirements.txt
python main.py
```

---

Le tracking par Structure-from-Motion (voir plus bas) s'appuie sur [COLMAP](https://colmap.github.io/) via son binding Python `pycolmap` (licence BSD, usage commercial autorisé), installé automatiquement avec les dépendances ci-dessus — aucune installation séparée de COLMAP n'est nécessaire.

Les presets (`profiles/`) et les fichiers de tracking générés (`data/`) ne sont pas versionnés (`.gitignore`) : sur une nouvelle machine, il faut recréer les presets ou copier manuellement le dossier `profiles/` depuis une installation existante.

---

## Architecture du pipeline

L'application (interface PyQt6, `main.py` / `main_window.py`) est organisée en trois onglets correspondant aux trois étapes du workflow :

### 1. Calibration

Détecte la cible Charuco simultanément dans la vidéo GoPro et la vidéo caméra cinéma (`calibration.py`) pour calculer la transformation rigide entre les deux caméras (le « rig »), et produit un fichier `calibration.json` réutilisé par l'étape de tracking.

### 2. Tracking

Reconstruit la trajectoire de la GoPro à partir de la vidéo de prise, puis la convertit vers la trajectoire du plan film de la caméra cinéma via le rig calculé à l'étape précédente. Deux modes sont disponibles, sélectionnables dans l'interface :

- **SfM (COLMAP)** — mode par défaut, adapté au workflow réel décrit plus haut : la cible Charuco n'est visible qu'au tout début de la prise. La trajectoire de la GoPro est reconstruite par Structure-from-Motion à partir des points caractéristiques naturels de la scène (`sfm_tracking.py`), puis recalée dans le repère métrique du Charuco à partir des quelques images où la cible et la reconstruction SfM se chevauchent (recalage par similarité, algorithme de Umeyama avec rejet des correspondances aberrantes, `alignment.py`).
- **Charuco continu** — mode plus simple (`tracking.py`), pour les prises où la cible reste visible tout du long ; la pose est alors calculée directement image par image par détection Charuco, sans reconstruction SfM.

Le résultat est écrit dans `data/tracking.json` (position, orientation et index réel de chaque image reconstruite).

### 3. Vérification et Export

Aperçu 3D interactif de la trajectoire reconstruite (matplotlib intégré à l'interface), généré automatiquement dès la sélection du fichier de tracking. L'export permet d'enregistrer ce fichier à l'emplacement de son choix pour l'utiliser dans un logiciel VFX/3D externe.

---

## Évolutions envisagées

Une seconde approche sera développée ultérieurement pour permettre un tracking en temps réel.

La première version du projet reste entièrement dédiée au traitement en postproduction, afin de maximiser la qualité et la robustesse du résultat.
