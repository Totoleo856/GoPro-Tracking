# GoPro Cinema Camera Tracker

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

## Architecture générale envisagée

Le pipeline est organisé autour de trois étapes principales :

### Calibration

Détermination de la relation géométrique entre :

- la GoPro ;
- la caméra cinéma ;
- le repère défini par la cible ArUco.

### Tracking

Reconstruction de la trajectoire de la GoPro, puis conversion vers la trajectoire du plan film de la caméra cinéma.

### Vérification et Export

Visualisation de la trajectoire reconstruite et export vers différents environnements VFX et 3D.

---

## Évolutions envisagées

Une seconde approche sera développée ultérieurement pour permettre un tracking en temps réel.

La première version du projet reste entièrement dédiée au traitement en postproduction, afin de maximiser la qualité et la robustesse du résultat.
