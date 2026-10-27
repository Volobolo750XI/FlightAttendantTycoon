using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - la DAILY SPIN du lobby : chaque joueur peut tourner la roue UNE FOIS PAR JOUR.
# La roue tourne vite puis ralentit, s'arrete sur une case, et le joueur gagne l'argent de la case
# (dans son avion_tycoon, avec le popup "+$..."). Le moment du dernier tour est SAUVEGARDE (meme apres
# avoir quitte la map), donc on ne peut pas tricher en se reconnectant.
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Support_DailySpin.glb et Roue_DailySpin.glb, Convert to Prop ;
#   - pose le support, puis la roue sur son axe (centre de la roue au bout de l'axe gris), "$500" en haut ;
#   - pose un appareil "Bouton" (Button) devant la roue (texte d'interaction : SPIN) ;
#   - (facultatif) un "Message ATH" (HUD Message) pour les messages "Reviens dans 12 h 30 min" ;
#   - pose ce device, et dans ses Details : Roue, Bouton, Avions (tes avion_tycoon), Message.
#   Reglages si besoin :
#     - la roue tourne a plat ou de travers : change AxeRoue (X, Y ou Z) ;
#     - le gain ne correspond pas a la case sous la fleche : coche SensInverse ;
#     - TestSansAttente : on peut tourner autant qu'on veut (pour tester). A DECOCHER avant de publier !

# Ce qui est sauvegarde pour chaque joueur.
daily_spin_sauvegarde := class<final><persistable>:
    DernierTour : float = 0.0

var DailySpinSauvegarde : weak_map(player, daily_spin_sauvegarde) = map{}

axe_roue := enum{X, Y, Z}

daily_spin_device := class(creative_device):

    @editable Roue : creative_prop = creative_prop{}
    @editable Bouton : button_device = button_device{}
    @editable Avions : []avion_tycoon = array{}
    @editable Message : ?hud_message_device = false
    # Gains des 8 cases, dans l'ordre de la roue (case 0 en haut, puis sens des aiguilles d'une montre).
    @editable Gains : []int = array{500, 1000, 2500, 5000, 10000, 25000, 50000, 100000}
    # Chances de chaque case (plus le nombre est grand, plus la case tombe souvent).
    @editable Chances : []int = array{30, 24, 16, 12, 8, 5, 3, 2}
    # Temps d'attente entre deux tours, en heures.
    @editable AttenteHeures : float = 24.0
    @editable AxeRoue : axe_roue = axe_roue.X
    @editable SensInverse : logic = false
    # TEST : tours illimites. A DECOCHER avant de publier !
    @editable TestSansAttente : logic = true

    var EnCours : logic = false
    var Repos : transform = transform{}
    var AngleActuel : float = 0.0

    OnBegin<override>()<suspends>:void =
        set Repos = Roue.GetTransform()
        Bouton.InteractedWithEvent.Subscribe(OnBouton)

    OnBouton(Agent:agent):void =
        spawn{ Tourner(Agent) }

    Afficher(Agent:agent, Texte:string):void =
        if (M := Message?):
            M.SetText(Msg(Texte))
            M.Show(Agent)

    # Choisit une case au hasard en tenant compte des chances.
    Tirage():int =
        var Total : int = 0
        for (C : Chances) { set Total += C }
        R := GetRandomInt(1, Max(1, Total))
        var Cumul : int = 0
        var Choix : int = 0
        var Trouve : logic = false
        for (I -> C : Chances, not Trouve?):
            set Cumul += C
            if (R <= Cumul):
                set Choix = I
                set Trouve = true
        Choix

    # x modulo 360 (pour les floats)
    Mod360(X:float):float =
        if (Q := Floor[X / 360.0]) then X - 360.0 * Q else X

    Tourner(Agent:agent)<suspends>:void =
        if (EnCours?):
            return
        if (P := player[Agent]):
            Maintenant := GetSecondsSinceEpoch()
            Dernier := if (S := DailySpinSauvegarde[P]) then S.DernierTour else 0.0
            Reste := AttenteHeures * 3600.0 - (Maintenant - Dernier)
            if (not TestSansAttente?, Reste > 0.0):
                H := if (V := Floor[Reste / 3600.0]) then V else 0
                Mi := if (V := Floor[(Reste - H * 3600.0) / 60.0]) then V else 0
                Afficher(Agent, "COME BACK IN {H}H {Mi}MIN")
                return
            set EnCours = true
            if (set DailySpinSauvegarde[P] = daily_spin_sauvegarde{DernierTour := Maintenant}) {}
            N := Max(1, Gains.Length)
            Pas := 360.0 / (N * 1.0)
            K := Tirage()
            # angle final (sens horaire vu de face) : la case K arrive sous la fleche
            Cible := (if (V := Mod[N - K, N]) then V else 0) * Pas + GetRandomFloat(-Pas * 0.3, Pas * 0.3)
            Tours := GetRandomInt(4, 6)
            Delta := Tours * 360.0 + Mod360(Cible - Mod360(AngleActuel))
            Depart := AngleActuel
            Axe := case (AxeRoue):
                axe_roue.X => Repos.Rotation.GetLocalForward()
                axe_roue.Y => Repos.Rotation.GetLocalRight()
                axe_roue.Z => Repos.Rotation.GetLocalUp()
            Signe := if (SensInverse?) then -1.0 else 1.0
            # rotation rapide puis de plus en plus lente (72 petits pas, aucun ne depasse 180 degres)
            Etapes := 72
            for (I := 1..Etapes):
                T := I * 1.0 / (Etapes * 1.0)
                E := 1.0 - (1.0 - T) * (1.0 - T) * (1.0 - T)
                A := Depart + Delta * E
                Rot := Repos.Rotation.RotateBy(MakeRotation(Axe, DegreesToRadians(A * Signe)))
                Roue.MoveTo(transform{Translation := Repos.Translation, Rotation := Rot, Scale := Repos.Scale}, 0.085)
            set AngleActuel = Mod360(Depart + Delta)
            # le gain
            if (Montant := Gains[K]):
                for (Av : Avions, J := Av.Proprio?, J = Agent):
                    Av.Gagner(Montant, 2)
                Afficher(Agent, if (K = N - 1) then "JACKPOT ! +${Montant}" else "+${Montant} !")
            set EnCours = false
