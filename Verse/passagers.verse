using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
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
    @editable MainCote:float = 36.0
    @editable MainAvant:float = 0.0
    # Où se trouve le haut des bretelles du sac (cm) : hauteur, avant (+) / arrière (-).
    @editable DosHauteur:float = 110.0
    @editable DosAvant:float = -12.0

bagage := class<concrete>:
    # EnMain : porté (valise poignée sortie / sac). Rangee : posé dans le coffre.
    @editable EnMain:creative_prop_asset = DefaultCreativePropAsset
    @editable Rangee:creative_prop_asset = DefaultCreativePropAsset

place_passager := class<concrete>:
    @editable Siege:creative_prop = creative_prop{}
    @editable Allee:creative_prop = creative_prop{}
    @editable Coffre:creative_prop = creative_prop{}

# Position d'un objet (bagage, personnage assis...) par rapport à une référence (personnage, repère).
relatif := struct:
    Decalage:vector3 = vector3{}
    Rot:rotation = IdentityRotation()
    Echelle:vector3 = vector3{X := 1.0, Y := 1.0, Z := 1.0}

# EXEMPLES : tu poses toi-même dans la map, à la main, UNE fois, exactement comme tu veux que ce soit :
#   - un personnage (blueprint marche valise) + une valise dans sa main ;
#   - un personnage (blueprint marche sac) + un sac sur son dos ;
#   - un personnage assis (blueprint assis) sur un siège + le repère siège de ce siège ;
#   - une valise rangée + un sac rangé dans un coffre + le repère coffre de ce coffre.
# Le code mesure où tu les as mis et reproduit exactement la même chose pour tous les passagers.
# Les exemples sont cachés au lancement. Laisse une case vide pour garder l'ancien réglage.
exemples := class<concrete>:
    @editable PersoValise:?creative_prop = false
    @editable Valise:?creative_prop = false
    @editable PersoSac:?creative_prop = false
    @editable Sac:?creative_prop = false
    @editable Assis:?creative_prop = false
    @editable RepereSiege:?creative_prop = false
    @editable ValiseRangee:?creative_prop = false
    @editable SacRange:?creative_prop = false
    @editable RepereCoffre:?creative_prop = false

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
    var DerniereDir:vector3 = vector3{X := 1.0, Y := 0.0, Z := 0.0}

