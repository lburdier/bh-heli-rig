# Black Hawk Rig

Extension Blender (4.2 → 5.x) qui pilote le rig de l'hélicoptère UH-60 Black Hawk : rotors, pales, vol stationnaire, portes et LEDs.

## Installation

1. Télécharge `bh_heli_rig-X.Y.Z.zip` dans la [dernière version](https://github.com/lburdier/bh-heli-rig/releases/latest).
2. Glisse le zip dans une fenêtre de Blender. Tu peux aussi passer par *Édition › Préférences › Extensions › ▾ › Installer depuis le disque*.
3. Dans la vue 3D, touche **N**, onglet **Black Hawk**.
4. Clique **Télécharger le modèle** pour récupérer le modèle 3D du UH-60, environ 190 Mo. Il ne se télécharge qu'une fois. Clique ensuite **Ajouter le UH-60 à la scène**.

Sans connexion, *Installer le modèle depuis un fichier* accepte le zip `UH60_BlackHawk_X.Y.zip` de la page des versions.

## Mises à jour automatiques

Au démarrage de Blender, au plus une fois toutes les 12 h, l'extension demande à GitHub s'il existe une nouvelle version. Si oui, elle la télécharge, vérifie sa taille et son empreinte SHA-256, puis l'installe toute seule. La scène ouverte est conservée.

- Si un téléchargement du modèle est en cours, l'installation attend qu'il se termine.
- Dans *Préférences › Extensions › Black Hawk Rig*, deux options : couper la recherche, ou remplacer l'installation automatique par un bouton dans le panneau.
- Si *Autoriser l'accès en ligne* est coupé dans *Préférences › Système › Réseau*, rien n'est envoyé.

## Fonctions

- **Rotors** : régime réel (rampe de démarrage, boucle, arrêt), sens de rotation, rapport du rotor de queue, flou des disques.
- **Pales** : pas collectif, conicité, affaissement au repos et en vol, oscillation.
- **Vol** : stationnaire, avec hauteur, dérive, lacet et inclinaison.
- **Portes** : cockpit à charnières et cabine coulissante. Elles s'ouvrent directement ou s'animent sur une durée choisie.
- **LEDs** : feux de navigation et anticollision, modes, préréglages aviation, rouge, blanc ou synchro.
- **Aide** : chaque réglage a une aide illustrée, et le panneau ouvre une documentation complète.

## Licence

- Code : GPL-3.0-or-later (voir `LICENSE`).
- Modèle 3D et textures : Lucas Burdier.

*UH-60 Black Hawk est une marque de Sikorsky. Ce projet personnel n'est ni affilié ni approuvé par cette société.*
