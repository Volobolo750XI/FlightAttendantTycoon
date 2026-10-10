using { /Fortnite.com/Devices }
using { /Fortnite.com/UI }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/UI }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Cinématique de décollage : quand on appuie sur le bouton, les 120 images du dossier
# Content/Cinematique/UN défilent en plein écran (24 images/s, 5 s), puis le joueur est
# téléporté dans la cabine en vol.
#
# Dans UEFN :
#   1. Crée le dossier Content/Cinematique/UN et importe dedans les 120 images Decollage_001 ... 120.
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
        Cinematique.UN.Decollage_001,
        Cinematique.UN.Decollage_002,
        Cinematique.UN.Decollage_003,
        Cinematique.UN.Decollage_004,
        Cinematique.UN.Decollage_005,
        Cinematique.UN.Decollage_006,
        Cinematique.UN.Decollage_007,
        Cinematique.UN.Decollage_008,
        Cinematique.UN.Decollage_009,
        Cinematique.UN.Decollage_010,
        Cinematique.UN.Decollage_011,
        Cinematique.UN.Decollage_012,
        Cinematique.UN.Decollage_013,
        Cinematique.UN.Decollage_014,
        Cinematique.UN.Decollage_015,
        Cinematique.UN.Decollage_016,
        Cinematique.UN.Decollage_017,
        Cinematique.UN.Decollage_018,
        Cinematique.UN.Decollage_019,
        Cinematique.UN.Decollage_020,
        Cinematique.UN.Decollage_021,
        Cinematique.UN.Decollage_022,
        Cinematique.UN.Decollage_023,
        Cinematique.UN.Decollage_024,
        Cinematique.UN.Decollage_025,
        Cinematique.UN.Decollage_026,
        Cinematique.UN.Decollage_027,
        Cinematique.UN.Decollage_028,
        Cinematique.UN.Decollage_029,
        Cinematique.UN.Decollage_030,
        Cinematique.UN.Decollage_031,
        Cinematique.UN.Decollage_032,
        Cinematique.UN.Decollage_033,
        Cinematique.UN.Decollage_034,
        Cinematique.UN.Decollage_035,
        Cinematique.UN.Decollage_036,
        Cinematique.UN.Decollage_037,
        Cinematique.UN.Decollage_038,
        Cinematique.UN.Decollage_039,
        Cinematique.UN.Decollage_040,
        Cinematique.UN.Decollage_041,
        Cinematique.UN.Decollage_042,
        Cinematique.UN.Decollage_043,
        Cinematique.UN.Decollage_044,
        Cinematique.UN.Decollage_045,
        Cinematique.UN.Decollage_046,
        Cinematique.UN.Decollage_047,
        Cinematique.UN.Decollage_048,
        Cinematique.UN.Decollage_049,
        Cinematique.UN.Decollage_050,
        Cinematique.UN.Decollage_051,
        Cinematique.UN.Decollage_052,
        Cinematique.UN.Decollage_053,
        Cinematique.UN.Decollage_054,
        Cinematique.UN.Decollage_055,
        Cinematique.UN.Decollage_056,
        Cinematique.UN.Decollage_057,
        Cinematique.UN.Decollage_058,
        Cinematique.UN.Decollage_059,
        Cinematique.UN.Decollage_060,
        Cinematique.UN.Decollage_061,
        Cinematique.UN.Decollage_062,
        Cinematique.UN.Decollage_063,
        Cinematique.UN.Decollage_064,
        Cinematique.UN.Decollage_065,
        Cinematique.UN.Decollage_066,
        Cinematique.UN.Decollage_067,
        Cinematique.UN.Decollage_068,
        Cinematique.UN.Decollage_069,
        Cinematique.UN.Decollage_070,
        Cinematique.UN.Decollage_071,
        Cinematique.UN.Decollage_072,
        Cinematique.UN.Decollage_073,
        Cinematique.UN.Decollage_074,
        Cinematique.UN.Decollage_075,
        Cinematique.UN.Decollage_076,
        Cinematique.UN.Decollage_077,
        Cinematique.UN.Decollage_078,
        Cinematique.UN.Decollage_079,
        Cinematique.UN.Decollage_080,
        Cinematique.UN.Decollage_081,
        Cinematique.UN.Decollage_082,
        Cinematique.UN.Decollage_083,
        Cinematique.UN.Decollage_084,
        Cinematique.UN.Decollage_085,
        Cinematique.UN.Decollage_086,
        Cinematique.UN.Decollage_087,
        Cinematique.UN.Decollage_088,
        Cinematique.UN.Decollage_089,
        Cinematique.UN.Decollage_090,
        Cinematique.UN.Decollage_091,
        Cinematique.UN.Decollage_092,
        Cinematique.UN.Decollage_093,
        Cinematique.UN.Decollage_094,
        Cinematique.UN.Decollage_095,
        Cinematique.UN.Decollage_096,
        Cinematique.UN.Decollage_097,
        Cinematique.UN.Decollage_098,
        Cinematique.UN.Decollage_099,
        Cinematique.UN.Decollage_100,
        Cinematique.UN.Decollage_101,
        Cinematique.UN.Decollage_102,
        Cinematique.UN.Decollage_103,
        Cinematique.UN.Decollage_104,
        Cinematique.UN.Decollage_105,
        Cinematique.UN.Decollage_106,
        Cinematique.UN.Decollage_107,
        Cinematique.UN.Decollage_108,
        Cinematique.UN.Decollage_109,
        Cinematique.UN.Decollage_110,
        Cinematique.UN.Decollage_111,
        Cinematique.UN.Decollage_112,
        Cinematique.UN.Decollage_113,
        Cinematique.UN.Decollage_114,
        Cinematique.UN.Decollage_115,
        Cinematique.UN.Decollage_116,
        Cinematique.UN.Decollage_117,
        Cinematique.UN.Decollage_118,
        Cinematique.UN.Decollage_119,
        Cinematique.UN.Decollage_120

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
