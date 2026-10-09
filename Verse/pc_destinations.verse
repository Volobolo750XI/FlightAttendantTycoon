using { /Fortnite.com/Devices }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - le PC des destinations.
#
# Le proprio interagit avec le PC -> l'écran holographique s'ouvre en plein écran :
#   - à gauche, la liste des destinations (5 visibles) ; on défile avec les deux
#     petites flèches discrètes à droite de la liste ;
#   - on clique sur une carte : si elle est achetée, elle devient le trajet actif,
#     sinon on l'achète (si on a assez d'argent) ;
#   - sur la carte : un point rouge sur chaque ville, un trajet courbé entre les deux,
#     et l'avion. Tant qu'on n'a pas décollé, l'avion attend sur la ville de départ.
#     Dès le décollage, il avance le long du trajet à la vitesse exacte du vol
#     (il arrive pile quand le vol en jeu se termine). Le vol suivant repart dans l'autre sens.
#
# Dans le Tiroir à contenu, dossier "Destinations" :
#   Dest01 ... Dest30 (les cartes), CarteMonde (la carte du monde),
#   AvionDroite et AvionGauche (l'icône d'avion).
#
# Dans l'éditeur :
#   Bouton          : un Appareil Bouton posé sur le PC (modèle invisible, texte "Open").
#   AvionTycoon     : le device avion_tycoon de cet avion (pour le proprio et l'argent).
#   BoutonDecollage : un Appareil Bouton dans le cockpit (texte "Take off").
#   Portes          : les portes passagers (devices porte_passager) qui doivent être fermées
#                     pour décoller. Elles restent verrouillées pendant le vol.
#   MessageHUD      : (facultatif) un Appareil Message HUD pour "CLOSE ALL DOORS".
#   Les réglages Carte... servent à caler les points sur l'image de la carte.

destination := class:
    Ville1:string
    Ville2:string
    Prix:int
    Multiplicateur:float
    MultiTexte:string
    VraiVol:string
    DureeMinutes:float
    # Position des 2 villes dans l'image CarteMonde (0..1), calée au pixel près.
    U1:float
    V1:float
    U2:float
    V2:float
    Carte:texture

# Un bouton de la liste : il retient quelle destination il représente.
bouton_destination := class:
    Index:int
    Ordinateur:pc_destinations
    Clique(Clic:widget_message):void = Ordinateur.ChoisirDestination(Index)

