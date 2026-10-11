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
    # Vitesse max du chariot (cm/s). Un joueur qui marche fait environ 450.
    # Si on va plus vite, le chariot ne suit pas : il faut ralentir pour le garder devant soi.
    @editable VitesseMax:float = 200.0
    # Si on s'eloigne trop du chariot (cm), on le lache sur place.
    @editable DistanceLacher:float = 350.0

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
        set Porteur = false
        set Numero += 1
        PlacerBouton(Chariot.GetTransform())

    # Le bouton suit le chariot.
    PlacerBouton(C:transform):void =
        Position := C.Translation + C.Rotation.RotateVector(BoutonRelatif)
        if (Bouton.TeleportTo[Position, C.Rotation.RotateBy(BoutonRotation)]) {}

    Lacet(Perso:fort_character)<transacts>:float =
        if (Angles := Perso.GetTransform().Rotation.GetYawPitchRollDegrees(), Y := Angles[0]) then Y else 0.0

    # Ou le joueur voudrait le chariot : devant lui, a la hauteur ou il est deja.
    Cible(Position:vector3, Angle:float)<transacts>:transform =
        Avant := MakeRotationFromYawPitchRollDegrees(Angle, 0.0, 0.0).GetLocalForward()
        transform:
            Translation := vector3:
                X := Position.X + Avant.X * Ecart
                Y := Position.Y + Avant.Y * Ecart
                Z := Chariot.GetTransform().Translation.Z
            Rotation := MakeRotationFromYawPitchRollDegrees(Angle + RotationModele, 0.0, 0.0)
            Scale := Chariot.GetTransform().Scale

    Distance2D(A:vector3, B:vector3):float =
        Sqrt((A.X - B.X) * (A.X - B.X) + (A.Y - B.Y) * (A.Y - B.Y))

    Suivre(Joueur:agent, MonNumero:int)<suspends>:void =
        if (Perso := Joueur.GetFortCharacter[]):
            if (Chariot.TeleportTo[Cible(Perso.GetTransform().Translation, Lacet(Perso))]) {}
        loop:
            if (MonNumero <> Numero) { break }
            if (Perso := Joueur.GetFortCharacter[], Perso.IsActive[]):
                PosJoueur := Perso.GetTransform().Translation
                Actuel := Chariot.GetTransform()
                if (Distance2D(PosJoueur, Actuel.Translation) > Ecart + DistanceLacher):
                    # trop loin : on a lache le chariot
                    Lacher()
                    break
                Voulu := Cible(PosJoueur, Lacet(Perso))
                # le chariot avance vers la place voulue, mais jamais plus vite que VitesseMax
                Ecartement := Voulu.Translation - Actuel.Translation
                Longueur := Distance2D(Voulu.Translation, Actuel.Translation)
                PasMax := VitesseMax * Douceur
                Arrivee := if (Longueur > PasMax) then Actuel.Translation + Ecartement * (PasMax / Longueur) else Voulu.Translation
                C := transform{Translation := Arrivee, Rotation := Voulu.Rotation, Scale := Voulu.Scale}
                PlacerBouton(C)
                Chariot.MoveTo(C, Douceur)
                Sleep(0.0)
            else:
                # joueur mort ou parti : on lache le chariot sur place
                if (MonNumero = Numero) { Lacher() }
                break
