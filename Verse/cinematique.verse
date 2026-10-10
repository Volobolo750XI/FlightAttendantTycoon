using { /Fortnite.com/Devices }
using { /Verse.org/Assets }
using { /Fortnite.com/UI }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/UI }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Cinematique de decollage : quand on appuie sur le bouton, les 120 images du dossier
# Content/Cinematique/UN defilent en plein ecran (24 images/s, 5 s), puis le joueur est
# teleporte dans la cabine en vol.
#
# Dans UEFN :
#   0. CE FICHIER VERSE DOIT ETRE DANS LE DOSSIER Content/Cinematique (a cote du dossier UN),
#      sinon Verse n'a pas le droit de lire le sous-dossier UN.
#   1. Cree le dossier Content/Cinematique/UN et importe dedans les 120 images Decollage_001 ... 120.
#   2. Compile, place ce device, et choisis :
#      Bouton      : le bouton qui lance la cinematique (pour tester).
#      Son         : (facultatif) un Appareil Lecteur audio avec le son du decollage.
#      ArriveeEnVol: (facultatif) un Appareil Teleporteur pose dans la cabine en vol.
cinematique_decollage := class(creative_device):
    @editable Bouton:button_device = button_device{}
    @editable Son:?audio_player_device = false
    @editable ArriveeEnVol:?teleporter_device = false
    # (facultatif) Appareil Controleur de HUD regle pour TOUT cacher (vie, carte, inventaire...) :
    # il est active pendant la cinematique puis desactive.
    @editable CacherHUD:?hud_controller_device = false
    # Duree totale de la cinematique en secondes (5 = vitesse normale de la video).
    @editable Duree:float = 5.0

    Images:[]texture = array:
        UN.Decollage_001,
        UN.Decollage_002,
        UN.Decollage_003,
        UN.Decollage_004,
        UN.Decollage_005,
        UN.Decollage_006,
        UN.Decollage_007,
        UN.Decollage_008,
        UN.Decollage_009,
        UN.Decollage_010,
        UN.Decollage_011,
        UN.Decollage_012,
        UN.Decollage_013,
        UN.Decollage_014,
        UN.Decollage_015,
        UN.Decollage_016,
        UN.Decollage_017,
        UN.Decollage_018,
        UN.Decollage_019,
        UN.Decollage_020,
        UN.Decollage_021,
        UN.Decollage_022,
        UN.Decollage_023,
        UN.Decollage_024,
        UN.Decollage_025,
        UN.Decollage_026,
        UN.Decollage_027,
        UN.Decollage_028,
        UN.Decollage_029,
        UN.Decollage_030,
        UN.Decollage_031,
        UN.Decollage_032,
        UN.Decollage_033,
        UN.Decollage_034,
        UN.Decollage_035,
        UN.Decollage_036,
        UN.Decollage_037,
        UN.Decollage_038,
        UN.Decollage_039,
        UN.Decollage_040,
        UN.Decollage_041,
        UN.Decollage_042,
        UN.Decollage_043,
        UN.Decollage_044,
        UN.Decollage_045,
        UN.Decollage_046,
        UN.Decollage_047,
        UN.Decollage_048,
        UN.Decollage_049,
        UN.Decollage_050,
        UN.Decollage_051,
        UN.Decollage_052,
        UN.Decollage_053,
        UN.Decollage_054,
        UN.Decollage_055,
        UN.Decollage_056,
        UN.Decollage_057,
        UN.Decollage_058,
        UN.Decollage_059,
        UN.Decollage_060,
        UN.Decollage_061,
        UN.Decollage_062,
        UN.Decollage_063,
        UN.Decollage_064,
        UN.Decollage_065,
        UN.Decollage_066,
        UN.Decollage_067,
        UN.Decollage_068,
        UN.Decollage_069,
        UN.Decollage_070,
        UN.Decollage_071,
        UN.Decollage_072,
        UN.Decollage_073,
        UN.Decollage_074,
        UN.Decollage_075,
        UN.Decollage_076,
        UN.Decollage_077,
        UN.Decollage_078,
        UN.Decollage_079,
        UN.Decollage_080,
        UN.Decollage_081,
        UN.Decollage_082,
        UN.Decollage_083,
        UN.Decollage_084,
        UN.Decollage_085,
        UN.Decollage_086,
        UN.Decollage_087,
        UN.Decollage_088,
        UN.Decollage_089,
        UN.Decollage_090,
        UN.Decollage_091,
        UN.Decollage_092,
        UN.Decollage_093,
        UN.Decollage_094,
        UN.Decollage_095,
        UN.Decollage_096,
        UN.Decollage_097,
        UN.Decollage_098,
        UN.Decollage_099,
        UN.Decollage_100,
        UN.Decollage_101,
        UN.Decollage_102,
        UN.Decollage_103,
        UN.Decollage_104,
        UN.Decollage_105,
        UN.Decollage_106,
        UN.Decollage_107,
        UN.Decollage_108,
        UN.Decollage_109,
        UN.Decollage_110,
        UN.Decollage_111,
        UN.Decollage_112,
        UN.Decollage_113,
        UN.Decollage_114,
        UN.Decollage_115,
        UN.Decollage_116,
        UN.Decollage_117,
        UN.Decollage_118,
        UN.Decollage_119,
        UN.Decollage_120

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
            # le joueur ne peut plus bouger ni viser pendant la cinematique
            if (Perso := Joueur.GetFortCharacter[]):
                Perso.PutInStasis(stasis_args{AllowTurning := false, AllowFalling := false, AllowEmotes := false})
            if (H := CacherHUD?) { H.Enable() }
            UI.AddWidget(Fond, player_ui_slot{ZOrder := 100, InputMode := ui_input_mode.All})
            if (S := Son?) { S.Play() }
            # l'image affichee depend du temps ecoule (et pas d'une pause par image) :
            # la cinematique dure exactement Duree secondes, meme si le serveur est lent
            Debut := GetSimulationElapsedTime()
            var Derniere:int = -1
            loop:
                Ecoule := GetSimulationElapsedTime() - Debut
                if (Ecoule >= Duree) { break }
                if (N := Floor[Ecoule / Duree * (Images.Length * 1.0)], N <> Derniere, Image := Images[N]):
                    set Derniere = N
                    Ecran.SetImage(Image)
                Sleep(0.0)
            if (Fin := Images[Images.Length - 1]) { Ecran.SetImage(Fin) }
            # on teleporte pendant que la derniere image est encore affichee
            if (T := ArriveeEnVol?) { T.Teleport(Joueur) }
            Sleep(0.3)
            UI.RemoveWidget(Fond)
            if (H := CacherHUD?) { H.Disable() }
            if (Perso := Joueur.GetFortCharacter[]) { Perso.ReleaseFromStasis() }
        set EnCours = false
