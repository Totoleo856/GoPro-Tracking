# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet suit [Semantic Versioning](https://semver.org/lang/fr/) (MAJOR.MINOR.PATCH).

## [Non publié]

## [1.4.0] - 2026-07-15

### Ajouté
- Onglet Tracking : threads COLMAP et nombre max de points par image (2048/4096/8192)
  configurables directement dans l'interface (mode SfM), visibles uniquement quand ce
  mode est sélectionné (masqués en mode Charuco continu).
- Onglet Calibration : les groupes Rig, Profil GoPro, Profil Caméra cinéma et Planche
  Charuco n'affichent plus qu'un sélecteur de profil et un bouton "Ajouter" — les champs
  détaillés s'ouvrent dans une fenêtre dédiée avec un bouton "Enregistrer". Le Rig est
  désormais lui aussi un profil réutilisable (nom + offsets).

### Corrigé
- **Aperçu 3D (onglet Vérification)** : la position et la direction de la caméra étaient
  lues directement depuis la matrice sans tenir compte de la convention monde→caméra du
  fichier de tracking, déformant la trajectoire et l'orientation affichées. La reconstruction
  elle-même n'était pas nécessairement en cause.
- Case à cocher "GoPro 2" et champ threads coupés par un espacement insuffisant des
  `QGroupBox`.

## [1.3.1] - 2026-07-15

### Corrigé
- Impossible de taper "." dans les champs numériques sur une machine dont la locale
  régionale utilise la virgule comme séparateur décimal (`QDoubleValidator` suivait la
  locale système). Le point est désormais forcé comme séparateur décimal partout dans
  l'app, quelle que soit la locale de la machine.

## [1.3.0] - 2026-07-15

### Ajouté
- `environment.yml` : environnement conda avec Python et versions des dépendances figées,
  pour reproduire l'environnement de développement sur une nouvelle machine.
- Section Installation du README complétée (méthode conda recommandée, méthode pip en
  alternative, prérequis Python 3.10+, note sur les presets/`profiles/` non versionnés).

## [1.2.2] - 2026-07-15

### Corrigé
- Calibration : le message d'erreur en cas d'échec de détection Charuco précise désormais
  quelle vidéo (GoPro ou caméra cinéma) est en cause et pourquoi (aucun coin détecté,
  contraste insuffisant, ou résolution/capteur incohérents) au lieu d'un message générique.
- Tracking SfM : le calcul COLMAP (extraction de features, matching, reconstruction) pouvait
  saturer entièrement le CPU et geler la machine sur un poste grand public. Les threads
  COLMAP sont désormais plafonnés (2 cœurs laissés au système), et l'espace disque
  disponible est vérifié avant l'extraction complète des frames (chaque frame étant
  sauvegardée en PNG plein format) pour échouer proprement plutôt que de saturer le disque.
  Aucun changement sur la précision : toujours résolution native, toutes les frames traitées.

## [1.2.1] - 2026-07-14

### Modifié
- Enregistrement des profils GoPro et Caméra cinéma : le nom du profil est désormais pris
  directement depuis le champ "Modèle" au clic sur "Enregistrer...", au lieu de redemander
  un nom via une boîte de dialogue.

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
