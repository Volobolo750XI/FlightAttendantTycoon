using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - la passerelle d'embarquement.
# Pose ce device une fois et remplis ses props dans l'éditeur.
#
# 1. PLAQUE  : on marche dessus -> on est téléporté dans l'avion.
# 2. TEXTE   : le texte au-dessus de la plaque tourne en douceur vers le joueur
#              le plus proche, et flotte doucement de haut en bas.
# 3. ARRIVEE : un petit prop repère posé dans l'avion (caché en jeu).
#              Sa position = où on arrive, sa rotation = où on regarde en arrivant.

passerelle_embarquement := class(creative_device):
    # Le prop de la plaque où on marche.
    @editable Plaque:creative_prop = creative_prop{}
    # Le prop du texte au-dessus (ex : "EMBARQUER").
    @editable Texte:creative_prop = creative_prop{}
    # Le repère d'arrivée dans l'avion.
    @editable Arrivee:creative_prop = creative_prop{}

    # Distance (cm) autour du centre de la plaque pour compter qu'on est dessus.
    @editable RayonPlaque:float = 150.0
    # Distance (cm) jusqu'à laquelle le texte suit un joueur.
    @editable DistanceSuivi:float = 3000.0
    # Si le texte montre son dos ou son côté, mets 180 ou 90 ici.
    @editable DecalageAngle:float = 0.0
    # Douceur de la rotation : 0.05 = très doux, 0.3 = rapide, 1.0 = instantané.
    @editable Lissage:float = 0.12
    # Flottement du texte : hauteur (cm) et nombre d'allers-retours par seconde.
    # Mets Flottement à 0 pour le désactiver.
    @editable Flottement:float = 8.0
    @editable VitesseFlottement:float = 0.5

    OnBegin<override>()<suspends>:void =
        Arrivee.Hide()
        spawn{SuivreRegard()}
        BouclePlaque()

    # ---------- Plaque -> téléportation dans l'avion ----------
    BouclePlaque()<suspends>:void =
        Centre := Plaque.GetTransform().Translation
        Destination := Arrivee.GetTransform()
        loop:
            Sleep(0.1)
            for (Joueur : GetPlayspace().GetPlayers(), Perso := Joueur.GetFortCharacter[]):
                if (Distance(Perso.GetTransform().Translation, Centre) < RayonPlaque):
                    if (Perso.TeleportTo[Destination.Translation, Destination.Rotation]) {}

    # ---------- Texte qui suit le regard, sans à-coups ----------
    # À chaque frame : on calcule l'angle vers le joueur le plus proche,
    # on s'en rapproche d'un petit pourcentage (lissage) et on replace le texte.
    SuivreRegard()<suspends>:void =
        Depart := Texte.GetTransform()
        Position := Depart.Translation
        var Yaw:float = if (Y := Depart.Rotation.GetYawPitchRollDegrees()[0]) then Y else 0.0
        loop:
            Sleep(0.0)
            if (Cible := JoueurLePlusProche[Position]):
                YawCible := ArcTan(Cible.Y - Position.Y, Cible.X - Position.X) * 180.0 / PiFloat + DecalageAngle
                set Yaw += AngleLePlusCourt(YawCible - Yaw) * Lissage
            Hauteur := Sin(GetSimulationElapsedTime() * VitesseFlottement * 2.0 * PiFloat) * Flottement
            NouvellePosition := Position + vector3{X := 0.0, Y := 0.0, Z := Hauteur}
            if (Texte.TeleportTo[NouvellePosition, MakeRotationFromYawPitchRollDegrees(Yaw, 0.0, 0.0)]) {}

    # Position du joueur le plus proche (dans DistanceSuivi), échoue s'il n'y en a pas.
    JoueurLePlusProche(Position:vector3)<decides><transacts>:vector3 =
        var PlusProche:float = DistanceSuivi
        var Cible:?vector3 = false
        for (Joueur : GetPlayspace().GetPlayers(), Perso := Joueur.GetFortCharacter[]):
            PosJoueur := Perso.GetTransform().Translation
            Dist := Distance(PosJoueur, Position)
            if (Dist < PlusProche):
                set PlusProche = Dist
                set Cible = option{PosJoueur}
        Cible?

    # Ramène un écart d'angle entre -180 et 180, pour tourner par le chemin le plus court
    # (sinon le texte ferait un tour complet en passant de 179° à -179°).
    AngleLePlusCourt(Angle:float):float =
        var A:float = Angle
        loop:
            if (A > 180.0):
                set A -= 360.0
            else if (A < -180.0):
                set A += 360.0
            else:
                break
        A
