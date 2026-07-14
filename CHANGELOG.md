# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet suit [Semantic Versioning](https://semver.org/lang/fr/) (MAJOR.MINOR.PATCH).

## [Non publié]

## [1.2.0] - 2026-07-14

### Ajouté
- **Mode Tracking à 2 GoPro** (onglet Tracking) : groupe "GoPro 2" facultatif (calibration +
  vidéo), à cocher pour activer une seconde caméra rigidement montée sur le même rig.
  - Synchronisation des deux flux par corrélation croisée des pistes audio (clap sonore en
    début de prise), convertie en décalage entier de frames.
  - Les deux vidéos sont reconstruites indépendamment (Charuco ou SfM) puis fusionnées image
    par image (position moyennée, rotation moyennée par SVD) pour réduire le bruit.
  - La trajectoire fusionnée est rééchantillonnée sur le fps réel de la caméra cinéma
    (interpolation linéaire + SLERP), au lieu de rester sur la timeline de la GoPro.
- Champ **FPS** dans les profils GoPro (auto-détecté depuis la vidéo si laissé vide) et
  Caméra cinéma (manuel, requis pour le rééchantillonnage ci-dessus).

## [1.1.0] - 2026-07-14

### Ajouté
- Champ **Nom du rig** (onglet Calibration, groupe Rig) : pré-remplit le nom de fichier
  proposé à l'enregistrement de `calibration.json`.

### Modifié
- Le champ auparavant nommé "Nom du projet" est renommé **Nom du rig** (`rig_name` dans
  `Calibration` et dans les métadonnées du fichier de calibration exporté).

## [1.0.0] - 2026-07-14

Première version stable de l'application.

### Ajouté
- Onglet **Calibration** : détection de pose Charuco sur la vidéo GoPro et la vidéo caméra
  cinéma, calcul de la transformation rigide du rig (offset GoPro ↔ caméra), export `calibration.json`.
- Onglet **Tracking** avec deux modes :
  - **Charuco** : suivi par détection continue de la planche Charuco (nécessite qu'elle reste
    dans le champ pendant toute la prise).
  - **SfM (Structure-from-Motion, via COLMAP/pycolmap)** : reconstruction de la trajectoire
    complète de la GoPro à partir des images seules, alignée dans le repère monde du Charuco
    par une transformation de similarité (Umeyama) affinée par moyennage de rotations (SVD) —
    permet de suivre la caméra même après que le Charuco a quitté le champ.
- Onglet **Vérification** : visionneuse 3D (matplotlib) de la trajectoire reconstruite,
  aperçu automatique à la sélection d'un fichier, export du fichier de tracking final.
- **Profils réutilisables** (GoPro, caméra cinéma, planche Charuco) stockés en JSON dans
  `profiles/`, rappelables d'une calibration à l'autre.
- Thème sombre façon outil VFX, barres de progression par étape (calcul en arrière-plan
  via `QThread`, sans limite de temps réel).
- Générateur de trajectoire de test synthétique (`samples/generate_sample_tracking.py`).

### Corrigé
- Bug de conflation des matrices caméra GoPro/cinéma en calibration (les deux caméras
  partageaient les mêmes paramètres optiques, faussant la profondeur estimée).
- Incompatibilité de l'API `cv2.aruco` avec les versions récentes d'OpenCV.
