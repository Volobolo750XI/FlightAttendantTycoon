using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - l'embarquement des passagers.
#
# Quand on appuie sur le bouton d'embarquement, les passagers apparaissent un par un au bout
# de la passerelle :
#   1. ils marchent sur la passerelle jusqu'à la porte puis dans l'allée, avec leur bagage
#      (valise à la main droite ou sac sur le dos) ;
#   2. s'il y a quelqu'un devant, ils s'arrêtent et attendent (queue dans l'allée) ;
#   3. arrivés à leur rangée, ils rangent le bagage dans le coffre (ouvert dès le départ,
#      c'est au joueur de refermer les coffres) ;
#   4. puis ils s'assoient (3 secondes).
#
# Animations : chaque état est un blueprint (classe parente Creative Prop) qui contient le
# personnage et joue son animation en boucle. Quand le passager change d'état, on remplace
# le prop par le blueprint suivant, au même endroit.
#
# Dans l'éditeur :
#   BoutonEmbarquement : ton bouton (Appareil Bouton).
#   Modeles            : un élément par personnage (ses 4 blueprints + où il tient ses bagages).
#   Valises / Sacs     : les bagages (un élément par couleur).
#   Chemin             : des repères (petits props) dans l'ordre : le 1er au bout de la
#                        passerelle (les passagers y apparaissent), puis le long de la passerelle,
#                        la porte de l'avion, et le dernier DANS l'allée, au niveau de la porte.
#                        La queue marche sur tout le chemin : passerelle, porte et allée.
#   Places             : un élément par siège : repère du siège (position assis), repère dans
#                        l'allée face à la rangée, repère dans le coffre.
#   PortesCoffres      : les portes des coffres (props Coffre_D1, Coffre_G1...). Elles sont
#                        ouvertes dès le départ.
#   BoutonsCoffres     : un bouton par porte (même ordre) pour que le joueur les referme.
#   Les repères sont cachés automatiquement au lancement de la partie.

modele_passager := class<concrete>:
    @editable MarcheValise:creative_prop_asset = DefaultCreativePropAsset
    @editable MarcheSac:creative_prop_asset = DefaultCreativePropAsset
    @editable Attente:creative_prop_asset = DefaultCreativePropAsset
    @editable Assis:creative_prop_asset = DefaultCreativePropAsset
    # Où se trouve la main droite (cm) par rapport aux pieds : hauteur, côté (droite +), avant (+).
    @editable MainHauteur:float = 82.0
    @editable MainCote:float = 28.0
    @editable MainAvant:float = 0.0
    # Où se trouve le haut des bretelles du sac (cm) : hauteur, avant (+) / arrière (-).
    @editable DosHauteur:float = 145.0
    @editable DosAvant:float = -12.0

bagage := class<concrete>:
    # EnMain : porté (valise poignée sortie / sac). Rangee : posé dans le coffre.
    @editable EnMain:creative_prop_asset = DefaultCreativePropAsset
    @editable Rangee:creative_prop_asset = DefaultCreativePropAsset

place_passager := class<concrete>:
    @editable Siege:creative_prop = creative_prop{}
    @editable Allee:creative_prop = creative_prop{}
    @editable Coffre:creative_prop = creative_prop{}

# Un passager en cours d'embarquement.
passager := class:
    Modele:modele_passager
    Valise:logic
    Sac:bagage
    var Corps:?creative_prop = false
    var Bagage:?creative_prop = false
    var Etat:int = -1
    var Avancee:float = 0.0
    var DansAllee:logic = true

