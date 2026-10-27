using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }

# Flight Attendant Tycoon - le CLASSEMENT du lobby (podium "TOP PILOTS").
#
# Toutes les quelques secondes, on classe les joueurs qui ont un avion :
#   d'abord par REBIRTHS, puis (a egalite) par ARGENT.
# Sur chaque marche du podium, un "Player Reference" montre le vrai personnage du joueur avec son
# nom, et un panneau (billboard) affiche son score. Les places vides affichent "---".
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Classement.glb (podium + panneau), Convert to Prop, pose-le dans le lobby ;
#   - sur chaque marche (1, 2, 3, 4), pose un appareil "Reference de joueur" (Player Reference) ;
#   - devant chaque marche, pose un "Panneau d'affichage" (Billboard) pour le score ;
#   - pose ce device, et dans ses Details :
#       Avions : tes devices avion_tycoon (un par parcelle) ;
#       Places : les 4 Player Reference, DANS L'ORDRE (1er, 2e, 3e, 4e) ;
#       Scores : les 4 Billboards, dans le meme ordre.

classement_device := class(creative_device):

    @editable Avions : []avion_tycoon = array{}
    @editable Places : []player_reference_device = array{}
    @editable Scores : []billboard_device = array{}
    # Mise a jour toutes les ... secondes.
    @editable Intervalle : float = 3.0

    OnBegin<override>()<suspends>:void =
        loop:
            MettreAJour()
            Sleep(Intervalle)

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
        # affichage
        for (I -> Ref : Places):
            if (A := Trie[I], Joueur := A.Proprio?):
                Ref.Register(Joueur)
                if (S := Scores[I]):
                    S.SetText(Msg("#{I + 1}   {A.Rebirths} REBIRTHS   ${A.Abreger(A.Argent)}"))
            else:
                Ref.Clear()
                if (S := Scores[I]):
                    S.SetText(Msg("#{I + 1}   ---"))
