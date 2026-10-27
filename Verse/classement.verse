using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - le CLASSEMENT du lobby (podium "TOP PILOTS").
#
# Toutes les quelques secondes, on classe les joueurs qui ont un avion :
#   d'abord par REBIRTHS, puis (a egalite) par ARGENT.
# Sur chaque marche, un "Player Reference" montre le vrai personnage du joueur avec son nom.
# Au-dessus, sur le panneau, chaque place a un COMPTEUR (la barre rose "rebirth") avec 4 TAMBOURS 3D
# qui tournent comme un compteur pour afficher son nombre de rebirths (0000 a 9999).
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Classement.glb (podium + panneau + compteurs), Convert to Prop ;
#   - importe Modeles/Lobby/Tambour_Chiffres.glb, Convert to Prop -> pose 12 tambours (4 par compteur) ;
#     pour chaque compteur, place JUSTE LE PREMIER tambour bien dans la 1re case (a gauche) de la barre rose,
#     le "0" vers l'avant. Les 3 autres, pose-les n'importe ou : le Verse les aligne tout seul ;
#   - sur chaque marche (1, 2, 3), pose un appareil "Reference de joueur" (Player Reference) ;
#   - pose ce device, et dans ses Details :
#       Avions    : tes devices avion_tycoon (un par parcelle) ;
#       Places    : les 3 Player Reference, DANS L'ORDRE (1er, 2e, 3e) ;
#       Compteurs : 3 lignes, dans le meme ordre ; dans chacune, Tambours = les 4 tambours de ce
#                   compteur, de GAUCHE a DROITE (le 1er = celui que tu as bien place).
#   Reglages si besoin (au 1er lancement, tous les compteurs affichent 0000) :
#     - les tambours ne s'alignent pas dans la barre (partent vers la gauche, en haut...) :
#       change Espacement (mets -56 au lieu de 56) ou AxeTambour ;
#     - les chiffres tournent mal (pas droits) : change AxeTambour ; ils comptent a l'envers : SensInverse.

axe_tambour := enum{X, Y, Z}

compteur_rebirths := class<concrete>:
    @editable Tambours : []creative_prop = array{}

classement_device := class(creative_device):

    @editable Avions : []avion_tycoon = array{}
    @editable Places : []player_reference_device = array{}
    @editable Compteurs : []compteur_rebirths = array{}
    # (facultatif) des billboards pour un texte en plus ; laisse vide si tu n'en veux pas.
    @editable Scores : []billboard_device = array{}
    # Mise a jour toutes les ... secondes.
    @editable Intervalle : float = 3.0
    # Axe de rotation des tambours (= l'axe le long duquel ils sont alignes).
    @editable AxeTambour : axe_tambour = axe_tambour.X
    # Ecart entre deux tambours, en cm (negatif si ils s'alignent du mauvais cote).
    @editable Espacement : float = -56.0
    @editable SensInverse : logic = false

    # position de repos de chaque tambour (chiffre 0 vers l'avant), et chiffre affiche
    var Repos : [][]transform = array{}
    var Affiche : [][]int = array{}

    OnBegin<override>()<suspends>:void =
        InstallerTambours()
        loop:
            MettreAJour()
            Sleep(Intervalle)

    # Le 1er tambour de chaque compteur sert de repere : les autres sont alignes a cote de lui.
    InstallerTambours():void =
        set Repos = for (C : Compteurs):
            if (Premier := C.Tambours[0]):
                T0 := Premier.GetTransform()
                Axe := AxeMonde(T0.Rotation)
                for (I -> Tb : C.Tambours):
                    T := transform{Translation := T0.Translation + Axe * (Espacement * 1.0 * I), Rotation := T0.Rotation, Scale := T0.Scale}
                    if (Tb.TeleportTo[T]) {}
                    T
            else:
                array{}
        set Affiche = for (C : Compteurs) { for (Tb : C.Tambours) { 0 } }

    AxeMonde(R:rotation):vector3 =
        case (AxeTambour):
            axe_tambour.X => R.GetLocalForward()
            axe_tambour.Y => R.GetLocalRight()
            axe_tambour.Z => R.GetLocalUp()

    Tourner(R:rotation, Chiffre:int):rotation =
        A := DegreesToRadians(36.0 * Chiffre * (if (SensInverse?) then -1.0 else 1.0))
        case (AxeTambour):
            axe_tambour.X => R.ApplyRoll(A)
            axe_tambour.Y => R.ApplyPitch(A)
            axe_tambour.Z => R.ApplyYaw(A)

    # Ecrit Valeur (0..9999) sur le compteur N, en faisant rouler les tambours qui changent.
    AfficherCompteur(N:int, Valeur:int):void =
        if (C := Compteurs[N], Positions := Repos[N]):
            Nb := C.Tambours.Length
            for (I -> Tb : C.Tambours, T := Positions[I]):
                # chiffre de la position I (de gauche a droite)
                var Puissance : int = 1
                for (K := 1..(Nb - 1 - I)) { set Puissance *= 10 }
                if (Q := Quotient[Valeur, Puissance], D := Mod[Q, 10]):
                    if (Ancien := Affiche[N][I], Ancien <> D):
                        if (set Affiche[N][I] = D) {}
                        spawn{ Rouler(Tb, T, D) }

    Rouler(Tb:creative_prop, T:transform, Chiffre:int)<suspends>:void =
        Tb.MoveTo(transform{Translation := T.Translation, Rotation := Tourner(T.Rotation, Chiffre), Scale := T.Scale}, 0.7)

    # A passe devant B ?
    Devant(A:avion_tycoon, B:avion_tycoon)<decides><transacts>:void =
        A.Rebirths > B.Rebirths or (A.Rebirths = B.Rebirths and A.Argent > B.Argent)

    MettreAJour():void =
        # tri par insertion des avions qui ont un proprio
        var Trie : []avion_tycoon = array{}
        for (A : Avions, A.Proprio?):
            var Place : logic = false
            var Nouveau : []avion_tycoon = array{}
            for (B : Trie):
                if (not Place?, Devant[A, B]):
                    set Nouveau += array{A}
                    set Place = true
                set Nouveau += array{B}
            if (not Place?):
                set Nouveau += array{A}
            set Trie = Nouveau
        # affichage : personnages, compteurs, et billboards (s'il y en a)
        for (I -> Ref : Places):
            if (A := Trie[I], Joueur := A.Proprio?):
                Ref.Register(Joueur)
                AfficherCompteur(I, Min(A.Rebirths, 9999))
                if (S := Scores[I]):
                    S.SetText(Msg("{A.Rebirths} REBIRTHS"))
            else:
                Ref.Clear()
                AfficherCompteur(I, 0)
                if (S := Scores[I]):
                    S.SetText(Msg("---"))
