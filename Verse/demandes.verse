using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - les demandes des passagers (pendant le vol).
#
# Un "cerveau" decide qui commande et quoi, comme dans un vrai avion :
#   - rien les premieres secondes apres le decollage, puis une VAGUE BOISSONS, puis une
#     VAGUE REPAS, puis quelques demandes isolees ;
#   - au debut 1 a 2 commandes en meme temps, un peu plus si l'avion est plein (maximum reglable) ;
#   - chaque passager a un caractere : assoiffe (boissons), affame (repas) ou calme (rare) ;
#   - apres une boisson, il demandera plutot a manger ; 3 commandes max par passager et par vol ;
#   - quand quelqu'un commande, ses voisins ont plus de chances de commander aussi ;
#   - il ne demande que ce qui est debloque, et surtout ce qui est en stock.
#
# Au-dessus du passager : la BULLE (materiau = le produit demande) et dessous la BARRE de patience
# (10 materiaux, du plein au vide). Elles n'apparaissent QUE quand il commande, suivent le
# passager et se tournent vers le joueur le plus proche.
#
# Servir : tu vises le passager (ou sa bulle) avec le bon objet en main et tu appuies sur la
# TOUCHE du galley (InputPoser du service_device).
#   boisson (eau, soda, cafe) : la bouteille / canette / tasse en main ;
#   plat : l'ASSIETTE avec le plat dessus.
# Paiement = prix d'une unite x Marge x multiplicateur de la destination x bonus de rapidite
#   (barre verte x1.5, jaune / orange x1, rouge x0.5). Trop tard : il part fache, 0 $.
#
# Dans l'editeur :
#   Passagers, Service, Menu, Vol, Avion, Destinations : tes devices.
#   ModeleBulle       : le prop (asset) de la bulle.
#   MateriauxBulle    : 8 materiaux, un par produit, dans l'ordre de la boutique
#                       (Eau, Soda, Croissant, Sandwich, Cafe, Burger, Homard, Caviar).
#   ModeleBarre       : le prop (asset) plat de la barre.
#   MateriauxPatience : 10 materiaux, du PLEIN au VIDE : Patience_10, 09, ... 01.
#   SonCommande / SonServi / SonErreur / SonFache : (facultatif) Lecteurs audio.
#   MessageGain       : (facultatif) Appareil Message HUD pour "+$..." et "Wrong order".

demande := class<unique>:
    Passager:passager
    Produit:int
    Debut:float
    Patience:float
    Bulle:?creative_prop
    Barre:?creative_prop
    var Palier:int = -1

profil_passager := class<unique>:
    Passager:passager
    # 0 assoiffe, 1 affame, 2 calme
    Caractere:int
    var Commandes:int = 0
    var DernierService:float = -100.0
    var ABu:logic = false

