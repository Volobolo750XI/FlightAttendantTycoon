using { /Fortnite.com/Devices }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - le menu du PC (style GTA) et la boutique SUPPLIES.
#
# On allume le PC -> 3 cartes : DESTINATIONS, SUPPLIES, UPGRADES (verrouillee pour l'instant).
# SUPPLIES = un vrai site : a gauche les produits (3 par ligne), a droite le panier.
# Un produit verrouille se debloque d'abord (paiement direct), ensuite on peut l'acheter.
#
# Dans le Tiroir a contenu :
#   dossier MenuPC   : Fond_Menu, Carte_Destinations, Carte_Marchandises,
#                      Carte_Ameliorations_Verrou, Icone_Panier,
#                      Bouton_Bleu, Bouton_Violet, Bouton_Vert, Bouton_Gris,
#                      Bouton_Gris_Court, Bouton_Gris_Carre
#   dossier Produits : Produit_01_Eau ... Produit_09_Caviar (sans le 07)
#
# Dans l'editeur : pose ce device, remplis AvionTycoon, puis dans le device
# pc_destinations mets ce device dans le champ "Menu".

produit := class:
    Nom:string
    # nombre d'unites dans un lot, et prix du lot
    Lot:int
    PrixLot:int
    # 0 = debloque des le depart
    PrixDeblocage:int
    # ce qu'on achete pour debloquer ("" = le produit lui-meme)
    Appareil:string
    Image:texture

# Un bouton du menu : il retient son action et son produit.
clic_menu := class:
    Menu:menu_pc
    Action:int
    Index:int
    Clique(Clic:widget_message):void = Menu.Agir(Action, Index)

