using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - la DAILY SPIN du lobby : chaque joueur peut tourner la roue UNE FOIS PAR JOUR.
# Les gains SUIVENT LA PROGRESSION du joueur (un debutant et un milliardaire gagnent tous les deux un vrai coup
# de pouce) :
#   5 MIN / 15 MIN / 1 HOUR : X minutes de ton revenu par seconde, d'un coup ;
#   +10%                    : 10 % de l'argent que tu as ;
#   x2 / x3                 : tes gains (billets du vol, commandes) multiplies pendant quelques minutes ;
#   REBIRTH                 : +1 rebirth gratuit ;
#   JACKPOT                 : 3 heures de revenu d'un coup.
# Le moment du dernier tour est SAUVEGARDE (meme apres avoir quitte la map).
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Support_DailySpin.glb et Roue_DailySpin.glb, Convert to Prop ;
#   - pose le support, puis la roue sur son axe (centre de la roue au bout de l'axe gris), "5 MIN" en haut ;
#   - pose un appareil "Bouton" (Button) devant la roue (texte d'interaction : SPIN) ;
#   - (facultatif) un "Message ATH" (HUD Message) pour les messages ;
#   - pose ce device, et dans ses Details : Roue, Bouton, Avions (tes avion_tycoon), Message.
#   Reglages si besoin :
#     - la roue tourne a plat ou de travers : change AxeRoue (X, Y ou Z) ;
#     - le gain ne correspond pas a la case sous la fleche : coche SensInverse ;
#     - TestSansAttente : on peut tourner autant qu'on veut (pour tester). A DECOCHER avant de publier !

daily_spin_sauvegarde := class<final><persistable>:
    DernierTour : float = 0.0

var DailySpinSauvegarde : weak_map(player, daily_spin_sauvegarde) = map{}

axe_roue := enum{X, Y, Z}
type_gain := enum{MinutesDeRevenu, PourcentArgent, Boost, Rebirth}

# Une case de la roue. Valeur : minutes (MinutesDeRevenu), pourcentage (PourcentArgent) ou multiplicateur (Boost).
case_roue := class<concrete>:
    @editable Nom : string = "5 MIN"
    @editable Type : type_gain = type_gain.MinutesDeRevenu
    @editable Valeur : float = 5.0
    # Boost seulement : duree en minutes.
    @editable DureeMinutes : float = 10.0
    @editable Chance : int = 10

daily_spin_device := class(creative_device):

    @editable Roue : creative_prop = creative_prop{}
    @editable Bouton : button_device = button_device{}
    @editable Avions : []avion_tycoon = array{}
    @editable Message : ?hud_message_device = false
    # Les 8 cases, dans l'ordre de la roue (case 0 en haut, puis sens des aiguilles d'une montre).
    @editable Cases : []case_roue = array:
        case_roue{Nom := "5 MIN", Type := type_gain.MinutesDeRevenu, Valeur := 5.0, Chance := 27}
        case_roue{Nom := "+10%", Type := type_gain.PourcentArgent, Valeur := 10.0, Chance := 18}
        case_roue{Nom := "x2 10 MIN", Type := type_gain.Boost, Valeur := 2.0, DureeMinutes := 10.0, Chance := 14}
        case_roue{Nom := "15 MIN", Type := type_gain.MinutesDeRevenu, Valeur := 15.0, Chance := 16}
        case_roue{Nom := "REBIRTH", Type := type_gain.Rebirth, Valeur := 1.0, Chance := 2}
        case_roue{Nom := "1 HOUR", Type := type_gain.MinutesDeRevenu, Valeur := 60.0, Chance := 10}
        case_roue{Nom := "x3 5 MIN", Type := type_gain.Boost, Valeur := 3.0, DureeMinutes := 5.0, Chance := 8}
        case_roue{Nom := "JACKPOT", Type := type_gain.MinutesDeRevenu, Valeur := 180.0, Chance := 5}
    # Gain minimum (pour les debutants qui ne gagnent encore presque rien).
    @editable GainMinimum : int = 1000
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

    Tirage():int =
        var Total : int = 0
        for (C : Cases) { set Total += C.Chance }
        R := GetRandomInt(1, Max(1, Total))
        var Cumul : int = 0
        var Choix : int = 0
        var Trouve : logic = false
        for (I -> C : Cases, not Trouve?):
            set Cumul += C.Chance
            if (R <= Cumul):
                set Choix = I
                set Trouve = true
        Choix

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
            N := Max(1, Cases.Length)
            Pas := 360.0 / (N * 1.0)
            K := Tirage()
            Cible := (if (V := Mod[N - K, N]) then V else 0) * Pas + GetRandomFloat(-Pas * 0.3, Pas * 0.3)
            Tours := GetRandomInt(4, 6)
            Delta := Tours * 360.0 + Mod360(Cible - Mod360(AngleActuel))
            Depart := AngleActuel
            Axe := case (AxeRoue):
                axe_roue.X => Repos.Rotation.GetLocalForward()
                axe_roue.Y => Repos.Rotation.GetLocalRight()
                axe_roue.Z => Repos.Rotation.GetLocalUp()
            Signe := if (SensInverse?) then -1.0 else 1.0
            # Rotation fluide : peu de mouvements, tous du MEME angle (120 deg, a vitesse constante chacun),
            # c'est leur duree qui s'allonge -> la roue ralentit en douceur, sans saccades.
            # Freinage "quadratique" : angle(t) = Delta * (1 - (1 - t)^2)  ->  t = 1 - Sqrt(1 - angle / Delta)
            DureeTotale := 6.0
            NbPas := Max(1, if (V := Ceil[Delta / 120.0]) then V else 1)
            var TPrec : float = 0.0
            for (J := 1..NbPas):
                Fraction := Min(1.0, (J * 120.0) / Delta)
                TJ := 1.0 - Sqrt(Max(0.0, 1.0 - Fraction))
                A := Depart + Delta * Fraction
                Rot := Repos.Rotation.RotateBy(MakeRotation(Axe, DegreesToRadians(A * Signe)))
                Roue.MoveTo(transform{Translation := Repos.Translation, Rotation := Rot, Scale := Repos.Scale}, Max(0.05, (TJ - TPrec) * DureeTotale))
                set TPrec = TJ
            set AngleActuel = Mod360(Depart + Delta)
            if (C := Cases[K]):
                for (Av : Avions, J := Av.Proprio?, J = Agent):
                    Donner(Av, C, Agent)
            set EnCours = false

    Donner(Av:avion_tycoon, C:case_roue, Agent:agent):void =
        case (C.Type):
            type_gain.MinutesDeRevenu =>
                Brut := Av.RevenuDeBase() * C.Valeur * 60.0
                Montant := Max(GainMinimum, if (V := Floor[Brut]) then V else 0)
                Av.Gagner(Montant, 2)
                Afficher(Agent, "{C.Nom} : +${Av.Abreger(Montant)}")
            type_gain.PourcentArgent =>
                Brut := Av.Argent * C.Valeur / 100.0
                Montant := Max(GainMinimum, if (V := Floor[Brut]) then V else 0)
                Av.Gagner(Montant, 2)
                Afficher(Agent, "{C.Nom} : +${Av.Abreger(Montant)}")
            type_gain.Boost =>
                spawn{ Av.ActiverBoost(C.Valeur, C.DureeMinutes * 60.0, C.Nom) }
                Afficher(Agent, "BOOST {C.Nom} !")
            type_gain.Rebirth =>
                Av.DonnerRebirth()
                Afficher(Agent, "+1 REBIRTH !")
