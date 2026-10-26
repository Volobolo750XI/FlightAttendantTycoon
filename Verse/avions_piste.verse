using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - le lobby vit : UN avion decolle et atterrit sur la piste, en boucle.
#
# Le cycle (sans fin) :
#   1. l'avion attend en bout de piste, puis accelere, cabre, decolle et monte dans le ciel ;
#   2. au loin, il disparait ;
#   3. un peu plus tard il reapparait loin dans l'axe de la piste, descend en approche,
#      touche la piste, freine et roule ;
#   4. il disparait, puis reapparait en bout de piste, pret a redecoller.
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Avion_Decor.glb, clic droit -> Convert to Prop ;
#   - pose UN avion en BOUT de piste, sur les roues, le nez dans le sens du decollage
#     (dans ses Details : Collision = pas de collision) ;
#   - pose ce device n'importe ou, et dans ses Details choisis l'avion (AvionPiste) ;
#   - lance la session. Si l'avion part de cote ou en arriere : change AxeDuNez.
#     S'il pique du nez au decollage au lieu de cabrer : mets Cabrage en negatif (ex : -12).

# Direction du nez de l'avion dans son propre repere (depend de l'import du modele).
axe_nez := enum{X, MoinsX, Y, MoinsY}

avions_piste_device := class(creative_device):

    @editable AvionPiste : creative_prop = creative_prop{}

    # Longueur de piste utilisee, en metres (depuis la position de depart de l'avion).
    @editable LongueurPiste : float = 380.0
    @editable AxeDuNez : axe_nez = axe_nez.X
    # Angle de montee au decollage, en degres (negatif si l'avion pique au lieu de cabrer).
    @editable Cabrage : float = 12.0
    # Attente en bout de piste avant chaque decollage (secondes, au hasard entre les deux).
    @editable AttenteMin : float = 6.0
    @editable AttenteMax : float = 14.0
    # Temps "en vol" (invisible) entre le decollage et le retour pour l'atterrissage.
    @editable TempsEnVol : float = 12.0
    # Jusqu'ou il part avant de disparaitre (et d'ou il revient), en metres.
    # Pas trop loin : au-dela de la zone chargee autour des joueurs, Fortnite peut figer l'avion.
    @editable DistanceVol : float = 1500.0
    @editable AltitudeVol : float = 400.0

    var Depart : transform = transform{}

    OnBegin<override>()<suspends>:void =
        set Depart = AvionPiste.GetTransform()
        loop:
            Placer(Depart.Translation, Depart.Rotation)
            AvionPiste.Show()
            Sleep(GetRandomFloat(AttenteMin, AttenteMax))
            Decoller()
            Disparaitre()
            Sleep(TempsEnVol)
            Atterrir()
            Disparaitre()
            Sleep(4.0)

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

    # Cache l'avion. Securite : en plus de Hide(), on le rend minuscule et on l'envoie sous le sol,
    # pour qu'il disparaisse a coup sur meme si Hide() ne suffit pas.
    Disparaitre():void =
        AvionPiste.Hide()
        Cache := Depart.Translation - vector3{X := 0.0, Y := 0.0, Z := 50000.0}
        if (AvionPiste.TeleportTo[transform{Translation := Cache, Rotation := Depart.Rotation,
                                            Scale := vector3{X := 0.001, Y := 0.001, Z := 0.001}}]) {}

    Aller(Pos:vector3, Rot:rotation, Duree:float)<suspends>:void =
        AvionPiste.MoveTo(transform{Translation := Pos, Rotation := Rot, Scale := Depart.Scale}, Duree)

    Placer(Pos:vector3, Rot:rotation):void =
        if (AvionPiste.TeleportTo[transform{Translation := Pos, Rotation := Rot, Scale := Depart.Scale}]) {}

    # ------------------------------------------------------------------ decollage
    Decoller()<suspends>:void =
        P := Depart.Translation
        R := Depart.Rotation
        D := Devant(R)
        L := LongueurPiste * 100.0
        Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
        Cabre := Incline(R, Cabrage)
        Sleep(2.0)                                                      # moteurs a fond...
        # acceleration : de plus en plus vite
        Aller(P + D * (L * 0.06), R, 4.0)
        Aller(P + D * (L * 0.20), R, 3.5)
        Aller(P + D * (L * 0.42), R, 3.0)
        Aller(P + D * (L * 0.62), R, 2.2)
        # rotation : le nez se leve, les roues quittent la piste
        Aller(P + D * (L * 0.80) + Haut * 300.0, Cabre, 1.8)
        # montee, puis il s'eloigne
        Aller(P + D * (L + 12000.0) + Haut * 4500.0, Cabre, 5.0)
        Aller(P + D * (L + 90000.0) + Haut * 30000.0, Cabre, 18.0)
        Aller(P + D * (L + DistanceVol * 100.0) + Haut * (AltitudeVol * 100.0), Cabre, 10.0)

    # ------------------------------------------------------------------ atterrissage
    # Il revient dans le MEME sens que le decollage : il arrive par l'arriere du point de depart
    # et touche la piste un peu apres le bout de piste.
    Atterrir()<suspends>:void =
        R := Depart.Rotation
        D := Devant(R)
        L := LongueurPiste * 100.0
        Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
        Toucher := Depart.Translation + D * (L * 0.12)
        Arrondi := Incline(R, Cabrage * 0.25)                          # leger nez haut
        Approche := Incline(R, Cabrage * 0.1)
        Placer(Toucher - D * (DistanceVol * 100.0) + Haut * (AltitudeVol * 100.0), Approche)
        AvionPiste.Show()
        Aller(Toucher - D * 90000.0 + Haut * 28000.0, Approche, 10.0)
        Aller(Toucher - D * 30000.0 + Haut * 8500.0, Approche, 12.0)
        Aller(Toucher - D * 6000.0 + Haut * 1500.0, Approche, 6.0)
        Aller(Toucher - D * 1200.0 + Haut * 250.0, Arrondi, 2.0)
        Aller(Toucher, Arrondi, 1.4)                                    # toucher des roues
        # freinage : de plus en plus lent
        Aller(Toucher + D * (L * 0.22), R, 3.0)
        Aller(Toucher + D * (L * 0.42), R, 4.0)
        Aller(Toucher + D * (L * 0.55), R, 4.5)
        Aller(Toucher + D * (L * 0.60), R, 4.0)
        Sleep(3.0)