passagers := class(creative_device):
    @editable BoutonEmbarquement:button_device = button_device{}
    @editable Modeles:[]modele_passager = array{}
    @editable Valises:[]bagage = array{}
    @editable Sacs:[]bagage = array{}
    @editable Chemin:[]creative_prop = array{}
    @editable Places:[]place_passager = array{}
    @editable PortesCoffres:[]creative_prop = array{}
    # Un Appareil Bouton par porte (même ordre que PortesCoffres) : on interagit pour fermer / rouvrir.
    @editable BoutonsCoffres:[]button_device = array{}

    # Vitesse de marche (cm/s), écart entre deux passagers dans la queue (cm),
    # temps entre deux arrivées (s), durée pour s'asseoir (s).
    @editable VitesseMarche:float = 130.0
    @editable Espacement:float = 110.0
    @editable IntervalleArrivee:float = 2.0
    @editable DureeAssis:float = 3.0
    # Angle d'ouverture des portes de coffre (degrés). Si elles s'ouvrent vers le bas, mets -100.
    @editable AngleCoffre:float = 100.0
    # Si tes personnages ne regardent pas dans le sens de la marche, tourne-les ici (degrés).
    @editable RotationModele:float = 0.0
    @editable RotationValise:float = 0.0
    @editable RotationSac:float = 0.0
    # Taille des bagages (1.5 = 1.5 partout) et inclinaison de la valise tirée (degrés).
    # Si la valise penche vers l'avant au lieu de traîner derrière, mets -35. Roulis : à régler si elle penche sur le côté.
    @editable EchelleValise:float = 1.5
    @editable EchelleSac:float = 2.0
    @editable InclinaisonValise:float = 35.0
    @editable RoulisValise:float = 0.0

    var EnCours:[]passager = array{}
    var Occupees:[]logic = array{}
    var CoffresOuverts:[]logic = array{}
    var FermesCoffres:[]transform = array{}
    var NbEnRoute:int = 0
    var Embarquement:logic = false

    OnBegin<override>()<suspends>:void =
        for (R : Chemin) { R.Hide() }
        for (P : Places):
            P.Siege.Hide()
            P.Allee.Hide()
            P.Coffre.Hide()
        set Occupees = for (P : Places) { false }
        set CoffresOuverts = for (P : PortesCoffres) { false }
        set FermesCoffres = for (P : PortesCoffres) { P.GetTransform() }
        # les coffres sont ouverts dès le départ ; c'est au joueur de les refermer
        for (I -> Porte : PortesCoffres) { spawn{OuvrirCoffre(I)} }
        for (I -> Bouton : BoutonsCoffres) { spawn{GererBoutonCoffre(I, Bouton)} }
        loop:
            BoutonEmbarquement.InteractedWithEvent.Await()
            if (not Embarquement?):
                spawn{Embarquer()}

    # ---------- l'embarquement complet ----------
    Embarquer()<suspends>:void =
        set Embarquement = true
        for (I -> P : Places, not Occupees[I]?, Modeles.Length > 0):
            if (set Occupees[I] = true) {}
            spawn{UnPassager(P)}
            Sleep(IntervalleArrivee)
        set Embarquement = false

    UnPassager(Place:place_passager)<suspends>:void =
        Valise := if (GetRandomInt(0, 1) = 0, Valises.Length > 0) then true else if (Sacs.Length = 0) then true else false
        Liste := if (Valise?) then Valises else Sacs
        if (Modele := Modeles[GetRandomInt(0, Modeles.Length - 1)], Sac := Liste[GetRandomInt(0, Liste.Length - 1)]):
            P := passager{Modele := Modele, Valise := Valise, Sac := Sac}
            Debut := for (R : Chemin) { R.GetTransform().Translation }
            Route := Debut + array{Place.Allee.GetTransform().Translation}
            if (Depart := Route[0], Suivant := Route[1]):
                Rot := Orientation(Suivant - Depart, RotationModele)
                if (Corps := SpawnProp(Marche(P), Depart, Rot)(0)?):
                    set P.Corps = option{Corps}
                    set P.Etat = 0
                if (B := SpawnProp(Sac.EnMain, TransformBagage(P, Depart, Suivant - Depart))(0)?):
                    set P.Bagage = option{B}
            set EnCours += array{P}
            set NbEnRoute += 1
            Marcher(P, Route)
            RangerBagage(P, Place)
            Asseoir(P, Place)
            set NbEnRoute -= 1

    # ---------- marche + queue ----------
    Marcher(P:passager, Route:[]vector3)<suspends>:void =
        Total := LongueurRoute(Route)
        Pas := 0.2
        loop:
            if (P.Avancee >= Total - 1.0) { break }
            # pas plus loin que le passager de devant (moins l'espacement)
            var Limite:float = Total
            for (Autre : EnCours, Autre.DansAllee?, Autre.Avancee > P.Avancee):
                set Limite = Min(Limite, Autre.Avancee - Espacement)
            Cible := Min(Limite, P.Avancee + VitesseMarche * Pas)
            if (Cible <= P.Avancee + 1.0):
                Changer(P, 1, P.Modele.Attente)
                Sleep(Pas)
            else:
                Changer(P, 0, Marche(P))
                Pos := PointRoute(Route, Cible)
                Dir := DirectionRoute(Route, Cible)
                DeplacerAvecBagage(P, Pos, Dir, (Cible - P.Avancee) / VitesseMarche)
                set P.Avancee = Cible

    # ---------- coffre ----------
    RangerBagage(P:passager, Place:place_passager)<suspends>:void =
        Changer(P, 1, P.Modele.Attente)
        T := Place.Coffre.GetTransform()
        if (B := P.Bagage?):
            Range := transform{Translation := T.Translation, Rotation := T.Rotation, Scale := EchelleBagage(P)}
            B.MoveTo(Range, 1.0)
            # on remplace par la version "rangée" (valise couchée, poignée rentrée)
            if (Rangee := SpawnProp(P.Sac.Rangee, Range)(0)?):
                B.Dispose()
                set P.Bagage = option{Rangee}
        Sleep(0.3)

    # La porte tourne autour de l'axe de l'allée ; le sens dépend du côté (gauche / droite).
    OuvrirCoffre(Numero:int)<suspends>:void =
        if (Porte := PortesCoffres[Numero], not CoffresOuverts[Numero]?, T := FermesCoffres[Numero]):
            if (set CoffresOuverts[Numero] = true) {}
            Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
            Axe := AxeAllee()
            var Milieu:vector3 = vector3{}
            if (Fin := Chemin[Chemin.Length - 1]) { set Milieu = Fin.GetTransform().Translation }
            Cote := if (DotProduct(CrossProduct(Axe, Haut), T.Translation - Milieu) > 0.0) then 1.0 else -1.0
            Ouverture := MakeRotation(Axe, DegreesToRadians(AngleCoffre * Cote))
            Porte.MoveTo(T.Translation, T.Rotation.RotateBy(Ouverture), 0.6)

    FermerCoffre(Numero:int)<suspends>:void =
        if (Porte := PortesCoffres[Numero], CoffresOuverts[Numero]?, T := FermesCoffres[Numero]):
            if (set CoffresOuverts[Numero] = false) {}
            Porte.MoveTo(T.Translation, T.Rotation, 0.6)

    GererBoutonCoffre(Numero:int, Bouton:button_device)<suspends>:void =
        loop:
            Bouton.InteractedWithEvent.Await()
            if (CoffresOuverts[Numero]?) then FermerCoffre(Numero) else OuvrirCoffre(Numero)

    # Direction de l'allée : du dernier repère du chemin vers la place la plus éloignée.
    AxeAllee():vector3 =
        var Axe:vector3 = vector3{X := 1.0, Y := 0.0, Z := 0.0}
        if (Fin := Chemin[Chemin.Length - 1]):
            Depart := Fin.GetTransform().Translation
            var Loin:float = 0.0
            for (P : Places):
                A := P.Allee.GetTransform().Translation
                D := Distance(A, Depart)
                if (D > Loin):
                    set Loin = D
                    set Axe = Normaliser(vector3{X := A.X - Depart.X, Y := A.Y - Depart.Y, Z := 0.0})
        Axe

    # ---------- s'asseoir ----------
    Asseoir(P:passager, Place:place_passager)<suspends>:void =
        set P.DansAllee = false
        T := Place.Siege.GetTransform()
        Changer(P, 2, P.Modele.Assis)
        if (C := P.Corps?):
            C.MoveTo(T.Translation, T.Rotation, DureeAssis)

    # ---------- outils ----------
    Marche(P:passager)<transacts>:creative_prop_asset =
        if (P.Valise?) then P.Modele.MarcheValise else P.Modele.MarcheSac

    RotationBagage(P:passager)<transacts>:float =
        if (P.Valise?) then RotationModele + RotationValise else RotationModele + RotationSac

    # Remplace le prop du personnage par un autre blueprint (autre animation), au même endroit.
    Changer(P:passager, Etat:int, Asset:creative_prop_asset):void =
        if (P.Etat <> Etat, C := P.Corps?):
            T := C.GetTransform()
            if (Nouveau := SpawnProp(Asset, T.Translation, T.Rotation)(0)?):
                C.Dispose()
                set P.Corps = option{Nouveau}
                set P.Etat = Etat

    DeplacerAvecBagage(P:passager, Pos:vector3, Dir:vector3, Duree:float)<suspends>:void =
        RotCorps := Orientation(Dir, RotationModele)
        TB := TransformBagage(P, Pos, Dir)
        if (C := P.Corps?, B := P.Bagage?):
            sync:
                C.MoveTo(Pos, RotCorps, Duree)
                B.MoveTo(TB, Duree)
        else if (C := P.Corps?):
            C.MoveTo(Pos, RotCorps, Duree)

    EchelleBagage(P:passager)<transacts>:vector3 =
        E := if (P.Valise?) then EchelleValise else EchelleSac
        vector3{X := E, Y := E, Z := E}

    # Transform complet du bagage : position, orientation (valise penchée) et taille.
    TransformBagage(P:passager, Pieds:vector3, Dir:vector3)<transacts>:transform =
        Lacet := RadiansToDegrees(ArcTan(Dir.Y, Dir.X)) + RotationBagage(P)
        Rot := if (P.Valise?) then MakeRotationFromYawPitchRollDegrees(Lacet, InclinaisonValise, RoulisValise) else MakeRotationFromYawPitchRollDegrees(Lacet, 0.0, 0.0)
        transform{Translation := PositionBagage(P, Pieds, Dir), Rotation := Rot, Scale := EchelleBagage(P)}

    # Position du bagage : main droite (valise) ou dos (sac), dans le repère du personnage.
    PositionBagage(P:passager, Pieds:vector3, Dir:vector3)<transacts>:vector3 =
        Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
        Avant := Normaliser(vector3{X := Dir.X, Y := Dir.Y, Z := 0.0})
        Droite := CrossProduct(Haut, Avant)
        M := P.Modele
        if (P.Valise?):
            Pieds + Droite * M.MainCote + Avant * M.MainAvant + Haut * M.MainHauteur
        else:
            Pieds + Avant * M.DosAvant + Haut * M.DosHauteur

    Orientation(Dir:vector3, Decalage:float)<transacts>:rotation =
        Lacet := RadiansToDegrees(ArcTan(Dir.Y, Dir.X)) + Decalage
        MakeRotationFromYawPitchRollDegrees(Lacet, 0.0, 0.0)

    Normaliser(V:vector3)<transacts>:vector3 =
        L := Distance(V, vector3{})
        if (L > 0.001) then V / L else vector3{X := 1.0, Y := 0.0, Z := 0.0}

    LongueurRoute(Route:[]vector3):float =
        var L:float = 0.0
        for (I := 1..Route.Length - 1, A := Route[I - 1], B := Route[I]):
            set L += Distance(A, B)
        L

    # Point situé à la distance D le long de la route.
    PointRoute(Route:[]vector3, D:float):vector3 =
        var Reste:float = D
        var Point:vector3 = if (Dernier := Route[Route.Length - 1]) then Dernier else vector3{}
        var Trouve:logic = false
        for (I := 1..Route.Length - 1, A := Route[I - 1], B := Route[I], not Trouve?):
            L := Distance(A, B)
            if (Reste <= L, L > 0.0):
                set Point = A + (B - A) * (Reste / L)
                set Trouve = true
            else:
                set Reste -= L
        Point

    DirectionRoute(Route:[]vector3, D:float):vector3 =
        var Reste:float = D
        var Dir:vector3 = vector3{X := 1.0, Y := 0.0, Z := 0.0}
        var Trouve:logic = false
        for (I := 1..Route.Length - 1, A := Route[I - 1], B := Route[I], not Trouve?):
            L := Distance(A, B)
            set Dir = B - A
            if (Reste <= L):
                set Trouve = true
            else:
                set Reste -= L
        Dir