demandes_device := class(creative_device):
    @editable Passagers:passagers = passagers{}
    @editable Service:?service_device = false
    @editable Menu:?menu_pc = false
    @editable Vol:?vol_device = false
    @editable Avion:?avion_tycoon = false
    @editable Destinations:?pc_destinations = false

    @editable ModeleBulle:creative_prop_asset = DefaultCreativePropAsset
    @editable MateriauxBulle:[]material = array{}
    @editable EchelleBulle:float = 1.0
    @editable ModeleBarre:creative_prop_asset = DefaultCreativePropAsset
    @editable MateriauxPatience:[]material = array{}
    @editable EchelleBarre:float = 1.0
    # Ou est la bulle : hauteur au-dessus du pivot du passager assis (cm)
    @editable HauteurBulle:float = 150.0
    # Barre : sous la bulle (cm) et decalage vers la gauche (cm) si son pivot est au bord gauche
    @editable EcartBarre:float = 45.0
    @editable DecalageBarre:float = 0.0
    # Si la bulle / la barre ne font pas face au joueur, essaie 90, -90 ou 180
    @editable RotationBulle:float = 0.0

    @editable SonCommande:?audio_player_device = false
    @editable SonServi:?audio_player_device = false
    @editable SonErreur:?audio_player_device = false
    @editable SonFache:?audio_player_device = false
    @editable MessageGain:?hud_message_device = false

    # ===== Reglages du cerveau =====
    # Secondes de calme juste apres le decollage
    @editable DelaiDepart:float = 12.0
    # Fin de la vague boissons, fin de la vague repas (secondes apres le decollage)
    @editable FinVagueBoissons:float = 70.0
    @editable FinVagueRepas:float = 160.0
    # Commandes en meme temps : minimum, et +1 tous les X passagers assis, plafond
    @editable MinSimultanees:int = 1
    @editable PassagersParCommande:int = 5
    @editable MaxSimultanees:int = 6
    @editable MaxCommandesParPassager:int = 3
    # Patience (secondes) et part au hasard en plus / en moins
    @editable Patience:float = 40.0
    @editable VariationPatience:float = 8.0
    # Distance (cm) pour etre "voisin" et effet de groupe
    @editable DistanceVoisin:float = 250.0
    # Viser un passager pour le servir : precision (cm) et portee (cm)
    @editable RayonService:float = 70.0
    @editable PorteeService:float = 450.0
    # Gain : prix d'achat d'une unite x Marge
    @editable Marge:float = 3.0

    Boissons:[]int = array{0, 1, 4}
    Repas:[]int = array{2, 3, 5, 6, 7}

    var Actives:[]demande = array{}
    var Profils:[]profil_passager = array{}
    var DebutVol:float = -1.0
    var DerniereCommande:float = -100.0
    var DernierePosition:?vector3 = false

    OnBegin<override>()<suspends>:void =
        loop:
            Sleep(0.1)
            if (EnVol[]):
                if (DebutVol < 0.0):
                    set DebutVol = GetSimulationElapsedTime()
                    set Profils = array{}
                Cerveau()
                MettreAJour()
            else if (DebutVol >= 0.0):
                # atterrissage : tout disparait
                set DebutVol = -1.0
                for (D : Actives) { Effacer(D) }
                set Actives = array{}

    EnVol()<transacts><decides>:void =
        V := Vol?
        V.EnVol?

    # ---------- le cerveau ----------
    Assis():[]passager = for (P : Passagers.EnCours, P.Etat = 2, P.Corps?) { P }

    Profil(P:passager):profil_passager =
        for (X : Profils, X.Passager = P):
            return X
        Tirage := GetRandomInt(0, 9)
        Car := if (Tirage < 4) then 0 else if (Tirage < 8) then 1 else 2
        Nouveau := profil_passager{Passager := P, Caractere := Car}
        set Profils += array{Nouveau}
        Nouveau

    ADemande(P:passager)<transacts><decides>:void =
        var Trouve:logic = false
        for (D : Actives, D.Passager = P) { set Trouve = true }
        Trouve?

    Cerveau():void =
        Maintenant := GetSimulationElapsedTime()
        Ecoule := Maintenant - DebutVol
        if (Ecoule < DelaiDepart) { return }
        Liste := Assis()
        Bonus := if (Q := Quotient[Liste.Length, Max(1, PassagersParCommande)]) then Q else 0
        Plafond := Min(MaxSimultanees, MinSimultanees + Bonus)
        if (Actives.Length >= Plafond) { return }
        # rythme : en vague, une commande toutes les ~4 s ; apres, toutes les ~12 s
        Rythme := if (Ecoule < FinVagueRepas) then 4.0 else 12.0
        if (Maintenant - DerniereCommande < Rythme * GetRandomFloat(0.6, 1.4)) { return }
        # candidats : assis, sans commande, pas trop servis, pas servis a l'instant
        var Poids:[]float = array{}
        var Candidats:[]passager = array{}
        for (P : Liste, not ADemande[P]):
            Pr := Profil(P)
            if (Pr.Commandes < MaxCommandesParPassager, Maintenant - Pr.DernierService > 20.0):
                var W:float = if (Pr.Caractere = 2) then 0.4 else 1.0
                if (Pos := DernierePosition?, C := P.Corps?, Distance(C.GetTransform().Translation, Pos) < DistanceVoisin):
                    set W *= 3.0
                set Candidats += array{P}
                set Poids += array{W}
        if (Choisi := TirerPondere(Poids)?, P := Candidats[Choisi]):
            Pr := Profil(P)
            if (Produit := ChoisirProduit(Pr, Ecoule)?):
                Commander(P, Produit)
                set Pr.Commandes += 1
                set DerniereCommande = Maintenant
                if (C := P.Corps?) { set DernierePosition = option{C.GetTransform().Translation} }

    TirerPondere(Poids:[]float)<transacts>:?int =
        var Total:float = 0.0
        for (W : Poids) { set Total += W }
        if (Total <= 0.0) { return false }
        var R:float = GetRandomFloat(0.0, Total)
        for (I -> W : Poids):
            if (R < W) { return option{I} }
            set R -= W
        false

    Debloque(I:int)<transacts><decides>:void =
        M := Menu?
        M.Debloque[I]?

    EnStock(I:int)<transacts><decides>:void =
        M := Menu?
        S := M.Stock[I]
        S > 0

    ChoisirProduit(Pr:profil_passager, Ecoule:float)<transacts>:?int =
        # envie de boire ? (selon la vague, le caractere et s'il a deja bu)
        var EnvieBoire:float = if (Ecoule < FinVagueBoissons) then 0.85 else if (Ecoule < FinVagueRepas) then 0.25 else 0.5
        if (Pr.Caractere = 0) { set EnvieBoire += 0.15 }
        if (Pr.Caractere = 1) { set EnvieBoire -= 0.15 }
        if (Pr.ABu?) { set EnvieBoire -= 0.4 }
        Famille := if (GetRandomFloat(0.0, 1.0) < EnvieBoire) then Boissons else Repas
        Autre := if (GetRandomFloat(0.0, 1.0) < EnvieBoire) then Repas else Boissons
        if (I := ProduitDans(Famille)?) { return option{I} }
        ProduitDans(Autre)

    # Un produit debloque de la famille ; ceux en stock ont 4 fois plus de chances
    ProduitDans(Famille:[]int)<transacts>:?int =
        var Poids:[]float = array{}
        var Ids:[]int = array{}
        for (I : Famille, Debloque[I]):
            set Ids += array{I}
            set Poids += array{if (EnStock[I]) then 4.0 else 1.0}
        if (K := TirerPondere(Poids)?, I := Ids[K]) then option{I} else false

    Commander(P:passager, Produit:int):void =
        if (C := P.Corps?):
            Base := C.GetTransform().Translation + vector3{Z := HauteurBulle}
            var Bulle:?creative_prop = false
            var Barre:?creative_prop = false
            if (B := SpawnProp(ModeleBulle, transform{Translation := Base, Rotation := IdentityRotation(), Scale := Uniforme(EchelleBulle)})(0)?):
                if (Mat := MateriauxBulle[Produit]) { B.SetMaterial(Mat) }
                set Bulle = option{B}
            if (B := SpawnProp(ModeleBarre, transform{Translation := Base - vector3{Z := EcartBarre}, Rotation := IdentityRotation(), Scale := Uniforme(EchelleBarre)})(0)?):
                set Barre = option{B}
            Pat := Patience + GetRandomFloat(-VariationPatience, VariationPatience)
            D := demande{Passager := P, Produit := Produit, Debut := GetSimulationElapsedTime(), Patience := Pat, Bulle := Bulle, Barre := Barre}
            set Actives += array{D}
            Placer(D)
            if (S := SonCommande?) { S.Play() }

    Uniforme(E:float):vector3 = vector3{X := E, Y := E, Z := E}

    # ---------- affichage ----------
    MettreAJour():void =
        Maintenant := GetSimulationElapsedTime()
        for (D : Actives):
            Reste := 1.0 - (Maintenant - D.Debut) / Max(1.0, D.Patience)
            if (Reste <= 0.0):
                Fache(D)
            else:
                Placer(D)
                # palier 0 = plein (Patience_10) ... 9 = presque vide (Patience_01)
                Palier := Max(0, Min(9, 9 - Entier(Reste * 10.0)))
                if (Palier <> D.Palier, B := D.Barre?, Mat := MateriauxPatience[Palier]):
                    B.SetMaterial(Mat)
                    set D.Palier = Palier

    Entier(V:float):int = if (N := Floor[V]) then N else 0

    # Bulle au-dessus du passager, tournee vers le joueur le plus proche ; barre accrochee dessous.
    Placer(D:demande):void =
        if (C := D.Passager.Corps?):
            Base := C.GetTransform().Translation + vector3{Z := HauteurBulle}
            var Vers:vector3 = vector3{X := 1.0, Y := 0.0, Z := 0.0}
            var Meilleure:float = 100000.0
            for (J : GetPlayspace().GetPlayers(), FC := J.GetFortCharacter[]):
                Dir := FC.GetTransform().Translation - Base
                Plat := vector3{X := Dir.X, Y := Dir.Y, Z := 0.0}
                if (Plat.Length() > 1.0, Plat.Length() < Meilleure):
                    set Meilleure = Plat.Length()
                    set Vers = Plat / Plat.Length()
            Face := MakeShortestRotationBetween(vector3{X := 1.0, Y := 0.0, Z := 0.0}, Vers).RotateBy(MakeRotationFromYawPitchRollDegrees(RotationBulle, 0.0, 0.0))
            # droite vue par le joueur (pour decaler la barre vers la gauche)
            Droite := vector3{X := Vers.Y, Y := -Vers.X, Z := 0.0}
            if (B := D.Bulle?):
                if (B.TeleportTo[transform{Translation := Base, Rotation := Face, Scale := Uniforme(EchelleBulle)}]) {}
            if (B := D.Barre?):
                PosBarre := Base - vector3{Z := EcartBarre} - Droite * DecalageBarre
                if (B.TeleportTo[transform{Translation := PosBarre, Rotation := Face, Scale := Uniforme(EchelleBarre)}]) {}

    Effacer(D:demande):void =
        if (B := D.Bulle?) { B.Dispose() }
        if (B := D.Barre?) { B.Dispose() }

    Retirer(D:demande):void =
        Effacer(D)
        set Actives = for (X : Actives, X <> D) { X }
        Pr := Profil(D.Passager)
        set Pr.DernierService = GetSimulationElapsedTime()

    Fache(D:demande):void =
        Retirer(D)
        if (S := SonFache?) { S.Play() }
        Message("A passenger left angry!")

    Message(Texte:string):void =
        if (M := MessageGain?):
            M.SetText(Msg(Texte))
            for (J : GetPlayspace().GetPlayers()) { M.Show(J) }

    # ---------- servir (appele par le service_device) ----------
    # 0 = tu ne vises aucun passager qui attend ; 1 = servi ; 2 = mauvais produit
    Servir(Joueur:player, Index:int, DessusIndex:int):int =
        if (FC := Joueur.GetFortCharacter[]):
            CamPos := FC.GetViewLocation()
            Avant := FC.GetViewRotation().RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})
            var Visee:?demande = false
            var MeilleurEcart:float = RayonService
            for (D : Actives, C := D.Passager.Corps?):
                # on vise le corps ou la bulle
                for (Pos : array{C.GetTransform().Translation + vector3{Z := 60.0}, C.GetTransform().Translation + vector3{Z := HauteurBulle}}):
                    T := (Pos - CamPos).X * Avant.X + (Pos - CamPos).Y * Avant.Y + (Pos - CamPos).Z * Avant.Z
                    Ecart := Distance(CamPos + Avant * T, Pos)
                    if (T > 0.0, T < PorteeService, Ecart < MeilleurEcart):
                        set MeilleurEcart = Ecart
                        set Visee = option{D}
            if (D := Visee?):
                Boisson := if (Index = D.Produit, not EstRepas[D.Produit]) then true else false
                Plat := if (Index < 0, DessusIndex = D.Produit, EstRepas[D.Produit]) then true else false
                Bon := if (Boisson? or Plat?) then true else false
                if (Bon?):
                    Payer(D)
                    return 1
                if (S := SonErreur?) { S.Play() }
                Message(if (EstRepas[D.Produit], Index >= 0) then "Put it on a plate!" else "Wrong order!")
                return 2
        0

    EstRepas(I:int)<transacts><decides>:void =
        var Oui:logic = false
        for (R : Repas, R = I) { set Oui = true }
        Oui?

    Payer(D:demande):void =
        Reste := 1.0 - (GetSimulationElapsedTime() - D.Debut) / Max(1.0, D.Patience)
        Bonus := if (Reste > 0.6) then 1.5 else if (Reste > 0.25) then 1.0 else 0.5
        Multi := if (Dest := Destinations?) then Dest.MultiplicateurActif() else 1.0
        var Unite:float = 1.0
        if (M := Menu?, P := M.ListeProduits[D.Produit]):
            set Unite = (P.PrixLot * 1.0) / (Max(1, P.Lot) * 1.0)
        Gain := if (G := Round[Unite * Marge * Multi * Bonus]) then Max(1, G) else 1
        if (A := Avion?):
            set A.Argent += Gain
            A.MettreAJourUI()
            Message("+${A.Abreger(Gain)}")
        Pr := Profil(D.Passager)
        if (not EstRepas[D.Produit]) { set Pr.ABu = true }
        Retirer(D)
        if (S := SonServi?) { S.Play() }
