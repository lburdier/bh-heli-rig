"""Textes d'aide du plugin (francais). Source unique : infos-bulles, fenetres d'aide et documentation HTML.
Aucun import bpy : ce fichier est aussi lu par tools/make_doc.py."""

# ico : icone Blender ('NOM') ou icone du plugin ('@nom') ; img : illustration (images/<img>.png)
# court : info-bulle au survol ; long : explication de la fenetre d'aide et de la doc ; conseil : valeurs utiles
HELP = {
    # ------------------------------------------------------------ onglets
    'tab_ANIM': dict(t="Animation", ico='@rotor', court="Mode d'animation, durée de la boucle et réglage des rotors"),
    'tab_PALES': dict(t="Pales", ico='@blade', court="Flexion, conicité, pas et inclinaison du disque rotor"),
    'tab_VOL': dict(t="Vol", ico='@hover', court="Vol stationnaire : hauteur, pompage, dérive, balancement"),
    'tab_PORTES': dict(t="Portes", ico='@door', court="Ouverture des portes du cockpit et de la cabine, une par une ou toutes ensemble"),
    'tab_LEDS': dict(t="LEDs", ico='@led', court="Feux de navigation, gyrophares et voyants du cockpit"),
    'tab_AIDE': dict(t="Aide", ico='@help', court="Prise en main, contrôles du rig, documentation et réinitialisation"),

    # ------------------------------------------------------------ modes
    'sec_mode': dict(t="Mode d'animation", ico='@mode_loop', img='mode_loop',
                     court="Choisit ce que fait l'hélico sur la plage d'images : boucle, démarrage, arrêt ou parking",
                     long="Un clic crée l'animation des rotors et du vol stationnaire, et cale la plage d'images de la scène.\n"
                          "Boucle : plein régime, à répéter à l'infini sans raccord visible.\n"
                          "Démarrage : les rotors accélèrent puis l'hélico décolle.\n"
                          "Arrêt : l'hélico se pose puis les rotors ralentissent.\n"
                          "Parking : rotors immobiles, pales fléchies sous leur poids."),
    'mode_LOOP': dict(t="Boucle", ico='@mode_loop', img='mode_loop',
                      court="Rotors à plein régime : la dernière image raccorde parfaitement avec la première",
                      long="Le régime est arrondi à un nombre entier de tours sur la durée de la boucle. "
                           "Le vol stationnaire et les LEDs utilisent aussi des cycles entiers : "
                           "la vidéo peut tourner en boucle sans saut.",
                      conseil="Idéal pour un plan de présentation ou un fond animé."),
    'mode_STARTUP': dict(t="Démarrage", ico='@mode_startup', img='mode_startup',
                         court="Les rotors accélèrent sans à-coup, puis l'hélico décolle sur la fin de la rampe",
                         long="Le régime suit une courbe douce de 0 à 1 pendant la « Durée de la rampe ». "
                              "Le décollage (vol stationnaire) commence aux trois quarts du régime. "
                              "Les rotors continuent à plein régime après la rampe."),
    'mode_SHUTDOWN': dict(t="Arrêt", ico='@mode_shutdown', img='mode_shutdown',
                          court="L'hélico se pose d'abord, puis les rotors ralentissent jusqu'à l'arrêt",
                          long="Inverse du démarrage : le vol stationnaire s'éteint au début de la rampe, "
                               "puis les pales ralentissent et se courbent en s'arrêtant."),
    'mode_PARKED': dict(t="Parking", ico='@mode_parked', img='mode_parked',
                        court="Rotors à l'arrêt, hélico posé, pales fléchies au repos",
                        long="Supprime l'animation des rotors. Pratique pour un rendu fixe au sol ou pour régler la flexion."),
    'ramp_frames': dict(t="Durée de la rampe", ico='PREVIEW_RANGE', img='mode_startup', unite="images",
                        court="Durée du démarrage ou de l'arrêt, en images (24 images = 1 s à 24 i/s)",
                        long="Utilisée par les modes Démarrage et Arrêt. La modifier recalcule aussitôt la rampe en cours.",
                        conseil="Réel : 30 à 60 s. En animation, 5 à 10 s (120 à 240 images) suffisent."),

    # ------------------------------------------------------------ boucle
    'sec_loop': dict(t="Boucle", ico='@mode_loop', img='loop',
                     court="Début et durée de l'animation : tout est calé pour boucler sans raccord",
                     long="Rotors, vol stationnaire et LEDs font un nombre entier de cycles entre la première image "
                          "et la dernière. La plage d'images de la scène est mise à jour automatiquement."),
    'loop_start': dict(t="Image de départ", ico='TIME', img='loop', unite="image",
                       court="Première image de l'animation (l'image où les rotors sont à leur position de départ)",
                       long="Décale toute l'animation dans la timeline, utile pour l'insérer dans un plan plus long."),
    'loop_frames': dict(t="Durée de la boucle", ico='PREVIEW_RANGE', img='loop', unite="images",
                        court="Longueur de la boucle en images. Le régime est arrondi pour faire des tours entiers",
                        long="Plus la boucle est longue, plus le régime réel est proche du régime demandé. "
                             "La ligne « Régime réel » sous les réglages indique la valeur obtenue.",
                        conseil="240 images (10 s à 24 i/s) : 43 tours, soit 258 tr/min exactement."),

    # ------------------------------------------------------------ rotors
    'sec_rotors': dict(t="Rotors", ico='@rotor', img='rpm',
                       court="Vitesse et sens de rotation des rotors principal et de queue",
                       long="Le rotor de queue est entraîné par le principal : son nombre de tours suit le rapport de queue."),
    'rpm': dict(t="Régime", ico='@rotor', img='rpm', unite="tr/min",
                court="Vitesse du rotor principal en tours par minute. Réel UH-60 : 258 tr/min = 100 % Nr",
                long="Un vrai UH-60 tourne à environ 258 tr/min. À l'écran, un régime réel produit souvent un effet "
                     "stroboscopique (les pales semblent tourner lentement ou à l'envers) : c'est normal, "
                     "le flou de mouvement du rendu l'atténue.",
                conseil="258 = réaliste ; 60 à 120 = lisible à l'œil mais irréaliste ; 0 = rotor figé."),
    'rpm_real': dict(t="Régime réel UH-60", ico='CHECKMARK', img='rpm',
                     court="Règle le régime réel du UH-60 : rotor principal 258 tr/min (100 % Nr), rotor de queue ≈ 1 190 tr/min",
                     long="Nr = régime nominal du rotor en vol. Pour le UH-60 : 258 tr/min, soit 4,3 tours par seconde. "
                          "Avec un rotor de 16,4 m de diamètre, le bout des pales file à environ 221 m/s (Mach 0,65). "
                          "Le rotor de queue tourne environ 4,6 fois plus vite : ≈ 1 190 tr/min. "
                          "Ce régime reste presque constant en vol : le pilote change le pas des pales, pas la vitesse du rotor.",
                     conseil="Garder 100 % Nr pour un rendu réaliste, avec le flou de mouvement activé au rendu."),
    'nr': dict(t="Régime nominal (Nr)", ico='DRIVER_DISTANCE', img='rpm', unite="%",
               court="Régime en pourcentage du régime nominal du UH-60 : 100 % = 258 tr/min",
               long="Modifie le régime en tr/min. 100 % = vol normal. Pendant un démarrage, le régime monte de 0 à 100 %.",
               conseil="100 % = réaliste en vol."),
    'rotor_info': dict(t="Ce que donne ce régime", ico='INFO', img='rpm',
                       court="Traduit le régime : tours par seconde, degrés par image, régime du rotor de queue, vitesse du bout de pale",
                       long="« Degrés par image » : rotation du rotor entre deux images du film. "
                            "Avec 4 pales identiques, l'image du rotor se répète tous les 90° : à 258 tr/min et 24 i/s, "
                            "le rotor tourne de 64,5° par image, ce que l'œil lit comme un recul de 25,5°. "
                            "C'est l'effet « roue de chariot » des vraies vidéos d'hélicoptère : il est réaliste, "
                            "et le flou de mouvement du rendu (déjà activé) le rend naturel.\n"
                            "La dernière ligne donne le régime à l'image courante : utile pendant un démarrage ou un arrêt."),
    'hud': dict(t="Régime dans la vue 3D", ico='OVERLAY',
                court="Affiche en bas à gauche de la vue 3D le régime instantané des rotors (tr/min et % Nr), mis à jour pendant la lecture"),
    'tail_ratio': dict(t="Rapport de queue", ico='@rotor', img='tail_ratio', unite="×",
                       court="Nombre de tours du rotor de queue pour un tour du rotor principal",
                       long="Le rotor de queue d'un UH-60 tourne environ 4,6 fois plus vite que le rotor principal : ≈ 1 190 tr/min.",
                       conseil="4,61 = réaliste (1 190 ÷ 258)."),
    'rotor_dir': dict(t="Sens principal", ico='LOOP_FORWARDS', img='rotor_dir',
                      court="Sens du rotor principal. Normal = anti-horaire vu de dessus, comme le vrai UH-60",
                      long="À inverser seulement pour un effet ou une autre machine."),
    'tail_dir': dict(t="Sens queue", ico='LOOP_FORWARDS', img='rotor_dir',
                     court="Sens du rotor de queue. Normal = sens d'origine du modèle",
                     long="À inverser si le rotor de queue doit tourner dans l'autre sens."),
    'readout': dict(t="Résultat", ico='INFO', img='loop',
                    court="Durée en secondes, tours entiers obtenus et régime réel après arrondi",
                    long="Le régime réel diffère légèrement du régime demandé parce que la boucle doit contenir un nombre entier de tours."),

    # ------------------------------------------------------------ pales
    'sec_spool': dict(t="Régime des pales", ico='@blade', img='spool',
                      court="Relie la forme des pales au régime : courbées à l'arrêt, tendues en vol",
                      long="Animé automatiquement par les modes Démarrage et Arrêt. En Boucle il vaut 1, en Parking 0."),
    'spool': dict(t="Régime des pales", ico='FORCE_VORTEX', img='spool', unite="0 à 1",
                  court="0 = pales à l'arrêt (fléchies), 1 = pales en vol (tendues, conicité et pas appliqués)",
                  long="Valeur intermédiaire : mélange progressif entre forme au repos et forme en vol. "
                       "Animé par les modes Démarrage et Arrêt : dans ces modes, la valeur affichée suit la timeline."),
    'sec_flex': dict(t="Flexion", ico='@blade', img='droop_rest',
                     court="Courbure des pales sous leur poids, à l'arrêt et en vol",
                     long="Chaque pale est déformée par 8 os : la courbe suit celle d'une vraie poutre encastrée, "
                          "plus forte en bout qu'à la racine. La longueur de la pale est conservée."),
    'droop_rest': dict(t="Flexion à l'arrêt", ico='MOD_SIMPLEDEFORM', img='droop_rest', unite="m",
                       court="Affaissement du bout de pale quand le rotor est arrêté, en mètres",
                       long="Mesuré au bout de la pale par rapport à une pale parfaitement droite.",
                       conseil="0,4 à 0,8 m = réaliste pour des pales de 8 m."),
    'droop_flight': dict(t="Flexion en vol", ico='MOD_SIMPLEDEFORM', img='droop_flight', unite="m",
                         court="Flexion qui reste à plein régime. 0 = pale droite, négatif = pale qui se relève",
                         long="En vol, la force centrifuge tend les pales. On garde un peu de flexion pour le réalisme.",
                         conseil="0,1 à 0,3 m."),
    'sec_angles': dict(t="Angles des pales", ico='DRIVER_ROTATIONAL_DIFFERENCE', img='coning',
                       court="Conicité, pas collectif et battement : la façon dont les pales prennent l'air",
                       long="Ces angles ne s'appliquent qu'en vol : ils sont multipliés par le régime des pales."),
    'coning': dict(t="Conicité", ico='DRIVER_ROTATIONAL_DIFFERENCE', img='coning', unite="°",
                   court="Les pales se relèvent en vol et forment un cône très ouvert, en degrés",
                   long="Effet de la portance qui soulève les pales. Visible surtout de profil.",
                   conseil="2 à 5°."),
    'collective': dict(t="Pas collectif", ico='ORIENTATION_GIMBAL', img='collective', unite="°",
                       court="Incidence commune de toutes les pales, en degrés : plus de pas = plus de portance",
                       long="Fait pivoter chaque pale sur son axe. Au sol on met peu de pas, au décollage davantage.",
                       conseil="4 à 8° en stationnaire, jusqu'à 16° en montée."),
    'blade_wobble': dict(t="Battement", ico='FORCE_HARMONIC', img='wobble', unite="°",
                         court="Petite oscillation des pales vers le haut et le bas pendant la rotation, en degrés",
                         long="Rend le rotor moins mécanique. Chaque pale a un décalage différent.",
                         conseil="0,2 à 0,6° ; 0 = rotor parfaitement rigide."),
    'sec_disc': dict(t="Inclinaison du disque", ico='@disc', img='disc',
                     court="Penche le plan des pales (commande cyclique) : l'hélico « tire » vers ce côté",
                     long="Réglage porté par l'os CTRL_Disque (limité à ±12°). On peut l'animer comme n'importe quel os : "
                          "pencher le disque vers l'avant pour accompagner une accélération."),
    'disc_x': dict(t="Latéral", ico='EMPTY_ARROWS', img='disc', unite="°",
                   court="Penche le disque à gauche ou à droite. Positif : le côté gauche monte, le disque penche à droite",
                   long="Rotation X de l'os CTRL_Disque."),
    'disc_z': dict(t="Avant / arrière", ico='EMPTY_ARROWS', img='disc', unite="°",
                   court="Penche le disque vers l'avant ou l'arrière. Positif : l'avant monte, le disque penche en arrière",
                   long="Rotation Z de l'os CTRL_Disque. Valeur négative = disque penché vers l'avant (accélération)."),

    # ------------------------------------------------------------ vol
    'sec_hover': dict(t="Vol stationnaire", ico='@hover', img='hover_on',
                      court="Fait flotter l'hélico au-dessus du sol avec de petits mouvements naturels",
                      long="Tous les mouvements sont calés sur la boucle (cycles entiers) : ils raccordent sans saut. "
                           "Pour un vrai déplacement, animer l'os CTRL_Main."),
    'hover_on': dict(t="Intensité", ico='FORCE_FORCE', img='hover_on', unite="0 à 1",
                     court="0 = posé au sol sans mouvement, 1 = vol stationnaire complet",
                     long="Animé par les modes Démarrage (décollage) et Arrêt (atterrissage). En Boucle il vaut 1, en Parking 0."),
    'hover_height': dict(t="Hauteur", ico='EMPTY_SINGLE_ARROW', img='hover_height', unite="m",
                         court="Altitude du vol stationnaire au-dessus de l'os CTRL_Main, en mètres",
                         long="Pendant le décollage, l'hélico monte de 0 à cette hauteur.",
                         conseil="1 à 3 m = effet de sol ; 5 à 20 m = vol."),
    'sec_moves': dict(t="Mouvements", ico='FORCE_TURBULENCE', img='hover_xy',
                      court="Amplitude des petits mouvements du stationnaire (0 = immobile)",
                      long="Les mouvements combinent deux ondes de fréquences différentes pour ne pas paraître répétitifs."),
    'hover_z': dict(t="Pompage", ico='SORT_DESC', img='hover_z', unite="m",
                    court="L'hélico monte et descend doucement, amplitude en mètres",
                    conseil="0,05 à 0,2 m."),
    'hover_xy': dict(t="Dérive", ico='ARROW_LEFTRIGHT', img='hover_xy', unite="m",
                     court="L'hélico glisse lentement autour de sa position, amplitude en mètres",
                     conseil="0,05 à 0,3 m."),
    'hover_tilt': dict(t="Roulis et tangage", ico='ORIENTATION_GIMBAL', img='hover_tilt', unite="°",
                       court="La cabine se balance sur les côtés et d'avant en arrière, amplitude en degrés",
                       conseil="0,5 à 2°."),
    'hover_yaw': dict(t="Lacet", ico='DRIVER_ROTATIONAL_DIFFERENCE', img='hover_yaw', unite="°",
                      court="L'hélico pivote légèrement sur lui-même, amplitude en degrés",
                      conseil="0,5 à 1,5°."),
    'sec_trajet': dict(t="Déplacer l'hélico", ico='OBJECT_ORIGIN', img='ctrl_main',
                       court="Pour une trajectoire : animer l'os CTRL_Main (position et rotation)",
                       long="CTRL_Main porte tout l'hélico. Le vol stationnaire s'ajoute par-dessus. "
                            "L'os root (grand cercle au sol) sert à placer le rig entier dans la scène."),

    # ------------------------------------------------------------ LEDs
    'sec_leds_gen': dict(t="Général", ico='@led', img='led_map',
                         court="Interrupteurs généraux et préréglages pour toutes les LEDs",
                         long="Chaque LED a une lentille lumineuse (matériau) et une vraie source de lumière qui éclaire la carlingue."),
    'leds_on': dict(t="Actives", ico='LIGHT', img='leds_master', unite="0 à 1",
                    court="Interrupteur général : 0 = toutes les LEDs éteintes, 1 = allumées",
                    long="Valeur intermédiaire = gradateur. Animable pour un allumage progressif."),
    'leds_blink': dict(t="Flash", ico='LIGHT_SUN', img='leds_master', unite="0 à 1",
                       court="0 = les LEDs clignotantes restent allumées fixes, 1 = elles clignotent",
                       long="Pratique pour un rendu fixe : toutes les LEDs sont visibles quelle que soit l'image."),
    'preset_AVIATION': dict(t="Aviation", ico='@preset_aviation', img='preset_aviation',
                            court="Réglage réel : rouge à gauche, vert à droite, flash blanc en queue, gyrophares rouges",
                            long="Remet couleurs, modes, éclats et décalages d'origine pour toutes les LEDs."),
    'preset_RED': dict(t="Rouge", ico='@preset_red', img='preset_red', court="Toutes les LEDs en rouge (les modes ne changent pas)"),
    'preset_WHITE': dict(t="Blanc", ico='@preset_white', img='preset_white', court="Toutes les LEDs en blanc (les modes ne changent pas)"),
    'preset_SYNC': dict(t="Synchro", ico='@preset_sync', img='preset_sync', court="Toutes les LEDs clignotent ensemble au même rythme"),
    'sec_leds_list': dict(t="LEDs une par une", ico='OUTLINER_OB_LIGHT', img='led_map',
                          court="Réglages individuels : couleur, mode, rythme et puissance de chaque LED",
                          long="Déplier une LED pour la régler. La pastille de couleur et le mode sont visibles directement dans l'en-tête."),
    'led_color': dict(t="Couleur", ico='COLOR', img='preset_aviation',
                      court="Couleur de la LED : appliquée à la fois à la lentille et à la lumière émise"),
    'led_mode': dict(t="Mode", ico='@led_mode_1', img='led_mode_1',
                     court="Fixe, clignotant, double flash ou gyrophare",
                     long="Fixe : toujours allumée. Clignotant : moitié allumée, moitié éteinte. "
                          "Double flash : deux éclats courts (feu anticollision). Gyrophare : montée et descente douces."),
    'led_mode_0': dict(t="Fixe", ico='@led_mode_0', img='led_mode_0', court="Toujours allumée"),
    'led_mode_1': dict(t="Clignotant", ico='@led_mode_1', img='led_mode_1', court="Moitié du cycle allumée, moitié éteinte"),
    'led_mode_2': dict(t="Double flash", ico='@led_mode_2', img='led_mode_2', court="Deux éclats courts par cycle, comme un feu anticollision"),
    'led_mode_3': dict(t="Gyrophare", ico='@led_mode_3', img='led_mode_3', court="Montée et descente douces, comme une balise tournante"),
    'led_cycles': dict(t="Éclats", ico='MOD_WAVE', img='led_cycles', unite="par boucle",
                       court="Nombre de cycles (éclats) pendant la boucle. Entier : la boucle reste sans raccord",
                       long="Pour connaître la fréquence : éclats ÷ durée de la boucle en secondes.",
                       conseil="10 éclats sur 10 s = 1 flash par seconde."),
    'led_phase': dict(t="Décalage", ico='MOD_TIME', img='led_phase', unite="0 à 1",
                      court="Décale le cycle de la LED : 0,5 = la LED s'allume quand l'autre s'éteint",
                      long="Utile pour que deux gyrophares ne clignotent pas en même temps."),
    'led_glow': dict(t="Lentille", ico='SHADING_RENDERED', img='led_glow', unite="intensité",
                     court="Brillance du verre de la LED (émission du matériau), visible directement à la caméra",
                     conseil="3 pour un voyant, 10 à 20 pour un feu extérieur."),
    'led_watts': dict(t="Lumière", ico='LIGHT_POINT', img='led_watts', unite="W",
                      court="Puissance de la vraie source de lumière qui éclaire la carlingue et le sol, en watts",
                      long="La source est invisible à la caméra : seule la lentille se voit, la lumière éclaire autour.",
                      conseil="25 W pour un feu de navigation, 60 à 150 W pour un flash ou un gyrophare."),
    'led_select': dict(t="Sélectionner", ico='RESTRICT_SELECT_OFF', court="Sélectionne la source de lumière de cette LED dans la scène"),

    # ------------------------------------------------------------ portes
    'sec_doors_all': dict(t="Toutes les portes", ico='@door', img='doors',
                          court="Ouvre ou ferme les quatre portes d'un clic, ou crée l'animation d'ouverture",
                          long="Le UH-60 a deux portes de cockpit à charnières (pilote à droite, copilote à gauche) "
                               "et deux grandes portes de cabine qui coulissent vers l'arrière. "
                               "Chaque porte a un curseur de 0 (fermée) à 1 (ouverte) que l'on peut animer avec des images clés."),
    'doors_open': dict(t="Tout ouvrir", ico='@door_open', img='doors',
                       court="Ouvre les portes choisies. Si elles sont animées, une image clé est ajoutée à l'image courante"),
    'doors_close': dict(t="Tout fermer", ico='@door', img='doors',
                        court="Ferme les portes choisies. Si elles sont animées, une image clé est ajoutée à l'image courante"),
    'door_anim': dict(t="Animer l'ouverture", ico='@door_anim', img='door_anim', unite="images",
                      court="Crée deux images clés : la porte part de son état actuel à l'image courante et arrive au bout de la durée choisie",
                      long="Le départ et l'arrivée sont adoucis (courbe en S), comme une porte poussée à la main. "
                           "Les clés s'ajoutent à l'animation existante : on peut enchaîner ouverture puis fermeture plus loin dans la timeline.",
                      conseil="Cockpit : 24 à 36 images (1 à 1,5 s). Cabine : 48 à 72 images (2 à 3 s), la porte est lourde."),
    'door_anim_close': dict(t="Animer la fermeture", ico='@door_anim', img='door_anim',
                            court="Comme « Animer l'ouverture », mais la porte se referme au bout de la durée choisie"),
    'door_frames': dict(t="Durée", ico='PREVIEW_RANGE', img='door_anim', unite="images",
                        court="Durée de l'ouverture ou de la fermeture animée (24 images = 1 s à 24 i/s)"),
    'door_which': dict(t="Portes concernées", ico='RESTRICT_SELECT_OFF', img='doors',
                       court="Choisit les portes que les boutons ouvrent, ferment ou animent"),
    'door_key': dict(t="Clé sur les portes", ico='DECORATE_KEYFRAME', img='door_anim',
                     court="Enregistre l'ouverture actuelle des quatre portes comme image clé, à l'image courante"),
    'door_clear': dict(t="Effacer l'animation", ico='X', img='door_anim',
                       court="Supprime les images clés des quatre portes (elles gardent leur position actuelle)"),
    'sec_doors_cockpit': dict(t="Portes cockpit", ico='@door_cockpit', img='door_cockpit',
                              court="Portes pilote et copilote : charnières à l'avant, elles pivotent vers l'extérieur",
                              long="Chaque porte tourne autour de l'axe de ses deux charnières avant, légèrement penché comme le flanc "
                                   "du cockpit. 0 = fermée, 1 = ouverte à l'« Angle d'ouverture »."),
    'door_cockpit_l': dict(t="Gauche (copilote)", ico='@door_cockpit', img='door_cockpit', unite="0 à 1",
                           court="Ouverture de la porte cockpit gauche, côté copilote : 0 = fermée, 1 = ouverte",
                           conseil="Survoler le curseur et appuyer sur I pour poser une image clé"),
    'door_cockpit_r': dict(t="Droite (pilote)", ico='@door_cockpit', img='door_cockpit', unite="0 à 1",
                           court="Ouverture de la porte cockpit droite, côté pilote (sur le UH-60, le commandant de bord est à droite) : 0 = fermée, 1 = ouverte",
                           conseil="Survoler le curseur et appuyer sur I pour poser une image clé"),
    'door_cockpit_angle': dict(t="Angle d'ouverture", ico='DRIVER_ROTATIONAL_DIFFERENCE', img='door_cockpit', unite="°",
                               court="Angle atteint par les portes cockpit quand leur curseur vaut 1",
                               conseil="80° par défaut. 30 à 45° pour une porte entrebâillée au parking."),
    'sec_doors_cabin': dict(t="Portes cabine", ico='@door_cabin', img='door_cabin',
                            court="Grandes portes coulissantes : elles s'écartent du fuselage puis glissent vers l'arrière sur leurs rails",
                            long="Pendant les premiers 12 % du curseur, la porte s'écarte de l'« Écart sur rails » (elle sort de son cadre). "
                                 "Ensuite elle glisse vers l'arrière de toute la « Course ». Ouverte, elle dégage le passage "
                                 "de la cabine (environ 1,7 m de large sur le vrai UH-60)."),
    'door_cabin_l': dict(t="Gauche", ico='@door_cabin', img='door_cabin', unite="0 à 1",
                         court="Ouverture de la porte cabine gauche : 0 = fermée, 0,12 = sortie du cadre, 1 = complètement ouverte",
                         conseil="Survoler le curseur et appuyer sur I pour poser une image clé"),
    'door_cabin_r': dict(t="Droite", ico='@door_cabin', img='door_cabin', unite="0 à 1",
                         court="Ouverture de la porte cabine droite : 0 = fermée, 0,12 = sortie du cadre, 1 = complètement ouverte",
                         conseil="Survoler le curseur et appuyer sur I pour poser une image clé"),
    'door_cabin_travel': dict(t="Course", ico='ARROW_LEFTRIGHT', img='door_cabin', unite="m",
                              court="Distance parcourue vers l'arrière par les portes cabine complètement ouvertes",
                              conseil="1,85 m : la porte dégage toute l'ouverture. Moins pour une porte à moitié ouverte en vol."),
    'door_cabin_out': dict(t="Écart sur rails", ico='EMPTY_SINGLE_ARROW', img='door_cabin', unite="m",
                           court="De combien la porte cabine s'écarte du fuselage avant de glisser",
                           conseil="Calculé sur le modèle pour que la porte ne traverse pas la carlingue : ne pas descendre en dessous."),
    'doors_install': dict(t="Ajouter les portes à ce rig", ico='@door', img='doors',
                          court="Rend ce rig compatible avec l'onglet Portes : sépare les portes gauche et droite et crée leurs charnières et glissières",
                          long="Pour les fichiers faits avec la version 1.0 ou 1.1 du rig. Les objets BH_Portes_Cockpit et BH_Portes_Cabine "
                               "sont remplacés par quatre portes indépendantes, sans bouger à l'écran. Annulable avec Ctrl+Z."),
    'door_cabin_travel_def': dict(t="Course d'origine (interne)", court="Valeur calculée à l'installation, utilisée par Réinitialiser"),
    'door_cabin_out_def': dict(t="Écart d'origine (interne)", court="Valeur calculée à l'installation, utilisée par Réinitialiser"),
    'bh_doors': dict(t="Portes installées (interne)", court="Indique que les portes animables sont installées sur ce rig"),
    'bh_model': dict(t="Version du modèle (interne)", court="Version du modèle UH-60 téléchargé"),

    # ------------------------------------------------------------ modele
    'sec_model': dict(t="Modèle UH-60", ico='@download', img='model',
                      court="Le plugin pilote le modèle 3D du UH-60 : on le télécharge une fois, puis on l'ajoute à n'importe quelle scène",
                      long="Le modèle est téléchargé depuis la page de publication du plugin, vérifié (taille et empreinte SHA-256) "
                           "puis rangé dans le dossier utilisateur de l'extension. « Ajouter à la scène » importe la collection "
                           "« UH-60 Black Hawk » au curseur 3D : maillages texturés, rig, portes et LEDs."),
    'model_download': dict(t="Télécharger le modèle", ico='@download', img='model',
                           court="Télécharge le modèle UH-60 et ses textures, puis l'installe pour le plugin (une seule fois)",
                           conseil="L'accès en ligne doit être autorisé : Préférences › Système › Réseau"),
    'model_update': dict(t="Mettre à jour le modèle", ico='FILE_REFRESH', img='model',
                         court="Télécharge à nouveau la dernière version publiée du modèle"),
    'model_cancel': dict(t="Annuler", ico='CANCEL', court="Arrête le téléchargement en cours"),
    'model_import': dict(t="Ajouter à la scène", ico='IMPORT', img='model',
                         court="Ajoute l'hélico complet au curseur 3D : maillages texturés, rig, portes et LEDs",
                         long="On peut l'ajouter plusieurs fois : chaque hélico a son propre rig et le panneau pilote celui qui est sélectionné."),
    'model_studio': dict(t="Avec studio et caméras", ico='OUTLINER_OB_CAMERA', img='model',
                         court="Ajoute aussi les quatre lumières de studio, les quatre caméras et le monde du modèle"),
    'model_file': dict(t="Installer depuis un fichier", ico='FILE_FOLDER', img='model',
                       court="Installe le modèle à partir de l'archive .zip déjà téléchargée (sans connexion)"),
    'model_folder': dict(t="Ouvrir le dossier", ico='FILEBROWSER', court="Ouvre le dossier où le modèle est installé"),
    'online': dict(t="Accès en ligne désactivé", ico='INTERNET_OFFLINE',
                   court="Blender bloque les connexions. Autoriser : Préférences › Système › Réseau › Autoriser l'accès en ligne"),

    # ------------------------------------------------------------ aide
    'sec_start': dict(t="Prise en main", ico='@help', img='cover',
                      court="Les 6 étapes pour animer le Black Hawk",
                      long="1. Sans hélico dans la scène : télécharger le modèle, puis « Ajouter à la scène ».\n"
                           "2. Onglet Animation : choisir Boucle, Démarrage, Arrêt ou Parking, et le régime.\n"
                           "3. Onglet Pales : ajuster la flexion et, si besoin, pencher le disque.\n"
                           "4. Onglet Vol : régler la hauteur et les petits mouvements du stationnaire.\n"
                           "5. Onglet Portes : ouvrir les portes ou animer leur ouverture.\n"
                           "6. Onglet LEDs : choisir un préréglage, puis affiner chaque feu."),
    'sec_ctrl': dict(t="Contrôles du rig", ico='ARMATURE_DATA', img='ctrl_main',
                     court="Les os à manipuler à la main : un clic les sélectionne en mode Pose"),
    'bone_root': dict(t="root", ico='PIVOT_CURSOR', court="Grand cercle au sol : place le rig entier dans la scène"),
    'bone_CTRL_Main': dict(t="CTRL_Main", ico='OBJECT_ORIGIN', img='ctrl_main', court="Contour de l'hélico : trajectoire et orientation de l'appareil"),
    'bone_CTRL_Disque': dict(t="CTRL_Disque", ico='@disc', img='disc', court="Croix au-dessus du rotor : inclinaison du disque (rotations X et Z, ±12°)"),
    'bone_CTRL_Rotor': dict(t="CTRL_Rotor", ico='@rotor', img='rpm', court="Cercle du mât : décalage manuel de l'angle du rotor principal (rotation Y)"),
    'bone_CTRL_Queue': dict(t="CTRL_Queue", ico='@rotor', img='tail_ratio', court="Cercle de queue : décalage manuel de l'angle du rotor de queue (rotation Y)"),
    'show_images': dict(t="Illustrations", ico='IMAGE_DATA', court="Affiche une illustration en tête de chaque section du panneau"),
    'img_scale': dict(t="Taille", ico='FULLSCREEN_ENTER', court="Taille des illustrations dans le panneau"),
    'open_doc': dict(t="Documentation complète", ico='@doc', court="Ouvre la documentation illustrée dans le navigateur"),
    'reset': dict(t="Réinitialiser", ico='LOOP_BACK', court="Remet les réglages de cet onglet à leurs valeurs d'origine"),
    'diag': dict(t="État du rig", ico='CHECKMARK', court="Vérifie que les drivers du rig sont valides"),

    # ------------------------------------------------------------ proprietes internes (lecture seule)
    'rotor_turns': dict(t="Tours rotor (interne)", court="Tours cumulés du rotor principal. Animé par le plugin : ne pas modifier"),
    'tail_turns': dict(t="Tours queue (interne)", court="Tours cumulés du rotor de queue. Animé par le plugin : ne pas modifier"),
    'loop_phase': dict(t="Phase (interne)", court="Position dans la boucle, calculée par un driver : ne pas modifier"),
    'anim_mode': dict(t="Mode (interne)", court="Mode d'animation choisi dans le panneau Black Hawk"),
    'led_names': dict(t="Noms des LEDs (interne)", court="Liste des LEDs du rig, utilisée par le panneau"),
    'bh_rig': dict(t="Marqueur du rig", court="Identifie cet objet comme rig Black Hawk : ne pas supprimer"),
    'led_t': dict(t="Position dans le cycle (interne)", court="Calculée par un driver : ne pas modifier"),
    'led_level': dict(t="Niveau instantané (interne)", court="Luminosité actuelle de la LED, calculée par un driver : ne pas modifier"),
    'led_def': dict(t="Valeur d'origine (interne)", court="Valeur d'origine utilisée par le préréglage Aviation"),
}

