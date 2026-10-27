using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - MUSIQUE ON / OFF.
# Le joueur interagit avec le bouton : la musique se coupe POUR LUI SEUL. Il re-clique : elle revient.
# Les autres joueurs ne sont pas touches.
# Le panneau (ton prop) flotte doucement (il monte puis revient, il ne descend JAMAIS sous sa place)
# et se tourne vers le joueur le plus proche, comme le panneau CLAIM.
#
# Dans UEFN :
#   - "Lecteur audio" (Audio Player) avec ta musique : Lecture automatique NON, En boucle OUI,
#     Peut etre entendu par : Joueurs enregistres, pas de spatialisation ;
#   - un "Bouton" (Button) sur ton panneau ;
#   - pose ce device et remplis Musique, Bouton et Panneau (ton prop).
#   Si le panneau montre son dos ou son cote au joueur : change DecalageAngle (90, 180 ou -90).

musique_device := class(creative_device):
    @editable Musique : audio_player_device = audio_player_device{}
    @editable Bouton : button_device = button_device{}
    @editable Panneau : ?creative_prop = false
    @editable Flottement : float = 12.0           # hauteur max de la montee (cm)
    @editable VitesseFlottement : float = 0.4     # allers-retours par seconde
    @editable DistanceSuivi : float = 3000.0      # se tourne vers les joueurs a moins de 30 m
    @editable DecalageAngle : float = 0.0
    @editable Lissage : float = 0.12

    var Coupes : [player]logic = map{}
    var Vus : [player]logic = map{}

    OnBegin<override>()<suspends>:void =
        Bouton.InteractedWithEvent.Subscribe(Basculer)
        spawn{ AnimerPanneau() }
        # chaque joueur qui arrive entend la musique
        loop:
            for (P : GetPlayspace().GetPlayers(), not Vus[P]):
                if (set Vus[P] = true) {}
                Musique.Register(P)
                Musique.Play(P)
            Sleep(1.0)

    Basculer(Agent:agent):void =
        if (P := player[Agent]):
            if (Coupes[P]?):
                if (set Coupes[P] = false) {}
                Musique.Register(P)
                Musique.Play(P)
            else:
                if (set Coupes[P] = true) {}
                Musique.Stop(P)
                Musique.Unregister(P)

    # ---------- le panneau : flotte + se tourne vers le joueur le plus proche ----------
    AnimerPanneau()<suspends>:void =
        if (Pan := Panneau?):
            Depart := Pan.GetTransform()
            Position := Depart.Translation
            var Yaw : float = if (Y := Depart.Rotation.GetYawPitchRollDegrees()[0]) then Y else 0.0
            loop:
                Sleep(0.0)
                if (Cible := JoueurLePlusProche[Position]):
                    YawCible := ArcTan(Cible.Y - Position.Y, Cible.X - Position.X) * 180.0 / PiFloat + DecalageAngle
                    set Yaw += AngleLePlusCourt(YawCible - Yaw) * Lissage
                # sinusoide entre 0 et Flottement : jamais plus bas que sa place de depart
                Onde := Sin(GetSimulationElapsedTime() * VitesseFlottement * 2.0 * PiFloat)
                Hauteur := (Onde + 1.0) * 0.5 * Flottement
                Pan.MoveTo(Position + vector3{X := 0.0, Y := 0.0, Z := Hauteur}, MakeRotationFromYawPitchRollDegrees(Yaw, 0.0, 0.0), 0.1)

    JoueurLePlusProche(Position:vector3)<decides><transacts>:vector3 =
        var PlusProche : float = DistanceSuivi
        var Cible : ?vector3 = false
        for (Joueur : GetPlayspace().GetPlayers(), Perso := Joueur.GetFortCharacter[]):
            PosJoueur := Perso.GetTransform().Translation
            Dist := Distance(PosJoueur, Position)
            if (Dist < PlusProche):
                set PlusProche = Dist
                set Cible = option{PosJoueur}
        Cible?

    AngleLePlusCourt(Angle:float):float =
        var A : float = Angle
        loop:
            if (A > 180.0):
                set A -= 360.0
            else if (A < -180.0):
                set A += 360.0
            else:
                break
        A
