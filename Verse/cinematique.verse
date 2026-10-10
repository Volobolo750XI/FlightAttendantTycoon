using { /Fortnite.com/Devices }
using { /Fortnite.com/UI }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/UI }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Cinématique de décollage : quand on appuie sur le bouton, les 120 images du dossier
# Content/Cinematique défilent en plein écran (24 images/s, 5 s), puis le joueur est
# téléporté dans la cabine en vol.
#
# Dans UEFN :
#   1. Crée le dossier Content/Cinematique et importe dedans les 120 images Decollage_001 ... 120.
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
        Cinematique.Decollage_001,
        Cinematique.Decollage_002,
        Cinematique.Decollage_003,
        Cinematique.Decollage_004,
        Cinematique.Decollage_005,
        Cinematique.Decollage_006,
        Cinematique.Decollage_007,
        Cinematique.Decollage_008,
        Cinematique.Decollage_009,
        Cinematique.Decollage_010,
        Cinematique.Decollage_011,
        Cinematique.Decollage_012,
        Cinematique.Decollage_013,
        Cinematique.Decollage_014,
        Cinematique.Decollage_015,
        Cinematique.Decollage_016,
        Cinematique.Decollage_017,
        Cinematique.Decollage_018,
        Cinematique.Decollage_019,
        Cinematique.Decollage_020,
        Cinematique.Decollage_021,
        Cinematique.Decollage_022,
        Cinematique.Decollage_023,
        Cinematique.Decollage_024,
        Cinematique.Decollage_025,
        Cinematique.Decollage_026,
        Cinematique.Decollage_027,
        Cinematique.Decollage_028,
        Cinematique.Decollage_029,
        Cinematique.Decollage_030,
        Cinematique.Decollage_031,
        Cinematique.Decollage_032,
        Cinematique.Decollage_033,
        Cinematique.Decollage_034,
        Cinematique.Decollage_035,
        Cinematique.Decollage_036,
        Cinematique.Decollage_037,
        Cinematique.Decollage_038,
        Cinematique.Decollage_039,
        Cinematique.Decollage_040,
        Cinematique.Decollage_041,
        Cinematique.Decollage_042,
        Cinematique.Decollage_043,
        Cinematique.Decollage_044,
        Cinematique.Decollage_045,
        Cinematique.Decollage_046,
        Cinematique.Decollage_047,
        Cinematique.Decollage_048,
        Cinematique.Decollage_049,
        Cinematique.Decollage_050,
        Cinematique.Decollage_051,
        Cinematique.Decollage_052,
        Cinematique.Decollage_053,
        Cinematique.Decollage_054,
        Cinematique.Decollage_055,
        Cinematique.Decollage_056,
        Cinematique.Decollage_057,
        Cinematique.Decollage_058,
        Cinematique.Decollage_059,
        Cinematique.Decollage_060,
        Cinematique.Decollage_061,
        Cinematique.Decollage_062,
        Cinematique.Decollage_063,
        Cinematique.Decollage_064,
        Cinematique.Decollage_065,
        Cinematique.Decollage_066,
        Cinematique.Decollage_067,
        Cinematique.Decollage_068,
        Cinematique.Decollage_069,
        Cinematique.Decollage_070,
        Cinematique.Decollage_071,
        Cinematique.Decollage_072,
        Cinematique.Decollage_073,
        Cinematique.Decollage_074,
        Cinematique.Decollage_075,
        Cinematique.Decollage_076,
        Cinematique.Decollage_077,
        Cinematique.Decollage_078,
        Cinematique.Decollage_079,
        Cinematique.Decollage_080,
        Cinematique.Decollage_081,
        Cinematique.Decollage_082,
        Cinematique.Decollage_083,
        Cinematique.Decollage_084,
        Cinematique.Decollage_085,
        Cinematique.Decollage_086,
        Cinematique.Decollage_087,
        Cinematique.Decollage_088,
        Cinematique.Decollage_089,
        Cinematique.Decollage_090,
        Cinematique.Decollage_091,
        Cinematique.Decollage_092,
        Cinematique.Decollage_093,
        Cinematique.Decollage_094,
        Cinematique.Decollage_095,
        Cinematique.Decollage_096,
        Cinematique.Decollage_097,
        Cinematique.Decollage_098,
        Cinematique.Decollage_099,
        Cinematique.Decollage_100,
        Cinematique.Decollage_101,
        Cinematique.Decollage_102,
        Cinematique.Decollage_103,
        Cinematique.Decollage_104,
        Cinematique.Decollage_105,
        Cinematique.Decollage_106,
        Cinematique.Decollage_107,
        Cinematique.Decollage_108,
        Cinematique.Decollage_109,
        Cinematique.Decollage_110,
        Cinematique.Decollage_111,
        Cinematique.Decollage_112,
        Cinematique.Decollage_113,
        Cinematique.Decollage_114,
        Cinematique.Decollage_115,
        Cinematique.Decollage_116,
        Cinematique.Decollage_117,
        Cinematique.Decollage_118,
        Cinematique.Decollage_119,
        Cinematique.Decollage_120

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
