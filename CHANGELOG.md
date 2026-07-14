# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet suit [Semantic Versioning](https://semver.org/lang/fr/) (MAJOR.MINOR.PATCH).

## [Non publié]

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
