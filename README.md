Vision du projet

Je souhaite développer un outil Python de camera tracking destiné aux workflows VFX cinéma.

L'outil doit permettre de récupérer la trajectoire d'une caméra cinéma en utilisant une ou plusieurs GoPro fixées rigidement sur celle-ci.

L'objectif est d'obtenir une trajectoire de très haute précision, exploitable directement dans des logiciels comme Nuke, Blender ou Unreal Engine.

Première approche : Postproduction

Cette première version fonctionne entièrement en postproduction.

Toutes les vidéos sont disponibles avant le traitement, il n'y a donc aucune contrainte de temps réel.

L'objectif est de privilégier la précision plutôt que la vitesse.

Workflow de tournage

Une ou plusieurs GoPro sont fixées rigidement sur la caméra cinéma.

Au début de la prise, une cible ArUco est placée au sol et visible pendant environ une seconde.

Cette cible sert uniquement à :

définir le repère du monde ;
calculer la transformation rigide entre la GoPro et la caméra cinéma.

Une fois cette phase terminée, la cible n'est plus utilisée et la prise se déroule normalement.

Le système ne doit pas nécessiter de revoir la cible pendant la prise afin de rester compatible avec les contraintes d'un tournage cinéma.

Résultat attendu

À partir des vidéos de la ou des GoPro, l'outil reconstruit la trajectoire complète de la caméra dans le repère défini lors de l'initialisation.

Cette trajectoire comprend :

la position de la caméra ;
son orientation ;
une pose pour chaque image de la vidéo.

Le résultat doit pouvoir être importé directement dans des logiciels de VFX ou de 3D.

Niveau de qualité recherché

L'objectif est d'obtenir une précision aussi proche que possible du pixel perfect, afin que le tracking soit exploitable dans un workflow VFX cinéma.

La qualité du résultat est prioritaire sur le temps de calcul.

Contraintes techniques

Le projet est développé en Python.

Il peut s'appuyer sur des bibliothèques ou outils open source existants, comme COLMAP, à condition que leur licence soit compatible avec un usage commercial.

L'utilisateur ne doit pas avoir à manipuler ces outils directement : ils font partie de l'implémentation interne du projet.

L'objectif est de fournir un outil autonome qui réalise l'ensemble du pipeline jusqu'à l'export du fichier de tracking.

Évolutions envisagées

Une seconde approche sera développée ultérieurement pour réaliser un tracking en temps réel.

Pour le moment, le projet est entièrement centré sur la version postproduction.

Ce que je retiens surtout, c'est que tu ne cherches pas simplement à "faire un tracker". Tu cherches à concevoir un workflow de tracking adapté aux contraintes d'un tournage cinéma, où la technique s'efface au maximum derrière la simplicité d'utilisation et la qualité du résultat.

Si tu trouves que ce résumé correspond bien à ta vision, nous pourrons nous y référer comme base de travail pour toutes les discussions suivantes.