passagers := class(creative_device):
    @editable BoutonEmbarquement:button_device = button_device{}
    # DeviceAvion : ton device avion_tycoon : sert à savoir combien de rangées sont achetées.
    @editable DeviceAvion:avion_tycoon = avion_tycoon{}
    # Le bouton rouge START BOARDING (le prop) : il s'enfonce quand on appuie. Les morceaux en plus
    # (si ton bouton est en plusieurs props, mets seulement le capuchon rouge ici).
    @editable BoutonVisuel:?creative_prop = false
    # Son de bouton quand on appuie sur START BOARDING : un Appareil Lecteur audio.
    @editable SonBouton:?audio_player_device = false
    @editable EnfoncementBouton:float = 4.0
    @editable Modeles:[]modele_passager = array{}
    @editable Valises:[]bagage = array{}
    @editable Sacs:[]bagage = array{}
    @editable Chemin:[]creative_prop = array{}
    @editable Places:[]place_passager = array{}
    @editable PortesCoffres:[]creative_prop = array{}
    # Un Appareil Bouton par porte (même ordre que PortesCoffres) : on interagit pour fermer / rouvrir.
    @editable BoutonsCoffres:[]button_device = array{}

    @editable Exemples:exemples = exemples{}

    # Vitesse de marche (cm/s), écart entre deux passagers dans la queue (cm),
    # temps entre deux arrivées (s), durée pour s'asseoir (s).
    @editable VitesseMarche:float = 130.0
    @editable Espacement:float = 110.0
    # Tout le monde finit par embarquer. DureeEmbarquement = temps moyen (s) pour que tout le monde
    # arrive ; les arrivées sont irrégulières (groupes, trous) et il y a parfois un retardataire
    # qui fait attendre jusqu'à RetardMax secondes.
    @editable DureeEmbarquement:float = 75.0
    @editable RetardMax:float = 25.0
    # Temps passé à ranger le bagage (immobile), puis le bagage apparaît d'un coup dans le coffre.
    @editable DureeRangement:float = 2.5
    # Sac rangé : de combien il est poussé au fond du coffre (cm, vers le hublot).
    @editable FondSac:float = 35.0
    # Rotation à plat (degrés) du sac à dos couché dans le coffre.
    @editable RotationSacRange:float = 90.0
    @editable DureeAssis:float = 3.0
    # Angle d'ouverture des portes de coffre (degrés). Si elles s'ouvrent vers le bas, mets -100.
    @editable AngleCoffre:float = 80.0
    # Taille des personnages (X, Y, Z).
    @editable EchellePersoX:float = 1.25
    @editable EchellePersoY:float = 1.2
    @editable EchellePersoZ:float = 1.25
    # Si tes personnages ne regardent pas dans le sens de la marche, tourne-les ici (degrés).
    # -90 = un quart de tour vers la gauche. S'ils marchent à reculons ou de l'autre côté, mets 90.
    @editable RotationModele:float = -90.0
    # Assis : rotation en plus (degrés) et décalage (cm) pour bien les coller au siège.
    # HauteurAssis négatif = plus bas. AvanceAssis positif = vers l'avant du siège.
    @editable RotationAssis:float = 180.0
    @editable HauteurAssis:float = -60.0
    @editable AvanceAssis:float = -95.0
    # CoteAssis : décalage sur le côté (cm). Positif = vers la droite quand on regarde vers le fond de l'avion.
    @editable CoteAssis:float = 80.0
    # 90 = la valise tournée d'un quart de tour : grande face vers l'arrière, poignée en travers.
    # Si elle est encore sur le côté, mets -90.
    @editable RotationValise:float = 90.0
    @editable RotationSac:float = -90.0
    # Taille des bagages (1.5 = 1.5 partout) et inclinaison de la valise tirée (degrés).
    # Si la valise penche vers l'avant au lieu de traîner derrière, mets -35. Roulis : à régler si elle penche sur le côté.
    @editable EchelleValise:float = 1.5
    @editable EchelleSac:float = 1.6
    @editable InclinaisonValise:float = 35.0
    @editable RoulisValise:float = 0.0

    var EnCours:[]passager = array{}
    var Occupees:[]logic = array{}
    var CoffresOuverts:[]logic = array{}
    var FermesCoffres:[]transform = array{}
    var NbEnRoute:int = 0
    var Embarquement:logic = false
    var RelValise:?relatif = false
    var BoutonRepos:?transform = false
    var BoutonEnCours:logic = false
    var RelSac:?relatif = false
    var RelAssis:?relatif = false
    var RelValiseRangee:?relatif = false
    var RelSacRange:?relatif = false

    OnBegin<override>()<suspends>:void =
        MesurerExemples()
        if (B := BoutonVisuel?) { set BoutonRepos = option{B.GetTransform()} }
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
            Joueur := BoutonEmbarquement.InteractedWithEvent.Await()
            if (Son := SonBouton?) { Son.Play() }
            spawn{AnimerBouton(Joueur)}
            if (not Embarquement?):
                spawn{Embarquer()}

    # ---------- l'embarquement complet ----------
    Embarquer()<suspends>:void =
        set Embarquement = true
        Achetes0 := for (P : Places) { SiegeAchete(P) }
        Total := for (I -> P : Places, not Occupees[I]?, Achetes0[I]?) { I }
        Moyenne := DureeEmbarquement / Max(1.0, Total.Length * 1.0)
        loop:
            # places libres dont la rangée est achetée
            Achetes := for (P : Places) { SiegeAchete(P) }
            Libres := for (I -> P : Places, not Occupees[I]?, Achetes[I]?) { I }
            if (Libres.Length = 0 or Modeles.Length = 0) { break }
            if (I := Libres[GetRandomInt(0, Libres.Length - 1)], P := Places[I]):
                if (set Occupees[I] = true) {}
                spawn{UnPassager(P)}
            # rythme réaliste : beaucoup d'écarts courts, quelques longs (loi très irrégulière,
            # moyenne = Moyenne), des groupes qui arrivent collés, et parfois un retardataire
            Tirage := GetRandomInt(1, 100)
            U := GetRandomFloat(0.0, 1.0)
            if (Tirage <= 20) then Sleep(GetRandomFloat(0.7, 1.4))
            else if (Tirage <= 30) then Sleep(GetRandomFloat(RetardMax * 0.4, RetardMax))
            else Sleep(Max(1.0, Moyenne * 3.0 * U * U))
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
                if (Corps := SpawnProp(Marche(P), transform{Translation := Depart, Rotation := Rot, Scale := EchellePerso()})(0)?):
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
        # il range son bagage : rien ne bouge pendant DureeRangement...
        Sleep(DureeRangement)
        # ...puis le bagage apparaît d'un coup dans le coffre
        T := Place.Coffre.GetTransform()
        if (B := P.Bagage?):
            Rel := if (P.Valise?) then RelValiseRangee else RelSacRange
            if (R := Rel?):
                if (Rangee := SpawnProp(P.Sac.Rangee, Appliquer(R, T))(0)?):
                    set P.Bagage = option{Rangee}
                    B.Dispose()
            else if (P.Valise?):
                Range := transform{Translation := T.Translation, Rotation := T.Rotation, Scale := EchelleBagage(P)}
                if (Rangee := SpawnProp(P.Sac.Rangee, Range)(0)?):
                    set P.Bagage = option{Rangee}
                    B.Dispose()
                else if (B.TeleportTo[Range]) {}
            else:
                # sac à dos : le MÊME sac, couché sur le côté (bascule de 90° autour de l'axe
                # avant-arrière du sac), posé à plat sur le fond du coffre, au niveau du repère
                # "au fond" = du côté opposé à l'allée (vers le hublot)
                A := Place.Allee.GetTransform().Translation
                Fond := Normaliser(vector3{X := T.Translation.X - A.X, Y := T.Translation.Y - A.Y, Z := 0.0})
                Repere := transform{Translation := T.Translation + Fond * FondSac, Rotation := T.Rotation, Scale := T.Scale}
                if (B.TeleportTo[SacCouche(P, B.GetTransform(), Repere)]) {}
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
        Rot := T.Rotation.RotateBy(MakeRotation(vector3{X := 0.0, Y := 0.0, Z := 1.0}, DegreesToRadians(RotationAssis)))
        Pos := T.Translation + Rot.GetLocalForward() * AvanceAssis + CrossProduct(vector3{X := 0.0, Y := 0.0, Z := 1.0}, AxeAllee()) * CoteAssis + vector3{X := 0.0, Y := 0.0, Z := HauteurAssis}
        # il s'assoit d'un coup : le blueprint assis apparaît directement sur le siège
        var Cible:transform = transform{Translation := Pos, Rotation := Rot, Scale := EchellePerso()}
        if (R := RelAssis?) { set Cible = Appliquer(R, T) }
        if (C := P.Corps?):
            if (Nouveau := SpawnProp(P.Modele.Assis, Cible)(0)?):
                C.Dispose()
                set P.Corps = option{Nouveau}
                set P.Etat = 2

    # ---------- bouton qui s'enfonce ----------
    # Le bouton s'enfonce dans le sens où le joueur appuie (du joueur vers le bouton,
    # à l'horizontale) : donc toujours vers le mur, quelle que soit la rotation du prop.
    AnimerBouton(Joueur:agent)<suspends>:void =
        # position de repos mémorisée au lancement : le bouton revient TOUJOURS au même endroit,
        # et on ignore les appuis pendant l'animation
        if (B := BoutonVisuel?, T := BoutonRepos?, not BoutonEnCours?):
            set BoutonEnCours = true
            var Dir:vector3 = vector3{X := 1.0, Y := 0.0, Z := 0.0}
            if (Perso := Joueur.GetFortCharacter[]):
                D := T.Translation - Perso.GetTransform().Translation
                set Dir = Normaliser(vector3{X := D.X, Y := D.Y, Z := 0.0})
            Bas := T.Translation + Dir * EnfoncementBouton
            B.MoveTo(Bas, T.Rotation, 0.08)
            Sleep(0.12)
            B.MoveTo(T.Translation, T.Rotation, 0.15)
            if (B.TeleportTo[T.Translation, T.Rotation]) {}
            set BoutonEnCours = false

    # Sac couché sur le côté : on part du sac tel qu'il est porté (debout, pivot en haut des
    # bretelles), on le bascule de 90° autour de l'axe de marche, et on met son centre sur le repère.
    SacCouche(P:passager, Porte:transform, Repere:transform)<transacts>:transform =
        Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
        Avant := Normaliser(vector3{X := P.DerniereDir.X, Y := P.DerniereDir.Y, Z := 0.0})
        Axe := CrossProduct(Haut, Avant)
        Bascule := MakeRotation(Axe, PiFloat / 2.0)
        Taille := EchelleSac * 100.0
        # du centre du sac jusqu'au pivot (haut des bretelles) quand il est debout
        CentreVersPivot := Haut * (0.285 * Taille)
        # puis on le tourne à plat (autour de la verticale) de RotationSacRange degrés
        Tour := MakeRotation(Haut, DegreesToRadians(RotationSacRange))
        Pivot := Repere.Translation + Haut * (0.15 * Taille) + Tour.RotateVector(Bascule.RotateVector(CentreVersPivot))
        transform{Translation := Pivot, Rotation := Porte.Rotation.RotateBy(Bascule).RotateBy(Tour), Scale := Porte.Scale}

    # ---------- exemples ----------
    MesurerExemples():void =
        E := Exemples
        if (A := E.PersoValise?, B := E.Valise?):
            set RelValise = option{Mesurer(A.GetTransform(), B.GetTransform())}
        if (A := E.PersoSac?, B := E.Sac?):
            set RelSac = option{Mesurer(A.GetTransform(), B.GetTransform())}
        if (A := E.RepereSiege?, B := E.Assis?):
            set RelAssis = option{Mesurer(A.GetTransform(), B.GetTransform())}
        if (A := E.RepereCoffre?, B := E.ValiseRangee?):
            set RelValiseRangee = option{Mesurer(A.GetTransform(), B.GetTransform())}
        if (A := E.RepereCoffre?, B := E.SacRange?):
            set RelSacRange = option{Mesurer(A.GetTransform(), B.GetTransform())}
        # on cache les exemples (le repère siège / coffre est déjà caché avec les places)
        for (X : array{E.PersoValise, E.Valise, E.PersoSac, E.Sac, E.Assis, E.ValiseRangee, E.SacRange}, O := X?):
            O.Hide()

    Mesurer(Ref:transform, Objet:transform)<transacts>:relatif =
        relatif:
            Decalage := Ref.Rotation.UnrotateVector(Objet.Translation - Ref.Translation)
            Rot := Objet.Rotation.UnrotateBy(Ref.Rotation)
            Echelle := Objet.Scale

    Appliquer(R:relatif, Ref:transform)<transacts>:transform =
        transform:
            Translation := Ref.Translation + Ref.Rotation.RotateVector(R.Decalage)
            Rotation := R.Rot.RotateBy(Ref.Rotation)
            Scale := R.Echelle

    # ---------- outils ----------
    Marche(P:passager)<transacts>:creative_prop_asset =
        if (P.Valise?) then P.Modele.MarcheValise else P.Modele.MarcheSac

    RotationBagage(P:passager)<transacts>:float =
        if (P.Valise?) then RotationValise else RotationSac

    # Remplace le prop du personnage par un autre blueprint (autre animation), au même endroit.
    Changer(P:passager, Etat:int, Asset:creative_prop_asset):void =
        if (P.Etat <> Etat, C := P.Corps?):
            T := C.GetTransform()
            if (Nouveau := SpawnProp(Asset, transform{Translation := T.Translation, Rotation := T.Rotation, Scale := EchellePerso()})(0)?):
                C.Dispose()
                set P.Corps = option{Nouveau}
                set P.Etat = Etat

    DeplacerAvecBagage(P:passager, Pos:vector3, Dir:vector3, Duree:float)<suspends>:void =
        RotCorps := Orientation(Dir, RotationModele)
        TB := TransformBagage(P, Pos, Dir)
        set P.DerniereDir = Dir
        if (C := P.Corps?, B := P.Bagage?):
            sync:
                C.MoveTo(transform{Translation := Pos, Rotation := RotCorps, Scale := EchellePerso()}, Duree)
                B.MoveTo(TB, Duree)
        else if (C := P.Corps?):
            C.MoveTo(transform{Translation := Pos, Rotation := RotCorps, Scale := EchellePerso()}, Duree)

    # Un siège est acheté si le siège le plus proche de son repère (dans DeviceAvion)
    # appartient à une rangée déjà achetée. Rien à numéroter à la main.
    SiegeAchete(Place:place_passager):logic =
        Pos := Place.Siege.GetTransform().Translation
        var Meilleur:float = 1000000.0
        var Achete:logic = false
        for (K -> R : DeviceAvion.Rangees, S : R.Sieges):
            D := Distance(S.GetTransform().Translation, Pos)
            if (D < Meilleur):
                set Meilleur = D
                set Achete = if (K < DeviceAvion.RangeesAchetees) then true else false
        Achete

    EchellePerso()<transacts>:vector3 =
        vector3{X := EchellePersoX, Y := EchellePersoY, Z := EchellePersoZ}

    EchelleBagage(P:passager)<transacts>:vector3 =
        E := if (P.Valise?) then EchelleValise else EchelleSac
        vector3{X := E, Y := E, Z := E}

    # Transform complet du bagage : position, orientation (valise penchée) et taille.
    TransformBagage(P:passager, Pieds:vector3, Dir:vector3)<transacts>:transform =
        Rel := if (P.Valise?) then RelValise else RelSac
        if (R := Rel?):
            Appliquer(R, transform{Translation := Pieds, Rotation := Orientation(Dir, RotationModele), Scale := EchellePerso()})
        else:
            TransformBagageReglages(P, Pieds, Dir)

    TransformBagageReglages(P:passager, Pieds:vector3, Dir:vector3)<transacts>:transform =
        Lacet := RadiansToDegrees(ArcTan(Dir.Y, Dir.X)) + RotationBagage(P)
        Base := MakeRotationFromYawPitchRollDegrees(Lacet, 0.0, 0.0)
        # la valise est penchée vers l'arrière autour de l'axe gauche-droite de la MARCHE
        # (pas de l'axe du modèle) : elle roule toujours sur ses roulettes, derrière la personne
        Avant := Normaliser(vector3{X := Dir.X, Y := Dir.Y, Z := 0.0})
        Lateral := CrossProduct(vector3{X := 0.0, Y := 0.0, Z := 1.0}, Avant)
        Rot := if (P.Valise?) then Base.RotateBy(MakeRotation(Lateral, DegreesToRadians(InclinaisonValise))).RotateBy(MakeRotation(Avant, DegreesToRadians(RoulisValise))) else Base
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
