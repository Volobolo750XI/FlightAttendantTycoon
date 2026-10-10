using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# En vol : l'avion ne bouge pas. On fait apparaitre une bulle de ciel autour de lui (elle cache
# l'aeroport) et des nuages defilent de l'avant vers l'arriere de l'avion, en boucle.
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
    @editable Nez:creative_prop = creative_prop{}
    @editable Queue:creative_prop = creative_prop{}
    # Vitesse des nuages (cm/s) et longueur de la boucle (cm) : ils partent loin devant et
    # reapparaissent devant quand ils sont loin derriere.
    @editable VitesseNuages:float = 6000.0
    @editable LongueurBoucle:float = 40000.0

    var EnVol:logic = false
    var Departs:[]transform = array{}

    OnBegin<override>()<suspends>:void =
        set Departs = for (N : Nuages) { N.GetTransform() }
        Ciel.Hide()
        Nez.Hide()
        Queue.Hide()
        for (N : Nuages) { N.Hide() }

    Decoller():void =
        if (not EnVol?):
            set EnVol = true
            Ciel.Show()
            for (I -> N : Nuages) { spawn{FaireDefiler(I, N)} }

    Atterrir():void =
        set EnVol = false
        Ciel.Hide()
        for (I -> N : Nuages, T := Departs[I]):
            N.Hide()
            if (N.TeleportTo[T]) {}

    # Chaque nuage part d'un point au hasard devant l'avion, file vers l'arriere, puis recommence.
    FaireDefiler(I:int, N:creative_prop)<suspends>:void =
        if (T := Departs[I]):
            D := Nez.GetTransform().Translation - Queue.GetTransform().Translation
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