# noms lisibles des LEDs
LED_LABEL = {
    'Nav_Babord': "Nav. gauche (rouge)",
    'Nav_Tribord': "Nav. droite (verte)",
    'Feu_Queue': "Feu de queue",
    'Gyro_Ventre': "Gyro ventral",
    'Gyro_Toit': "Gyro dorsal",
    'Cockpit_Gauche': "Cockpit gauche",
    'Cockpit_Centre': "Cockpit centre",
    'Cockpit_Droit': "Cockpit droit",
}
# description complete (documentation)
LED_DESC = {
    'Nav_Babord': "Feu de navigation gauche (babord), rouge fixe",
    'Nav_Tribord': "Feu de navigation droit (tribord), vert fixe",
    'Feu_Queue': "Feu de queue : double flash blanc anticollision",
    'Gyro_Ventre': "Gyrophare rouge sous le fuselage",
    'Gyro_Toit': "Gyrophare rouge sur le dessus de la cabine",
    'Cockpit_Gauche': "Voyant de la planche de bord, côté gauche",
    'Cockpit_Centre': "Voyant de la planche de bord, au centre",
    'Cockpit_Droit': "Voyant de la planche de bord, côté droit",
}

# ordre de la documentation : (titre de chapitre, [cles])
DOC = [
    ("Animation", ['sec_mode', 'mode_LOOP', 'mode_STARTUP', 'mode_SHUTDOWN', 'mode_PARKED', 'ramp_frames',
                   'sec_loop', 'loop_start', 'loop_frames', 'readout', 'sec_rotors', 'rpm_real', 'rpm', 'nr', 'tail_ratio', 'rotor_info', 'hud', 'rotor_dir', 'tail_dir']),
    ("Pales", ['sec_spool', 'spool', 'sec_flex', 'droop_rest', 'droop_flight', 'sec_angles', 'coning', 'collective', 'blade_wobble',
               'sec_disc', 'disc_x', 'disc_z']),
    ("Vol", ['sec_hover', 'hover_on', 'hover_height', 'sec_moves', 'hover_z', 'hover_xy', 'hover_tilt', 'hover_yaw', 'sec_trajet']),
    ("LEDs", ['sec_leds_gen', 'leds_on', 'leds_blink', 'preset_AVIATION', 'preset_RED', 'preset_WHITE', 'preset_SYNC',
              'sec_leds_list', 'led_color', 'led_mode', 'led_mode_0', 'led_mode_1', 'led_mode_2', 'led_mode_3',
              'led_cycles', 'led_phase', 'led_glow', 'led_watts']),
    ("Portes", ['sec_doors_all', 'doors_open', 'doors_close', 'door_which', 'door_anim', 'door_anim_close', 'door_frames', 'door_key', 'door_clear',
                'sec_doors_cockpit', 'door_cockpit_l', 'door_cockpit_r', 'door_cockpit_angle',
                'sec_doors_cabin', 'door_cabin_l', 'door_cabin_r', 'door_cabin_travel', 'door_cabin_out', 'doors_install']),
    ("Modèle UH-60", ['sec_model', 'model_download', 'model_update', 'model_import', 'model_studio', 'model_file', 'model_folder', 'online']),
    ("Contrôles du rig", ['sec_ctrl', 'bone_root', 'bone_CTRL_Main', 'bone_CTRL_Disque', 'bone_CTRL_Rotor', 'bone_CTRL_Queue']),
]


def tooltip(key):
    """Info-bulle complete : phrase courte + conseil."""
    h = HELP.get(key)
    if not h:
        return ""
    s = h['court']
    if h.get('unite'):
        s += f" ({h['unite']})"
    if h.get('conseil'):
        s += ". Conseil : " + h['conseil']
    return s


def full_text(key):
    h = HELP.get(key, {})
    parts = [h.get('court', '')]
    if h.get('long'):
        parts.append(h['long'])
    if h.get('conseil'):
        parts.append("Conseil : " + h['conseil'])
    return "\n".join(p for p in parts if p)
