using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# En vol : l'avion ne bouge pas. On fait apparaitre une bulle de ciel autour de lui (elle cache
# l'aeroport) qui tourne lentement sur elle-meme. Les nuages qui defilent sont facultatifs
# (laisse la liste Nuages vide pour ne pas en avoir).
#
# Dans UEFN :
#   Ciel       : le prop Ciel.glb, centre sur l'avion (pas de collision).
#   Nuages     : des props Nuage_1..4 poses autour de l'avion (a cote des hublots, au-dessus, en dessous),
#                n'importe ou le long de l'avion. Pas de collision.
#   Nez, Queue : deux petits reperes (props) : un au nez de l'avion, un a la queue (pour connaitre la direction).
# Tout est cache au debut. La cinematique appelle Decoller() a la fin ; Atterrir() remet tout comme avant.
vol_device := class(creative_device):
    @editable Ciel:creative_prop = creative_prop{}
    @editable Nuages:[]creative_prop = array{}
    # Le grand disque de nuages (SolNuages.glb), pose JUSTE SOUS le ventre de l'avion : il cache le sol.
    @editable SolNuages:?creative_prop = false
    # Tout ce qui depasse au-dessus du disque et se voit des hublots (passerelle, terminal, panneaux...) :
    # cache pendant le vol.
    @editable ACacher:[]creative_prop = array{}
    # Nez / Queue : seulement utiles s'il y a des nuages qui defilent.
    @editable Nez:?creative_prop = false
    @editable Queue:?creative_prop = false
    # Vitesse des nuages (cm/s) et longueur de la boucle (cm) : ils partent loin devant et
    # reapparaissent devant quand ils sont loin derriere.
    @editable VitesseNuages:float = 6000.0
    @editable LongueurBoucle:float = 40000.0
    # Rotation lente de la bulle de ciel sur elle-meme (degres par seconde). 0 = immobile.
    @editable RotationCiel:float = 1.0

    var CielDepart:transform = transform{}

    var EnVol:logic = false
    var Departs:[]transform = array{}

    OnBegin<override>()<suspends>:void =
        set Departs = for (N : Nuages) { N.GetTransform() }
        set CielDepart = Ciel.GetTransform()
        Ciel.Hide()
        if (S := SolNuages?) { S.Hide() }
        if (N := Nez?) { N.Hide() }
        if (Q := Queue?) { Q.Hide() }
        for (N : Nuages) { N.Hide() }

    Decoller():void =
        if (not EnVol?):
            set EnVol = true
            Ciel.Show()
            spawn{TournerCiel()}
            if (S := SolNuages?) { S.Show() }
            for (X : ACacher) { X.Hide() }
            for (I -> N : Nuages) { spawn{FaireDefiler(I, N)} }

    Atterrir():void =
        set EnVol = false
        Ciel.Hide()
        if (Ciel.TeleportTo[CielDepart]) {}
        if (S := SolNuages?) { S.Hide() }
        for (X : ACacher) { X.Show() }
        for (I -> N : Nuages, T := Departs[I]):
            N.Hide()
            if (N.TeleportTo[T]) {}

    # La bulle tourne lentement autour de l'axe vertical, par pas de 10 degres.
    TournerCiel()<suspends>:void =
        Haut := vector3{X := 0.0, Y := 0.0, Z := 1.0}
        loop:
            if (not EnVol? or RotationCiel <= 0.0) { break }
            T := Ciel.GetTransform()
            Pas := MakeRotation(Haut, DegreesToRadians(10.0))
            Ciel.MoveTo(T.Translation, T.Rotation.RotateBy(Pas), 10.0 / RotationCiel)

    # Chaque nuage part d'un point au hasard devant l'avion, file vers l'arriere, puis recommence.
    FaireDefiler(I:int, N:creative_prop)<suspends>:void =
        if (T := Departs[I]):
            var D:vector3 = vector3{X := 1.0, Y := 0.0, Z := 0.0}
            if (N1 := Nez?, Q1 := Queue?) { set D = N1.GetTransform().Translation - Q1.GetTransform().Translation }
            L := Distance(D, vector3{})
            Avant := if (L > 1.0) then D / L else vector3{X := 1.0, Y := 0.0, Z := 0.0}
            Demi := LongueurBoucle / 2.0
            # premier passage : depuis un point au hasard de la boucle (pour qu'ils ne soient pas alignes)
            var Debut:float = GetRandomFloat(-Demi, Demi)
            N.Show()
            loop:
                if (not EnVol?) { break }
                A := T.Translation + Avant * Debut
                B := T.Translation - Avant * Demi
                if (N.TeleportTo[A, T.Rotation]) {}
                N.MoveTo(B, T.Rotation, (Debut + Demi) / Max(1.0, VitesseNuages))
                set Debut = Demi