pc_destinations := class(creative_device):
    @editable Bouton:button_device = button_device{}
    @editable AvionTycoon:avion_tycoon = avion_tycoon{}
    @editable BoutonDecollage:button_device = button_device{}
    @editable Portes:[]porte_passager = array{}
    @editable MessageHUD:hud_message_device = hud_message_device{}

    # Taille (pixels) de l'image de la carte à l'écran. L'écran fait 1920 x 1080 :
    # avec 1960, la liste + la carte prennent toute la largeur.
    @editable TailleCarte:float = 1960.0
    # Où est le cadre de la carte du monde dans l'image (0 = bord gauche/haut, 1 = droite/bas).
    @editable CarteGauche:float = 0.283
    @editable CarteDroite:float = 0.974
    @editable CarteHaut:float = 0.254
    @editable CarteBas:float = 0.746
    # Où est le panneau de la liste dans l'image.
    @editable ListeGauche:float = 0.036
    @editable ListeDroite:float = 0.270
    @editable ListeHaut:float = 0.270
    @editable ListeBas:float = 0.730
    # Haut et bas du cadre de la liste (les flèches se mettent entre le cadre et les cartes).
    @editable ListeCadreHaut:float = 0.260
    @editable ListeCadreBas:float = 0.7425
    # Boutons cachés derrière les cartes (invisibles). Si les clics ne marchent pas, décoche.
    @editable BoutonsDerriere:logic = true

    ListeDestinations:[]destination = array:
        destination{Ville1 := "TIRANA", Ville2 := "MINSK", Prix := 0, Multiplicateur := 1.0, MultiTexte := "x1", VraiVol := "2h30", DureeMinutes := 11.0, U1 := 0.6496, V1 := 0.4427, U2 := 0.6654, V2 := 0.4078, Carte := Destinations.Dest01}
        destination{Ville1 := "LAGOS", Ville2 := "DAKAR", Prix := 150, Multiplicateur := 1.3, MultiTexte := "x1.3", VraiVol := "3h30", DureeMinutes := 12.5, U1 := 0.6161, V1 := 0.5240, U2 := 0.5737, V2 := 0.5059, Carte := Destinations.Dest02}
        destination{Ville1 := "LIMA", Ville2 := "ASUNCION", Prix := 400, Multiplicateur := 1.6, MultiTexte := "x1.6", VraiVol := "3h00", DureeMinutes := 12.0, U1 := 0.4524, V1 := 0.5646, U2 := 0.4920, V2 := 0.5945, Carte := Destinations.Dest03}
        destination{Ville1 := "DHAKA", Ville2 := "KATHMANDU", Prix := 900, Multiplicateur := 2.0, MultiTexte := "x2", VraiVol := "1h15", DureeMinutes := 10.0, U1 := 0.7934, V1 := 0.4854, U2 := 0.7830, V2 := 0.4763, Carte := Destinations.Dest04}
        destination{Ville1 := "ALMATY", Ville2 := "BAKU", Prix := 1800, Multiplicateur := 2.5, MultiTexte := "x2.5", VraiVol := "3h00", DureeMinutes := 12.0, U1 := 0.7659, V1 := 0.4377, U2 := 0.7108, V2 := 0.4451, Carte := Destinations.Dest05}
        destination{Ville1 := "MANILA", Ville2 := "HANOI", Prix := 4000, Multiplicateur := 3.0, MultiTexte := "x3", VraiVol := "2h50", DureeMinutes := 11.5, U1 := 0.8557, V1 := 0.5062, U2 := 0.8249, V2 := 0.4917, Carte := Destinations.Dest06}
        destination{Ville1 := "NAIROBI", Ville2 := "JOHANNESBURG", Prix := 8000, Multiplicateur := 4.0, MultiTexte := "x4", VraiVol := "4h00", DureeMinutes := 13.5, U1 := 0.6843, V1 := 0.5411, U2 := 0.6664, V2 := 0.5967, Carte := Destinations.Dest07}
        destination{Ville1 := "BUCHAREST", Ville2 := "DUBLIN", Prix := 15000, Multiplicateur := 5.0, MultiTexte := "x5", VraiVol := "3h40", DureeMinutes := 13.0, U1 := 0.6624, V1 := 0.4345, U2 := 0.5965, V2 := 0.4094, Carte := Destinations.Dest08}
        destination{Ville1 := "PANAMA CITY", Ville2 := "HAVANA", Prix := 25000, Multiplicateur := 6.0, MultiTexte := "x6", VraiVol := "2h45", DureeMinutes := 11.5, U1 := 0.4473, V1 := 0.5186, U2 := 0.4415, V2 := 0.4870, Carte := Destinations.Dest09}
        destination{Ville1 := "CASABLANCA", Ville2 := "ISTANBUL", Prix := 50000, Multiplicateur := 8.0, MultiTexte := "x8", VraiVol := "4h00", DureeMinutes := 13.5, U1 := 0.5938, V1 := 0.4622, U2 := 0.6683, V2 := 0.4435, Carte := Destinations.Dest10}
        destination{Ville1 := "DELHI", Ville2 := "BANGKOK", Prix := 90000, Multiplicateur := 10.0, MultiTexte := "x10", VraiVol := "4h15", DureeMinutes := 14.0, U1 := 0.7665, V1 := 0.4742, U2 := 0.8140, V2 := 0.5081, Carte := Destinations.Dest11}
        destination{Ville1 := "CAIRO", Ville2 := "ROME", Prix := 160000, Multiplicateur := 13.0, MultiTexte := "x13", VraiVol := "3h30", DureeMinutes := 12.5, U1 := 0.6729, V1 := 0.4708, U2 := 0.6347, V2 := 0.4412, Carte := Destinations.Dest12}
        destination{Ville1 := "MONTREAL", Ville2 := "CANCUN", Prix := 280000, Multiplicateur := 16.0, MultiTexte := "x16", VraiVol := "4h45", DureeMinutes := 14.5, U1 := 0.4594, V1 := 0.4316, U2 := 0.4324, V2 := 0.4914, Carte := Destinations.Dest13}
        destination{Ville1 := "BUENOS AIRES", Ville2 := "LIMA", Prix := 480000, Multiplicateur := 20.0, MultiTexte := "x20", VraiVol := "4h00", DureeMinutes := 13.5, U1 := 0.4904, V1 := 0.6168, U2 := 0.4524, V2 := 0.5646, Carte := Destinations.Dest14}
        destination{Ville1 := "SEOUL", Ville2 := "BALI", Prix := 800000, Multiplicateur := 25.0, MultiTexte := "x25", VraiVol := "7h00", DureeMinutes := 18.0, U1 := 0.8679, V1 := 0.4523, U2 := 0.8437, V2 := 0.5565, Carte := Destinations.Dest15}
        destination{Ville1 := "LONDON", Ville2 := "NEW YORK", Prix := 1400000, Multiplicateur := 32.0, MultiTexte := "x32", VraiVol := "8h00", DureeMinutes := 19.5, U1 := 0.6090, V1 := 0.4148, U2 := 0.4585, V2 := 0.4443, Carte := Destinations.Dest16}
        destination{Ville1 := "LISBON", Ville2 := "RIO DE JANEIRO", Prix := 2400000, Multiplicateur := 40.0, MultiTexte := "x40", VraiVol := "9h45", DureeMinutes := 22.0, U1 := 0.5906, V1 := 0.4494, U2 := 0.5213, V2 := 0.5891, Carte := Destinations.Dest17}
        destination{Ville1 := "JOHANNESBURG", Ville2 := "SYDNEY", Prix := 4000000, Multiplicateur := 50.0, MultiTexte := "x50", VraiVol := "11h00", DureeMinutes := 24.0, U1 := 0.6664, V1 := 0.5967, U2 := 0.9172, V2 := 0.6150, Carte := Destinations.Dest18}
        destination{Ville1 := "MADRID", Ville2 := "MEXICO CITY", Prix := 7000000, Multiplicateur := 65.0, MultiTexte := "x65", VraiVol := "12h00", DureeMinutes := 25.5, U1 := 0.6017, V1 := 0.4451, U2 := 0.4074, V2 := 0.4954, Carte := Destinations.Dest19}
        destination{Ville1 := "ISTANBUL", Ville2 := "BANGKOK", Prix := 12000000, Multiplicateur := 80.0, MultiTexte := "x80", VraiVol := "9h45", DureeMinutes := 22.0, U1 := 0.6683, V1 := 0.4435, U2 := 0.8140, V2 := 0.5081, Carte := Destinations.Dest20}
        destination{Ville1 := "ROME", Ville2 := "LOS ANGELES", Prix := 20000000, Multiplicateur := 100.0, MultiTexte := "x100", VraiVol := "13h00", DureeMinutes := 27.0, U1 := 0.6347, V1 := 0.4412, U2 := 0.3684, V2 := 0.4611, Carte := Destinations.Dest21}
        destination{Ville1 := "ZURICH", Ville2 := "SINGAPORE", Prix := 35000000, Multiplicateur := 130.0, MultiTexte := "x130", VraiVol := "12h30", DureeMinutes := 26.0, U1 := 0.6267, V1 := 0.4265, U2 := 0.8207, V2 := 0.5353, Carte := Destinations.Dest22}
        destination{Ville1 := "VANCOUVER", Ville2 := "HONG KONG", Prix := 60000000, Multiplicateur := 160.0, MultiTexte := "x160", VraiVol := "13h00", DureeMinutes := 27.0, U1 := 0.3585, V1 := 0.4212, U2 := 0.8418, V2 := 0.4888, Carte := Destinations.Dest23}
        destination{Ville1 := "MILAN", Ville2 := "TOKYO", Prix := 100000000, Multiplicateur := 200.0, MultiTexte := "x200", VraiVol := "13h30", DureeMinutes := 27.5, U1 := 0.6280, V1 := 0.4318, U2 := 0.8938, V2 := 0.4570, Carte := Destinations.Dest24}
        destination{Ville1 := "NEW YORK", Ville2 := "SYDNEY", Prix := 170000000, Multiplicateur := 250.0, MultiTexte := "x250", VraiVol := "21h00", DureeMinutes := 39.0, U1 := 0.4585, V1 := 0.4443, U2 := 0.9172, V2 := 0.6150, Carte := Destinations.Dest25}
        destination{Ville1 := "PARIS", Ville2 := "DUBAI", Prix := 300000000, Multiplicateur := 320.0, MultiTexte := "x320", VraiVol := "6h45", DureeMinutes := 17.5, U1 := 0.6141, V1 := 0.4224, U2 := 0.7218, V2 := 0.4822, Carte := Destinations.Dest26}
        destination{Ville1 := "DOHA", Ville2 := "MALE", Prix := 500000000, Multiplicateur := 400.0, MultiTexte := "x400", VraiVol := "4h30", DureeMinutes := 14.0, U1 := 0.7142, V1 := 0.4819, U2 := 0.7590, V2 := 0.5291, Carte := Destinations.Dest27}
        destination{Ville1 := "GENEVA", Ville2 := "MAHE", Prix := 850000000, Multiplicateur := 500.0, MultiTexte := "x500", VraiVol := "10h00", DureeMinutes := 22.5, U1 := 0.6218, V1 := 0.4297, U2 := 0.7223, V2 := 0.5485, Carte := Destinations.Dest28}
        destination{Ville1 := "LOS ANGELES", Ville2 := "BORA BORA", Prix := 1400000000, Multiplicateur := 650.0, MultiTexte := "x650", VraiVol := "8h30", DureeMinutes := 20.0, U1 := 0.3684, V1 := 0.4611, U2 := 0.3002, V2 := 0.5745, Carte := Destinations.Dest29}
        destination{Ville1 := "MONACO", Ville2 := "TAHITI", Prix := 2500000000, Multiplicateur := 800.0, MultiTexte := "x800", VraiVol := "22h00", DureeMinutes := 40.0, U1 := 0.6244, V1 := 0.4364, U2 := 0.3049, V2 := 0.5771, Carte := Destinations.Dest30}

    NbVisibles:int = 5
    # Partie visible d'une carte dans son image 2048 x 2048 (le reste est transparent).
    CarteLargeurVisible:float = 0.9502
    CarteHauteurVisible:float = 0.254

    var Achetees:[]logic = array{}
    # -1 = aucun trajet choisi : rien sur la carte tant qu'on n'a pas choisi une destination.
    var Active:int = -1
    var Debut:int = 0
    var MessageErreur:string = ""
    var NumeroMessage:int = 0
    var Ecran:?canvas = false
    # Ce qui change sur l'écran (on le remplace sans refermer l'écran : pas de saut de souris).
    var Dynamiques:[]widget = array{}
    # Destination en attente de confirmation d'achat (-1 = aucune).
    var Confirmation:int = -1
    var EcranJoueur:?player = false
    var NumeroAnimation:int = 0

    # Vol : DebutVol < 0 = l'avion est au sol.
    var DebutVol:float = -1.0
    var DureeVol:float = 600.0
    # false = Ville1 -> Ville2, true = retour Ville2 -> Ville1.
    var Retour:logic = false

    OnBegin<override>()<suspends>:void =
        # la première destination (FREE) est déjà à nous
        set Achetees = for (I := 0..ListeDestinations.Length - 1) { if (I = 0) then true else false }
        spawn{AttendreDecollage()}
        loop:
            Joueur := Bouton.InteractedWithEvent.Await()
            if (EstProprio[Joueur], P := player[Joueur]):
                Ouvrir(P)

    EstProprio(Joueur:agent)<transacts><decides>:void =
        Proprio := AvionTycoon.Proprio?
        Proprio = Joueur

    # ---------- Vol ----------
    EnVol()<transacts><decides>:void = DebutVol >= 0.0

    AttendreDecollage()<suspends>:void =
        loop:
            Joueur := BoutonDecollage.InteractedWithEvent.Await()
            if (EstProprio[Joueur]):
                Decoller(Joueur)

    Decoller(Joueur:agent):void =
        PortesOuvertes := for (Porte : Portes, Porte.Ouverte?) { Porte }
        if (not ListeDestinations[Active]):
            MessageHUD.SetText(Msg("CHOOSE A DESTINATION ON THE PC FIRST"))
            MessageHUD.Show(Joueur)
        else if (EnVol[]):
            MessageHUD.SetText(Msg("ALREADY FLYING"))
            MessageHUD.Show(Joueur)
        else if (PortesOuvertes.Length > 0):
            MessageHUD.SetText(Msg("CLOSE ALL DOORS BEFORE TAKE OFF"))
            MessageHUD.Show(Joueur)
        else:
            for (Porte : Portes) { Porte.Verrouiller(true) }
            Decollage()

    Decollage():void =
        set DureeVol = DureeVolActive()
        set DebutVol = GetSimulationElapsedTime()
        spawn{Voler()}
        Afficher()

    Voler()<suspends>:void =
        Sleep(DureeVol)
        set DebutVol = -1.0
        # l'avion est arrivé : le prochain vol repart dans l'autre sens
        set Retour = if (Retour?) then false else true
        for (Porte : Portes) { Porte.Verrouiller(false) }
        Afficher()

    # Avancement du vol entre 0 (départ) et 1 (arrivée).
    Progression():float =
        if (EnVol[], DureeVol > 0.0):
            Max(0.0, Min(1.0, (GetSimulationElapsedTime() - DebutVol) / DureeVol))
        else:
            0.0

    # ---------- Ouverture / fermeture ----------
    Ouvrir(P:player):void =
        Fermer()
        set EcranJoueur = option{P}
        Afficher()

    Fermer():void =
        set NumeroAnimation += 1
        if (P := EcranJoueur?, UI := GetPlayerUI[P], C := Ecran?):
            UI.RemoveWidget(C)
        set Ecran = false
        set Dynamiques = array{}
        set Confirmation = -1

    FermerClique(Clic:widget_message):void =
        Fermer()
        set EcranJoueur = false

    Monter(Clic:widget_message):void =
        set Debut = Max(Debut - 1, 0)
        Afficher()

    Descendre(Clic:widget_message):void =
        set Debut = Min(Debut + 1, ListeDestinations.Length - NbVisibles)
        Afficher()

    # ---------- Achat / choix d'une destination ----------
    ChoisirDestination(Index:int):void =
        if (D := ListeDestinations[Index]):
            if (Achetees[Index]?):
                set Confirmation = -1
                # (si c'est déjà le trajet actif, rien à faire)
                if (Index = Active):
                    Afficher()
                else:
                    if (EnVol[]):
                        AfficherErreur("WAIT FOR LANDING")
                    else:
                        set Active = Index
                        set Retour = false
                        set MessageErreur = ""
                        Afficher()
            else:
                # pas encore achetée : on demande confirmation
                set Confirmation = Index
                set MessageErreur = ""
                Afficher()

    ConfirmerAchat(Clic:widget_message):void =
        Index := Confirmation
        set Confirmation = -1
        if (D := ListeDestinations[Index]):
            if (AvionTycoon.Argent >= D.Prix):
                set AvionTycoon.Argent -= D.Prix
                AvionTycoon.MettreAJourUI()
                if (set Achetees[Index] = true) {}
                # pendant un vol, on achète mais le trajet change seulement à l'atterrissage
                if (not EnVol[]):
                    set Active = Index
                    set Retour = false
                set MessageErreur = ""
                Afficher()
            else:
                AfficherErreur("NOT ENOUGH MONEY")

    AnnulerAchat(Clic:widget_message):void =
        set Confirmation = -1
        Afficher()

    # Message rouge sur la carte, qui disparaît tout seul après 2 secondes.
    AfficherErreur(Texte:string):void =
        set MessageErreur = Texte
        set NumeroMessage += 1
        Afficher()
        spawn{EffacerErreur(NumeroMessage)}

    EffacerErreur(Numero:int)<suspends>:void =
        Sleep(2.0)
        if (Numero = NumeroMessage):
            set MessageErreur = ""
            Afficher()

    # Multiplicateur et durée du trajet actif (pour la suite : revenu et vol).
    MultiplicateurActif():float = if (D := ListeDestinations[Active]) then D.Multiplicateur else 1.0
    DureeVolActive():float = if (D := ListeDestinations[Active]) then D.DureeMinutes * 60.0 else 600.0

    # ---------- Construction de l'écran ----------
    # L'image est centrée sur le cadre (liste + carte), pas sur le milieu de l'image.
    CentreU():float = (ListeGauche + CarteDroite) / 2.0
    CentreV():float = (CarteHaut + CarteBas) / 2.0

    Place(W:widget, U:float, V:float, Largeur:float, Hauteur:float):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.5}, Maximum := vector2{X := 0.5, Y := 0.5}}
            Alignment := vector2{X := 0.5, Y := 0.5}
            Offsets := margin{Left := (U - CentreU()) * TailleCarte, Top := (V - CentreV()) * TailleCarte, Right := Largeur, Bottom := Hauteur}
            SizeToContent := false
            Widget := W

    PleinEcran(W:widget):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.0}, Maximum := vector2{X := 1.0, Y := 1.0}}
            Offsets := margin{Left := 0.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
            SizeToContent := false
            Widget := W

    # Point de la courbe (Bézier) entre A et B, bombée vers le haut comme une route aérienne.
    Courbe(A:vector2, B:vector2, T:float):vector2 =
        Dist := Sqrt((B.X - A.X) * (B.X - A.X) + (B.Y - A.Y) * (B.Y - A.Y))
        C := vector2{X := (A.X + B.X) / 2.0, Y := (A.Y + B.Y) / 2.0 - Dist * 0.3}
        U := 1.0 - T
        vector2:
            X := U * U * A.X + 2.0 * U * T * C.X + T * T * B.X
            Y := U * U * A.Y + 2.0 * U * T * C.Y + T * T * B.Y

    # Icône cliquable dessinée avec des petits carrés bleus (aucune image à importer),
    # avec son bouton caché derrière. Forme : 0 = flèche haut, 1 = flèche bas, 2 = croix.
    IconeCliquable(U:float, V:float, Forme:int, BoutonIcone:button_quiet):[]canvas_slot =
        SlotBouton := Place(BoutonIcone, U, V, 50.0, 44.0)
        Cache := Place(color_block{DefaultColor := MakeColorFromHex("1E313C"), DefaultOpacity := 1.0}, U, V, 50.0, 44.0)
        Dessin := for (K := -7..7, Point := PointIcone(Forme, K)):
            Place(color_block{DefaultColor := MakeColorFromHex("5ADCFF"), DefaultOpacity := 1.0}, U + Point.X / TailleCarte, V + Point.Y / TailleCarte, 5.0, 5.0)
        Dessin2 := for (K := -7..7, Forme = 2, Point := PointIcone(3, K)):
            Place(color_block{DefaultColor := MakeColorFromHex("5ADCFF"), DefaultOpacity := 1.0}, U + Point.X / TailleCarte, V + Point.Y / TailleCarte, 5.0, 5.0)
        if (BoutonsDerriere?) then array{SlotBouton, Cache} + Dessin + Dessin2 else Dessin + Dessin2 + array{SlotBouton}

    # Position (pixels) du K-ième carré de la forme.
    PointIcone(Forme:int, K:int):vector2 =
        Decalage := if (K < 0) then -K else K
        if (Forme = 0) then vector2{X := K * 2.5, Y := Decalage * 1.8 - 6.0}
        else if (Forme = 1) then vector2{X := K * 2.5, Y := 6.0 - Decalage * 1.8}
        else if (Forme = 2) then vector2{X := K * 1.6, Y := K * 1.6}
        else vector2{X := K * 1.6, Y := -K * 1.6}

    Vignette(T:texture, Taille:float):texture_block =
        texture_block{DefaultImage := T, DefaultDesiredSize := vector2{X := Taille, Y := Taille}}

    Afficher():void =
        if (P := EcranJoueur?, UI := GetPlayerUI[P]):
            # l'écran (fond sombre + carte du monde) n'est créé qu'une fois à l'ouverture
            var Toile:canvas = canvas{}
            if (C := Ecran?):
                set Toile = C
            else:
                Fond := PleinEcran(color_block{DefaultColor := NamedColors.Black, DefaultOpacity := 0.85})
                Monde := Place(Vignette(Destinations.CarteMonde, TailleCarte), 0.5, 0.5, TailleCarte, TailleCarte)
                Base := canvas{Slots := array{Fond, Monde}}
                UI.AddWidget(Base, player_ui_slot{InputMode := ui_input_mode.All})
                set Ecran = option{Base}
                set Toile = Base
            # on enlève seulement ce qui change
            for (W : Dynamiques) { Toile.RemoveWidget(W) }
            set NumeroAnimation += 1
            var Slots:[]canvas_slot = array{}

            # liste des destinations (5 visibles)
            TailleImageCarte := (ListeDroite - ListeGauche) * TailleCarte
            LargeurVisible := TailleImageCarte * CarteLargeurVisible
            HauteurVisible := TailleImageCarte * CarteHauteurVisible
            Pas := (ListeBas - ListeHaut) / (NbVisibles * 1.0)
            UListe := (ListeGauche + ListeDroite) / 2.0
            for (Ligne := 0..NbVisibles - 1, Index := Debut + Ligne, D := ListeDestinations[Index]):
                V := ListeHaut + Pas * (Ligne * 1.0 + 0.5)
                # bouton exactement de la taille de la carte, caché derrière elle
                BoutonCarte := button_quiet{DefaultText := Msg("")}
                Gestion := bouton_destination{Index := Index, Ordinateur := Self}
                BoutonCarte.OnClick().Subscribe(Gestion.Clique)
                SlotBouton := Place(BoutonCarte, UListe, V, LargeurVisible, HauteurVisible)
                if (BoutonsDerriere?) { set Slots += array{SlotBouton} }
                set Slots += array{Place(Vignette(D.Carte, TailleImageCarte), UListe, V, TailleImageCarte, TailleImageCarte)}
                if (not Achetees[Index]?):
                    set Slots += array{Place(color_block{DefaultColor := NamedColors.Black, DefaultOpacity := 0.5}, UListe, V, LargeurVisible, HauteurVisible)}
                if (Index = Active):
                    set Slots += array{Place(color_block{DefaultColor := NamedColors.Lime, DefaultOpacity := 0.9}, UListe - LargeurVisible / TailleCarte / 2.0 + 6.0 / TailleCarte, V, 4.0, HauteurVisible * 0.7)}
                if (not BoutonsDerriere?) { set Slots += array{SlotBouton} }

            # défilement : une flèche centrée dans l'espace au-dessus de la 1re carte,
            # une autre dans l'espace sous la dernière carte
            DemiCarte := HauteurVisible / TailleCarte / 2.0
            VHaut := (ListeCadreHaut + ListeHaut + Pas * 0.5 - DemiCarte) / 2.0
            VBas := (ListeCadreBas + ListeBas - Pas * 0.5 + DemiCarte) / 2.0
            DernierDebut := ListeDestinations.Length - NbVisibles
            if (Debut > 0):
                Haut := button_quiet{DefaultText := Msg("")}
                Haut.OnClick().Subscribe(Monter)
                set Slots += IconeCliquable(UListe, VHaut, 0, Haut)
            if (Debut < DernierDebut):
                Bas := button_quiet{DefaultText := Msg("")}
                Bas.OnClick().Subscribe(Descendre)
                set Slots += IconeCliquable(UListe, VBas, 1, Bas)

            # fermeture
            Croix := button_quiet{DefaultText := Msg("")}
            Croix.OnClick().Subscribe(FermerClique)
            set Slots += IconeCliquable(CarteDroite - 0.02, CarteHaut + 0.025, 2, Croix)

            # trajet actif : points rouges, courbe, avion
            var IconeVol:?texture_block = false
            var Depart:vector2 = vector2{}
            var Arrivee:vector2 = vector2{}
            if (D := ListeDestinations[Active]):
                A := vector2{X := D.U1, Y := D.V1}
                B := vector2{X := D.U2, Y := D.V2}
                set Depart = if (Retour?) then B else A
                set Arrivee = if (Retour?) then A else B
                for (I := 0..39):
                    Pt := Courbe(A, B, (I * 1.0 + 0.5) / 40.0)
                    set Slots += array{Place(color_block{DefaultColor := MakeColorFromHex("5ADCFF"), DefaultOpacity := 0.85}, Pt.X, Pt.Y, 4.0, 4.0)}
                for (Ville : array{A, B}):
                    set Slots += array{Place(color_block{DefaultColor := NamedColors.Red, DefaultOpacity := 0.35}, Ville.X, Ville.Y, 26.0, 26.0)}
                    set Slots += array{Place(color_block{DefaultColor := NamedColors.Red}, Ville.X, Ville.Y, 12.0, 12.0)}
                Icone := if (Arrivee.X >= Depart.X) then Destinations.AvionDroite else Destinations.AvionGauche
                ImageAvion := Vignette(Icone, 44.0)
                PosAvion := Courbe(Depart, Arrivee, Progression())
                set Slots += array{Place(ImageAvion, PosAvion.X, PosAvion.Y, 44.0, 44.0)}
                set IconeVol = option{ImageAvion}
            if (MessageErreur <> ""):
                Erreur := text_block{DefaultText := Msg(MessageErreur), DefaultTextColor := NamedColors.Red, DefaultJustification := text_justification.Center}
                set Slots += array{Place(Erreur, (CarteGauche + CarteDroite) / 2.0, CarteHaut + 0.03, 700.0, 40.0)}

            # fenêtre de confirmation d'achat, au milieu de la carte
            if (D := ListeDestinations[Confirmation]):
                UC := (CarteGauche + CarteDroite) / 2.0
                VC := (CarteHaut + CarteBas) / 2.0
                PrixTexte := if (D.Prix = 0) then "FREE" else "{AvionTycoon.Abreger(D.Prix)} $"
                set Slots += array{Place(color_block{DefaultColor := MakeColorFromHex("5ADCFF"), DefaultOpacity := 0.9}, UC, VC, 624.0, 254.0)}
                set Slots += array{Place(color_block{DefaultColor := MakeColorFromHex("0B1620"), DefaultOpacity := 1.0}, UC, VC, 620.0, 250.0)}
                Titre := text_block{DefaultText := Msg("BUY THIS ROUTE?"), DefaultTextColor := MakeColorFromHex("5ADCFF"), DefaultJustification := text_justification.Center}
                Trajet := text_block{DefaultText := Msg("{D.Ville1}  <->  {D.Ville2}"), DefaultTextColor := NamedColors.White, DefaultJustification := text_justification.Center}
                TextePrix := text_block{DefaultText := Msg("{PrixTexte}     INCOME {D.MultiTexte}"), DefaultTextColor := NamedColors.Lime, DefaultJustification := text_justification.Center}
                set Slots += array{Place(Titre, UC, VC - 85.0 / TailleCarte, 600.0, 40.0)}
                set Slots += array{Place(Trajet, UC, VC - 35.0 / TailleCarte, 600.0, 40.0)}
                set Slots += array{Place(TextePrix, UC, VC + 10.0 / TailleCarte, 600.0, 40.0)}
                Oui := button_loud{DefaultText := Msg("BUY")}
                Oui.OnClick().Subscribe(ConfirmerAchat)
                Non := button_quiet{DefaultText := Msg("CANCEL")}
                Non.OnClick().Subscribe(AnnulerAchat)
                set Slots += array{Place(Oui, UC - 110.0 / TailleCarte, VC + 80.0 / TailleCarte, 190.0, 56.0)}
                set Slots += array{Place(Non, UC + 110.0 / TailleCarte, VC + 80.0 / TailleCarte, 190.0, 56.0)}

            for (S : Slots) { Toile.AddWidget(S) }
            set Dynamiques = for (S : Slots) { S.Widget }
            if (EnVol[], ImageAvion := IconeVol?):
                spawn{AnimerAvion(NumeroAnimation, Toile, ImageAvion, Depart, Arrivee)}

    # Pendant le vol, l'avion est replacé 10 fois par seconde à sa vraie position.
    AnimerAvion(Numero:int, Toile:canvas, Img:texture_block, Depart:vector2, Arrivee:vector2)<suspends>:void =
        loop:
            Sleep(0.1)
            if (Numero <> NumeroAnimation or not EnVol[]) { break }
            Pt := Courbe(Depart, Arrivee, Progression())
            Toile.RemoveWidget(Img)
            Toile.AddWidget(Place(Img, Pt.X, Pt.Y, 44.0, 44.0))
