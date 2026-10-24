using { /Fortnite.com/Devices }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - le PC des destinations : un RÉSEAU de villes reliées par des lignes.
#
# L'avion est toujours dans une ville (au début : PARIS). Depuis cette ville, on ne peut acheter
# et prendre QUE les lignes qui en partent (à Los Angeles, pas de Zurich - Singapour !). Quand on
# atterrit, on est dans la nouvelle ville ; le vol suivant part de là (par défaut : le retour).
#
# Le PC s'ouvre en plein écran :
#   - à gauche, "YOU ARE IN ..." et les lignes qui partent de la ville (une carte par ligne) ;
#   - à droite, la carte du monde : toutes les lignes en pointillés (bleu = achetée, jaune = à
#     acheter d'ici, gris = trop loin pour l'instant, vert = le prochain vol) et l'avion ;
#   - on clique une ligne -> une FICHE s'ouvre : l'illustration de la ville, sa description, la
#     durée du vol, ce que ça rapporte, et les boutons BUY / FLY HERE NEXT / CLOSE.
# 8 niveaux de lignes : plus c'est loin, plus c'est cher, long (5 min -> 15 min) et rentable.
#
# En haut de l'écran du proprio (un peu sous le bord, pour laisser la place au code de la map) :
# une barre de vol avec le départ, l'arrivée, le temps restant et un avion qui avance.
#
# Dans le Tiroir à contenu :
#   dossier "Destinations" : CarteVols (la nouvelle carte du monde, Textures/Destinations),
#   AvionDroite, AvionGauche (déjà là) ;
#   dossier "Villes" : les 30 illustrations (Textures/Villes) : Paris, London, Rome, Madrid,
#   Istanbul, Cairo, NewYork, Dubai, Rio, MexicoCity, LosAngeles, Delhi, Singapore, Tokyo,
#   Sydney, BoraBora, Bangkok, HongKong, Seoul, Vancouver, Amsterdam, Athens, Marrakech,
#   CapeTown, Miami, SanFrancisco, Shanghai, Maldives, Bali, Cusco.
#
# Dans l'éditeur :
#   Bouton          : un Appareil Bouton posé sur le PC (modèle invisible, texte "Open").
#   AvionTycoon     : le device avion_tycoon de cet avion (pour le proprio et l'argent).
#   BoutonDecollage : (facultatif) un Appareil Bouton dans le cockpit (texte "Take off").
#   Portes          : les portes passagers (devices porte_passager) qui doivent être fermées
#                     pour décoller avec BoutonDecollage. Elles restent verrouillées pendant le vol.
#   MessageHUD      : un Appareil Message HUD pour les messages.
#   Menu            : (facultatif) le device menu_pc : le PC ouvre alors le menu des 3 cartes.

ville_reseau := class:
    Nom:string
    Pays:string
    Description:string
    # Position de la ville sur l'image CarteVols (0..1), calculée avec Outils/carte_monde.py.
    U:float
    V:float
    Image:texture

# Une ligne entre deux villes (numéros dans LesVilles), avec son niveau (1..8).
route_reseau := class:
    A:int
    B:int
    Palier:int

# Un bouton de l'écran : il retient son action et le numéro de la ligne.
clic_pc := class:
    Ordinateur:pc_destinations
    Action:int
    Index:int
    Clique(Clic:widget_message):void = Ordinateur.Agir(Action, Index)

