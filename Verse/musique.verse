using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }
using { /Fortnite.com/UI }
using { /Verse.org/Assets }

# Flight Attendant Tycoon - MUSIQUE ON / OFF, pour chaque joueur.
# Le joueur coupe ou remet la musique avec une TOUCHE (Declencheur d'entree) et/ou des BOUTONS poses dans
# la map. Une petite icone ronde sous les barres d'argent montre l'etat : verte = ON, rouge = OFF.
# Le choix est SAUVEGARDE : s'il a coupe la musique, elle reste coupee la prochaine fois.
# (Dans Fortnite, une icone du HUD ne peut pas etre cliquee sans afficher la souris et bloquer le jeu :
#  c'est pour ca qu'on passe par une touche ou un bouton.)
#
# Installation dans UEFN :
#   - importe le dossier Textures/InterfaceMusique a la racine du projet (comme InterfacePC),
#     reglages des 2 images : UserInterface2D, groupe UI, sRGB coche, NoMipmaps ;
#   - ta musique : un appareil "Lecteur audio" (Audio Player) avec ton son, et dans ses options :
#       Lecture automatique (Auto Play) : NON, En boucle / Redemarrer : OUI,
#       Peut etre entendu par (Can Be Heard By) : Joueurs enregistres (Registered Players),
#       Spatialisation / Attenuation : desactivee (pour l'entendre partout) ;
#   - (au choix) un "Declencheur d'entree" (Input Trigger) : choisis la touche (ex. M) et
#     "Afficher sur le HUD" pour que les joueurs voient la touche ;
#   - (au choix) un ou plusieurs "Bouton" (Button) dans le lobby, texte d'interaction : MUSIC ON/OFF ;
#   - pose ce device et remplis : Musique, Touche, Boutons.

musique_sauvegarde := class<final><persistable>:
    Coupee : logic = false

var MusiqueSauvegarde : weak_map(player, musique_sauvegarde) = map{}

musique_device := class(creative_device):
    @editable Musique : audio_player_device = audio_player_device{}
    @editable Touche : ?input_trigger_device = false
    @editable Boutons : []button_device = array{}
    @editable AfficherIcone : logic = true

    var Icones : [player]texture_block = map{}
    var Vus : [player]logic = map{}

    OnBegin<override>()<suspends>:void =
        if (T := Touche?):
            T.PressedEvent.Subscribe(Basculer)
        for (B : Boutons):
            B.InteractedWithEvent.Subscribe(Basculer)
        loop:
            for (P : GetPlayspace().GetPlayers(), not Vus[P]):
                if (set Vus[P] = true) {}
                Appliquer(P)
            Sleep(1.0)

    EstCoupee(P:player):logic =
        if (S := MusiqueSauvegarde[P]) then S.Coupee else false

    Basculer(Agent:agent):void =
        if (P := player[Agent]):
            Coupee := EstCoupee(P)
            Nouveau := if (Coupee?) then false else true
            if (set MusiqueSauvegarde[P] = musique_sauvegarde{Coupee := Nouveau}) {}
            Appliquer(P)

    # lance ou coupe la musique pour CE joueur seulement, et met l'icone a jour
    Appliquer(P:player):void =
        Coupee := EstCoupee(P)
        if (Coupee?):
            Musique.Unregister(P)
            Musique.Stop(P)
        else:
            Musique.Register(P)
            Musique.Play(P)
        if (AfficherIcone?):
            Img := if (Coupee?) then InterfaceMusique.Musique_Off else InterfaceMusique.Musique_On
            if (I := Icones[P]):
                I.SetImage(Img)
            else if (UI := GetPlayerUI[P]):
                I := texture_block{DefaultImage := Img, DefaultDesiredSize := vector2{X := 72.0, Y := 72.0}}
                # sous les 3 barres d'argent / revenu / rebirth (milieu du bord gauche)
                C := canvas:
                    Slots := array:
                        canvas_slot:
                            Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.5}, Maximum := vector2{X := 0.0, Y := 0.5}}
                            Alignment := vector2{X := 0.0, Y := 0.0}
                            Offsets := margin{Left := 20.0, Top := 128.0, Right := 72.0, Bottom := 72.0}
                            SizeToContent := false
                            Widget := I
                UI.AddWidget(C)
                if (set Icones[P] = I) {}
