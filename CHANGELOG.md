# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet suit [Semantic Versioning](https://semver.org/lang/fr/) (MAJOR.MINOR.PATCH).

## [Non publié]

## [1.11.0] - 2026-07-21

### Ajouté
- **Premier build installeur Windows**, pour diffuser l'app à des collègues sans qu'ils
  aient besoin d'installer Python/conda :
  - Empaquetage autonome via PyInstaller (`GoProTracking.spec`).
  - Installeur `.exe` via Inno Setup (`installer/GoProTracking.iss`) : sans droits admin
    requis, raccourci menu Démarrer, désinstalleur propre. Instructions de build dans le
    README.
  - Icône de l'app (`Icone.png` / `icon.ico`), affichée dans la fenêtre et l'exécutable.
- Les profils et fichiers de tracking par défaut sont désormais stockés dans le dossier
  utilisateur (`%APPDATA%\GoPro-Tracking`) plutôt qu'à côté du script — indispensable une
  fois l'app installée (`Program Files` est en lecture seule pour un utilisateur
  standard). Migration automatique et transparente des profils existants au premier
  lancement, sans toucher à l'ancien dossier.

## [1.10.0] - 2026-07-20

### Ajouté
- Onglet Vérification : second champ de calibration optionnel ("Calibration GoPro 2")
  pour afficher les deux GoPro du mode double rig dans la même visionneuse (caméra
  cinéma + GoPro 1 + GoPro 2), avec leurs distances respectives.
- Bouton "×" pour vider/décharger un fichier sur les champs "Fichier résultat",
  "Calibration GoPro 1" et "Calibration GoPro 2" de l'onglet Vérification.

### Corrigé
- L'aperçu du rig ne fonctionnait que si "Calibration GoPro 1" était rempli en premier —
  chaque champ de calibration (GoPro 1, GoPro 2) fonctionne désormais indépendamment.

## [1.9.1] - 2026-07-20

### Modifié
- Interface resserrée dans l'ensemble de l'app : police, champs, boutons et encadrés
  plus compacts (moins d'espace perdu à l'écran).

## [1.9.0] - 2026-07-20

### Ajouté
- Onglet Vérification : le bouton EXPORT ouvre une fenêtre de choix du logiciel de
  destination (Blender, Nuke, Maya, After Effects).
  - **Blender** : génère un script Python (`_blender.py`) à exécuter dans l'onglet
    Scripting, qui crée une caméra animée (position + rotation par quaternions) ; focale
    et capteur appliqués si un fichier de calibration est chargé.
  - **Nuke** : génère un fichier `.chan` standard (`_nuke.chan`, `frame tx ty tz rx ry
    rz`), à importer sur un nœud Camera (clic droit sur "translate"/"rotate" > Import
    chan file...) ; focale/capteur indiqués dans le message de fin (à renseigner
    manuellement, le format .chan ne portant que l'animation).
  - Maya et After Effects affichent un message "bientôt disponible" pour l'instant.
  - Le nom de fichier proposé reprend celui du tracking avec le suffixe du logiciel
    choisi (`..._blender.py`, `..._nuke.chan`).

## [1.8.0] - 2026-07-20

### Ajouté
- Mode Tracking à 2 GoPro : vérification de cohérence entre les deux reconstructions
  avant fusion. L'écart de position (mm) sur les frames communes après synchronisation
  audio est calculé et affiché systématiquement ; si aucune frame commune n'est trouvée,
  ou si l'écart dépasse une tolérance réglable ("Tolérance de cohérence (mm)", 30 mm par
  défaut), le tracking s'arrête avec une erreur explicite plutôt que de fusionner un
  résultat incohérent.

## [1.7.0] - 2026-07-20

### Ajouté
- Onglet Vérification : curseur (slider) sous l'aperçu 3D de trajectoire pour se déplacer
  pose par pose, avec une frustum mise en avant à la position courante et un label
  affichant l'index de frame réel et le timecode.
- Onglet Tracking : champ "Dossier de destination" (optionnel) pour choisir où écrire le
  fichier de tracking généré, au lieu du chemin `data/tracking.json` fixe (fonctionne en
  mode simple comme double GoPro).

### Modifié
- Onglet Vérification : les positions échantillonnées le long de la trajectoire sont
  affichées comme de simples points (au lieu d'un schéma de caméra à chacune) pour ne
  garder le détail visuel que sur la position courante du curseur.
- Aperçu du rig (GoPro / caméra cinéma) simplifié : quadrillage, cube/graduations et titre
  du graphique retirés, ne conservant que les schémas de caméra, la légende et la distance.

## [1.6.0] - 2026-07-20

### Ajouté
- Onglet Calibration : sélectionner un profil de Rig charge désormais automatiquement les
  profils GoPro et Caméra cinéma enregistrés avec lui.
- Onglet Vérification : nouvelle visionneuse 3D à gauche de l'aperçu de trajectoire,
  affichant un schéma simple (GoPro + caméra cinéma) positionné et orienté selon le
  `rig_transform` du fichier de calibration sélectionné, pour vérifier au premier coup
  d'œil que la calibration est physiquement cohérente. S'affiche dès qu'un fichier de
  calibration est chargé, indépendamment du résultat de tracking.

### Modifié
- Onglet Calibration : les profils GoPro et Caméra cinéma sont regroupés dans un seul
  encadré "Configuration" (au lieu de deux encadrés séparés).

### Corrigé
- Le profil Caméra cinéma ne sauvegardait/rechargeait jamais la focale (`focal_length`),
  contrairement au profil GoPro — corrigé.
- Aperçu 3D de la trajectoire (onglet Vérification) : le sens de l'axe Z du repère Charuco
  dépend de l'orientation physique de la planche au sol et peut ressortir inversé (hauteur
  caméra affichée négative). L'affichage force maintenant Z positif = au-dessus du sol,
  via une rotation propre à 180° (Z et Y) pour ne pas inverser au passage le sens gauche-
  droite des déplacements (un simple flip de Z seul transforme le repère droitier en
  repère gaucher).

## [1.5.0] - 2026-07-16

### Ajouté
- Onglet Vérification : l'aperçu 3D affiche désormais un petit schéma de caméra (frustum
  filaire) à chaque point échantillonné de la trajectoire, à la place de simples flèches,
  ainsi que la board Charuco dessinée à sa taille et sa position réelles (damier), à partir
  d'un nouveau champ optionnel "Calibration" permettant de sélectionner le fichier de
  calibration utilisé pour ce tracking.



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