pc_destinations := class(creative_device):
    @editable Bouton:button_device = button_device{}
    @editable AvionTycoon:avion_tycoon = avion_tycoon{}
    @editable BoutonDecollage:?button_device = false
    # Son joué à chaque achat de ligne : un Appareil Lecteur audio.
    @editable SonAchat:?audio_player_device = false
    @editable Portes:[]porte_passager = array{}
    @editable MessageHUD:hud_message_device = hud_message_device{}
    # (facultatif) le device menu_pc : le PC ouvre alors le menu des 3 cartes.
    @editable Menu:?menu_pc = false
    # La barre de vol en haut de l'écran : sa distance au bord du haut (pixels, sur un écran
    # 1920 x 1080). Laisse de la place pour le code de la map.
    @editable HautBarre:float = 64.0

    # La carte du monde à l'écran (onglet MAP) : 1800 x 900 pixels, sous les onglets.
    LargeurCarte:float = 1800.0
    HauteurCarte:float = 900.0
    CentreCarteY:float = 610.0

    LesVilles:[]ville_reseau = array:
        ville_reseau{Nom := "PARIS", Pays := "FRANCE", Description := "Your home base. Croissants included!", U := 0.5065, V := 0.2790, Image := Villes.Paris}
        ville_reseau{Nom := "LONDON", Pays := "UNITED KINGDOM", Description := "Tea time under Big Ben.", U := 0.4996, V := 0.2556, Image := Villes.London}
        ville_reseau{Nom := "ROME", Pays := "ITALY", Description := "Pasta, gelato and ancient history.", U := 0.5347, V := 0.3350, Image := Villes.Rome}
        ville_reseau{Nom := "MADRID", Pays := "SPAIN", Description := "Sunny plazas and late dinners.", U := 0.4897, V := 0.3461, Image := Villes.Madrid}
        ville_reseau{Nom := "ISTANBUL", Pays := "TURKEY", Description := "Where Europe meets Asia.", U := 0.5805, V := 0.3417, Image := Villes.Istanbul}
        ville_reseau{Nom := "CAIRO", Pays := "EGYPT", Description := "The pyramids are waiting.", U := 0.5868, V := 0.4181, Image := Villes.Cairo}
        ville_reseau{Nom := "NEW YORK", Pays := "USA", Description := "The city that never sleeps.", U := 0.2944, V := 0.3440, Image := Villes.NewYork}
        ville_reseau{Nom := "DUBAI", Pays := "UAE", Description := "Gold, sand and the tallest tower.", U := 0.6535, V := 0.4489, Image := Villes.Dubai}
        ville_reseau{Nom := "RIO", Pays := "BRAZIL", Description := "Beaches, samba and sunshine.", U := 0.3801, V := 0.7289, Image := Villes.Rio}
        ville_reseau{Nom := "MEXICO CITY", Pays := "MEXICO", Description := "Tacos, colors and old pyramids.", U := 0.2246, V := 0.4841, Image := Villes.MexicoCity}
        ville_reseau{Nom := "LOS ANGELES", Pays := "USA", Description := "Palm trees and movie stars.", U := 0.1716, V := 0.3914, Image := Villes.LosAngeles}
        ville_reseau{Nom := "DELHI", Pays := "INDIA", Description := "Spices, palaces and busy streets.", U := 0.7145, V := 0.4273, Image := Villes.Delhi}
        ville_reseau{Nom := "SINGAPORE", Pays := "SINGAPORE", Description := "A garden city of the future.", U := 0.7884, V := 0.5884, Image := Villes.Singapore}
        ville_reseau{Nom := "TOKYO", Pays := "JAPAN", Description := "Neon lights under Mount Fuji.", U := 0.8880, V := 0.3801, Image := Villes.Tokyo}
        ville_reseau{Nom := "SYDNEY", Pays := "AUSTRALIA", Description := "Surf, sun and the Opera House.", U := 0.9200, V := 0.7994, Image := Villes.Sydney}
        ville_reseau{Nom := "BORA BORA", Pays := "FRENCH POLYNESIA", Description := "The dream island. Pure luxury.", U := 0.0785, V := 0.6904, Image := Villes.BoraBora}
        ville_reseau{Nom := "BANGKOK", Pays := "THAILAND", Description := "Golden temples and street food.", U := 0.7792, V := 0.5176, Image := Villes.Bangkok}
        ville_reseau{Nom := "HONG KONG", Pays := "CHINA", Description := "Skyscrapers above the harbour.", U := 0.8171, V := 0.4667, Image := Villes.HongKong}
        ville_reseau{Nom := "SEOUL", Pays := "SOUTH KOREA", Description := "Palaces, K-pop and city lights.", U := 0.8527, V := 0.3668, Image := Villes.Seoul}
        ville_reseau{Nom := "VANCOUVER", Pays := "CANADA", Description := "Mountains, forests and the ocean.", U := 0.1580, V := 0.2754, Image := Villes.Vancouver}
        ville_reseau{Nom := "AMSTERDAM", Pays := "NETHERLANDS", Description := "Canals, bikes and tulips.", U := 0.5136, V := 0.2478, Image := Villes.Amsterdam}
        ville_reseau{Nom := "ATHENS", Pays := "GREECE", Description := "The Acropolis above the city.", U := 0.5659, V := 0.3639, Image := Villes.Athens}
        ville_reseau{Nom := "MARRAKECH", Pays := "MOROCCO", Description := "Red walls and busy souks.", U := 0.4778, V := 0.4076, Image := Villes.Marrakech}
        ville_reseau{Nom := "CAPE TOWN", Pays := "SOUTH AFRICA", Description := "Table Mountain over the sea.", U := 0.5512, V := 0.7997, Image := Villes.CapeTown}
        ville_reseau{Nom := "MIAMI", Pays := "USA", Description := "Neon nights and sunny beaches.", U := 0.2772, V := 0.4454, Image := Villes.Miami}
        ville_reseau{Nom := "SAN FRANCISCO", Pays := "USA", Description := "The Golden Gate in the fog.", U := 0.1599, V := 0.3654, Image := Villes.SanFrancisco}
        ville_reseau{Nom := "SHANGHAI", Pays := "CHINA", Description := "A skyline from the future.", U := 0.8374, V := 0.4103, Image := Villes.Shanghai}
        ville_reseau{Nom := "MALDIVES", Pays := "MALDIVES", Description := "Crystal water, private islands.", U := 0.7042, V := 0.5724, Image := Villes.Maldives}
        ville_reseau{Nom := "BALI", Pays := "INDONESIA", Description := "Rice terraces and temples.", U := 0.8200, V := 0.6450, Image := Villes.Bali}
        ville_reseau{Nom := "CUSCO", Pays := "PERU", Description := "The gate to Machu Picchu.", U := 0.3001, V := 0.6731, Image := Villes.Cusco}

    # 0 PARIS 1 LONDON 2 ROME 3 MADRID 4 ISTANBUL 5 CAIRO 6 NEW YORK 7 DUBAI 8 RIO 9 MEXICO CITY
    # 10 LOS ANGELES 11 DELHI 12 SINGAPORE 13 TOKYO 14 SYDNEY 15 BORA BORA
    # 16 BANGKOK 17 HONG KONG 18 SEOUL 19 VANCOUVER
    # 20 AMSTERDAM 21 ATHENS 22 MARRAKECH 23 CAPE TOWN 24 MIAMI 25 SAN FRANCISCO 26 SHANGHAI
    # 27 MALDIVES 28 BALI 29 CUSCO
    Routes:[]route_reseau = array:
        route_reseau{A := 0, B := 1, Palier := 1}
        route_reseau{A := 0, B := 2, Palier := 1}
        route_reseau{A := 0, B := 3, Palier := 1}
        route_reseau{A := 2, B := 4, Palier := 2}
        route_reseau{A := 2, B := 5, Palier := 2}
        route_reseau{A := 1, B := 6, Palier := 3}
        route_reseau{A := 4, B := 7, Palier := 3}
        route_reseau{A := 5, B := 7, Palier := 3}
        route_reseau{A := 3, B := 8, Palier := 4}
        route_reseau{A := 6, B := 9, Palier := 4}
        route_reseau{A := 6, B := 10, Palier := 4}
        route_reseau{A := 7, B := 11, Palier := 5}
        route_reseau{A := 9, B := 10, Palier := 5}
        route_reseau{A := 8, B := 9, Palier := 5}
        route_reseau{A := 10, B := 19, Palier := 5}
        route_reseau{A := 11, B := 16, Palier := 6}
        route_reseau{A := 16, B := 12, Palier := 6}
        route_reseau{A := 16, B := 17, Palier := 6}
        route_reseau{A := 12, B := 14, Palier := 7}
        route_reseau{A := 17, B := 18, Palier := 7}
        route_reseau{A := 18, B := 13, Palier := 7}
        route_reseau{A := 17, B := 14, Palier := 8}
        route_reseau{A := 13, B := 14, Palier := 8}
        route_reseau{A := 19, B := 15, Palier := 8}
        route_reseau{A := 10, B := 15, Palier := 8}
        route_reseau{A := 0, B := 20, Palier := 1}
        route_reseau{A := 1, B := 20, Palier := 2}
        route_reseau{A := 2, B := 21, Palier := 2}
        route_reseau{A := 21, B := 4, Palier := 2}
        route_reseau{A := 3, B := 22, Palier := 2}
        route_reseau{A := 22, B := 5, Palier := 3}
        route_reseau{A := 5, B := 23, Palier := 5}
        route_reseau{A := 23, B := 8, Palier := 6}
        route_reseau{A := 6, B := 24, Palier := 4}
        route_reseau{A := 24, B := 9, Palier := 4}
        route_reseau{A := 10, B := 25, Palier := 5}
        route_reseau{A := 25, B := 19, Palier := 5}
        route_reseau{A := 17, B := 26, Palier := 6}
        route_reseau{A := 26, B := 13, Palier := 7}
        route_reseau{A := 7, B := 27, Palier := 6}
        route_reseau{A := 27, B := 12, Palier := 7}
        route_reseau{A := 12, B := 28, Palier := 7}
        route_reseau{A := 28, B := 14, Palier := 8}
        route_reseau{A := 8, B := 29, Palier := 5}
        route_reseau{A := 29, B := 9, Palier := 5}

    # Par niveau de ligne (1..8) : prix, valeur d'un vol (ce que rapportent passagers et missions,
    # voir passagers / feuille_mission), durée (minutes), multiplicateur (commandes des passagers).
    PrixPalier:[]int = array{2000, 5000, 50000, 400000, 3000000, 25000000, 200000000, 1500000000}
    ValeurPalier:[]float = array{1000.0, 8000.0, 60000.0, 500000.0, 4000000.0, 30000000.0, 250000000.0, 2000000000.0}
    MinutesPalier:[]float = array{5.0, 6.0, 7.0, 8.0, 9.0, 11.0, 13.0, 15.0}
    MultiPalier:[]float = array{1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0}

    # La ville où est l'avion, les lignes achetées, le prochain vol.
    var Position:int = 0
    var Achetees:[]logic = array{}
    var Choisie:int = 0
    # Vol : DebutVol < 0 = l'avion est au sol. RouteVol / Vers : la ligne et la ville d'arrivée.
    var DebutVol:float = -1.0
    var DureeVol:float = 300.0
    var RouteVol:int = -1
    var Vers:int = -1

    # L'écran du PC
    var EcranJoueur:?player = false
    var Ecran:?canvas = false
    # Ce qui change sur l'écran (on le remplace sans refermer l'écran : pas de saut de souris).
    var Dynamiques:[]widget = array{}
    var NumeroAnimation:int = 0
    # La ligne dont la fiche est ouverte (-1 = aucune).
    # la carte du monde : créée une seule fois à l'ouverture, puis juste montrée / cachée
    # (comme ça l'onglet WORLD MAP s'affiche instantanément)
    var CarteCadre:?color_block = false
    var CarteImage:?texture_block = false
    # vue du PC : 0 = les vols possibles d'ici (FLIGHTS), 1 = la carte du monde (WORLD MAP)
    var Vue:int = 0
    # pendant un vol : la ligne choisie pour le vol suivant (au départ de la ville d'arrivée)
    var ChoixApres:int = -1
    var MessageErreur:string = ""
    var NumeroMessage:int = 0

    # La barre de vol en haut de l'écran
    var Barre:?canvas = false
    var BarreJoueur:?player = false
    var BarreMobile:[]widget = array{}
    TexteDepart:text_block = text_block{DefaultTextColor := NamedColors.White, DefaultJustification := text_justification.Right, DefaultShadowColor := MakeColorFromHex("1B2541"), DefaultShadowOpacity := 1.0, DefaultShadowOffset := option{vector2{X := 3.0, Y := 3.0}}}
    TexteArrivee:text_block = text_block{DefaultTextColor := NamedColors.White, DefaultJustification := text_justification.Left, DefaultShadowColor := MakeColorFromHex("1B2541"), DefaultShadowOpacity := 1.0, DefaultShadowOffset := option{vector2{X := 3.0, Y := 3.0}}}
    TexteTemps:text_block = text_block{DefaultTextColor := MakeColorFromHex("BBF7D0"), DefaultJustification := text_justification.Center, DefaultShadowColor := MakeColorFromHex("1B2541"), DefaultShadowOpacity := 1.0, DefaultShadowOffset := option{vector2{X := 3.0, Y := 3.0}}}

    OnBegin<override>()<suspends>:void =
        # au départ : aucune ligne ; la première (PARIS - LONDON) est gratuite, mais il faut
        # quand même l'acheter sur le PC (BUY - FREE)
        set Achetees = for (I -> R : Routes) { false }
        set Choisie = -1
        if (B := BoutonDecollage?) { spawn{AttendreDecollage(B)} }
        spawn{BoucleBarre()}
        loop:
            Joueur := Bouton.InteractedWithEvent.Await()
            if (EstProprio[Joueur], P := player[Joueur]):
                if (M := Menu?) then M.Ouvrir(P, Self) else Ouvrir(P)

    EstProprio(Joueur:agent)<transacts><decides>:void =
        Proprio := AvionTycoon.Proprio?
        Proprio = Joueur

    # ---------- le réseau ----------
    NomVille(V:int)<transacts>:string = if (Ville := LesVilles[V]) then Ville.Nom else "?"

    Autre(R:int, V:int)<transacts>:int =
        if (Rt := Routes[R]) then (if (Rt.A = V) then Rt.B else Rt.A) else V

    # La ligne R part-elle de la ville V ?
    Touche(R:int, V:int)<transacts><decides>:void =
        Rt := Routes[R]
        Rt.A = V or Rt.B = V

    Achetee(R:int)<transacts><decides>:void = Achetees[R]?

    # La ville V est sur une ligne achetée.
    VilleAchetee(V:int)<transacts><decides>:void =
        Trouve := for (X : RoutesDe(V), Achetee[X]) { X }
        Trouve.Length > 0

    # Les lignes qui partent de la ville V.
    RoutesDe(V:int)<transacts>:[]int = for (I -> R : Routes, R.A = V or R.B = V) { I }

    # Une ligne achetée qui part de la ville où est l'avion (pour le prochain vol).
    PremiereRoute()<transacts>:int =
        for (R : RoutesDe(Position), Achetee[R]):
            return R
        -1

    Palier(R:int)<transacts>:int = if (Rt := Routes[R]) then Rt.Palier else 1
    # La ligne 0 (PARIS - LONDON) est gratuite.
    PrixRoute(R:int)<transacts>:int = if (R = 0) then 0 else if (P := PrixPalier[Palier(R) - 1]) then P else 0
    TextePrix(P:int):string = if (P = 0) then "FREE" else "${Abreger(P)}"

    # On peut décoller : au sol, avec une ligne achetée qui part d'ici.
    PretADecoller()<transacts><decides>:void =
        not EnVol[]
        (Touche[Choisie, Position] and Achetee[Choisie]) or PremiereRoute() >= 0
    MinutesRoute(R:int)<transacts>:float = if (M := MinutesPalier[Palier(R) - 1]) then M else 5.0

    # La ligne du vol en cours, sinon celle du prochain vol.
    RouteCourante()<transacts>:int = if (DebutVol >= 0.0) then RouteVol else Choisie

    # ---------- ce que les autres devices utilisent ----------
    EnVol()<transacts><decides>:void = DebutVol >= 0.0

    # Valeur d'un vol (passagers + missions en dépendent) et multiplicateur des commandes.
    ValeurVol()<transacts>:float = if (V := ValeurPalier[Palier(RouteCourante()) - 1]) then V else 1000.0
    MultiplicateurActif()<transacts>:float = if (M := MultiPalier[Palier(RouteCourante()) - 1]) then M else 1.0
    DureeVolActive()<transacts>:float = MinutesRoute(Choisie) * 60.0
    # Niveau de la ligne (1..8)
    Niveau()<transacts>:int = Palier(RouteCourante())

    VilleDepart()<transacts>:string = NomVille(Position)
    # (avant le tout premier achat : la destination de la ligne gratuite)
    VilleArrivee()<transacts>:string =
        if (DebutVol >= 0.0) then NomVille(Vers)
        else if (Routes[Choisie]) then NomVille(Autre(Choisie, Position))
        else NomVille(Autre(0, Position))

    # Avancement du vol entre 0 (départ) et 1 (arrivée).
    Progression():float =
        if (EnVol[], DureeVol > 0.0):
            Max(0.0, Min(1.0, (GetSimulationElapsedTime() - DebutVol) / DureeVol))
        else:
            0.0

    # ---------- le vol ----------
    AttendreDecollage(B:button_device)<suspends>:void =
        loop:
            Joueur := B.InteractedWithEvent.Await()
            if (EstProprio[Joueur]):
                Decoller(Joueur)

    Decoller(Joueur:agent):void =
        PortesOuvertes := for (Porte : Portes, Porte.Ouverte?) { Porte }
        if (EnVol[]):
            Annoncer(Joueur, "ALREADY FLYING")
        else if (not PretADecoller[]):
            Annoncer(Joueur, "BUY A FLIGHT ON THE PC FIRST")
        else if (PortesOuvertes.Length > 0):
            Annoncer(Joueur, "CLOSE ALL DOORS BEFORE TAKE OFF")
        else:
            for (Porte : Portes) { Porte.Verrouiller(true) }
            Decollage()

    # Décollage sur le prochain vol (appelé par le bouton TAKE OFF des passagers).
    Decollage():void =
        if (not EnVol[]):
            if (not Touche[Choisie, Position] or not Achetee[Choisie]):
                set Choisie = PremiereRoute()
            if (Routes[Choisie]):
                set RouteVol = Choisie
                set Vers = Autre(Choisie, Position)
                set DureeVol = MinutesRoute(Choisie) * 60.0
                set DebutVol = GetSimulationElapsedTime()
                spawn{Voler()}
                Afficher()

    Voler()<suspends>:void =
        Sleep(DureeVol)
        set DebutVol = -1.0
        # on est arrivé : l'avion est dans la nouvelle ville ; le prochain vol par défaut = le retour
        if (Vers >= 0) { set Position = Vers }
        Retour := RouteVol
        set Choisie = if (Touche[ChoixApres, Position], Achetee[ChoixApres]) then ChoixApres else Retour
        set ChoixApres = -1
        set RouteVol = -1
        set Vers = -1
        for (Porte : Portes) { Porte.Verrouiller(false) }
        Afficher()

    # ---------- ouverture / fermeture ----------
    Ouvrir(P:player):void =
        Fermer()
        set EcranJoueur = option{P}
        set Vue = 0
        Afficher()

    Fermer():void =
        set NumeroAnimation += 1
        if (P := EcranJoueur?, UI := GetPlayerUI[P], C := Ecran?):
            UI.RemoveWidget(C)
        set Ecran = false
        set CarteCadre = false
        set CarteImage = false
        set Dynamiques = array{}

    # ---------- les clics ----------
    # 5 fermer le PC, 9 changer d'onglet (0 FLIGHTS, 1 WORLD MAP), 12 bouton d'une carte de vol
    Agir(Action:int, Index:int):void =
        if (Action = 12):
            Principal(Index)
        else if (Action = 9):
            set Vue = Index
            Afficher()
        else:
            Joueur := EcranJoueur
            Fermer()
            set EcranJoueur = false
            # avec le menu : on revient au menu des 3 cartes
            if (M := Menu?, P := Joueur?):
                M.Ouvrir(P, Self)

    Acheter(R:int):void =
        if (Routes[R], not Achetee[R]):
            Prix := PrixRoute(R)
            if (AvionTycoon.Argent >= Prix):
                AvionTycoon.Depenser(Prix)
                if (S := SonAchat?) { S.Play() }
                if (set Achetees[R] = true) {}
                # elle devient tout de suite le prochain vol (au sol : depuis ici ; en vol : depuis
                # la ville d'arrivée)
                if (not EnVol[], Touche[R, Position]) { set Choisie = R }
                if (EnVol[], Touche[R, Vers]) { set ChoixApres = R }
                set MessageErreur = ""
                Afficher()
            else:
                AfficherErreur("NOT ENOUGH MONEY")

    # Le clic sur la carte d'un vol : pas encore achetée -> on l'achète (et elle est choisie) ;
    # déjà à nous -> elle devient le prochain vol. Un seul clic dans tous les cas.
    Principal(R:int):void =
        if (not Achetee[R]):
            Acheter(R)
        else if (EnVol[]):
            if (Touche[R, Vers]):
                set ChoixApres = R
                Afficher()
        else:
            Choisir(R)

    # La ville d'où partira le prochain vol (ici au sol, la ville d'arrivée en vol).
    VilleBase()<transacts>:int = if (EnVol[]) then Vers else Position

    # La ligne du prochain vol (au sol : celle choisie ; en vol : celle choisie pour après,
    # sinon le retour).
    ProchainVol()<transacts>:int =
        if (EnVol[]) then (if (ChoixApres >= 0) then ChoixApres else RouteVol) else Choisie

    Choisir(R:int):void =
        if (EnVol[]):
            AfficherErreur("WAIT FOR LANDING")
        else if (Touche[R, Position], Achetee[R]):
            set Choisie = R
            Afficher()

    Annoncer(Joueur:agent, Texte:string):void =
        MessageHUD.SetText(Msg(Texte))
        MessageHUD.Show(Joueur)

    # Message rouge sur l'écran, qui disparaît tout seul après 2 secondes.
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

    # ---------- placement sur l'écran ----------
    # Un widget centré sur le point (U, V) de la carte CarteVols, décalé de DX, DY pixels.
    # ZOrder : plus le nombre est grand, plus c'est au-dessus. Les boutons sont TOUJOURS tout en
    # haut (30) : rien ne peut bloquer un clic.
    PlaceC(W:widget, U:float, V:float, DX:float, DY:float, Largeur:float, Hauteur:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.5}, Maximum := vector2{X := 0.5, Y := 0.5}}
            Alignment := vector2{X := 0.5, Y := 0.5}
            Offsets := margin{Left := (U - 0.5) * LargeurCarte + DX, Top := (V - 0.5) * HauteurCarte + CentreCarteY - 540.0 + DY, Right := Largeur, Bottom := Hauteur}
            SizeToContent := false
            ZOrder := Couche
            Widget := W

    # Un widget placé comme sur un écran 1920 x 1080 (X, Y = coin haut gauche).
    Bloc(W:widget, X:float, Y:float, L:float, H:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.5}, Maximum := vector2{X := 0.5, Y := 0.5}}
            Alignment := vector2{X := 0.0, Y := 0.0}
            Offsets := margin{Left := X - 960.0, Top := Y - 540.0, Right := L, Bottom := H}
            SizeToContent := false
            ZOrder := Couche
            Widget := W

    PleinEcran(W:widget):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.0}, Maximum := vector2{X := 1.0, Y := 1.0}}
            Offsets := margin{Left := 0.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
            SizeToContent := false
            Widget := W

    Rect(Hex:string, Opacite:type{_X:float where 0.0 <= _X, _X <= 1.0}):color_block =
        color_block{DefaultColor := MakeColorFromHex(Hex), DefaultOpacity := Opacite}

    Ecrit(S:string, Hex:string, J:text_justification):text_block =
        text_block{DefaultText := Msg(S), DefaultTextColor := MakeColorFromHex(Hex), DefaultJustification := J}

    # Un texte avec une ombre, lisible sur la carte.
    Etiquette(S:string, Hex:string):text_block =
        text_block:
            DefaultText := Msg(S)
            DefaultTextColor := MakeColorFromHex(Hex)
            DefaultJustification := text_justification.Center
            DefaultShadowColor := MakeColorFromHex("052E16")
            DefaultShadowOpacity := 1.0
            DefaultShadowOffset := option{vector2{X := 3.0, Y := 3.0}}

    Vignette(T:texture, L:float, H:float):texture_block =
        texture_block{DefaultImage := T, DefaultDesiredSize := vector2{X := L, Y := H}}

    # Zone cliquable invisible (toujours au-dessus de tout).
    Zone(Action:int, Index:int):button_quiet =
        B := button_quiet{DefaultText := Msg("")}
        B.OnClick().Subscribe(clic_pc{Ordinateur := Self, Action := Action, Index := Index}.Clique)
        B

    # Un bouton cartoon (image du kit InterfacePC) + son texte + la zone de clic par-dessus
    # (écran 1920 x 1080).
    BoutonKit(Texte:string, Img:texture, X:float, Y:float, L:float, H:float, Action:int, Index:int):[]canvas_slot =
        array:
            Bloc(Vignette(Img, L, H), X, Y, L, H, 16)
            Bloc(Etiquette(Texte, "FFFFFF"), X, Y + H / 2.0 - 22.0, L, 40.0, 17)
            Bloc(Zone(Action, Index), X, Y, L, H, 30)

    Abreger(N:int):string = AvionTycoon.Abreger(N)

    # Point (Bézier) entre A et B, bombé vers le haut comme une route aérienne.
    Courbe(A:vector2, B:vector2, T:float):vector2 =
        Dist := Sqrt((B.X - A.X) * (B.X - A.X) + (B.Y - A.Y) * (B.Y - A.Y))
        C := vector2{X := (A.X + B.X) / 2.0, Y := (A.Y + B.Y) / 2.0 - Dist * 0.3}
        U := 1.0 - T
        vector2:
            X := U * U * A.X + 2.0 * U * T * C.X + T * T * B.X
            Y := U * U * A.Y + 2.0 * U * T * C.Y + T * T * B.Y

    PointVille(V:int)<transacts>:vector2 =
        if (Ville := LesVilles[V]) then vector2{X := Ville.U, Y := Ville.V} else vector2{}

    # ---------- l'écran du PC ----------
    Afficher():void =
        if (P := EcranJoueur?, UI := GetPlayerUI[P]):
            # le fond et la carte du monde ne sont créés qu'une fois, à l'ouverture
            var Toile:canvas = canvas{}
            if (C := Ecran?):
                set Toile = C
            else:
                Fond := PleinEcran(Vignette(InterfacePC.Fond, 1920.0, 1080.0))
                Cadre := Rect("4ADE80", 1.0)
                ImageCarte := Vignette(Destinations.CarteVols, LargeurCarte, HauteurCarte)
                Cadre.SetVisibility(widget_visibility.Collapsed)
                ImageCarte.SetVisibility(widget_visibility.Collapsed)
                Base := canvas:
                    Slots := array:
                        Fond
                        PlaceC(Cadre, 0.5, 0.5, 0.0, 0.0, LargeurCarte + 6.0, HauteurCarte + 6.0, 2)
                        PlaceC(ImageCarte, 0.5, 0.5, 0.0, 0.0, LargeurCarte, HauteurCarte, 3)
                UI.AddWidget(Base, player_ui_slot{InputMode := ui_input_mode.All})
                set Ecran = option{Base}
                set CarteCadre = option{Cadre}
                set CarteImage = option{ImageCarte}
                set Toile = Base
            # la carte : visible seulement dans l'onglet WORLD MAP
            Montrer := if (Vue = 1) then widget_visibility.Visible else widget_visibility.Collapsed
            if (Cadre := CarteCadre?) { Cadre.SetVisibility(Montrer) }
            if (ImageCarte := CarteImage?) { ImageCarte.SetVisibility(Montrer) }
            for (W : Dynamiques) { Toile.RemoveWidget(W) }
            set NumeroAnimation += 1
            var Slots:[]canvas_slot = array{}
            var IconeVol:?texture_block = false
            if (Vue = 0):
                set Slots += EcranVols()
            else:
                Carte := CarteReseau()
                set Slots += Carte(0)
                set IconeVol = Carte(1)
            set Slots += Onglets()
            if (MessageErreur <> ""):
                set Slots += array{Bloc(Rect("7F1D1D", 0.95), 610.0, 170.0, 700.0, 50.0, 25)}
                set Slots += array{Bloc(Ecrit(MessageErreur, "FFFFFF", text_justification.Center), 610.0, 175.0, 700.0, 40.0, 26)}
            set Slots += BoutonKit("CLOSE", InterfacePC.OngletSombre, 1700.0, 10.0, 200.0, 56.0, 5, 0)
            for (S : Slots) { Toile.AddWidget(S) }
            set Dynamiques = for (S : Slots) { S.Widget }
            if (EnVol[], IconeAvion := IconeVol?):
                spawn{AnimerAvion(NumeroAnimation, Toile, IconeAvion)}

    # ---------- l'écran des vols : simple et rapide ----------
    # Seulement les vols possibles depuis la ville de l'avion (2 à 5), en grandes cartes côte à
    # côte. Un clic sur le bouton d'une carte = acheter la ligne ou la choisir. En bas : le
    # prochain vol.
    EcranVols():[]canvas_slot =
        var S:[]canvas_slot = array{}
        Base := VilleBase()
        Prochain := ProchainVol()
        # le titre et ce qu'il faut faire
        Titre := if (EnVol[]) then "FLYING TO {NomVille(Vers)}" else "YOU ARE IN {NomVille(Base)}"
        Aide := if (EnVol[]) then "CHOOSE YOUR FLIGHT AFTER LANDING" else "CLICK A FLIGHT TO BUY IT OR CHOOSE IT"
        set S += array{Bloc(Etiquette(Titre, "FFFFFF"), 360.0, 165.0, 1200.0, 44.0, 6)}
        set S += array{Bloc(Etiquette(Aide, "BBF7D0"), 360.0, 208.0, 1200.0, 40.0, 6)}
        # les cartes, triées du moins cher au plus cher
        var Lignes:[]int = array{}
        for (Niv := 1..8):
            set Lignes += for (R : RoutesDe(Base), Palier(R) = Niv) { R }
        Largeur := 300.0
        Ecart := 30.0
        Total := Lignes.Length * Largeur + (Lignes.Length - 1) * Ecart
        for (N -> R : Lignes, Ville := LesVilles[Autre(R, Base)]):
            X := 960.0 - Total / 2.0 + N * (Largeur + Ecart)
            set S += CarteVol(R, Ville, X, 262.0, Largeur, Prochain)
        # le prochain vol, en gros, en bas
        if (Rt := Routes[Prochain], Arrivee := LesVilles[Autre(Prochain, Base)]):
            Minutes := if (M := Round[MinutesRoute(Prochain)]) then M else 5
            Debut := if (EnVol[]) then "AFTER LANDING" else "NEXT FLIGHT"
            set S += array{Bloc(Vignette(InterfacePC.Bandeau, 1000.0, 125.0), 460.0, 882.0, 1000.0, 125.0, 6)}
            set S += array{Bloc(Etiquette("{Debut} :  {NomVille(Base)}  >  {Arrivee.Nom}  -  {Minutes} MIN", "FFFFFF"), 460.0, 904.0, 1000.0, 40.0, 8)}
            Ensuite := if (EnVol[]) then "IT STARTS WHEN YOU LAND" else "CLOSE THE DOORS AND TAKE OFF !"
            set S += array{Bloc(Etiquette(Ensuite, "DCFCE7"), 460.0, 942.0, 1000.0, 36.0, 8)}
        else:
            set S += array{Bloc(Etiquette("BUY A FLIGHT ABOVE TO START", "FFFFFF"), 460.0, 920.0, 1000.0, 44.0, 8)}
        S

    # Une carte de vol cartoon (300 x 600) : l'image de la ville, son nom, durée, gain, et un
    # gros bouton. La bague de la carte dit l'état : vert vif = prochain vol, cyan = à nous,
    # vert clair = à acheter, gris = pas assez d'argent.
    CarteVol(R:int, Ville:ville_reseau, X:float, Y:float, L:float, Prochain:int):[]canvas_slot =
        var S:[]canvas_slot = array{}
        Achat := if (Achetee[R]) then true else false
        Choisi := if (R = Prochain) then true else false
        Prix := PrixRoute(R)
        Assez := if (AvionTycoon.Argent >= Prix) then true else false
        Minutes := if (M := Round[MinutesRoute(R)]) then M else 5
        Gain := if (V := ValeurPalier[Palier(R) - 1], Arrondi := Round[V]) then Arrondi else 0
        Fond := if (Choisi?) then InterfacePC.CarteChoisie else if (Achat?) then InterfacePC.CarteAchetee else if (Assez?) then InterfacePC.Carte else InterfacePC.CarteGrise
        set S += array{Bloc(Vignette(Fond, L, 600.0), X, Y, L, 600.0, 6)}
        set S += array{Bloc(Rect("052E16", 1.0), X + 19.0, Y + 19.0, L - 38.0, 134.0, 7)}
        set S += array{Bloc(Vignette(Ville.Image, L - 44.0, 128.0), X + 22.0, Y + 22.0, L - 44.0, 128.0, 8)}
        set S += array{Bloc(Etiquette(Ville.Nom, "FFFFFF"), X, Y + 165.0, L, 40.0, 9)}
        set S += array{Bloc(Etiquette(Ville.Pays, "A7F3D0"), X, Y + 204.0, L, 34.0, 9)}
        set S += array{Bloc(Etiquette("{Minutes} MIN FLIGHT", "FFFFFF"), X, Y + 260.0, L, 36.0, 9)}
        set S += array{Bloc(Etiquette("EARNS ~${Abreger(Gain)}", "86EFAC"), X, Y + 300.0, L, 36.0, 9)}
        # le gros bouton
        if (Choisi?):
            set S += array{Bloc(Vignette(InterfacePC.BoutonChoisi, L - 44.0, 128.0), X + 22.0, Y + 440.0, L - 44.0, 128.0, 9)}
            set S += array{Bloc(Etiquette("NEXT FLIGHT", "FFFFFF"), X + 22.0, Y + 482.0, L - 44.0, 40.0, 10)}
        else:
            if (not Achat?, not Assez?):
                set S += array{Bloc(Etiquette("NOT ENOUGH MONEY", "FECACA"), X, Y + 390.0, L, 34.0, 10)}
            Texte := if (Achat?) then "FLY HERE" else "BUY  {TextePrix(Prix)}"
            ImageBouton := if (Achat?) then InterfacePC.BoutonCyan else if (Assez?) then InterfacePC.BoutonVert else InterfacePC.BoutonGris
            set S += BoutonKit(Texte, ImageBouton, X + 22.0, Y + 440.0, L - 44.0, 128.0, 12, R)
        S

    # Les 2 onglets en haut à gauche : FLIGHTS (les vols d'ici) et WORLD MAP (la carte).
    Onglets():[]canvas_slot =
        # l'onglet ouvert est vert vif, l'autre vert foncé
        Vols0 := if (Vue = 0) then InterfacePC.OngletVert else InterfacePC.OngletSombre
        Carte1 := if (Vue = 1) then InterfacePC.OngletVert else InterfacePC.OngletSombre
        BoutonKit("FLIGHTS", Vols0, 40.0, 10.0, 220.0, 56.0, 9, 0) + BoutonKit("WORLD MAP", Carte1, 275.0, 10.0, 240.0, 56.0, 9, 1)

    # L'onglet WORLD MAP, épuré : seulement les lignes achetées, leurs villes, et l'avion.
    # Renvoie les slots et l'image de l'avion (pour l'animer pendant le vol).
    CarteReseau():tuple([]canvas_slot, ?texture_block) =
        var S:[]canvas_slot = array{}
        Titre := if (EnVol[]) then "FLYING TO {NomVille(Vers)}" else "YOU ARE IN {NomVille(Position)}"
        set S += array{Bloc(Etiquette(Titre, "FFFFFF"), 560.0, 168.0, 800.0, 40.0, 6)}
        # seulement les lignes achetées (le prochain vol en vert, plus gros)
        Prochain := ProchainVol()
        for (I -> R : Routes, Achetee[I]):
            A := PointVille(R.A)
            B := PointVille(R.B)
            Vert := if (I = Prochain) then true else if (I = RouteVol, EnVol[]) then true else false
            Couleur := if (Vert?) then "22C55E" else "38BDF8"
            Taille := if (Vert?) then 7.0 else 5.0
            for (K := 0..19):
                Pt := Courbe(A, B, (K * 1.0 + 0.5) / 20.0)
                set S += array{PlaceC(Rect(Couleur, 1.0), Pt.X, Pt.Y, 0.0, 0.0, Taille, Taille, 4)}
        # seulement les villes de ces lignes, et celle où on est
        Cible := Autre(Prochain, VilleBase())
        for (I -> Ville : LesVilles, I = Position or I = Cible or VilleAchetee[I]):
            Ici := if (I = Position) then true else false
            Voisine := if (I = Cible, I <> Position) then true else false
            Couleur := if (Ici?) then "4ADE80" else if (Voisine?) then "FFFFFF" else "BBF7D0"
            Cote := if (Ici?) then 16.0 else 11.0
            set S += array{PlaceC(Rect("0B1620", 1.0), Ville.U, Ville.V, 0.0, 0.0, Cote + 6.0, Cote + 6.0, 5)}
            set S += array{PlaceC(Rect(Couleur, 1.0), Ville.U, Ville.V, 0.0, 0.0, Cote, Cote, 6)}
            # le nom : seulement la ville où on est et la prochaine destination
            if (Ici? or Voisine?):
                Decale := if (Ici?) then 30.0 else -30.0
                set S += array{PlaceC(Etiquette(Ville.Nom, Couleur), Ville.U, Ville.V, 0.0, Decale, 320.0, 40.0, 7)}
        # l'avion : sur la ville au sol, sur la ligne pendant le vol
        Depart := PointVille(Position)
        Arrivee := if (EnVol[]) then PointVille(Vers) else PointVille(Autre(Choisie, Position))
        Icone := if (Arrivee.X >= Depart.X) then Destinations.AvionDroite else Destinations.AvionGauche
        IconeAvion := Vignette(Icone, 44.0, 44.0)
        Pos := if (EnVol[]) then Courbe(Depart, Arrivee, Progression()) else Depart
        set S += array{PlaceC(IconeAvion, Pos.X, Pos.Y, 0.0, -18.0, 44.0, 44.0, 9)}
        (S, option{IconeAvion})

    # Pendant le vol, l'avion de la carte est replacé 10 fois par seconde à sa vraie position.
    AnimerAvion(Numero:int, Toile:canvas, Img:texture_block)<suspends>:void =
        Depart := PointVille(Position)
        Arrivee := PointVille(Vers)
        loop:
            Sleep(0.1)
            if (Numero <> NumeroAnimation or not EnVol[]) { break }
            Pt := Courbe(Depart, Arrivee, Progression())
            Toile.RemoveWidget(Img)
            Toile.AddWidget(PlaceC(Img, Pt.X, Pt.Y, 0.0, -18.0, 44.0, 44.0, 9))

    # ---------- la barre de vol en haut de l'écran ----------
    # Jauge cartoon, petite : 400 x 50 pixels (l'image JaugeVol.Fond fait 8 fois plus large que
    # haut). Le remplissage jaune fait 37 pixels de haut, à 6,5 pixels du bord. DebutJauge = le
    # centre du rond de départ du remplissage. L'avion est plus grand que la jauge : il dépasse.
    LargeurJauge:float = 400.0
    HauteurJauge:float = 50.0
    MargeJauge:float = 6.5
    Remplissage:float = 37.0
    DebutJauge:float = -200.0 + 6.5 + 18.5
    TailleAvion:float = 120.0
    # Toujours affichée sur l'écran du joueur propriétaire de l'avion (en jeu, pas seulement au PC).
    # Une jauge ronde qui se remplit de jaune, avec l'avion cartoon au bout ; la ville de départ
    # à gauche, l'arrivée à droite, le temps restant en dessous. Au sol : le prochain vol.
    BoucleBarre()<suspends>:void =
        loop:
            Sleep(0.05)
            # nouveau propriétaire (ou plus personne) : on retire la barre de l'ancien écran
            if (Ancien := BarreJoueur?, C := Barre?, not EstProprio[Ancien]):
                if (AncienUI := GetPlayerUI[Ancien]) { AncienUI.RemoveWidget(C) }
                set Barre = false
                set BarreJoueur = false
                set BarreMobile = array{}
            if (Proprio := AvionTycoon.Proprio?, J := player[Proprio], UI := GetPlayerUI[J]):
                var Toile:canvas = canvas{}
                if (C := Barre?):
                    set Toile = C
                else:
                    # la jauge vide (ronde, contour foncé), le bout gauche du remplissage, les textes
                    Fixes := array:
                        EnHaut(Vignette(JaugeVol.Fond, LargeurJauge, HauteurJauge), 0.0, 0.0, LargeurJauge, HauteurJauge, 0)
                        EnHaut(Vignette(JaugeVol.Rond, Remplissage, Remplissage), DebutJauge, MargeJauge, Remplissage, Remplissage, 2)
                        EnHaut(TexteDepart, -LargeurJauge / 2.0 - 190.0, HauteurJauge / 2.0 - 20.0, 300.0, 40.0, 5)
                        EnHaut(TexteArrivee, LargeurJauge / 2.0 + 190.0, HauteurJauge / 2.0 - 20.0, 300.0, 40.0, 5)
                        EnHaut(TexteTemps, 0.0, HauteurJauge + 6.0, 260.0, 40.0, 5)
                    Nouvelle := canvas{Slots := Fixes}
                    UI.AddWidget(Nouvelle)
                    set Barre = option{Nouvelle}
                    set BarreJoueur = option{J}
                    set Toile = Nouvelle
                # les textes
                Restant := if (EnVol[]) then DureeVol * (1.0 - Progression()) else DureeVolActive()
                Secondes := if (S := Floor[Restant + 0.5]) then S else 0
                Mn := if (M := Quotient[Secondes, 60]) then M else 0
                Sec := if (X := Mod[Secondes, 60]) then X else 0
                Chrono := if (Sec < 10) then "{Mn}:0{Sec}" else "{Mn}:{Sec}"
                TexteDepart.SetText(Msg(VilleDepart()))
                if (EnVol[] or Routes[Choisie]):
                    TexteArrivee.SetText(Msg(VilleArrivee()))
                    TexteTemps.SetText(Msg(if (EnVol[]) then Chrono else "NEXT  {Chrono}"))
                else:
                    # pas encore de vol : on dit quoi faire
                    TexteArrivee.SetText(Msg("?"))
                    TexteTemps.SetText(Msg("BUY A FLIGHT ON THE PC"))
                # la piste remplie et l'avion
                for (W : BarreMobile) { Toile.RemoveWidget(W) }
                # le remplissage jaune : un rond au début, un rond au bout, un rectangle entre les deux
                # (comme ça les 2 bouts restent bien ronds) ; l'avion cartoon roule sur le bout
                Course := LargeurJauge - 2.0 * MargeJauge - Remplissage
                Bout := DebutJauge + Course * Progression()
                Mobiles := array:
                    EnHaut(Rect("22C55E", 1.0), (DebutJauge + Bout) / 2.0, MargeJauge, Max(1.0, Bout - DebutJauge), Remplissage, 1)
                    EnHaut(Rect("86EFAC", 1.0), (DebutJauge + Bout) / 2.0, MargeJauge + Remplissage * 0.08, Max(1.0, Bout - DebutJauge), Remplissage * 0.3, 1)
                    EnHaut(Vignette(JaugeVol.Rond, Remplissage, Remplissage), Bout, MargeJauge, Remplissage, Remplissage, 2)
                    EnHaut(Vignette(JaugeVol.Avion, TailleAvion, TailleAvion), Bout, HauteurJauge / 2.0 - TailleAvion / 2.0 - 4.0, TailleAvion, TailleAvion, 4)
                for (S : Mobiles) { Toile.AddWidget(S) }
                set BarreMobile = for (S : Mobiles) { S.Widget }

    # Un widget centré horizontalement en haut de l'écran, à DX pixels du milieu, Y pixels sous
    # le haut de la barre.
    EnHaut(W:widget, DX:float, Y:float, L:float, H:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.0}, Maximum := vector2{X := 0.5, Y := 0.0}}
            Alignment := vector2{X := 0.5, Y := 0.0}
            Offsets := margin{Left := DX, Top := HautBarre + Y, Right := L, Bottom := H}
            SizeToContent := false
            ZOrder := Couche
            Widget := W
