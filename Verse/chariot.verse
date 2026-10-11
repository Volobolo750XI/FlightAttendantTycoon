using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - le chariot de service, pousse comme un vrai chariot.
#
# Le chariot roule SUR UN RAIL : il reste au milieu de l'allee et avance seulement
# dans le sens de l'allee, a vitesse lente et reguliere (pas d'a-coups).
# Il a des collisions : tu ne peux pas le traverser ni le depasser dans l'allee,
# donc quand tu pousses, TU avances a la vitesse du chariot. C'est ca qui te ralentit.
#
#   E sur le chariot -> on le prend : il part dans le sens ou on regarde (le long de l'allee).
#   On avance -> il avance devant nous. On s'arrete -> il s'arrete. On recule -> il revient.
#   E encore -> on le lache. Pour changer de sens : lache-le, passe de l'autre cote, reprends-le.
# Si le joueur meurt, part, ou s'eloigne trop : le chariot est lache sur place.
#
# Dans l'editeur :
#   Chariot     : le prop du chariot, pose au milieu de l'allee.
#                 Decoche "Peut etre endommage". LAISSE LES COLLISIONS ACTIVEES.
#   Bouton      : un Appareil Bouton pose SUR le chariot (il suit le chariot).
#   AvionTycoon : (facultatif) seul le proprio de l'avion peut prendre le chariot.

chariot_device := class(creative_device):
    @editable Chariot:creative_prop = creative_prop{}
    @editable Bouton:button_device = button_device{}
    @editable AvionTycoon:?avion_tycoon = false
    # Distance entre le joueur et le centre du chariot (cm).
    @editable Ecart:float = 100.0
    # Vitesse du chariot quand on pousse (cm/s). Un joueur qui marche fait environ 450.
    @editable VitesseChariot:float = 150.0
    # Pour que la poignee soit vers toi. Si ce n'est pas bon, essaie -90, 0 ou 180.
    @editable RotationModele:float = 90.0
    # Si le joueur est plus loin que ca du chariot (cm), il le lache.
    @editable DistanceLacher:float = 300.0

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
        spawn{Pousser(Joueur, Numero)}

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

    Absolu(V:float)<transacts>:float = if (V < 0.0) then -V else V

    Pousser(Joueur:agent, MonNumero:int)<suspends>:void =
        if (Perso := Joueur.GetFortCharacter[]):
            Depart := Chariot.GetTransform()
            # sens de l'allee = l'axe du monde (X ou Y) le plus proche du regard du joueur,
            # et le chariot part du cote ou le joueur regarde
            Regard := MakeRotationFromYawPitchRollDegrees(Lacet(Perso), 0.0, 0.0).GetLocalForward()
            SurX := if (Absolu(Regard.X) >= Absolu(Regard.Y)) then true else false
            Signe := if (SurX?) then (if (Regard.X >= 0.0) then 1.0 else -1.0) else (if (Regard.Y >= 0.0) then 1.0 else -1.0)
            Angle := if (SurX?) then (if (Signe > 0.0) then 0.0 else 180.0) else (if (Signe > 0.0) then 90.0 else -90.0)
            Orientation := MakeRotationFromYawPitchRollDegrees(Angle + RotationModele, 0.0, 0.0)
            # le chariot garde toujours sa place sur le cote (il reste au milieu de l'allee)
            Lateral := if (SurX?) then Depart.Translation.Y else Depart.Translation.X
            Pas := 0.1
            loop:
                if (MonNumero <> Numero) { break }
                if (P := Joueur.GetFortCharacter[], P.IsActive[]):
                    PosJoueur := P.GetTransform().Translation
                    Actuel := Chariot.GetTransform().Translation
                    # positions le long de l'allee (dans le sens de la poussee)
                    Joueur1D := if (SurX?) then PosJoueur.X * Signe else PosJoueur.Y * Signe
                    Chariot1D := if (SurX?) then Actuel.X * Signe else Actuel.Y * Signe
                    Voulu1D := Joueur1D + Ecart
                    if (Absolu(Voulu1D - Chariot1D) > DistanceLacher):
                        Lacher()
                        break
                    # on avance vers la place voulue, jamais plus vite que VitesseChariot
                    PasMax := VitesseChariot * Pas
                    Delta := Voulu1D - Chariot1D
                    Bouge := if (Delta > PasMax) then PasMax else if (Delta < -PasMax) then -PasMax else Delta
                    Nouveau := (Chariot1D + Bouge) * Signe
                    Position := if (SurX?):
                        vector3{X := Nouveau, Y := Lateral, Z := Depart.Translation.Z}
                    else:
                        vector3{X := Lateral, Y := Nouveau, Z := Depart.Translation.Z}
                    C := transform{Translation := Position, Rotation := Orientation, Scale := Depart.Scale}
                    PlacerBouton(C)
                    Chariot.MoveTo(C, Pas)
                    Sleep(0.0)
                else:
                    # joueur mort ou parti : on lache le chariot sur place
                    if (MonNumero = Numero) { Lacher() }
                    break
