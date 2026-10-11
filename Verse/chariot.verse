using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - le chariot de service.
#
# Le bouton est colle au chariot et le suit partout.
#   E sur le chariot -> on le prend : il se place devant nous et nous suit (poignee vers nous).
#   E encore        -> on le lache la ou il est.
# Si le joueur meurt ou quitte la partie, le chariot est lache sur place.
#
# Dans l'editeur :
#   Chariot     : le prop du chariot. Dans ses reglages : decoche "Peut etre endommage"
#                 et desactive les collisions avec les joueurs.
#   Bouton      : un Appareil Bouton pose SUR le chariot (la ou tu veux voir "Interagir").
#                 Il garde cette place par rapport au chariot quand il bouge.
#   AvionTycoon : (facultatif) seul le proprio de l'avion peut prendre le chariot.

chariot_device := class(creative_device):
    @editable Chariot:creative_prop = creative_prop{}
    @editable Bouton:button_device = button_device{}
    @editable AvionTycoon:?avion_tycoon = false
    # Distance entre le joueur et le centre du chariot (cm).
    @editable Ecart:float = 100.0
    # Pour que la poignee soit vers toi. Si ce n'est pas bon, essaie -90, 0 ou 180.
    @editable RotationModele:float = 90.0
    # Temps de chaque petit mouvement (s).
    @editable Douceur:float = 0.1
    # Ralentit le joueur quand il pousse le chariot, avec 2 classes (Concepteur de classe) :
    #   ClasseLente   : Selecteur de classe et d'equipe qui donne la classe lente
    #                   (Multiplicateur de deplacement bas).
    #   ClasseNormale : Selecteur de classe et d'equipe qui redonne la classe normale.
    @editable ClasseLente:?class_and_team_selector_device = false
    @editable ClasseNormale:?class_and_team_selector_device = false

    # Le bouton par rapport au chariot (mesure au debut, dans le repere du chariot).
    var BoutonRelatif:vector3 = vector3{}
    var BoutonRotation:rotation = IdentityRotation()
    var Porteur:?agent = false
    # Change a chaque prise / lacher : la boucle de suivi d'avant s'arrete toute seule.
    var Numero:int = 0

    OnBegin<override>()<suspends>:void =
        C := Chariot.GetTransform()
        B := Bouton.GetTransform()
        set BoutonRelatif = C.Rotation.UnrotateVector(B.Translation - C.Translation)
        set BoutonRotation = C.Rotation.Invert().RotateBy(B.Rotation)
        loop:
            Joueur := Bouton.InteractedWithEvent.Await()
            if (Actuel := Porteur?):
                # seul celui qui le tient peut le lacher
                if (Actuel = Joueur):
                    Lacher()
            else if (PeutPrendre[Joueur]):
                Prendre(Joueur)

    PeutPrendre(Joueur:agent)<transacts><decides>:void =
        if (A := AvionTycoon?):
            Proprio := A.Proprio?
            Proprio = Joueur

    Prendre(Joueur:agent):void =
        set Porteur = option{Joueur}
        set Numero += 1
        spawn{Suivre(Joueur, Numero)}

    Lacher():void =
        if (J := Porteur?, S := ClasseNormale?) { S.ChangeClass(J) }
        set Porteur = false
        set Numero += 1
        PlacerBouton(Chariot.GetTransform())

    # Le bouton suit le chariot.
    PlacerBouton(C:transform):void =
        Position := C.Translation + C.Rotation.RotateVector(BoutonRelatif)
        if (Bouton.TeleportTo[Position, C.Rotation.RotateBy(BoutonRotation)]) {}

    Lacet(Perso:fort_character)<transacts>:float =
        if (Angles := Perso.GetTransform().Rotation.GetYawPitchRollDegrees(), Y := Angles[0]) then Y else 0.0

    # Ou doit etre le chariot : devant le joueur, a la hauteur ou il est deja.
    # Avance = petite avance pour compenser le temps du mouvement (sinon il traine derriere).
    Cible(Position:vector3, Angle:float, Avance:vector3)<transacts>:transform =
        Avant := MakeRotationFromYawPitchRollDegrees(Angle, 0.0, 0.0).GetLocalForward()
        transform:
            Translation := vector3:
                X := Position.X + Avant.X * Ecart + Avance.X
                Y := Position.Y + Avant.Y * Ecart + Avance.Y
                Z := Chariot.GetTransform().Translation.Z
            Rotation := MakeRotationFromYawPitchRollDegrees(Angle + RotationModele, 0.0, 0.0)
            Scale := Chariot.GetTransform().Scale

    Suivre(Joueur:agent, MonNumero:int)<suspends>:void =
        var Precedente:vector3 = vector3{}
        var Temps:float = GetSimulationElapsedTime()
        # vitesse lissee : evite les a-coups dus aux petites variations de position
        var Vitesse:vector3 = vector3{}
        if (S := ClasseLente?) { S.ChangeClass(Joueur) }
        if (Perso := Joueur.GetFortCharacter[]):
            set Precedente = Perso.GetTransform().Translation
            if (Chariot.TeleportTo[Cible(Precedente, Lacet(Perso), vector3{})]) {}
        loop:
            if (MonNumero <> Numero) { break }
            if (Perso := Joueur.GetFortCharacter[], Perso.IsActive[]):
                Maintenant := GetSimulationElapsedTime()
                Position := Perso.GetTransform().Translation
                Ecoule := Maintenant - Temps
                # vitesse du joueur (a plat), pour viser la ou il sera a la fin du mouvement
                if (Ecoule > 0.001):
                    Brute := (Position - Precedente) / Ecoule
                    set Vitesse = vector3:
                        X := Vitesse.X * 0.75 + Brute.X * 0.25
                        Y := Vitesse.Y * 0.75 + Brute.Y * 0.25
                        Z := 0.0
                Avance := vector3{X := Vitesse.X * Douceur, Y := Vitesse.Y * Douceur, Z := 0.0}
                set Precedente = Position
                set Temps = Maintenant
                C := Cible(Position, Lacet(Perso), Avance)
                PlacerBouton(C)
                Chariot.MoveTo(C, Douceur)
                Sleep(0.0)
            else:
                # joueur mort ou parti : on lache le chariot sur place
                if (MonNumero = Numero) { Lacher() }
                break
