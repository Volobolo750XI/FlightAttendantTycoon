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
#   AvionDroite, AvionGauche, FlecheHaut, FlecheBas.
#
# Dans l'éditeur :
#   Bouton          : un Appareil Bouton posé sur le PC (modèle invisible, texte "Open").
#   AvionTycoon     : le device avion_tycoon de cet avion (pour le proprio et l'argent).
#   BoutonDecollage : un Appareil Bouton dans le cockpit (texte "Take off").
#   Portes          : les portes passagers (devices porte_avion) qui doivent être fermées
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
    Lat1:float
    Lon1:float
    Lat2:float
    Lon2:float
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
    @editable Portes:[]porte_avion = array{}
    @editable MessageHUD:hud_message_device = hud_message_device{}

    # Taille (pixels) de l'image de la carte à l'écran. L'écran fait 1920 x 1080 :
    # avec 1960, la liste + la carte prennent toute la largeur.
    @editable TailleCarte:float = 1960.0
    # Où est le cadre de la carte du monde dans l'image (0 = bord gauche/haut, 1 = droite/bas).
    @editable CarteGauche:float = 0.283
    @editable CarteDroite:float = 0.974
    @editable CarteHaut:float = 0.254
    @editable CarteBas:float = 0.746
    # Latitudes du haut et du bas de la carte (longitudes : -180 à 180).
    @editable LatHaut:float = 80.0
    @editable LatBas:float = -58.0
    # Où est le panneau de la liste dans l'image.
    @editable ListeGauche:float = 0.036
    @editable ListeDroite:float = 0.270
    @editable ListeHaut:float = 0.270
    @editable ListeBas:float = 0.730

    ListeDestinations:[]destination = array:
        destination{Ville1 := "TIRANA", Ville2 := "MINSK", Prix := 0, Multiplicateur := 1.0, MultiTexte := "x1", VraiVol := "2h30", DureeMinutes := 11.0, Lat1 := 41.33, Lon1 := 19.82, Lat2 := 53.9, Lon2 := 27.57, Carte := Destinations.Dest01}
        destination{Ville1 := "LAGOS", Ville2 := "DAKAR", Prix := 150, Multiplicateur := 1.3, MultiTexte := "x1.3", VraiVol := "3h30", DureeMinutes := 12.5, Lat1 := 6.52, Lon1 := 3.38, Lat2 := 14.72, Lon2 := -17.47, Carte := Destinations.Dest02}
        destination{Ville1 := "LIMA", Ville2 := "ASUNCION", Prix := 400, Multiplicateur := 1.6, MultiTexte := "x1.6", VraiVol := "3h00", DureeMinutes := 12.0, Lat1 := -12.05, Lon1 := -77.04, Lat2 := -25.26, Lon2 := -57.58, Carte := Destinations.Dest03}
        destination{Ville1 := "DHAKA", Ville2 := "KATHMANDU", Prix := 900, Multiplicateur := 2.0, MultiTexte := "x2", VraiVol := "1h15", DureeMinutes := 10.0, Lat1 := 23.81, Lon1 := 90.41, Lat2 := 27.72, Lon2 := 85.32, Carte := Destinations.Dest04}
        destination{Ville1 := "ALMATY", Ville2 := "BAKU", Prix := 1800, Multiplicateur := 2.5, MultiTexte := "x2.5", VraiVol := "3h00", DureeMinutes := 12.0, Lat1 := 43.24, Lon1 := 76.89, Lat2 := 40.41, Lon2 := 49.87, Carte := Destinations.Dest05}
        destination{Ville1 := "MANILA", Ville2 := "HANOI", Prix := 4000, Multiplicateur := 3.0, MultiTexte := "x3", VraiVol := "2h50", DureeMinutes := 11.5, Lat1 := 14.6, Lon1 := 120.98, Lat2 := 21.03, Lon2 := 105.85, Carte := Destinations.Dest06}
        destination{Ville1 := "NAIROBI", Ville2 := "JOHANNESBURG", Prix := 8000, Multiplicateur := 4.0, MultiTexte := "x4", VraiVol := "4h00", DureeMinutes := 13.5, Lat1 := -1.29, Lon1 := 36.82, Lat2 := -26.2, Lon2 := 28.05, Carte := Destinations.Dest07}
        destination{Ville1 := "BUCHAREST", Ville2 := "DUBLIN", Prix := 15000, Multiplicateur := 5.0, MultiTexte := "x5", VraiVol := "3h40", DureeMinutes := 13.0, Lat1 := 44.43, Lon1 := 26.1, Lat2 := 53.35, Lon2 := -6.26, Carte := Destinations.Dest08}
        destination{Ville1 := "PANAMA CITY", Ville2 := "HAVANA", Prix := 25000, Multiplicateur := 6.0, MultiTexte := "x6", VraiVol := "2h45", DureeMinutes := 11.5, Lat1 := 8.98, Lon1 := -79.52, Lat2 := 23.11, Lon2 := -82.37, Carte := Destinations.Dest09}
        destination{Ville1 := "CASABLANCA", Ville2 := "ISTANBUL", Prix := 50000, Multiplicateur := 8.0, MultiTexte := "x8", VraiVol := "4h00", DureeMinutes := 13.5, Lat1 := 33.57, Lon1 := -7.59, Lat2 := 41.01, Lon2 := 28.98, Carte := Destinations.Dest10}
        destination{Ville1 := "DELHI", Ville2 := "BANGKOK", Prix := 90000, Multiplicateur := 10.0, MultiTexte := "x10", VraiVol := "4h15", DureeMinutes := 14.0, Lat1 := 28.61, Lon1 := 77.21, Lat2 := 13.76, Lon2 := 100.5, Carte := Destinations.Dest11}
        destination{Ville1 := "CAIRO", Ville2 := "ROME", Prix := 160000, Multiplicateur := 13.0, MultiTexte := "x13", VraiVol := "3h30", DureeMinutes := 12.5, Lat1 := 30.04, Lon1 := 31.24, Lat2 := 41.9, Lon2 := 12.5, Carte := Destinations.Dest12}
        destination{Ville1 := "MONTREAL", Ville2 := "CANCUN", Prix := 280000, Multiplicateur := 16.0, MultiTexte := "x16", VraiVol := "4h45", DureeMinutes := 14.5, Lat1 := 45.5, Lon1 := -73.57, Lat2 := 21.16, Lon2 := -86.85, Carte := Destinations.Dest13}
        destination{Ville1 := "BUENOS AIRES", Ville2 := "LIMA", Prix := 480000, Multiplicateur := 20.0, MultiTexte := "x20", VraiVol := "4h00", DureeMinutes := 13.5, Lat1 := -34.6, Lon1 := -58.38, Lat2 := -12.05, Lon2 := -77.04, Carte := Destinations.Dest14}
        destination{Ville1 := "SEOUL", Ville2 := "BALI", Prix := 800000, Multiplicateur := 25.0, MultiTexte := "x25", VraiVol := "7h00", DureeMinutes := 18.0, Lat1 := 37.57, Lon1 := 126.98, Lat2 := -8.34, Lon2 := 115.09, Carte := Destinations.Dest15}
        destination{Ville1 := "LONDON", Ville2 := "NEW YORK", Prix := 1400000, Multiplicateur := 32.0, MultiTexte := "x32", VraiVol := "8h00", DureeMinutes := 19.5, Lat1 := 51.51, Lon1 := -0.13, Lat2 := 40.71, Lon2 := -74.01, Carte := Destinations.Dest16}
        destination{Ville1 := "LISBON", Ville2 := "RIO DE JANEIRO", Prix := 2400000, Multiplicateur := 40.0, MultiTexte := "x40", VraiVol := "9h45", DureeMinutes := 22.0, Lat1 := 38.72, Lon1 := -9.14, Lat2 := -22.91, Lon2 := -43.17, Carte := Destinations.Dest17}
        destination{Ville1 := "JOHANNESBURG", Ville2 := "SYDNEY", Prix := 4000000, Multiplicateur := 50.0, MultiTexte := "x50", VraiVol := "11h00", DureeMinutes := 24.0, Lat1 := -26.2, Lon1 := 28.05, Lat2 := -33.87, Lon2 := 151.21, Carte := Destinations.Dest18}
        destination{Ville1 := "MADRID", Ville2 := "MEXICO CITY", Prix := 7000000, Multiplicateur := 65.0, MultiTexte := "x65", VraiVol := "12h00", DureeMinutes := 25.5, Lat1 := 40.42, Lon1 := -3.7, Lat2 := 19.43, Lon2 := -99.13, Carte := Destinations.Dest19}
        destination{Ville1 := "ISTANBUL", Ville2 := "BANGKOK", Prix := 12000000, Multiplicateur := 80.0, MultiTexte := "x80", VraiVol := "9h45", DureeMinutes := 22.0, Lat1 := 41.01, Lon1 := 28.98, Lat2 := 13.76, Lon2 := 100.5, Carte := Destinations.Dest20}
        destination{Ville1 := "ROME", Ville2 := "LOS ANGELES", Prix := 20000000, Multiplicateur := 100.0, MultiTexte := "x100", VraiVol := "13h00", DureeMinutes := 27.0, Lat1 := 41.9, Lon1 := 12.5, Lat2 := 34.05, Lon2 := -118.24, Carte := Destinations.Dest21}
        destination{Ville1 := "ZURICH", Ville2 := "SINGAPORE", Prix := 35000000, Multiplicateur := 130.0, MultiTexte := "x130", VraiVol := "12h30", DureeMinutes := 26.0, Lat1 := 47.38, Lon1 := 8.54, Lat2 := 1.35, Lon2 := 103.82, Carte := Destinations.Dest22}
        destination{Ville1 := "VANCOUVER", Ville2 := "HONG KONG", Prix := 60000000, Multiplicateur := 160.0, MultiTexte := "x160", VraiVol := "13h00", DureeMinutes := 27.0, Lat1 := 49.28, Lon1 := -123.12, Lat2 := 22.32, Lon2 := 114.17, Carte := Destinations.Dest23}
        destination{Ville1 := "MILAN", Ville2 := "TOKYO", Prix := 100000000, Multiplicateur := 200.0, MultiTexte := "x200", VraiVol := "13h30", DureeMinutes := 27.5, Lat1 := 45.46, Lon1 := 9.19, Lat2 := 35.68, Lon2 := 139.69, Carte := Destinations.Dest24}
        destination{Ville1 := "NEW YORK", Ville2 := "SYDNEY", Prix := 170000000, Multiplicateur := 250.0, MultiTexte := "x250", VraiVol := "21h00", DureeMinutes := 39.0, Lat1 := 40.71, Lon1 := -74.01, Lat2 := -33.87, Lon2 := 151.21, Carte := Destinations.Dest25}
        destination{Ville1 := "PARIS", Ville2 := "DUBAI", Prix := 300000000, Multiplicateur := 320.0, MultiTexte := "x320", VraiVol := "6h45", DureeMinutes := 17.5, Lat1 := 48.86, Lon1 := 2.35, Lat2 := 25.2, Lon2 := 55.27, Carte := Destinations.Dest26}
        destination{Ville1 := "DOHA", Ville2 := "MALE", Prix := 500000000, Multiplicateur := 400.0, MultiTexte := "x400", VraiVol := "4h30", DureeMinutes := 14.0, Lat1 := 25.29, Lon1 := 51.53, Lat2 := 4.18, Lon2 := 73.51, Carte := Destinations.Dest27}
        destination{Ville1 := "GENEVA", Ville2 := "MAHE", Prix := 850000000, Multiplicateur := 500.0, MultiTexte := "x500", VraiVol := "10h00", DureeMinutes := 22.5, Lat1 := 46.2, Lon1 := 6.14, Lat2 := -4.68, Lon2 := 55.49, Carte := Destinations.Dest28}
        destination{Ville1 := "LOS ANGELES", Ville2 := "BORA BORA", Prix := 1400000000, Multiplicateur := 650.0, MultiTexte := "x650", VraiVol := "8h30", DureeMinutes := 20.0, Lat1 := 34.05, Lon1 := -118.24, Lat2 := -16.5, Lon2 := -151.74, Carte := Destinations.Dest29}
        destination{Ville1 := "MONACO", Ville2 := "TAHITI", Prix := 2500000000, Multiplicateur := 800.0, MultiTexte := "x800", VraiVol := "22h00", DureeMinutes := 40.0, Lat1 := 43.74, Lon1 := 7.42, Lat2 := -17.65, Lon2 := -149.43, Carte := Destinations.Dest30}

    NbVisibles:int = 5
    # Partie visible d'une carte dans son image 2048 x 2048 (le reste est transparent).
    CarteLargeurVisible:float = 0.9716
    CarteHauteurVisible:float = 0.2744

    var Achetees:[]logic = array{}
    var Active:int = 0
    var Debut:int = 0
    var MessageErreur:string = ""
    var NumeroMessage:int = 0
    var Ecran:?canvas = false
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
        if (EnVol[]):
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
                # (si c'est déjà le trajet actif, rien à faire)
                if (Index <> Active):
                    if (EnVol[]):
                        AfficherErreur("WAIT FOR LANDING")
                    else:
                        set Active = Index
                        set Retour = false
                        set MessageErreur = ""
                        Afficher()
            else if (AvionTycoon.Argent >= D.Prix):
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
            Widget := W

    PleinEcran(W:widget):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.0}, Maximum := vector2{X := 1.0, Y := 1.0}}
            Offsets := margin{Left := 0.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
            Widget := W

    # Latitude / longitude -> position dans l'image.
    PointCarte(Lat:float, Lon:float):vector2 =
        vector2:
            X := CarteGauche + (Lon + 180.0) / 360.0 * (CarteDroite - CarteGauche)
            Y := CarteHaut + (LatHaut - Lat) / (LatHaut - LatBas) * (CarteBas - CarteHaut)

    # Point de la courbe (Bézier) entre A et B, bombée vers le haut comme une route aérienne.
    Courbe(A:vector2, B:vector2, T:float):vector2 =
        Dist := Sqrt((B.X - A.X) * (B.X - A.X) + (B.Y - A.Y) * (B.Y - A.Y))
        C := vector2{X := (A.X + B.X) / 2.0, Y := (A.Y + B.Y) / 2.0 - Dist * 0.3}
        U := 1.0 - T
        vector2:
            X := U * U * A.X + 2.0 * U * T * C.X + T * T * B.X
            Y := U * U * A.Y + 2.0 * U * T * C.Y + T * T * B.Y

    Vignette(T:texture, Taille:float):texture_block =
        texture_block{DefaultImage := T, DefaultDesiredSize := vector2{X := Taille, Y := Taille}}

    Afficher():void =
        if (P := EcranJoueur?, UI := GetPlayerUI[P]):
            if (C := Ecran?):
                UI.RemoveWidget(C)
            set NumeroAnimation += 1
            var Slots:[]canvas_slot = array{}
            # fond sombre + carte du monde
            set Slots += array{PleinEcran(color_block{DefaultColor := NamedColors.Black, DefaultOpacity := 0.85})}
            set Slots += array{Place(Vignette(Destinations.CarteMonde, TailleCarte), 0.5, 0.5, TailleCarte, TailleCarte)}

            # liste des destinations (5 visibles)
            TailleImageCarte := (ListeDroite - ListeGauche) * TailleCarte
            LargeurVisible := TailleImageCarte * CarteLargeurVisible
            HauteurVisible := TailleImageCarte * CarteHauteurVisible
            Pas := (ListeBas - ListeHaut) / (NbVisibles * 1.0)
            UListe := (ListeGauche + ListeDroite) / 2.0
            for (Ligne := 0..NbVisibles - 1, Index := Debut + Ligne, D := ListeDestinations[Index]):
                V := ListeHaut + Pas * (Ligne * 1.0 + 0.5)
                set Slots += array{Place(Vignette(D.Carte, TailleImageCarte), UListe, V, TailleImageCarte, TailleImageCarte)}
                if (not Achetees[Index]?):
                    set Slots += array{Place(color_block{DefaultColor := NamedColors.Black, DefaultOpacity := 0.55}, UListe, V, LargeurVisible, HauteurVisible)}
                if (Index = Active):
                    set Slots += array{Place(color_block{DefaultColor := NamedColors.Lime, DefaultOpacity := 0.9}, UListe - LargeurVisible / TailleCarte / 2.0 - 0.004, V, 5.0, HauteurVisible * 0.8)}
                # bouton invisible, exactement de la taille de la carte
                BoutonCarte := button_quiet{DefaultText := Msg("")}
                Gestion := bouton_destination{Index := Index, Ordinateur := Self}
                BoutonCarte.OnClick().Subscribe(Gestion.Clique)
                set Slots += array{Place(BoutonCarte, UListe, V, LargeurVisible, HauteurVisible)}

            # défilement : une fine barre à droite de la liste, avec une flèche en haut et en bas
            UFleches := (UListe + LargeurVisible / TailleCarte / 2.0 + CarteGauche) / 2.0
            VHaut := ListeHaut + Pas * 0.5 - HauteurVisible / TailleCarte / 2.0
            VBas := ListeBas - Pas * 0.5 + HauteurVisible / TailleCarte / 2.0
            Rail := (VBas - VHaut) - 0.03
            set Slots += array{Place(color_block{DefaultColor := MakeColorFromHex("5ADCFF"), DefaultOpacity := 0.15}, UFleches, (VHaut + VBas) / 2.0, 2.0, Rail * TailleCarte)}
            DernierDebut := ListeDestinations.Length - NbVisibles
            if (DernierDebut > 0):
                HauteurCurseur := Rail * (NbVisibles * 1.0) / (ListeDestinations.Length * 1.0)
                VCurseur := VHaut + 0.015 + HauteurCurseur / 2.0 + (Rail - HauteurCurseur) * (Debut * 1.0) / (DernierDebut * 1.0)
                set Slots += array{Place(color_block{DefaultColor := MakeColorFromHex("5ADCFF"), DefaultOpacity := 0.6}, UFleches, VCurseur, 3.0, HauteurCurseur * TailleCarte)}
            if (Debut > 0):
                set Slots += array{Place(Vignette(Destinations.FlecheHaut, 26.0), UFleches, VHaut, 26.0, 26.0)}
                Haut := button_quiet{DefaultText := Msg("")}
                Haut.OnClick().Subscribe(Monter)
                set Slots += array{Place(Haut, UFleches, VHaut, 34.0, 34.0)}
            if (Debut < DernierDebut):
                set Slots += array{Place(Vignette(Destinations.FlecheBas, 26.0), UFleches, VBas, 26.0, 26.0)}
                Bas := button_quiet{DefaultText := Msg("")}
                Bas.OnClick().Subscribe(Descendre)
                set Slots += array{Place(Bas, UFleches, VBas, 34.0, 34.0)}

            # fermeture
            Croix := button_quiet{DefaultText := Msg("X")}
            Croix.OnClick().Subscribe(FermerClique)
            set Slots += array{Place(Croix, CarteDroite - 0.015, CarteHaut + 0.02, 40.0, 40.0)}

            # trajet actif : points rouges, courbe, avion
            var Avion:?texture_block = false
            var Depart:vector2 = vector2{}
            var Arrivee:vector2 = vector2{}
            if (D := ListeDestinations[Active]):
                A := PointCarte(D.Lat1, D.Lon1)
                B := PointCarte(D.Lat2, D.Lon2)
                set Depart = if (Retour?) then B else A
                set Arrivee = if (Retour?) then A else B
                for (I := 0..39):
                    Pt := Courbe(A, B, (I * 1.0 + 0.5) / 40.0)
                    set Slots += array{Place(color_block{DefaultColor := MakeColorFromHex("5ADCFF"), DefaultOpacity := 0.85}, Pt.X, Pt.Y, 4.0, 4.0)}
                for (Ville : array{A, B}):
                    set Slots += array{Place(color_block{DefaultColor := NamedColors.Red, DefaultOpacity := 0.35}, Ville.X, Ville.Y, 26.0, 26.0)}
                    set Slots += array{Place(color_block{DefaultColor := NamedColors.Red}, Ville.X, Ville.Y, 12.0, 12.0)}
                Icone := if (Arrivee.X >= Depart.X) then Destinations.AvionDroite else Destinations.AvionGauche
                ImageAvion := Vignette(Icone, 34.0)
                PosAvion := Courbe(Depart, Arrivee, Progression())
                set Slots += array{Place(ImageAvion, PosAvion.X, PosAvion.Y, 34.0, 34.0)}
                set Avion = option{ImageAvion}
            if (MessageErreur <> ""):
                Erreur := text_block{DefaultText := Msg(MessageErreur), DefaultTextColor := NamedColors.Red, DefaultJustification := text_justification.Center}
                set Slots += array{Place(Erreur, (CarteGauche + CarteDroite) / 2.0, CarteHaut + 0.03, 700.0, 40.0)}

            Nouveau := canvas{Slots := Slots}
            UI.AddWidget(Nouveau, player_ui_slot{InputMode := ui_input_mode.All})
            set Ecran = option{Nouveau}
            if (EnVol[], ImageAvion := Avion?):
                spawn{AnimerAvion(NumeroAnimation, Nouveau, ImageAvion, Depart, Arrivee)}

    # Pendant le vol, l'avion est replacé 10 fois par seconde à sa vraie position.
    AnimerAvion(Numero:int, Toile:canvas, Img:texture_block, Depart:vector2, Arrivee:vector2)<suspends>:void =
        loop:
            Sleep(0.1)
            if (Numero <> NumeroAnimation or not EnVol[]) { break }
            Pt := Courbe(Depart, Arrivee, Progression())
            Toile.RemoveWidget(Img)
            Toile.AddWidget(Place(Img, Pt.X, Pt.Y, 34.0, 34.0))
