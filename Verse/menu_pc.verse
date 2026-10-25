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
#                         IconeDestinations, IconeSupplies, IconeUpgrades)
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

# Une amelioration de l'onglet UPGRADES.
# Cat : 0 AIRPLANE, 1 SPACES, 2 CLASSES, 3 STAFF, 4 REBIRTH.
# Requis : nom d'une autre amelioration a acheter avant (ex : BARMAN demande BAR).
# Les bonus se multiplient entre eux (ex : PREMIUM x2 puis BUSINESS x2.5 = billets x5).
amelioration := class:
    Nom:string
    Effet:string
    Prix:int
    Cat:int
    Image:texture
    # nom de l'image du dossier Ameliorations (en attendant qu'elles soient importees)
    Fichier:string = ""
    Requis:string = ""
    Billet:float = 1.0
    Service:float = 1.0
    Repas:float = 1.0
    Patience:float = 1.0

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
    # ANCIENNE METHODE (changer d'avion depuis le PC) : NE PLUS REMPLIR, laisser vide.
    # On change maintenant d'avion avec la dalle WIDER CABIN (avion_tycoon, ArriveeNouvelAvion).
    @editable AvionDepart:?creative_prop = false
    # Les Blueprints des avions, dans l'ordre : 1er = Avion_Niveau1, 2e = Avion_Niveau2 (MIDDLE ROW), etc.
    # (rien a poser dans la map, juste les choisir ici). Tant qu'un avion manque, sa carte affiche COMING SOON.
    @editable ModelesAvions:[]creative_prop_asset = array{}
    # Le texte cartoon (images du dossier TexteCartoon) : ecriture_cartoon.verse
    Ecriture:ecriture_cartoon = ecriture_cartoon{}

    ListeProduits:[]produit = array:
        produit{Nom := "WATER", Lot := 20, PrixLot := 20, PrixDeblocage := 0, Appareil := "", Image := Produits.Produit_01_Eau}
        produit{Nom := "SODA", Lot := 20, PrixLot := 300, PrixDeblocage := 750, Appareil := "", Image := Produits.Produit_02_Soda}
        produit{Nom := "CROISSANT", Lot := 10, PrixLot := 1000, PrixDeblocage := 6000, Appareil := "", Image := Produits.Produit_03_Croissant}
        produit{Nom := "SANDWICH", Lot := 10, PrixLot := 8000, PrixDeblocage := 50000, Appareil := "", Image := Produits.Produit_04_Sandwich}
        produit{Nom := "COFFEE", Lot := 10, PrixLot := 60000, PrixDeblocage := 750000, Appareil := "COFFEE MACHINE", Image := Produits.Produit_05_Cafe}
        produit{Nom := "BURGER", Lot := 5, PrixLot := 250000, PrixDeblocage := 8000000, Appareil := "OVEN", Image := Produits.Produit_06_Burger}
        produit{Nom := "LOBSTER", Lot := 2, PrixLot := 10000000, PrixDeblocage := 1000000000, Appareil := "LOBSTER TANK", Image := Produits.Produit_08_Homard}
        produit{Nom := "CAVIAR", Lot := 1, PrixLot := 60000000, PrixDeblocage := 15000000000, Appareil := "SAFE", Image := Produits.Produit_09_Caviar}

    # Prix calés sur les gains : un vol plein rapporte ~1.6K (lignes niveau 1) ... ~3B (niveau 8),
    # sans compter les bonus. Une amelioration coute ~2 a 10 vols du niveau ou on l'achete ;
    # les dernieres demandent des bonus et des rebirths (fin du jeu tres longue).
    ListeAmeliorations:[]amelioration = array:
        # 0 AIRPLANE : d'abord plus large (1|1 -> 2|2 -> 3|3|3), ensuite des etages
        amelioration{Nom := "A320", Effet := "1 | 1 SEATS", Prix := 0, Cat := 0, Image := InterfacePC.IconeUpgrades, Fichier := "Avion_01"}
        amelioration{Nom := "WIDER CABIN", Effet := "2 | 2 SEATS", Prix := 300000, Cat := 0, Image := InterfacePC.IconeUpgrades, Fichier := "Avion_02", Billet := 1.5}
        amelioration{Nom := "WIDE BODY", Effet := "3 | 3 | 3 SEATS", Prix := 50000000, Cat := 0, Image := InterfacePC.IconeUpgrades, Fichier := "Avion_03", Billet := 2.0}
        amelioration{Nom := "2ND FLOOR", Effet := "TICKETS x2", Prix := 20000000000, Cat := 0, Image := InterfacePC.IconeUpgrades, Fichier := "Avion_04", Billet := 2.0}
        amelioration{Nom := "3RD FLOOR", Effet := "TICKETS x2", Prix := 1000000000000, Cat := 0, Image := InterfacePC.IconeUpgrades, Fichier := "Avion_05", Billet := 2.0}
        amelioration{Nom := "4TH FLOOR", Effet := "TICKETS x3", Prix := 50000000000000, Cat := 0, Image := InterfacePC.IconeUpgrades, Fichier := "Avion_06", Billet := 3.0}
        amelioration{Nom := "GOLDEN GIANT", Effet := "TICKETS x5", Prix := 5000000000000000, Cat := 0, Image := InterfacePC.IconeUpgrades, Fichier := "Avion_07", Billet := 5.0}
        # 1 SPACES (debloquent certains employes)
        amelioration{Nom := "BAR", Effet := "SERVICE x1.5", Prix := 50000, Cat := 1, Image := InterfacePC.IconeUpgrades, Fichier := "Espace_Bar", Service := 1.5}
        amelioration{Nom := "LOUNGE", Effet := "PATIENCE x1.5", Prix := 3000000, Cat := 1, Image := InterfacePC.IconeUpgrades, Fichier := "Espace_Salon", Patience := 1.5}
        amelioration{Nom := "RESTAURANT", Effet := "MEALS x2", Prix := 200000000, Cat := 1, Image := InterfacePC.IconeUpgrades, Fichier := "Espace_Restaurant", Repas := 2.0}
        amelioration{Nom := "CINEMA", Effet := "PATIENCE x2", Prix := 8000000000, Cat := 1, Image := InterfacePC.IconeUpgrades, Fichier := "Espace_Cinema", Patience := 2.0}
        amelioration{Nom := "DUTY FREE", Effet := "TICKETS x2", Prix := 400000000000, Cat := 1, Image := InterfacePC.IconeUpgrades, Fichier := "Espace_DutyFree", Billet := 2.0}
        # 2 CLASSES : chacune = toute une zone de l'avion (ses rangees, ses sieges, un rideau)
        amelioration{Nom := "PREMIUM ZONE", Effet := "TICKETS x2", Prix := 20000, Cat := 2, Image := InterfacePC.IconeUpgrades, Fichier := "Classe_Premium", Billet := 2.0}
        amelioration{Nom := "BUSINESS ZONE", Effet := "TICKETS x2.5", Prix := 1000000, Cat := 2, Image := InterfacePC.IconeUpgrades, Fichier := "Classe_Business", Billet := 2.5}
        amelioration{Nom := "FIRST ZONE", Effet := "TICKETS x3", Prix := 80000000, Cat := 2, Image := InterfacePC.IconeUpgrades, Fichier := "Classe_First", Billet := 3.0}
        amelioration{Nom := "ROYAL SUITES", Effet := "TICKETS x3.5", Prix := 5000000000, Cat := 2, Image := InterfacePC.IconeUpgrades, Fichier := "Classe_Suite", Billet := 3.5}
        # 3 STAFF : des employes qui font une partie du travail
        amelioration{Nom := "TICKET AGENT", Effet := "CHECKS TICKETS", Prix := 10000, Cat := 3, Image := InterfacePC.IconeUpgrades, Fichier := "Equipe_Billets", Billet := 1.5}
        amelioration{Nom := "BIN AGENT", Effet := "CLOSES THE BINS", Prix := 400000, Cat := 3, Image := InterfacePC.IconeUpgrades, Fichier := "Equipe_Coffres", Patience := 1.5}
        amelioration{Nom := "GALLEY STEWARD", Effet := "SERVES WITH YOU", Prix := 20000000, Cat := 3, Image := InterfacePC.IconeUpgrades, Fichier := "Equipe_Galley", Service := 2.0}
        amelioration{Nom := "BARMAN", Effet := "SERVICE x2", Prix := 500000000, Cat := 3, Image := InterfacePC.IconeUpgrades, Fichier := "Equipe_Barman", Requis := "BAR", Service := 2.0}
        amelioration{Nom := "CHEF", Effet := "MEALS x3", Prix := 30000000000, Cat := 3, Image := InterfacePC.IconeUpgrades, Fichier := "Equipe_Chef", Requis := "RESTAURANT", Repas := 3.0}
        # 5 REBIRTH (se rachete a l'infini, demande le GOLDEN GIANT)
        amelioration{Nom := "REBIRTH", Effet := "RESTART, EARN MORE", Prix := 0, Cat := 4, Image := InterfacePC.IconeUpgrades, Fichier := "Rebirth"}

    # En attendant les images du dossier Ameliorations : l'icone UPGRADES (la cle) partout.
    # Quand les 29 images seront importees, on remplace par Ameliorations.<Fichier>.

    NomsOnglets:[]string = array{"AIRPLANE", "SPACES", "CLASSES", "STAFF", "REBIRTH"}

    # Ameliorations achetees (meme ordre que ListeAmeliorations)
    var Achete:[]logic = array{}
    # Onglet ouvert dans UPGRADES
    var Onglet:int = 0
    # L'avion actuellement dans la map, et son niveau (0 = A320)
    var AvionActuel:?creative_prop = false
    var NiveauAvion:int = 0

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
        set AvionActuel = AvionDepart
        RemettreAmeliorations()

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
    # 5 debloquer, 7 payer, 8 vider, 9 retour, 10 fermer,
    # 11 onglet des upgrades (Index = onglet), 12 acheter une amelioration (Index), 13 rien
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
            set Page = 2
            set Onglet = 0
            set Message = ""
            Afficher()
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
        else if (Action = 11):
            set Onglet = Index
            set Message = ""
            Afficher()
        else if (Action = 12):
            AcheterAmelioration(Index)

    # ---------- UPGRADES ----------
    RemettreAmeliorations():void =
        set Achete = for (A : ListeAmeliorations) { if (A.Prix = 0, A.Cat <> 4) then true else false }
        AppliquerEffets()

    # Place de l'amelioration dans sa categorie (0 = la 1re).
    Rang(I:int)<transacts>:int =
        var N:int = 0
        if (A := ListeAmeliorations[I]):
            for (J -> B : ListeAmeliorations, J < I, B.Cat = A.Cat) { set N += 1 }
        N

    # Achetable : toutes les precedentes de la meme categorie sont deja achetees.
    Disponible(I:int)<transacts>:logic =
        var Ok:logic = true
        if (A := ListeAmeliorations[I]):
            for (J -> B : ListeAmeliorations, J < I, B.Cat = A.Cat, not Achete[J]?) { set Ok = false }
        Ok

    # L'amelioration demandee (Requis) est achetee.
    RequisOk(I:int)<transacts>:logic =
        var Ok:logic = true
        if (A := ListeAmeliorations[I], A.Requis <> ""):
            set Ok = false
            for (J -> B : ListeAmeliorations, B.Nom = A.Requis, Achete[J]?) { set Ok = true }
        Ok

    # Tous les avions achetes (condition du rebirth).
    TousLesAvions()<transacts>:logic =
        var Ok:logic = true
        for (J -> B : ListeAmeliorations, B.Cat = 0, not Achete[J]?) { set Ok = false }
        Ok

    AvionExiste(Niveau:int)<transacts>:logic =
        if (Niveau = 0) then true else if (ModelesAvions[Niveau]) then true else false

    # Remplace l'avion de la map par celui du niveau donne (meme position, meme rotation).
    ChangerAvion(Niveau:int):void =
        if (Niveau <> NiveauAvion, Modele := ModelesAvions[Niveau], Ancien := AvionActuel?):
            T := Ancien.GetTransform()
            Resultat := SpawnProp(Modele, T.Translation, T.Rotation)
            if (Nouveau := Resultat(0)?):
                Ancien.Dispose()
                set AvionActuel = option{Nouveau}
                set NiveauAvion = Niveau

    AppliquerEffets():void =
        var Billet:float = 1.0
        var Service:float = 1.0
        var Repas:float = 1.0
        var Pat:float = 1.0
        for (I -> A : ListeAmeliorations, Achete[I]?):
            set Billet *= A.Billet
            set Service *= A.Service
            set Repas *= A.Repas
            set Pat *= A.Patience
        set AvionTycoon.MultiBillet = Billet
        set AvionTycoon.MultiService = Service
        set AvionTycoon.MultiRepas = Repas
        set AvionTycoon.MultiPatience = Pat
        set AvionTycoon.MultiRebirth = 1.0 + AvionTycoon.Rebirths * 1.0

    AcheterAmelioration(I:int):void =
        if (A := ListeAmeliorations[I]):
            if (A.Cat = 4):
                Renaitre()
            else if (Achete[I]?):
                AfficherMessage("ALREADY OWNED", true)
            else if (not RequisOk(I)?):
                AfficherMessage("BUY THE {A.Requis} FIRST", false)
            else if (not Disponible(I)?):
                AfficherMessage("BUY THE PREVIOUS ONE FIRST", false)
            else if (A.Cat = 0, not AvionExiste(Rang(I))?):
                AfficherMessage("COMING SOON", false)
            else if (AvionTycoon.Argent < A.Prix):
                AfficherMessage("NOT ENOUGH MONEY", false)
            else:
                AvionTycoon.Depenser(A.Prix)
                if (set Achete[I] = true) {}
                AppliquerEffets()
                AvionTycoon.MettreAJourUI()
                if (Son := SonAchat?) { Son.Play() }
                if (A.Cat = 0) { ChangerAvion(Rang(I)) }
                AfficherMessage("{A.Nom} UNLOCKED!", true)

    # Rebirth : on repart de zero (argent, ameliorations, A320) mais tout rapporte plus, pour toujours.
    Renaitre():void =
        if (not TousLesAvions()?):
            AfficherMessage("BUY THE GOLDEN GIANT FIRST", false)
        else:
            set AvionTycoon.Rebirths += 1
            set AvionTycoon.Argent = 0
            RemettreAmeliorations()
            ChangerAvion(0)
            AvionTycoon.MettreAJourUI()
            if (Son := SonAchat?) { Son.Play() }
            AfficherMessage("REBIRTH! EVERYTHING EARNS x{AvionTycoon.Rebirths + 1}", true)

    # Deblocage : paye tout de suite, ensuite le produit s'achete normalement.
    Debloquer(Index:int):void =
        if (P := ListeProduits[Index], not Debloque[Index]?):
            if (AvionTycoon.Argent < P.PrixDeblocage):
                AfficherMessage("NOT ENOUGH MONEY", false)
            else:
                AvionTycoon.Depenser(P.PrixDeblocage)
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
            AvionTycoon.Depenser(Total)
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
        # le texte est un peu au-dessus du centre : le bas du bouton est son epaisseur 3D
        var Slots:[]canvas_slot = array{Bloc(Vignette(Img, L, H), X, Y, L, H, 6)}
        set Slots += Ecriture.Ecrire(S, "FFFFFF", text_justification.Center, X + L * 0.08, Y + H * 0.20, L * 0.84, H * 0.50, 7)
        set Slots += array{Bloc(B, X, Y, L, H, 30)}
        Slots

    # Une fenetre cartoon : grand panneau clair, bandeau bleu avec son icone et son titre,
    # gros bouton rouge X en haut a droite (Action : fermer ou revenir).
    Fenetre(Titre:string, Icone:texture, X:float, Y:float, L:float, H:float, Action:int):[]canvas_slot =
        var Slots:[]canvas_slot = array{Bloc(Vignette(InterfacePC.Panneau, L, H - 60.0), X, Y + 60.0, L, H - 60.0, 1)}
        set Slots += array{Bloc(Vignette(InterfacePC.Entete, L + 20.0, 140.0), X - 10.0, Y, L + 20.0, 140.0, 3)}
        set Slots += array{Bloc(Vignette(Icone, 160.0, 160.0), X + 10.0, Y - 30.0, 160.0, 160.0, 4)}
        set Slots += Ecriture.Ecrire(Titre, "FFFFFF", text_justification.Center, X + 180.0, Y + 22.0, L - 360.0, 76.0, 5)
        set Slots += Bouton("", InterfacePC.Fermer, X + L - 110.0, Y - 14.0, 130.0, 130.0, Action, 0)
        Slots

    # Bandeau du haut des grandes pages (SUPPLIES, UPGRADES) : titre a gauche, bouton X (retour) a droite.
    BandeauHaut(Titre:string, Icone:texture):[]canvas_slot =
        var Slots:[]canvas_slot = array{Bloc(Vignette(InterfacePC.Entete, 1900.0, 84.0), 10.0, 2.0, 1900.0, 84.0, 4)}
        set Slots += array{Bloc(Vignette(Icone, 96.0, 96.0), 24.0, 0.0, 84.0, 84.0, 5)}
        set Slots += Ecriture.Ecrire(Titre, "FFFFFF", text_justification.Left, 130.0, 12.0, 420.0, 54.0, 6)
        set Slots += Bouton("", InterfacePC.Fermer, 1824.0, 0.0, 88.0, 88.0, 9, 0)
        Slots

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
            Slots := if (Page = 0) then PageMenu() else if (Page = 1) then PageBoutique() else PageAmeliorations()
            for (S : Slots) { Toile.AddWidget(S) }
            set Dynamiques = for (S : Slots) { S.Widget }

    # Le menu : une fenetre cartoon avec 3 grandes lignes de couleur (icone + gros bouton).
    PageMenu():[]canvas_slot =
        var Slots:[]canvas_slot = Fenetre("FLIGHT OPS", InterfacePC.IconeSupplies, 460.0, 130.0, 1000.0, 830.0, 10)
        set Slots += LigneMenu(0, "DESTINATIONS", "BUY ROUTES AND FLY", InterfacePC.IconeDestinations, InterfacePC.LigneCyan, true)
        set Slots += LigneMenu(1, "SUPPLIES", "FOOD AND DRINKS", InterfacePC.IconeSupplies, InterfacePC.LigneVerte, true)
        set Slots += LigneMenu(2, "UPGRADES", "GROW YOUR PLANE", InterfacePC.IconeUpgrades, InterfacePC.LigneViolette, true)
        set Slots += LigneMessage(460.0, 895.0, 1000.0)
        Slots

    LigneMenu(I:int, Titre:string, Sous:string, Icone:texture, Couleur:texture, Ouverte:logic):[]canvas_slot =
        X := 500.0
        Y := 290.0 + I * 195.0
        var Slots:[]canvas_slot = array{}
        Fond := if (Ouverte?) then Couleur else InterfacePC.LigneGrise
        set Slots += array{Bloc(Vignette(Fond, 920.0, 180.0), X, Y, 920.0, 180.0, 2)}
        set Slots += Ecriture.Ecrire(Titre, "FFFFFF", text_justification.Left, X + 40.0, Y + 28.0, 470.0, 64.0, 5)
        set Slots += Ecriture.Ecrire(Sous, "E6FBFF", text_justification.Left, X + 40.0, Y + 102.0, 470.0, 36.0, 5)
        set Slots += array{Bloc(Vignette(Icone, 165.0, 165.0), X + 500.0, Y + 6.0, 165.0, 165.0, 3)}
        Img := if (Ouverte?) then InterfacePC.BoutonVert else InterfacePC.BoutonGris
        TexteBouton := if (Ouverte?) then "OPEN" else "LOCKED"
        set Slots += Bouton(TexteBouton, Img, X + 690.0, Y + 38.0, 200.0, 100.0, I, 0)
        Slots

    LigneMessage(X:float, Y:float, L:float):[]canvas_slot =
        if (Message <> ""):
            Couleur := if (MessageOk?) then "86EFAC" else "FCA5A5"
            Ecriture.Ecrire(Message, Couleur, text_justification.Center, X, Y, L, 40.0, 8)
        else:
            array{}

    PageBoutique():[]canvas_slot =
        var Slots:[]canvas_slot = array{}
        # en-tete
        set Slots += BandeauHaut("SUPPLIES", InterfacePC.IconeSupplies)
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
        set Slots += Ecriture.Ecrire(P.Nom, "FFFFFF", text_justification.Center, X, Y + 150.0, 400.0, 36.0, 5)
        if (Ouvert?):
            set Slots += Ecriture.Ecrire("x{P.Lot}  -  {Prix(P.PrixLot)}", "86EFAC", text_justification.Center, X, Y + 186.0, 400.0, 32.0, 5)
            set Slots += Bouton("ADD TO CART", InterfacePC.BoutonVert, X + 80.0, Y + 222.0, 240.0, 72.0, 3, I)
        else:
            # verrouillé (carte grise) : prix du déblocage
            set Slots += Ecriture.Ecrire(Prix(P.PrixDeblocage), "A5F3FC", text_justification.Center, X, Y + 186.0, 400.0, 32.0, 5)
            Quoi := if (P.Appareil = "") then "UNLOCK" else "BUY {P.Appareil}"
            set Slots += Bouton(Quoi, InterfacePC.BoutonCyan, X + 40.0, Y + 222.0, 320.0, 72.0, 5, I)
        Slots

    Panier():[]canvas_slot =
        X := 1330.0
        L := 540.0
        var Slots:[]canvas_slot = array{Bloc(Vignette(InterfacePC.Carte, L, 980.0), X, 80.0, L, 980.0, 2)}
        set Slots += array{Bloc(Vignette(MenuPC.Icone_Panier, 48.0, 48.0), X + 40.0, 110.0, 48.0, 48.0, 3)}
        set Slots += Ecriture.Ecrire("YOUR CART", "FFFFFF", text_justification.Left, X + 100.0, 114.0, 300.0, 40.0, 5)
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
            set Slots += Ecriture.Ecrire("YOUR CART IS EMPTY", "A7F3D0", text_justification.Center, X, 440.0, L, 36.0, 5)
        if (Cachees > 0):
            set Slots += Ecriture.Ecrire("+ {Cachees} MORE...", "A7F3D0", text_justification.Left, X + 40.0, 185.0 + MaxLignesPanier * 52.0, 300.0, 30.0, 5)

        # recapitulatif
        Total := TotalPanier()
        Solde := AvionTycoon.Argent
        set Slots += array{Bloc(Rect("BBF7D0", 0.5), X + 36.0, 790.0, L - 72.0, 3.0, 3)}
        set Slots += Ecriture.Ecrire("TOTAL", "FFFFFF", text_justification.Left, X + 40.0, 802.0, 200.0, 40.0, 5)
        set Slots += Ecriture.Ecrire(Prix(Total), "FFFFFF", text_justification.Right, X + L - 240.0, 802.0, 200.0, 40.0, 5)
        set Slots += Ecriture.Ecrire("YOUR MONEY", "A7F3D0", text_justification.Left, X + 40.0, 842.0, 250.0, 34.0, 5)
        CouleurSolde := if (Solde >= Total) then "86EFAC" else "FCA5A5"
        set Slots += Ecriture.Ecrire(Prix(Solde), CouleurSolde, text_justification.Right, X + L - 240.0, 842.0, 200.0, 34.0, 5)
        set Slots += Bouton("CHECKOUT", InterfacePC.BoutonVert, X + 130.0, 885.0, 280.0, 100.0, 7, 0)
        set Slots += Bouton("EMPTY CART", InterfacePC.OngletSombre, X + 150.0, 990.0, 240.0, 56.0, 8, 0)
        Slots

    # Une ligne : nom a gauche, prix a droite, petit bouton "-" pour retirer un lot.
    LignePanier(Ligne:int, Nom:string, Montant:int, Index:int):[]canvas_slot =
        X := 1330.0
        Y := 185.0 + Ligne * 52.0
        var Slots:[]canvas_slot = array{}
        set Slots += Ecriture.Ecrire(Nom, "FFFFFF", text_justification.Left, X + 40.0, Y + 6.0, 290.0, 32.0, 5)
        set Slots += Ecriture.Ecrire(Prix(Montant), "86EFAC", text_justification.Right, X + 300.0, Y + 6.0, 130.0, 32.0, 5)
        set Slots += Bouton("-", InterfacePC.BoutonGris, X + 446.0, Y, 64.0, 44.0, 4, Index)
        Slots

    # ---------- Page UPGRADES : onglets + cartes (5 par ligne) ----------
    PageAmeliorations():[]canvas_slot =
        var Slots:[]canvas_slot = array{}
        # en-tete
        set Slots += BandeauHaut("UPGRADES", InterfacePC.IconeUpgrades)
        set Slots += Ecriture.Ecrire(Prix(AvionTycoon.Argent), "BBF7D0", text_justification.Right, 1380.0, 16.0, 420.0, 50.0, 6)
        set Slots += LigneMessage(560.0, 22.0, 800.0)
        # onglets
        for (K -> Nom : NomsOnglets):
            Img := if (K = Onglet) then InterfacePC.OngletVert else InterfacePC.OngletSombre
            set Slots += Bouton(Nom, Img, 270.0 + K * 280.0, 86.0, 260.0, 64.0, 11, K)
        if (Onglet = 4):
            set Slots += PageRebirth()
        else:
            Indices := for (I -> A : ListeAmeliorations, A.Cat = Onglet) { I }
            for (K -> I : Indices, Col := Mod[K, 5], Ligne := Quotient[K, 5], A := ListeAmeliorations[I]):
                set Slots += CarteAmelioration(I, A, 60.0 + Col * 365.0, 175.0 + Ligne * 450.0)
        Slots

    # Carte : fond (verte / achetee / grise), icone, nom, bonus, prix, bouton.
    CarteAmelioration(I:int, A:amelioration, X:float, Y:float):[]canvas_slot =
        Possede := if (Achete[I]?) then true else false
        Ouvert := if (not Possede?, Disponible(I)?, RequisOk(I)?) then true else false
        Bientot := if (A.Cat = 0, not AvionExiste(Rang(I))?) then true else false
        Fond := if (Possede?) then InterfacePC.CarteAchetee else if (Ouvert?) then InterfacePC.CarteCarree else InterfacePC.CarteCarreeGrise
        var Slots:[]canvas_slot = array{Bloc(Vignette(Fond, 340.0, 430.0), X, Y, 340.0, 430.0, 2)}
        set Slots += array{Bloc(Vignette(A.Image, 190.0, 190.0), X + 75.0, Y + 20.0, 190.0, 190.0, 3)}
        set Slots += Ecriture.Ecrire(A.Nom, "FFFFFF", text_justification.Center, X, Y + 218.0, 340.0, 40.0, 5)
        set Slots += Ecriture.Ecrire(A.Effet, "A7F3D0", text_justification.Center, X, Y + 260.0, 340.0, 32.0, 5)
        if (Possede?):
            set Slots += Bouton("OWNED", InterfacePC.BoutonChoisi, X + 50.0, Y + 330.0, 240.0, 80.0, 13, I)
        else if (Bientot?):
            set Slots += Ecriture.Ecrire(Prix(A.Prix), "CBD5E1", text_justification.Center, X, Y + 294.0, 340.0, 32.0, 5)
            set Slots += Bouton("COMING SOON", InterfacePC.BoutonGris, X + 30.0, Y + 330.0, 280.0, 80.0, 12, I)
        else if (Ouvert?):
            Couleur := if (AvionTycoon.Argent >= A.Prix) then "86EFAC" else "FCA5A5"
            set Slots += Ecriture.Ecrire(Prix(A.Prix), Couleur, text_justification.Center, X, Y + 294.0, 340.0, 32.0, 5)
            set Slots += Bouton("BUY", InterfacePC.BoutonVert, X + 50.0, Y + 330.0, 240.0, 80.0, 12, I)
        else if (not RequisOk(I)?):
            set Slots += Ecriture.Ecrire("NEEDS {A.Requis}", "FCA5A5", text_justification.Center, X, Y + 294.0, 340.0, 32.0, 5)
            set Slots += Bouton("LOCKED", InterfacePC.BoutonGris, X + 50.0, Y + 330.0, 240.0, 80.0, 12, I)
        else:
            set Slots += Ecriture.Ecrire(Prix(A.Prix), "CBD5E1", text_justification.Center, X, Y + 294.0, 340.0, 32.0, 5)
            set Slots += Bouton("LOCKED", InterfacePC.BoutonGris, X + 50.0, Y + 330.0, 240.0, 80.0, 12, I)
        Slots

    # Onglet REBIRTH : une grande carte au centre + l'explication.
    PageRebirth():[]canvas_slot =
        var Slots:[]canvas_slot = array{}
        Pret := TousLesAvions()
        Suivant := AvionTycoon.Rebirths + 2
        X := 710.0
        Y := 190.0
        set Slots += array{Bloc(Vignette(if (Pret?) then InterfacePC.CarteCarree else InterfacePC.CarteCarreeGrise, 500.0, 560.0), X, Y, 500.0, 560.0, 2)}
        set Slots += array{Bloc(Vignette(InterfacePC.IconeUpgrades, 260.0, 260.0), X + 120.0, Y + 25.0, 260.0, 260.0, 3)}
        set Slots += Ecriture.Ecrire("REBIRTH  #{AvionTycoon.Rebirths + 1}", "FFFFFF", text_justification.Center, X, Y + 300.0, 500.0, 44.0, 5)
        set Slots += Ecriture.Ecrire("EVERYTHING EARNS x{Suivant}", "A7F3D0", text_justification.Center, X, Y + 348.0, 500.0, 36.0, 5)
        if (Pret?):
            if (I := Indice["REBIRTH"]):
                set Slots += Bouton("REBIRTH", InterfacePC.BoutonCyan, X + 110.0, Y + 420.0, 280.0, 100.0, 12, I)
        else:
            set Slots += Ecriture.Ecrire("BUY THE GOLDEN GIANT FIRST", "FCA5A5", text_justification.Center, X, Y + 400.0, 500.0, 36.0, 5)
        set Slots += Ecriture.Ecrire("YOU RESTART WITH THE A320 AND 0 MONEY,", "FFFFFF", text_justification.Center, 360.0, 790.0, 1200.0, 36.0, 5)
        set Slots += Ecriture.Ecrire("BUT EVERY TICKET AND EVERY SERVICE PAYS MORE, FOREVER.", "FFFFFF", text_justification.Center, 360.0, 830.0, 1200.0, 36.0, 5)
        set Slots += Ecriture.Ecrire("ROUTES AND SUPPLIES ARE KEPT.", "A7F3D0", text_justification.Center, 360.0, 870.0, 1200.0, 36.0, 5)
        Slots

    Indice(Nom:string)<transacts><decides>:int =
        var Trouve:int = -1
        for (I -> A : ListeAmeliorations, A.Nom = Nom) { set Trouve = I }
        Trouve >= 0
        Trouve
