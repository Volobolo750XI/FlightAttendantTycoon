using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - une porte qui s'ouvre (cuisine, chambre, WC, cockpit...).
# Pose ce device une fois par porte.
#
# On interagit avec le bouton (touche E) -> la poignée s'abaisse puis remonte,
# et la porte pivote sur sa charnière, toujours du côté opposé au joueur
# (elle est poussée, jamais tirée vers lui). On réinteragit -> elle se referme.
#
# Dans l'éditeur :
#   Battant    : le prop de la porte ("...Portes"). Son point de pivot doit être
#                sur la charnière (c'est le cas des portes du modèle d'avion).
#   Poignee    : le prop de la poignée ("...Inox"). Son point de pivot doit être
#                au centre de la poignée, là où elle traverse la porte.
#   Bouton     : un Appareil Bouton posé contre la porte (mets son modèle invisible,
#                et son texte d'interaction à "Ouvrir").

porte_avion := class(creative_device):
    @editable Battant:creative_prop = creative_prop{}
    @editable Poignee:creative_prop = creative_prop{}
    @editable Bouton:button_device = button_device{}

    # Angle d'ouverture en degrés.
    @editable AngleOuverture:float = 90.0
    # Si la porte s'ouvre VERS le joueur au lieu de s'éloigner, coche ceci.
    @editable InverserSens:logic = false
    # Durée de l'ouverture / fermeture (secondes).
    @editable DureeOuverture:float = 0.7
    # De combien la poignée s'abaisse (degrés). Si elle monte au lieu de descendre, mets -35.
    @editable AnglePoignee:float = 35.0
    # Refermeture automatique après X secondes (0 = jamais, il faut réinteragir).
    @editable FermetureAuto:float = 0.0

    var Ouverte:logic = false
    # Verrouillée (pendant un vol) : on ne peut plus l'ouvrir.
    var Verrouillee:logic = false

    Verrouiller(Etat:logic):void =
        set Verrouillee = Etat

    OnBegin<override>()<suspends>:void =
        FermeeBattant := Battant.GetTransform()
        FermeePoignee := Poignee.GetTransform()
        loop:
            Joueur := Bouton.InteractedWithEvent.Await()
            if (Ouverte?):
                Fermer(FermeeBattant, FermeePoignee)
            else if (Verrouillee?):
                # porte verrouillée pendant le vol : la poignée bouge mais rien ne s'ouvre
                TournerPoignee(FermeePoignee)
            else:
                Ouvrir(FermeeBattant, FermeePoignee, Joueur)
                if (FermetureAuto > 0.0):
                    race:
                        Sleep(FermetureAuto)
                        Bouton.InteractedWithEvent.Await()
                    Fermer(FermeeBattant, FermeePoignee)

    Ouvrir(Battant0:transform, Poignee0:transform, Joueur:agent)<suspends>:void =
        TournerPoignee(Poignee0)
        set Ouverte = true
        Charniere := MakeRotation(vector3{X := 0.0, Y := 0.0, Z := 1.0}, DegreesToRadians(SensOuverture(Battant0, Poignee0, Joueur)))
        # la poignée tourne autour de la charnière avec la porte
        Pivot := Battant0.Translation
        PositionPoignee := Pivot + Charniere.RotateVector(Poignee0.Translation - Pivot)
        sync:
            Battant.MoveTo(Battant0.Translation, Battant0.Rotation.RotateBy(Charniere), DureeOuverture)
            Poignee.MoveTo(PositionPoignee, Poignee0.Rotation.RotateBy(Charniere), DureeOuverture)

    # Angle signé pour que la porte s'éloigne du joueur : on regarde de quel côté
    # du plan de la porte il se trouve.
    SensOuverture(Battant0:transform, Poignee0:transform, Joueur:agent):float =
        Pivot := Battant0.Translation
        Largeur := vector3{X := Poignee0.Translation.X - Pivot.X, Y := Poignee0.Translation.Y - Pivot.Y, Z := 0.0}
        Normale := CrossProduct(Largeur, vector3{X := 0.0, Y := 0.0, Z := 1.0})
        var Cote:float = 1.0
        if (Perso := Joueur.GetFortCharacter[]):
            if (DotProduct(Perso.GetTransform().Translation - Pivot, Normale) < 0.0):
                set Cote = -1.0
        if (InverserSens?) then -Cote * AngleOuverture else Cote * AngleOuverture

    Fermer(Battant0:transform, Poignee0:transform)<suspends>:void =
        sync:
            Battant.MoveTo(Battant0.Translation, Battant0.Rotation, DureeOuverture)
            Poignee.MoveTo(Poignee0.Translation, Poignee0.Rotation, DureeOuverture)
        set Ouverte = false

    # La poignée tourne sur son propre pivot, autour de l'axe perpendiculaire
    # à la porte : elle s'abaisse puis remonte.
    TournerPoignee(Poignee0:transform)<suspends>:void =
        Centre := Poignee0.Translation
        Charniere := Battant.GetTransform().Translation
        # direction "largeur de porte" (charnière -> poignée), à plat
        Largeur := vector3{X := Centre.X - Charniere.X, Y := Centre.Y - Charniere.Y, Z := 0.0}
        Axe := CrossProduct(Largeur, vector3{X := 0.0, Y := 0.0, Z := 1.0})
        Longueur := Distance(Axe, vector3{})
        if (Longueur > 0.001):
            Bas := MakeRotation(Axe / Longueur, DegreesToRadians(AnglePoignee))
            Poignee.MoveTo(Centre, Poignee0.Rotation.RotateBy(Bas), 0.15)
            Sleep(0.1)
            Poignee.MoveTo(Centre, Poignee0.Rotation, 0.15)
