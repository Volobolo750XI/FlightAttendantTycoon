using { /Fortnite.com/Devices }
using { /Fortnite.com/UI }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/UI }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Cinématique de décollage : quand on appuie sur le bouton, les 120 images du dossier
# Content/Cinematique/Vol1 défilent en plein écran (24 images/s, 5 s), puis le joueur est
# téléporté dans la cabine en vol.
#
# Dans UEFN :
#   1. Crée le dossier Content/Cinematique/Vol1 et importe dedans les 120 images Decollage_001 ... 120.
#   2. Compile, place ce device, et choisis :
#      Bouton      : le bouton qui lance la cinématique (pour tester).
#      Son         : (facultatif) un Appareil Lecteur audio avec le son du décollage.
#      ArriveeEnVol: (facultatif) un Appareil Téléporteur posé dans la cabine en vol.
cinematique_decollage := class(creative_device):
    @editable Bouton:button_device = button_device{}
    @editable Son:?audio_player_device = false
    @editable ArriveeEnVol:?teleporter_device = false
    # Images par seconde (24 = vitesse normale de la vidéo).
    @editable ImagesParSeconde:float = 24.0

    Images:[]texture = array:
        Cinematique.Vol1.Decollage_001,
        Cinematique.Vol1.Decollage_002,
        Cinematique.Vol1.Decollage_003,
        Cinematique.Vol1.Decollage_004,
        Cinematique.Vol1.Decollage_005,
        Cinematique.Vol1.Decollage_006,
        Cinematique.Vol1.Decollage_007,
        Cinematique.Vol1.Decollage_008,
        Cinematique.Vol1.Decollage_009,
        Cinematique.Vol1.Decollage_010,
        Cinematique.Vol1.Decollage_011,
        Cinematique.Vol1.Decollage_012,
        Cinematique.Vol1.Decollage_013,
        Cinematique.Vol1.Decollage_014,
        Cinematique.Vol1.Decollage_015,
        Cinematique.Vol1.Decollage_016,
        Cinematique.Vol1.Decollage_017,
        Cinematique.Vol1.Decollage_018,
        Cinematique.Vol1.Decollage_019,
        Cinematique.Vol1.Decollage_020,
        Cinematique.Vol1.Decollage_021,
        Cinematique.Vol1.Decollage_022,
        Cinematique.Vol1.Decollage_023,
        Cinematique.Vol1.Decollage_024,
        Cinematique.Vol1.Decollage_025,
        Cinematique.Vol1.Decollage_026,
        Cinematique.Vol1.Decollage_027,
        Cinematique.Vol1.Decollage_028,
        Cinematique.Vol1.Decollage_029,
        Cinematique.Vol1.Decollage_030,
        Cinematique.Vol1.Decollage_031,
        Cinematique.Vol1.Decollage_032,
        Cinematique.Vol1.Decollage_033,
        Cinematique.Vol1.Decollage_034,
        Cinematique.Vol1.Decollage_035,
        Cinematique.Vol1.Decollage_036,
        Cinematique.Vol1.Decollage_037,
        Cinematique.Vol1.Decollage_038,
        Cinematique.Vol1.Decollage_039,
        Cinematique.Vol1.Decollage_040,
        Cinematique.Vol1.Decollage_041,
        Cinematique.Vol1.Decollage_042,
        Cinematique.Vol1.Decollage_043,
        Cinematique.Vol1.Decollage_044,
        Cinematique.Vol1.Decollage_045,
        Cinematique.Vol1.Decollage_046,
        Cinematique.Vol1.Decollage_047,
        Cinematique.Vol1.Decollage_048,
        Cinematique.Vol1.Decollage_049,
        Cinematique.Vol1.Decollage_050,
        Cinematique.Vol1.Decollage_051,
        Cinematique.Vol1.Decollage_052,
        Cinematique.Vol1.Decollage_053,
        Cinematique.Vol1.Decollage_054,
        Cinematique.Vol1.Decollage_055,
        Cinematique.Vol1.Decollage_056,
        Cinematique.Vol1.Decollage_057,
        Cinematique.Vol1.Decollage_058,
        Cinematique.Vol1.Decollage_059,
        Cinematique.Vol1.Decollage_060,
        Cinematique.Vol1.Decollage_061,
        Cinematique.Vol1.Decollage_062,
        Cinematique.Vol1.Decollage_063,
        Cinematique.Vol1.Decollage_064,
        Cinematique.Vol1.Decollage_065,
        Cinematique.Vol1.Decollage_066,
        Cinematique.Vol1.Decollage_067,
        Cinematique.Vol1.Decollage_068,
        Cinematique.Vol1.Decollage_069,
        Cinematique.Vol1.Decollage_070,
        Cinematique.Vol1.Decollage_071,
        Cinematique.Vol1.Decollage_072,
        Cinematique.Vol1.Decollage_073,
        Cinematique.Vol1.Decollage_074,
        Cinematique.Vol1.Decollage_075,
        Cinematique.Vol1.Decollage_076,
        Cinematique.Vol1.Decollage_077,
        Cinematique.Vol1.Decollage_078,
        Cinematique.Vol1.Decollage_079,
        Cinematique.Vol1.Decollage_080,
        Cinematique.Vol1.Decollage_081,
        Cinematique.Vol1.Decollage_082,
        Cinematique.Vol1.Decollage_083,
        Cinematique.Vol1.Decollage_084,
        Cinematique.Vol1.Decollage_085,
        Cinematique.Vol1.Decollage_086,
        Cinematique.Vol1.Decollage_087,
        Cinematique.Vol1.Decollage_088,
        Cinematique.Vol1.Decollage_089,
        Cinematique.Vol1.Decollage_090,
        Cinematique.Vol1.Decollage_091,
        Cinematique.Vol1.Decollage_092,
        Cinematique.Vol1.Decollage_093,
        Cinematique.Vol1.Decollage_094,
        Cinematique.Vol1.Decollage_095,
        Cinematique.Vol1.Decollage_096,
        Cinematique.Vol1.Decollage_097,
        Cinematique.Vol1.Decollage_098,
        Cinematique.Vol1.Decollage_099,
        Cinematique.Vol1.Decollage_100,
        Cinematique.Vol1.Decollage_101,
        Cinematique.Vol1.Decollage_102,
        Cinematique.Vol1.Decollage_103,
        Cinematique.Vol1.Decollage_104,
        Cinematique.Vol1.Decollage_105,
        Cinematique.Vol1.Decollage_106,
        Cinematique.Vol1.Decollage_107,
        Cinematique.Vol1.Decollage_108,
        Cinematique.Vol1.Decollage_109,
        Cinematique.Vol1.Decollage_110,
        Cinematique.Vol1.Decollage_111,
        Cinematique.Vol1.Decollage_112,
        Cinematique.Vol1.Decollage_113,
        Cinematique.Vol1.Decollage_114,
        Cinematique.Vol1.Decollage_115,
        Cinematique.Vol1.Decollage_116,
        Cinematique.Vol1.Decollage_117,
        Cinematique.Vol1.Decollage_118,
        Cinematique.Vol1.Decollage_119,
        Cinematique.Vol1.Decollage_120

    var EnCours:logic = false

    OnBegin<override>()<suspends>:void =
        loop:
            Joueur := Bouton.InteractedWithEvent.Await()
            if (not EnCours?):
                spawn{Jouer(Joueur)}

    Jouer(Joueur:agent)<suspends>:void =
        set EnCours = true
        if (P := player[Joueur], UI := GetPlayerUI[P], Premiere := Images[0]):
            Ecran := texture_block{DefaultImage := Premiere, DefaultDesiredSize := vector2{X := 1920.0, Y := 1080.0}}
            Fond := canvas:
                Slots := array:
                    canvas_slot:
                        Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.0}, Maximum := vector2{X := 1.0, Y := 1.0}}
                        Offsets := margin{Left := 0.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
                        SizeToContent := false
                        Widget := Ecran
            UI.AddWidget(Fond, player_ui_slot{ZOrder := 100, InputMode := ui_input_mode.None})
            if (S := Son?) { S.Play() }
            Pause := 1.0 / Max(1.0, ImagesParSeconde)
            for (Image : Images):
                Ecran.SetImage(Image)
                Sleep(Pause)
            # on téléporte pendant que la dernière image est encore affichée
            if (T := ArriveeEnVol?) { T.Teleport(Joueur) }
            Sleep(0.3)
            UI.RemoveWidget(Fond)
        set EnCours = false
