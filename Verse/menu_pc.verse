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
# Style cartoon vert "argent", comme l'écran des vols.
# Dans le Tiroir a contenu :
#   dossier InterfacePC : le kit cartoon (Fond, CarteCarree, Carte, Bouton..., Onglet...,
#                         IconeSupplies, IconeUpgrades)
#   dossier JaugeVol    : Avion (l'avion cartoon, icône de DESTINATIONS)
#   dossier MenuPC      : Icone_Panier
#   dossier Produits    : Produit_01_Eau ... Produit_09_Caviar (sans le 07)
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
            # le stock augmente tout de suite
            for (I -> P : ListeProduits, N := PanierLots[I], N > 0):
                AjouterStock(I, N * P.Lot)
            ViderPanier()
            AfficherMessage("THANK YOU FOR YOUR PURCHASE!", true)

    # Appele au paiement : le stock augmente.
    # Le galley prend 1 produit dans le stock (echoue si le stock est vide).
    RetirerUn(Index:int)<transacts><decides>:void =
        S := Stock[Index]
        S > 0
        set Stock[Index] = S - 1

    AjouterStock(Index:int, Unites:int):void =
        if (S := Stock[Index], set Stock[Index] = S + Unites) {}
        if (Page = 1) { Afficher() }

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

    Rect(Hex:string, Opacite:type{_X:float where 0.0 <= _X, _X <= 1.0}):color_block =
        color_block{DefaultColor := MakeColorFromHex(Hex), DefaultOpacity := Opacite}

    # Texte cartoon : ombre vert très foncé.
    Texte(S:string, Hex:string, J:text_justification):text_block =
        text_block:
            DefaultText := Msg(S)
            DefaultTextColor := MakeColorFromHex(Hex)
            DefaultJustification := J
            DefaultShadowColor := MakeColorFromHex("052E16")
            DefaultShadowOpacity := 1.0
            DefaultShadowOffset := option{vector2{X := 3.0, Y := 3.0}}

    Vignette(T:texture, L:float, H:float):texture_block =
        texture_block{DefaultImage := T, DefaultDesiredSize := vector2{X := L, Y := H}}

    # Bouton cartoon : l'image arrondie du kit + le texte + la zone de clic par-dessus.
    Bouton(S:string, Img:texture, X:float, Y:float, L:float, H:float, Action:int, Index:int):[]canvas_slot =
        B := button_quiet{DefaultText := Msg("")}
        B.OnClick().Subscribe(clic_menu{Menu := Self, Action := Action, Index := Index}.Clique)
        array:
            Bloc(Vignette(Img, L, H), X, Y, L, H, 6)
            Bloc(Texte(S, "FFFFFF", text_justification.Center), X, Y + H / 2.0 - 20.0, L, 40.0, 7)
            Bloc(B, X, Y, L, H, 30)

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
                    Widget := texture_block{DefaultImage := InterfacePC.Fond}
                Nouveau := canvas{Slots := array{Fond}}
                UI.AddWidget(Nouveau, player_ui_slot{InputMode := ui_input_mode.All})
                set Base = option{Nouveau}
                set Toile = Nouveau
            for (W : Dynamiques) { Toile.RemoveWidget(W) }
            Slots := if (Page = 0) then PageMenu() else PageBoutique()
            for (S : Slots) { Toile.AddWidget(S) }
            set Dynamiques = for (S : Slots) { S.Widget }

    # Le menu : 3 grandes cartes cartoon, chacune avec son icône et un gros bouton.
    PageMenu():[]canvas_slot =
        var Slots:[]canvas_slot = array{}
        set Slots += array{Bloc(Texte("FLIGHT OPS", "FFFFFF", text_justification.Center), 560.0, 150.0, 800.0, 50.0, 5)}
        set Slots += array{Bloc(Texte("WHAT DO YOU WANT TO DO ?", "BBF7D0", text_justification.Center), 560.0, 200.0, 800.0, 40.0, 5)}
        set Slots += Bouton("CLOSE", InterfacePC.OngletSombre, 1700.0, 10.0, 200.0, 56.0, 10, 0)
        set Slots += CarteMenu(0, "DESTINATIONS", "BUY ROUTES AND FLY", JaugeVol.Avion, true)
        set Slots += CarteMenu(1, "SUPPLIES", "FOOD AND DRINKS", InterfacePC.IconeSupplies, true)
        set Slots += CarteMenu(2, "UPGRADES", "COMING SOON", InterfacePC.IconeUpgrades, false)
        set Slots += LigneMessage(560.0, 900.0, 800.0)
        Slots

    CarteMenu(I:int, Titre:string, Sous:string, Icone:texture, Ouverte:logic):[]canvas_slot =
        X := 225.0 + I * 500.0
        Y := 280.0
        var Slots:[]canvas_slot = array{}
        Fond := if (Ouverte?) then InterfacePC.CarteCarree else InterfacePC.CarteCarreeGrise
        set Slots += array{Bloc(Vignette(Fond, 470.0, 560.0), X, Y, 470.0, 560.0, 2)}
        set Slots += array{Bloc(Vignette(Icone, 250.0, 250.0), X + 110.0, Y + 30.0, 250.0, 250.0, 3)}
        set Slots += array{Bloc(Texte(Titre, "FFFFFF", text_justification.Center), X, Y + 300.0, 470.0, 44.0, 5)}
        CouleurSous := if (Ouverte?) then "A7F3D0" else "CBD5E1"
        set Slots += array{Bloc(Texte(Sous, CouleurSous, text_justification.Center), X, Y + 345.0, 470.0, 36.0, 5)}
        Img := if (Ouverte?) then InterfacePC.BoutonVert else InterfacePC.BoutonGris
        TexteBouton := if (Ouverte?) then "OPEN" else "LOCKED"
        set Slots += Bouton(TexteBouton, Img, X + 115.0, Y + 410.0, 240.0, 120.0, I, 0)
        Slots

    LigneMessage(X:float, Y:float, L:float):[]canvas_slot =
        if (Message <> ""):
            Couleur := if (MessageOk?) then "86EFAC" else "FCA5A5"
            array{Bloc(Texte(Message, Couleur, text_justification.Center), X, Y, L, 40.0, 8)}
        else:
            array{}

    PageBoutique():[]canvas_slot =
        var Slots:[]canvas_slot = array{}
        # en-tete
        set Slots += Bouton("<  BACK", InterfacePC.OngletSombre, 40.0, 10.0, 220.0, 56.0, 9, 0)
        set Slots += array{Bloc(Texte("SUPPLIES", "FFFFFF", text_justification.Left), 290.0, 18.0, 400.0, 44.0, 5)}
        set Slots += LigneMessage(560.0, 22.0, 700.0)
        # produits : 3 par ligne
        for (Ligne := 0..2, Col := 0..2, I := Ligne * 3 + Col, P := ListeProduits[I]):
            set Slots += CarteProduit(I, P, 50.0 + Col * 420.0, 90.0 + Ligne * 325.0)
        # panier
        set Slots += Panier()
        Slots

    # Carte produit cartoon : image, nom, prix, un gros bouton.
    CarteProduit(I:int, P:produit, X:float, Y:float):[]canvas_slot =
        Ouvert := if (Debloque[I]?) then true else false
        Fond := if (Ouvert?) then InterfacePC.CarteCarree else InterfacePC.CarteCarreeGrise
        var Slots:[]canvas_slot = array{Bloc(Vignette(Fond, 400.0, 310.0), X, Y, 400.0, 310.0, 2)}
        set Slots += array{Bloc(Vignette(P.Image, 130.0, 130.0), X + 135.0, Y + 18.0, 130.0, 130.0, 3)}
        set Slots += array{Bloc(Texte(P.Nom, "FFFFFF", text_justification.Center), X, Y + 150.0, 400.0, 36.0, 5)}
        if (Ouvert?):
            set Slots += array{Bloc(Texte("x{P.Lot}  -  {Prix(P.PrixLot)}", "86EFAC", text_justification.Center), X, Y + 186.0, 400.0, 32.0, 5)}
            set Slots += Bouton("ADD TO CART", InterfacePC.BoutonVert, X + 80.0, Y + 222.0, 240.0, 72.0, 3, I)
        else:
            # verrouillé (carte grise) : prix du déblocage
            set Slots += array{Bloc(Texte(Prix(P.PrixDeblocage), "A5F3FC", text_justification.Center), X, Y + 186.0, 400.0, 32.0, 5)}
            Quoi := if (P.Appareil = "") then "UNLOCK" else "BUY {P.Appareil}"
            set Slots += Bouton(Quoi, InterfacePC.BoutonCyan, X + 40.0, Y + 222.0, 320.0, 72.0, 5, I)
        Slots

    Panier():[]canvas_slot =
        X := 1330.0
        L := 540.0
        var Slots:[]canvas_slot = array{Bloc(Vignette(InterfacePC.Carte, L, 980.0), X, 80.0, L, 980.0, 2)}
        set Slots += array{Bloc(Vignette(MenuPC.Icone_Panier, 48.0, 48.0), X + 40.0, 110.0, 48.0, 48.0, 3)}
        set Slots += array{Bloc(Texte("YOUR CART", "FFFFFF", text_justification.Left), X + 100.0, 114.0, 300.0, 40.0, 5)}
        set Slots += array{Bloc(Rect("BBF7D0", 0.5), X + 36.0, 172.0, L - 72.0, 3.0, 3)}

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
            set Slots += array{Bloc(Texte("YOUR CART IS EMPTY", "A7F3D0", text_justification.Center), X, 440.0, L, 36.0, 5)}
        if (Cachees > 0):
            set Slots += array{Bloc(Texte("+ {Cachees} MORE...", "A7F3D0", text_justification.Left), X + 40.0, 185.0 + MaxLignesPanier * 52.0, 300.0, 30.0, 5)}

        # recapitulatif
        Total := TotalPanier()
        Solde := AvionTycoon.Argent
        set Slots += array{Bloc(Rect("BBF7D0", 0.5), X + 36.0, 790.0, L - 72.0, 3.0, 3)}
        set Slots += array{Bloc(Texte("TOTAL", "FFFFFF", text_justification.Left), X + 40.0, 802.0, 200.0, 40.0, 5)}
        set Slots += array{Bloc(Texte(Prix(Total), "FFFFFF", text_justification.Right), X + L - 240.0, 802.0, 200.0, 40.0, 5)}
        set Slots += array{Bloc(Texte("YOUR MONEY", "A7F3D0", text_justification.Left), X + 40.0, 842.0, 250.0, 34.0, 5)}
        CouleurSolde := if (Solde >= Total) then "86EFAC" else "FCA5A5"
        set Slots += array{Bloc(Texte(Prix(Solde), CouleurSolde, text_justification.Right), X + L - 240.0, 842.0, 200.0, 34.0, 5)}
        set Slots += Bouton("CHECKOUT", InterfacePC.BoutonVert, X + 130.0, 885.0, 280.0, 100.0, 7, 0)
        set Slots += Bouton("EMPTY CART", InterfacePC.OngletSombre, X + 150.0, 990.0, 240.0, 56.0, 8, 0)
        Slots

    # Une ligne : nom a gauche, prix a droite, petit bouton "-" pour retirer un lot.
    LignePanier(Ligne:int, Nom:string, Montant:int, Index:int):[]canvas_slot =
        X := 1330.0
        Y := 185.0 + Ligne * 52.0
        var Slots:[]canvas_slot = array{}
        set Slots += array{Bloc(Texte(Nom, "FFFFFF", text_justification.Left), X + 40.0, Y + 6.0, 290.0, 32.0, 5)}
        set Slots += array{Bloc(Texte(Prix(Montant), "86EFAC", text_justification.Right), X + 300.0, Y + 6.0, 130.0, 32.0, 5)}
        set Slots += Bouton("-", InterfacePC.BoutonGris, X + 446.0, Y, 64.0, 44.0, 4, Index)
        Slots
