using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - le chariot de service.
#
# On appuie sur le bouton du galley -> le chariot vient devant nous et nous suit
# (il reste au sol, il tourne seulement a l'horizontale, comme si on le poussait).
# On rappuie sur le bouton -> le chariot retourne a sa place.
# Il retourne aussi tout seul a sa place si le joueur meurt ou quitte la partie.
#
# Dans l'editeur :
#   Chariot     : le prop du chariot, pose a sa place dans le galley.
#                 Dans ses reglages : decoche "Peut etre endommage" et desactive les collisions
#                 avec les joueurs, sinon il te bloque quand il avance devant toi.
#   Bouton      : un Appareil Bouton pose dans le galley (texte "Cart").
#   AvionTycoon : (facultatif) seul le proprio de l'avion peut prendre le chariot.

chariot_device := class(creative_device):
    @editable Chariot:creative_prop = creative_prop{}
    @editable Bouton:button_device = button_device{}
    @editable AvionTycoon:?avion_tycoon = false
    # Distance entre le joueur et le chariot (cm).
    @editable Distance:float = 130.0
    # Si le chariot n'est pas tourne dans le bon sens, essaie 90, -90 ou 180.
    @editable RotationModele:float = 0.0
    # Temps de chaque petit mouvement (plus petit = plus colle, plus grand = plus doux).
    @editable Douceur:float = 0.1

    var Place:transform = transform{}
    var Porteur:?agent = false
    # Change a chaque prise / depot : la boucle de suivi d'avant s'arrete toute seule.
    var Numero:int = 0

    OnBegin<override>()<suspends>:void =
        set Place = Chariot.GetTransform()
        loop:
            Joueur := Bouton.InteractedWithEvent.Await()
            if (Actuel := Porteur?):
                # seul celui qui le tient peut le reposer
                if (Actuel = Joueur):
                    Reposer()
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

    Reposer():void =
        set Porteur = false
        set Numero += 1
        if (Chariot.TeleportTo[Place]) {}

    # Position du chariot devant le joueur : au sol (hauteur de sa place), tourne comme le joueur.
    Cible(Perso:fort_character):transform =
        T := Perso.GetTransform()
        Lacet := if (Angles := T.Rotation.GetYawPitchRollDegrees(), Y := Angles[0]) then Y else 0.0
        Direction := MakeRotationFromYawPitchRollDegrees(Lacet, 0.0, 0.0)
        Avant := Direction.GetLocalForward()
        Position := vector3:
            X := T.Translation.X + Avant.X * Distance
            Y := T.Translation.Y + Avant.Y * Distance
            Z := Place.Translation.Z
        transform:
            Translation := Position
            Rotation := MakeRotationFromYawPitchRollDegrees(Lacet + RotationModele, 0.0, 0.0)
            Scale := Place.Scale

    Suivre(Joueur:agent, MonNumero:int)<suspends>:void =
        # premiere fois : le chariot apparait directement devant le joueur
        if (Perso := Joueur.GetFortCharacter[], Chariot.TeleportTo[Cible(Perso)]) {}
        loop:
            if (MonNumero <> Numero) { break }
            if (Perso := Joueur.GetFortCharacter[], Perso.IsActive[]):
                Chariot.MoveTo(Cible(Perso), Douceur)
            else:
                # joueur mort ou parti : le chariot rentre a sa place
                if (MonNumero = Numero) { Reposer() }
                break
            Sleep(0.0)
