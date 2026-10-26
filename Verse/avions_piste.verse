using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - le lobby vit : des avions ATTERRISSENT et DECOLLENT sur la piste, en boucle.
#
# Le cycle (sans fin) :
#   1. un avion arrive de loin, descend en approche, touche la piste, freine et roule jusqu'au bout,
#      puis disparait (il "part au parking") ;
#   2. pause ;
#   3. l'autre avion, qui attend en bout de piste, accelere, cabre, decolle et monte dans le ciel,
#      puis disparait au loin et revient se placer en bout de piste ;
#   4. pause, et on recommence.
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Avion_Decor.glb, clic droit -> Convert to Prop ;
#   - pose 2 avions sur la piste du lobby (meme echelle que le reste) :
#       * AvionDecollage : en BOUT de piste, sur les roues, le nez dans le sens du decollage ;
#       * AvionAtterrissage : au point ou il doit TOUCHER la piste (vers le debut), meme sens ;
#     -> dans leurs Details : Collision = pas de collision (sinon le deplacement peut bloquer) ;
#   - pose ce device n'importe ou, et dans ses Details choisis les 2 avions ;
#   - lance la session. Si les avions partent de cote ou en arriere : change AxeDuNez.
#     S'ils piquent du nez au decollage au lieu de cabrer : mets Cabrage en negatif (ex : -12).

# Direction du nez de l'avion dans son propre repere (depend de l'import du modele).
axe_nez := enum{X, MoinsX, Y, MoinsY}

avions_piste_device := class(creative_device):

    @editable AvionDecollage : creative_prop = creative_prop{}
    @editable AvionAtterrissage : creative_prop = creative_prop{}

    # Longueur de piste utilisee, en metres (depuis la position de chaque avion).
    @editable LongueurPiste : float = 380.0
    @editable AxeDuNez : axe_nez = axe_nez.X
    # Angle de montee au decollage, en degres (negatif si l'avion pique au lieu de cabrer).
    @editable Cabrage : float = 12.0
    # Pause entre deux mouvements, en secondes (tiree au hasard entre les deux).
    @editable PauseMin : float = 8.0
    @editable PauseMax : float = 18.0
    @editable AtterrissageActif : logic = true
    @editable DecollageActif : logic = true

    var DepartDecollage : transform = transform{}
    var PointToucher : transform = transform{}

    OnBegin<override>()<suspends>:void =
        set DepartDecollage = AvionDecollage.GetTransform()
        set PointToucher = AvionAtterrissage.GetTransform()
        AvionAtterrissage.Hide()
        loop:
            if (AtterrissageActif?):
                Atterrir()
            Sleep(GetRandomFloat(PauseMin, PauseMax))
            if (DecollageActif?):
                Decoller()
            Sleep(GetRandomFloat(PauseMin, PauseMax))

    # Vecteur "devant" de l'avion (a plat, longueur 1).
    Devant(R:rotation):vector3 =
        V := case (AxeDuNez):
            axe_nez.X => R.GetLocalForward()
            axe_nez.MoinsX => R.GetLocalForward() * -1.0
            axe_nez.Y => R.GetLocalRight()
            axe_nez.MoinsY => R.GetLocalRight() * -1.0
        Plat := vector3{X := V.X, Y := V.Y, Z := 0.0}
        L := Plat.Length()
        if (L > 0.001) then Plat / L else vector3{X := 1.0, Y := 0.0, Z := 0.0}

    # Leve (ou baisse) le nez de l'avion de Degres.
    Incline(R:rotation, Degres:float):rotation =
        A := DegreesToRadians(Degres)
        case (AxeDuNez):
            axe_nez.X => R.ApplyPitch(A)
            axe_nez.MoinsX => R.ApplyPitch(-A)
            axe_nez.Y => R.ApplyRoll(-A)
            axe_nez.MoinsY => R.ApplyRoll(A)

    Aller(Avion:creative_prop, Pos:vector3, Rot:rotation, Echelle:vector3, Duree:float)<suspends>:void =
        Avion.MoveTo(transform{Translation := Pos, Rotation := Rot, Scale := Echelle}, Duree)

    Placer(Avion:creative_prop, Pos:vector3, Rot:rotation, Echelle:vector3):void =
        if (Avion.TeleportTo[transform{Translation := Pos, Rotation := Rot, Scale := Echelle}]) {}

    # ------------------------------------------------------------------ atterrissage
    Atterrir()<suspends>:void =
        Avion := AvionAtterrissage
        T := PointToucher
        D := Devant(T.Rotation)
        L := LongueurPiste * 100.0
        Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
        NezHaut := Incline(T.Rotation, Cabrage * 0.25)               # leger arrondi a l'atterrissage
        Approche := Incline(T.Rotation, Cabrage * 0.1)
        # tres loin et haut, dans l'axe de la piste
        Placer(Avion, T.Translation - D * 90000.0 + Haut * 28000.0, Approche, T.Scale)
        Avion.Show()
        Aller(Avion, T.Translation - D * 30000.0 + Haut * 8500.0, Approche, T.Scale, 12.0)
        Aller(Avion, T.Translation - D * 6000.0 + Haut * 1500.0, Approche, T.Scale, 6.0)
        Aller(Avion, T.Translation - D * 1200.0 + Haut * 250.0, NezHaut, T.Scale, 2.0)
        Aller(Avion, T.Translation, NezHaut, T.Scale, 1.4)                # toucher des roues
        # freinage : de plus en plus lent
        Aller(Avion, T.Translation + D * (L * 0.22), T.Rotation, T.Scale, 3.0)
        Aller(Avion, T.Translation + D * (L * 0.42), T.Rotation, T.Scale, 4.0)
        Aller(Avion, T.Translation + D * (L * 0.55), T.Rotation, T.Scale, 4.5)
        Aller(Avion, T.Translation + D * (L * 0.60), T.Rotation, T.Scale, 4.0)
        Sleep(3.0)
        Avion.Hide()

    # ------------------------------------------------------------------ decollage
    Decoller()<suspends>:void =
        Avion := AvionDecollage
        T := DepartDecollage
        D := Devant(T.Rotation)
        L := LongueurPiste * 100.0
        Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
        Cabre := Incline(T.Rotation, Cabrage)
        Placer(Avion, T.Translation, T.Rotation, T.Scale)
        Avion.Show()
        Sleep(3.0)                                                      # moteurs a fond...
        # acceleration : de plus en plus vite
        Aller(Avion, T.Translation + D * (L * 0.06), T.Rotation, T.Scale, 4.0)
        Aller(Avion, T.Translation + D * (L * 0.20), T.Rotation, T.Scale, 3.5)
        Aller(Avion, T.Translation + D * (L * 0.42), T.Rotation, T.Scale, 3.0)
        Aller(Avion, T.Translation + D * (L * 0.62), T.Rotation, T.Scale, 2.2)
        # rotation : le nez se leve, les roues quittent la piste
        Aller(Avion, T.Translation + D * (L * 0.80) + Haut * 300.0, Cabre, T.Scale, 1.8)
        # montee
        Aller(Avion, T.Translation + D * (L + 12000.0) + Haut * 4500.0, Cabre, T.Scale, 5.0)
        Aller(Avion, T.Translation + D * (L + 90000.0) + Haut * 30000.0, Cabre, T.Scale, 18.0)
        Avion.Hide()
        # retour discret en bout de piste pour le prochain decollage
        Placer(Avion, T.Translation, T.Rotation, T.Scale)
        Avion.Show()
