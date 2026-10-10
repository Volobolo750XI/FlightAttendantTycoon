using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - porte passagers (avant / arrière), comme une vraie porte d'A320.
# Pose ce device une fois par porte passagers (les portes intérieures gardent porte_avion).
#
# On interagit avec le bouton (touche E) :
#   1. la poignée s'abaisse puis remonte ;
#   2. la porte se soulève un peu et sort vers l'extérieur de l'avion ;
#   3. elle glisse le long du fuselage, vers la gauche (vu de l'intérieur), en restant
#      bien parallèle à l'avion. Elle ne tourne pas.
# On réinteragit -> elle revient de la gauche et se referme.
# Pendant un vol, le PC la verrouille : la poignée bouge mais elle ne s'ouvre pas.
#
# Dans l'éditeur :
#   Battant : le prop de la porte. Son point de pivot doit être sur le bord
#             de la porte (la charnière, comme dans le modèle d'avion).
#   Poignee : le prop de la poignée (pivot au centre de la poignée).
#   Bouton  : un Appareil Bouton posé contre la porte, À L'INTÉRIEUR de l'avion
#             (c'est lui qui indique où est l'intérieur), texte "Open".

porte_passager := class(creative_device):
    @editable Battant:creative_prop = creative_prop{}
    @editable Poignee:creative_prop = creative_prop{}
    @editable Bouton:button_device = button_device{}

    # De combien la porte sort de l'avion avant de glisser (cm).
    @editable Sortie:float = 60.0
    # De combien elle glisse le long du fuselage (cm), à peu près la largeur de la porte.
    @editable Glissement:float = 110.0
    # De combien elle se soulève au début (cm).
    @editable Levage:float = 5.0
    # Coche si elle glisse vers la droite au lieu de la gauche.
    @editable InverserGlissement:logic = false
    # Coche si elle rentre dans l'avion au lieu de sortir.
    @editable InverserSortie:logic = false
    # Durée de la sortie et du glissement (secondes).
    @editable DureeSortie:float = 0.8
    @editable DureeGlissement:float = 1.4
    # De combien la poignée s'abaisse (degrés). Si elle monte au lieu de descendre, mets -35.
    @editable AnglePoignee:float = 35.0

    var Ouverte:logic = false
    var Verrouillee:logic = false
    # pendant l'embarquement, la porte est forcée ouverte : son propre bouton ne peut pas la fermer
    var BloqueeOuverte:logic = false
    var EnMouvement:logic = false
    var Pret:logic = false
    var Battant0:transform = transform{}
    var Poignee0:transform = transform{}
    var Etape1:vector3 = vector3{}
    var Etape2:vector3 = vector3{}
    var Long:vector3 = vector3{X := 1.0, Y := 0.0, Z := 0.0}

    Verrouiller(Etat:logic):void =
        set Verrouillee = Etat

    OnBegin<override>()<suspends>:void =
        set Battant0 = Battant.GetTransform()
        set Poignee0 = Poignee.GetTransform()
        Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
        # axe du fuselage : de la charnière vers la poignée (à plat)
        set Long = Normaliser(vector3{X := Poignee0.Translation.X - Battant0.Translation.X, Y := Poignee0.Translation.Y - Battant0.Translation.Y, Z := 0.0})
        if (Distance(Long, vector3{}) < 0.5):
            set Long = Normaliser(Battant0.Rotation.GetLocalForward())
        # vers l'extérieur : perpendiculaire au fuselage, du côté opposé au bouton
        var Dehors:vector3 = CrossProduct(Long, Haut)
        if (DotProduct(Bouton.GetTransform().Translation - Battant0.Translation, Dehors) > 0.0):
            set Dehors = Dehors * -1.0
        if (InverserSortie?):
            set Dehors = Dehors * -1.0
        # gauche vue de l'intérieur, en regardant vers l'extérieur
        var Gauche:vector3 = CrossProduct(Dehors, Haut)
        if (InverserGlissement?):
            set Gauche = Gauche * -1.0
        set Etape1 = Dehors * Sortie + Haut * Levage
        set Etape2 = Etape1 + Gauche * Glissement
        set Pret = true
        loop:
            Bouton.InteractedWithEvent.Await()
            if (Ouverte?):
                if (not BloqueeOuverte?) { Fermer() }
            else if (Verrouillee?):
                TournerPoignee(Poignee0, Long)
            else:
                Ouvrir()

    # Ouvre la porte (sort puis glisse à gauche). Ne fait rien si elle est déjà ouverte.
    Ouvrir()<suspends>:void =
        if (Pret?, not Ouverte?, not EnMouvement?):
            set EnMouvement = true
            TournerPoignee(Poignee0, Long)
            set Ouverte = true
            sync:
                Battant.MoveTo(Battant0.Translation + Etape1, Battant0.Rotation, DureeSortie)
                Poignee.MoveTo(Poignee0.Translation + Etape1, Poignee0.Rotation, DureeSortie)
            sync:
                Battant.MoveTo(Battant0.Translation + Etape2, Battant0.Rotation, DureeGlissement)
                Poignee.MoveTo(Poignee0.Translation + Etape2, Poignee0.Rotation, DureeGlissement)
            set EnMouvement = false

    # Referme la porte (revient de la gauche puis rentre). Ne fait rien si elle est déjà fermée.
    Fermer()<suspends>:void =
        if (Pret?, Ouverte?, not EnMouvement?):
            set EnMouvement = true
            sync:
                Battant.MoveTo(Battant0.Translation + Etape1, Battant0.Rotation, DureeGlissement)
                Poignee.MoveTo(Poignee0.Translation + Etape1, Poignee0.Rotation, DureeGlissement)
            sync:
                Battant.MoveTo(Battant0.Translation, Battant0.Rotation, DureeSortie)
                Poignee.MoveTo(Poignee0.Translation, Poignee0.Rotation, DureeSortie)
            set Ouverte = false
            set EnMouvement = false

    # Utilisé par l'embarquement : ouverte et bloquée ouverte / débloquée puis fermée.
    OuvrirPourEmbarquement()<suspends>:void =
        set BloqueeOuverte = true
        Ouvrir()

    FermerApresEmbarquement()<suspends>:void =
        set BloqueeOuverte = false
        # si elle est en train de bouger, on attend la fin du mouvement
        loop:
            if (not EnMouvement?) { break }
            Sleep(0.1)
        Fermer()

    Normaliser(V:vector3):vector3 =
        L := Distance(V, vector3{})
        if (L > 0.001) then V / L else vector3{}

    # La poignée tourne sur son propre pivot, autour de l'axe perpendiculaire
    # à la porte : elle s'abaisse puis remonte.
    TournerPoignee(P0:transform, L0:vector3)<suspends>:void =
        Axe := CrossProduct(L0, vector3{X := 0.0, Y := 0.0, Z := 1.0})
        if (Distance(Axe, vector3{}) > 0.001):
            Bas := MakeRotation(Normaliser(Axe), DegreesToRadians(AnglePoignee))
            Poignee.MoveTo(P0.Translation, P0.Rotation.RotateBy(Bas), 0.15)
            Sleep(0.1)
            Poignee.MoveTo(P0.Translation, P0.Rotation, 0.15)
