using { /Fortnite.com/Devices }
using { /Fortnite.com/UI }
using { /Verse.org/Colors }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/UI }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Decollage (remplace l'ancienne cinematique en images) :
#   fondu au noir (fluide) -> ecran noir ~4 s avec le son du decollage -> teleport en vol
#   -> retour de l'image en fondu -> son de cabine en continu.
# La musique de fond se lance des le debut de la partie et tourne tout le temps.
#
# Dans UEFN :
#   Musique      : Appareil Lecteur audio avec ta musique. Dans le fichier son (Sound Wave),
#                  coche "Looping" pour qu'elle boucle. Volume bas (0.2 - 0.3).
#   SonDecollage : Appareil Lecteur audio avec le son du decollage.
#   SonCabine    : Appareil Lecteur audio avec le bruit de l'avion en vol (Sound Wave en "Looping").
#                  Il s'arrete a l'atterrissage (Vol.Atterrir).
#   ArriveeEnVol : (facultatif) un Appareil Teleporteur dans la cabine en vol.
#   Vol          : le device vol_device.
#   CacherHUD    : (facultatif) Controleur de HUD regle pour tout cacher.

# Opacite du voile noir (Fortnite exige une valeur entre 0 et 1 connue a l'avance).
opacite_voile := type{_X:float where 0.0 <= _X, _X <= 1.0}

cinematique_decollage := class(creative_device):
    # (facultatif) bouton de test ; en jeu, c'est le bouton TAKE OFF du device passagers qui lance.
    @editable Bouton:?button_device = false
    @editable Musique:?audio_player_device = false
    @editable SonDecollage:?audio_player_device = false
    @editable SonCabine:?audio_player_device = false
    @editable ArriveeEnVol:?teleporter_device = false
    @editable Vol:?vol_device = false
    @editable CacherHUD:?hud_controller_device = false
    # Temps passe dans le noir (secondes)
    @editable DureeNoir:float = 4.0

    # 25 paliers : a 1 palier par image (30 / s) le fondu est fluide.
    Paliers:[]opacite_voile = array{0.0, 0.04, 0.08, 0.12, 0.16, 0.2, 0.24, 0.28, 0.32, 0.36, 0.4, 0.44, 0.48, 0.52, 0.56, 0.6, 0.64, 0.68, 0.72, 0.76, 0.8, 0.84, 0.88, 0.92, 0.96, 1.0}

    var EnCours:logic = false

    OnBegin<override>()<suspends>:void =
        if (M := Musique?) { M.Play() }
        if (B := Bouton?):
            loop:
                Joueur := B.InteractedWithEvent.Await()
                if (not EnCours?):
                    spawn{Jouer(Joueur)}

    Jouer(Joueur:agent)<suspends>:void =
        if (not EnCours?):
            set EnCours = true
            Decollage(Joueur)
            set EnCours = false

    # Fondu : Duree secondes, du noir transparent au noir opaque (ou l'inverse)
    Fondu(Noir:color_block, Duree:float, VersNoir:logic)<suspends>:void =
        Debut := GetSimulationElapsedTime()
        Dernier := Paliers.Length - 1
        loop:
            T := Min(1.0, (GetSimulationElapsedTime() - Debut) / Max(0.01, Duree))
            Avance := if (VersNoir?) then T else 1.0 - T
            if (N := Floor[Avance * (Dernier * 1.0) + 0.5], Op := Paliers[N]):
                Noir.SetOpacity(Op)
            if (T >= 1.0) { break }
            Sleep(0.0)

    Decollage(Joueur:agent)<suspends>:void =
        if (P := player[Joueur], UI := GetPlayerUI[P]):
            if (Perso := Joueur.GetFortCharacter[]):
                Perso.PutInStasis(stasis_args{AllowTurning := false, AllowFalling := false, AllowEmotes := false})
            if (H := CacherHUD?) { H.Enable() }
            Noir := color_block{DefaultColor := NamedColors.Black, DefaultOpacity := 0.0}
            Voile := canvas:
                Slots := array:
                    canvas_slot:
                        Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.0}, Maximum := vector2{X := 1.0, Y := 1.0}}
                        Offsets := margin{Left := 0.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
                        SizeToContent := false
                        Widget := Noir
            UI.AddWidget(Voile, player_ui_slot{ZOrder := 101, InputMode := ui_input_mode.All})
            # 1. fondu au noir
            Fondu(Noir, 1.0, true)
            # 2. noir : son du decollage, on passe en vol pendant qu'on ne voit rien
            if (S := SonDecollage?) { S.Play() }
            Sleep(DureeNoir / 2.0)
            if (T := ArriveeEnVol?) { T.Teleport(Joueur) }
            if (V := Vol?) { V.Decoller() }
            Sleep(DureeNoir / 2.0)
            # 3. bruit de la cabine en continu, puis l'image revient
            if (C := SonCabine?) { C.Play() }
            if (Perso := Joueur.GetFortCharacter[]) { Perso.ReleaseFromStasis() }
            if (H := CacherHUD?) { H.Disable() }
            Fondu(Noir, 1.2, false)
            UI.RemoveWidget(Voile)

    # Appele a l'atterrissage pour couper le bruit de cabine.
    Atterrissage():void =
        if (C := SonCabine?) { C.Stop() }