menu_pc := class(creative_device):
    @editable AvionTycoon:avion_tycoon = avion_tycoon{}
    # Son joue a chaque paiement : un Appareil Lecteur audio.
    @editable SonAchat:?audio_player_device = false

    ListeProduits:[]produit = array:
        produit{Nom := "WATER", Lot := 20, PrixLot := 20, PrixDeblocage := 0, Appareil := "", Image := Produits.Produit_01_Eau}
        produit{Nom := "SODA", Lot := 20, PrixLot := 300, PrixDeblocage := 750, Appareil := "", Image := Produits.Produit_02_Soda}
        produit{Nom := "CROISSANT", Lot := 10, PrixLot := 1000, PrixDeblocage := 6000, Appareil := "", Image := Produits.Produit_03_Croissant}
        produit{Nom := "SANDWICH", Lot := 10, PrixLot := 8000, PrixDeblocage := 50000, Appareil := "", Image := Produits.Produit_04_Sandwich}
        produit{Nom := "COFFEE", Lot := 10, PrixLot := 60000, PrixDeblocage := 750000, Appareil := "COFFEE MACHINE", Image := Produits.Produit_05_Cafe}
        produit{Nom := "BURGER", Lot := 5, PrixLot := 250000, PrixDeblocage := 8000000, Appareil := "OVEN", Image := Produits.Produit_06_Burger}
        produit{Nom := "LOBSTER", Lot := 2, PrixLot := 10000000, PrixDeblocage := 1000000000, Appareil := "LOBSTER TANK", Image := Produits.Produit_08_Homard}
        produit{Nom := "CAVIAR", Lot := 1, PrixLot := 60000000, PrixDeblocage := 15000000000, Appareil := "SAFE", Image := Produits.Produit_09_Caviar}

    # Ce que le joueur possede (le galley s'en servira).
    var Debloque:[]logic = array{}
    var Stock:[]int = array{}
    # Le panier : nombre de lots de chaque produit.
    var PanierLots:[]int = array{}

    # 0 = menu des 3 cartes, 1 = SUPPLIES
    var Page:int = 0
    var Joueur:?player = false
    var OrdiPC:?pc_destinations = false
    var Base:?canvas = false
    var Dynamiques:[]widget = array{}
    var Message:string = ""
    var MessageOk:logic = false
    var NumeroMessage:int = 0

    # Couleurs du site
    CouleurCarte:string = "18212D"
    CouleurBord:string = "2A3648"
    CouleurPanneau:string = "111827"
    MaxLignesPanier:int = 11

    OnBegin<override>()<suspends>:void =
        set Debloque = for (P : ListeProduits) { if (P.PrixDeblocage = 0) then true else false }
        set Stock = for (P : ListeProduits) { 0 }
        ViderPanier()

    ViderPanier():void =
        set PanierLots = for (P : ListeProduits) { 0 }

    # ---------- Ouverture / fermeture ----------
    Ouvrir(P:player, Ordinateur:pc_destinations):void =
        Fermer()
        set OrdiPC = option{Ordinateur}
        set Joueur = option{P}
        set Page = 0
        Afficher()

    Fermer():void =
        if (P := Joueur?, UI := GetPlayerUI[P], C := Base?):
            UI.RemoveWidget(C)
        set Base = false
        set Dynamiques = array{}

    # Actions : 0 Destinations, 1 Supplies, 2 Upgrades, 3 ajouter un lot, 4 retirer un lot,
    # 5 debloquer, 7 payer, 8 vider, 9 retour, 10 fermer
    Agir(Action:int, Index:int):void =
        if (Action = 0):
            if (P := Joueur?, Ordinateur := OrdiPC?):
                Fermer()
                set Joueur = false
                Ordinateur.Ouvrir(P)
        else if (Action = 1):
            set Page = 1
            set Message = ""
            Afficher()
        else if (Action = 2):
            AfficherMessage("COMING SOON", false)
        else if (Action = 3):
            if (Debloque[Index]?, N := PanierLots[Index], set PanierLots[Index] = N + 1) {}
            Afficher()
        else if (Action = 4):
            if (N := PanierLots[Index], N > 0, set PanierLots[Index] = N - 1) {}
            Afficher()
        else if (Action = 5):
            Debloquer(Index)
        else if (Action = 7):
            Payer()
        else if (Action = 8):
            ViderPanier()
            Afficher()
        else if (Action = 9):
            set Page = 0
            set Message = ""
            Afficher()
        else if (Action = 10):
            Fermer()
            set Joueur = false

    # Deblocage : paye tout de suite, ensuite le produit s'achete normalement.
    Debloquer(Index:int):void =
        if (P := ListeProduits[Index], not Debloque[Index]?):
            if (AvionTycoon.Argent < P.PrixDeblocage):
                AfficherMessage("NOT ENOUGH MONEY", false)
            else:
                set AvionTycoon.Argent -= P.PrixDeblocage
                AvionTycoon.MettreAJourUI()
                if (Son := SonAchat?) { Son.Play() }
                if (set Debloque[Index] = true) {}
                AfficherMessage("{P.Nom} UNLOCKED!", true)

    TotalPanier():int =
        var Total:int = 0
        for (I -> P : ListeProduits, N := PanierLots[I]):
            set Total += N * P.PrixLot
        Total

    Payer():void =
        Total := TotalPanier()
        if (Total = 0):
            AfficherMessage("YOUR CART IS EMPTY", false)
        else if (AvionTycoon.Argent < Total):
            AfficherMessage("NOT ENOUGH MONEY", false)
        else:
            set AvionTycoon.Argent -= Total
            AvionTycoon.MettreAJourUI()
            if (Son := SonAchat?) { Son.Play() }
            for (I -> P : ListeProduits, N := PanierLots[I], S := Stock[I]):
                if (set Stock[I] = S + N * P.Lot) {}
            ViderPanier()
            AfficherMessage("THANK YOU FOR YOUR PURCHASE!", true)

    AfficherMessage(Contenu:string, Ok:logic):void =
        set Message = Contenu
        set MessageOk = Ok
        set NumeroMessage += 1
        Afficher()
        spawn{EffacerMessage(NumeroMessage)}

    EffacerMessage(Numero:int)<suspends>:void =
        Sleep(2.5)
        if (Numero = NumeroMessage):
            set Message = ""
            Afficher()

    Prix(N:int):string = "${AvionTycoon.Abreger(N)}"

    # ---------- Petits outils d'affichage ----------
    # Tout est place comme sur un ecran 1920 x 1080 (X, Y = coin haut gauche).
    Bloc(W:widget, X:float, Y:float, L:float, H:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.5}, Maximum := vector2{X := 0.5, Y := 0.5}}
            Alignment := vector2{X := 0.0, Y := 0.0}
            Offsets := margin{Left := X - 960.0, Top := Y - 540.0, Right := L, Bottom := H}
            SizeToContent := false
            ZOrder := Couche
            Widget := W

    Rect(Hex:string):color_block = color_block{DefaultColor := MakeColorFromHex(Hex), DefaultOpacity := 1.0}

    Texte(S:string, Hex:string, J:text_justification):text_block =
        text_block{DefaultText := Msg(S), DefaultTextColor := MakeColorFromHex(Hex), DefaultJustification := J}

    Vignette(T:texture, L:float, H:float):texture_block =
        texture_block{DefaultImage := T, DefaultDesiredSize := vector2{X := L, Y := H}}

    # Bouton : une image arrondie de la meme taille que le bouton, le bouton transparent dessus.
    # Tailles prevues pour les images : 8:1 (Bouton_Bleu...), 4:1 (Court), 1:1 (Carre).
    Bouton(S:string, Fond:texture, X:float, Y:float, L:float, H:float, Action:int, Index:int):[]canvas_slot =
        B := button_quiet{DefaultText := Msg(S)}
        B.OnClick().Subscribe(clic_menu{Menu := Self, Action := Action, Index := Index}.Clique)
        array{Bloc(Vignette(Fond, L, H), X, Y, L, H, 3), Bloc(B, X, Y, L, H, 4)}

    # Zone cliquable invisible (sur les cartes du menu).
    Zone(X:float, Y:float, L:float, H:float, Action:int):canvas_slot =
        B := button_quiet{DefaultText := Msg("")}
        B.OnClick().Subscribe(clic_menu{Menu := Self, Action := Action, Index := 0}.Clique)
        Bloc(B, X, Y, L, H, 4)

    # Cadre avec bordure fine.
    Cadre(X:float, Y:float, L:float, H:float, Hex:string):[]canvas_slot =
        array{Bloc(Rect(CouleurBord), X - 1.0, Y - 1.0, L + 2.0, H + 2.0, 1), Bloc(Rect(Hex), X, Y, L, H, 2)}

    # ---------- Construction de l'ecran ----------
    Afficher():void =
        if (P := Joueur?, UI := GetPlayerUI[P]):
            var Toile:canvas = canvas{}
            if (C := Base?):
                set Toile = C
            else:
                Fond := canvas_slot:
                    Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.0}, Maximum := vector2{X := 1.0, Y := 1.0}}
                    Offsets := margin{Left := 0.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
                    SizeToContent := false
                    Widget := texture_block{DefaultImage := MenuPC.Fond_Menu}
                Nouveau := canvas{Slots := array{Fond}}
                UI.AddWidget(Nouveau, player_ui_slot{InputMode := ui_input_mode.All})
                set Base = option{Nouveau}
                set Toile = Nouveau
            for (W : Dynamiques) { Toile.RemoveWidget(W) }
            Slots := if (Page = 0) then PageMenu() else PageBoutique()
            for (S : Slots) { Toile.AddWidget(S) }
            set Dynamiques = for (S : Slots) { S.Widget }

    PageMenu():[]canvas_slot =
        var Slots:[]canvas_slot = array{}
        set Slots += array{Bloc(Texte("FLIGHT OPS", "FFFFFF", text_justification.Left), 60.0, 40.0, 600.0, 50.0, 5)}
        set Slots += Bouton("CLOSE", MenuPC.Bouton_Gris_Court, 1668.0, 40.0, 192.0, 48.0, 10, 0)
        Cartes := array{MenuPC.Carte_Destinations, MenuPC.Carte_Marchandises, MenuPC.Carte_Ameliorations_Verrou}
        for (I -> Carte : Cartes):
            X := 225.0 + I * 500.0
            set Slots += array{Bloc(Vignette(Carte, 470.0, 470.0), X, 300.0, 470.0, 470.0, 2)}
            set Slots += array{Zone(X, 300.0, 470.0, 470.0, I)}
        set Slots += LigneMessage(560.0, 820.0, 800.0)
        Slots

    LigneMessage(X:float, Y:float, L:float):[]canvas_slot =
        if (Message <> ""):
            Couleur := if (MessageOk?) then "4ADE80" else "F87171"
            array{Bloc(Texte(Message, Couleur, text_justification.Center), X, Y, L, 40.0, 6)}
        else:
            array{}

    PageBoutique():[]canvas_slot =
        var Slots:[]canvas_slot = array{}
        # en-tete
        set Slots += Bouton("<  BACK", MenuPC.Bouton_Gris_Court, 60.0, 41.0, 192.0, 48.0, 9, 0)
        set Slots += array{Bloc(Texte("SUPPLIES", "FFFFFF", text_justification.Left), 280.0, 48.0, 400.0, 40.0, 5)}
        set Slots += LigneMessage(560.0, 48.0, 700.0)
        # produits : 3 par ligne
        for (Ligne := 0..2, Col := 0..2, I := Ligne * 3 + Col, P := ListeProduits[I]):
            set Slots += CarteProduit(I, P, 60.0 + Col * 415.0, 120.0 + Ligne * 310.0)
        # panier
        set Slots += Panier()
        Slots

    # Carte produit : image, nom, une ligne de prix, un bouton. Rien de plus.
    CarteProduit(I:int, P:produit, X:float, Y:float):[]canvas_slot =
        var Slots:[]canvas_slot = Cadre(X, Y, 390.0, 295.0, CouleurCarte)
        set Slots += array{Bloc(Vignette(P.Image, 150.0, 150.0), X + 120.0, Y + 14.0, 150.0, 150.0, 3)}
        set Slots += array{Bloc(Texte(P.Nom, "FFFFFF", text_justification.Center), X, Y + 172.0, 390.0, 32.0, 5)}
        if (Debloque[I]?):
            set Slots += array{Bloc(Texte("x{P.Lot}  -  {Prix(P.PrixLot)}", "7DD3FC", text_justification.Center), X, Y + 204.0, 390.0, 28.0, 5)}
            set Slots += Bouton("ADD TO CART", MenuPC.Bouton_Bleu, X + 19.0, Y + 238.0, 352.0, 44.0, 3, I)
        else:
            # verrouille : image assombrie, prix du deblocage
            set Slots += array{Bloc(color_block{DefaultColor := MakeColorFromHex(CouleurCarte), DefaultOpacity := 0.6}, X + 120.0, Y + 14.0, 150.0, 150.0, 4)}
            set Slots += array{Bloc(Texte(Prix(P.PrixDeblocage), "C4B5FD", text_justification.Center), X, Y + 204.0, 390.0, 28.0, 5)}
            Quoi := if (P.Appareil = "") then "UNLOCK" else "BUY {P.Appareil}"
            set Slots += Bouton(Quoi, MenuPC.Bouton_Violet, X + 19.0, Y + 238.0, 352.0, 44.0, 5, I)
        Slots

    Panier():[]canvas_slot =
        X := 1330.0
        L := 530.0
        var Slots:[]canvas_slot = Cadre(X, 40.0, L, 1000.0, CouleurPanneau)
        set Slots += array{Bloc(Vignette(MenuPC.Icone_Panier, 48.0, 48.0), X + 24.0, 60.0, 48.0, 48.0, 3)}
        set Slots += array{Bloc(Texte("YOUR CART", "FFFFFF", text_justification.Left), X + 86.0, 68.0, 300.0, 36.0, 5)}
        set Slots += array{Bloc(Rect(CouleurBord), X + 20.0, 128.0, L - 40.0, 2.0, 3)}

        # lignes du panier
        var Ligne:int = 0
        var Cachees:int = 0
        for (I -> P : ListeProduits, N := PanierLots[I], N > 0):
            if (Ligne < MaxLignesPanier):
                set Slots += LignePanier(Ligne, "{P.Nom} x{N * P.Lot}", N * P.PrixLot, I)
                set Ligne += 1
            else:
                set Cachees += 1
        if (Ligne = 0):
            set Slots += array{Bloc(Texte("Your cart is empty", "64748B", text_justification.Center), X, 400.0, L, 36.0, 5)}
        if (Cachees > 0):
            set Slots += array{Bloc(Texte("+ {Cachees} more...", "94A3B8", text_justification.Left), X + 24.0, 145.0 + MaxLignesPanier * 54.0, 300.0, 30.0, 5)}

        # recapitulatif
        Total := TotalPanier()
        Solde := AvionTycoon.Argent
        set Slots += array{Bloc(Rect(CouleurBord), X + 20.0, 790.0, L - 40.0, 2.0, 3)}
        set Slots += array{Bloc(Texte("TOTAL", "FFFFFF", text_justification.Left), X + 24.0, 805.0, 200.0, 36.0, 5)}
        set Slots += array{Bloc(Texte(Prix(Total), "FFFFFF", text_justification.Right), X + L - 224.0, 805.0, 200.0, 36.0, 5)}
        set Slots += array{Bloc(Texte("YOUR BALANCE", "94A3B8", text_justification.Left), X + 24.0, 843.0, 250.0, 30.0, 5)}
        CouleurSolde := if (Solde >= Total) then "94A3B8" else "F87171"
        set Slots += array{Bloc(Texte(Prix(Solde), CouleurSolde, text_justification.Right), X + L - 224.0, 843.0, 200.0, 30.0, 5)}
        set Slots += Bouton("CHECKOUT", MenuPC.Bouton_Vert, X + 25.0, 895.0, 480.0, 60.0, 7, 0)
        set Slots += Bouton("EMPTY CART", MenuPC.Bouton_Gris, X + 89.0, 970.0, 352.0, 44.0, 8, 0)
        Slots

    # Une ligne : nom a gauche, prix a droite, petit bouton "-" pour retirer un lot.
    LignePanier(Ligne:int, Nom:string, Montant:int, Index:int):[]canvas_slot =
        X := 1330.0
        Y := 145.0 + Ligne * 54.0
        var Slots:[]canvas_slot = array{}
        set Slots += array{Bloc(Texte(Nom, "E2E8F0", text_justification.Left), X + 24.0, Y + 6.0, 300.0, 32.0, 5)}
        set Slots += array{Bloc(Texte(Prix(Montant), "E2E8F0", text_justification.Right), X + 310.0, Y + 6.0, 140.0, 32.0, 5)}
        set Slots += Bouton("-", MenuPC.Bouton_Gris_Carre, X + 466.0, Y + 2.0, 40.0, 40.0, 4, Index)
        Slots
