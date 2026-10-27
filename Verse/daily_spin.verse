using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }
using { /Fortnite.com/UI }
using { /Verse.org/Colors }

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
    # (facultatif) un Message ATH en plus du bandeau a l'ecran
    @editable Message : ?hud_message_device = false
    # Le bandeau apparait quand le joueur VISE la roue, a moins de DistanceBandeau (cm).
    @editable DistanceBandeau : float = 450.0
    # Taille de la zone a viser autour du centre de la roue (cm) : ~ le rayon de la roue.
    @editable RayonVisee : float = 240.0
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
    @editable GainMinimum : int = 500
    @editable AttenteHeures : float = 24.0
    @editable AxeRoue : axe_roue = axe_roue.X
    @editable SensInverse : logic = false
    # Il faut avoir termine au moins ce nombre de vols pour pouvoir tourner la roue.
    @editable VolsRequis : int = 1
    # TEST : force la case gagnante (0 = "5 MIN" en haut ... 7 = "JACKPOT"). -1 = tirage normal.
    # Sert a verifier que la roue s'arrete bien sur la case gagnee (sinon : coche SensInverse).
    @editable TestCaseForcee : int = -1
    # TEST : tours illimites. A DECOCHER avant de publier !
    @editable TestSansAttente : logic = true

    var EnCours : logic = false
    var Repos : transform = transform{}
    var AngleActuel : float = 0.0
    # bandeau a l'ecran de chaque joueur proche de la roue
    var Bandeaux : [player]canvas = map{}
    var TextesBandeau : [player]text_block = map{}
    var Annonces : [player]string = map{}
    var FinAnnonces : [player]float = map{}

    OnBegin<override>()<suspends>:void =
        set Repos = Roue.GetTransform()
        Bouton.InteractedWithEvent.Subscribe(OnBouton)
        spawn{ BoucleBandeaux() }

    OnBouton(Agent:agent):void =
        spawn{ Tourner(Agent) }

    # Message important (resultat, refus) : affiche 5 s dans le bandeau du joueur (+ Message ATH s'il y en a un).
    Afficher(Agent:agent, Texte:string):void =
        if (P := player[Agent]):
            if (set Annonces[P] = Texte, set FinAnnonces[P] = GetSecondsSinceEpoch() + 5.0) {}
            MontrerBandeau(P, Texte)
        if (M := Message?):
            M.SetText(Msg(Texte))
            M.Show(Agent)

    # ---------- bandeau a l'ecran (quand on est pres de la roue) ----------
    BoucleBandeaux()<suspends>:void =
        loop:
            Sleep(0.15)
            for (P : GetPlayspace().GetPlayers()):
                if (Perso := P.GetFortCharacter[], Vise[Perso]):
                    MontrerBandeau(P, TexteEtat(P))
                else:
                    CacherBandeau(P)

    # Le joueur est assez pres ET regarde la roue (sa ligne de visee passe a moins de RayonVisee du centre).
    Vise(Perso:fort_character)<transacts><decides>:void =
        Oeil := Perso.GetViewLocation()
        Devant := Perso.GetViewRotation().GetLocalForward()
        VersRoue := Repos.Translation - Oeil
        Distance(Oeil, Repos.Translation) < DistanceBandeau
        Profondeur := DotProduct(VersRoue, Devant)
        Profondeur > 0.0
        Ecart := VersRoue - Devant * Profondeur
        Ecart.Length() < RayonVisee

    # Ce que la roue dit a ce joueur en ce moment.
    TexteEtat(P:player):string =
        Maintenant := GetSecondsSinceEpoch()
        if (Fin := FinAnnonces[P], Maintenant < Fin, A := Annonces[P]):
            A
        else if (EnCours?):
            "SPINNING..."
        else:
            var Sien : ?avion_tycoon = false
            for (Av : Avions, J := Av.Proprio?, J = P) { set Sien = option{Av} }
            if (not Sien?):
                "DAILY SPIN : CLAIM A PLANE TO UNLOCK"
            else if (Av := Sien?, Av.VolsTermines < VolsRequis):
                "DAILY SPIN : COMPLETE {VolsRequis} FLIGHT TO UNLOCK"
            else:
                Dernier := if (S := DailySpinSauvegarde[P]) then S.DernierTour else 0.0
                Reste := AttenteHeures * 3600.0 - (Maintenant - Dernier)
                if (not TestSansAttente?, Reste > 0.0):
                    "NEXT DAILY SPIN IN {Duree(Reste)}"
                else:
                    "DAILY SPIN READY !  PRESS E TO SPIN"

    Duree(Secondes:float):string =
        H := if (V := Floor[Secondes / 3600.0]) then V else 0
        Mi := if (V := Floor[(Secondes - H * 3600.0) / 60.0]) then V else 0
        Se := if (V := Floor[Secondes - H * 3600.0 - Mi * 60.0]) then V else 0
        "{H}H {Mi}MIN {Se}S"

    MontrerBandeau(P:player, Texte:string):void =
        if (T := TextesBandeau[P]):
            T.SetText(Msg(Texte))
        else if (UI := GetPlayerUI[P]):
            T := text_block{DefaultTextColor := NamedColors.White, DefaultShadowColor := NamedColors.Black,
                            DefaultShadowOpacity := 0.9, DefaultShadowOffset := option{vector2{X := 2.0, Y := 2.0}}}
            T.SetText(Msg(Texte))
            Fond := color_block{DefaultColor := MakeColorFromHex("16203A"), DefaultOpacity := 0.88}
            Liseret := color_block{DefaultColor := MakeColorFromHex("F05CA8"), DefaultOpacity := 1.0}
            C := canvas:
                Slots := array:
                    canvas_slot:
                        Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.80}, Maximum := vector2{X := 0.5, Y := 0.80}}
                        Alignment := vector2{X := 0.5, Y := 0.5}
                        SizeToContent := true
                        Widget := overlay:
                            Slots := array:
                                overlay_slot{Widget := Liseret, HorizontalAlignment := horizontal_alignment.Fill, VerticalAlignment := vertical_alignment.Fill}
                                overlay_slot{Widget := Fond, HorizontalAlignment := horizontal_alignment.Fill, VerticalAlignment := vertical_alignment.Fill,
                                             Padding := margin{Left := 4.0, Right := 4.0, Top := 4.0, Bottom := 4.0}}
                                overlay_slot{Widget := T, HorizontalAlignment := horizontal_alignment.Center, VerticalAlignment := vertical_alignment.Center,
                                             Padding := margin{Left := 34.0, Right := 34.0, Top := 16.0, Bottom := 16.0}}
            UI.AddWidget(C)
            if (set Bandeaux[P] = C, set TextesBandeau[P] = T) {}

    CacherBandeau(P:player):void =
        if (C := Bandeaux[P], UI := GetPlayerUI[P]):
            UI.RemoveWidget(C)
        var B : [player]canvas = map{}
        for (Cle -> V : Bandeaux, Cle <> P) { if (set B[Cle] = V) {} }
        set Bandeaux = B
        var Tx : [player]text_block = map{}
        for (Cle -> V : TextesBandeau, Cle <> P) { if (set Tx[Cle] = V) {} }
        set TextesBandeau = Tx

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
            # il faut un avion et au moins VolsRequis vols termines
            var Sien : ?avion_tycoon = false
            for (Av : Avions, J := Av.Proprio?, J = Agent) { set Sien = option{Av} }
            if (not Sien?):
                Afficher(Agent, "CLAIM A PLANE FIRST !")
                return
            if (Av := Sien?, Av.VolsTermines < VolsRequis):
                Afficher(Agent, "COMPLETE {VolsRequis} FLIGHT TO SPIN !")
                return
            set EnCours = true
            if (set DailySpinSauvegarde[P] = daily_spin_sauvegarde{DernierTour := Maintenant}) {}
            N := Max(1, Cases.Length)
            Pas := 360.0 / (N * 1.0)
            K := if (TestCaseForcee >= 0, TestCaseForcee < N) then TestCaseForcee else Tirage()
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
