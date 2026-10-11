using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - les colis de la boutique (meme systeme que la pizzeria).
#
# On paye sur le PC (SUPPLIES) -> la commande devient des colis (1 colis par produit).
#   Avion au sol : les colis apparaissent tout de suite dans la passerelle (PointLivraison).
#   En vol       : la commande attend, les colis apparaissent a l'atterrissage.
# On vise un colis + touche InputColis (ou son bouton) -> on le porte devant soi.
# Pres du depot (BoutonDepot), touche InputColis (ou le bouton) -> le colis glisse vers
# son emplacement de rangement, disparait, et le stock du produit augmente.
#
# Dans l'editeur :
#   PoolBoites      : tes props de colis (ton modele 3D), poses n'importe ou (caches au debut).
#   PoolBoutons     : 1 bouton par colis, dans le meme ordre (pour ramasser au bouton).
#   PointLivraison  : un prop (invisible) dans la passerelle, la ou les colis tombent.
#   BoutonDepot     : un Appareil Bouton dans le galley, la ou on range les colis.
#   PropsStockage   : 1 prop par produit, DANS L'ORDRE de la boutique
#                     (Eau, Soda, Croissant, Sandwich, Cafe, Burger, Homard, Caviar) :
#                     c'est la ou le colis glisse au rangement.
#   InputColis      : un Appareil Declencheur d'entree (la touche pour prendre / ranger).
#   Vol             : le device vol_device (pour savoir si on est en vol).

ligne_colis := struct:
    Index:int
    Unites:int

colis_avion := class<unique>:
    Prop:creative_prop
    Bouton:button_device
    var Contenu:[]ligne_colis = array{}
    var Actif:logic = false
    # true = le colis est par terre et peut etre ramasse
    var AuSol:logic = false

colis_clic := class:
    Manager:colis_device
    LeColis:colis_avion
    OnClick(Agent:agent):void = Manager.Ramasser(Agent, LeColis)

# Mesure la vitesse horizontale du joueur (pour placer le colis la ou il va etre).
vitesse_porteur := class:
    var DernierePos:?vector3 = false
    var DernierTemps:float = 0.0
    var VitesseLissee:vector3 = vector3{}

    Mesurer(Pos:vector3):vector3 =
        Maintenant := GetSimulationElapsedTime()
        var Vitesse:vector3 = vector3{}
        if (Prec := DernierePos?):
            Dt := Maintenant - DernierTemps
            if (Dt > 0.001):
                Brute := (Pos - Prec) * (1.0 / Dt)
                Plate := vector3{X := Brute.X, Y := Brute.Y, Z := 0.0}
                if (Plate.Length() < 2000.0):
                    set Vitesse = Plate
        set DernierePos = option{Pos}
        set DernierTemps = Maintenant
        set VitesseLissee = VitesseLissee * 0.5 + Vitesse * 0.5
        VitesseLissee

colis_device := class(creative_device):
    @editable PoolBoites:[]creative_prop = array{}
    @editable PoolBoutons:[]button_device = array{}
    @editable PointLivraison:?creative_prop = false
    @editable BoutonDepot:button_device = button_device{}
    @editable PropsStockage:[]creative_prop = array{}
    @editable InputColis:input_trigger_device = input_trigger_device{}
    @editable Vol:?vol_device = false

    # Ecart au hasard autour du point de livraison (cm)
    @editable Eparpillement:float = 120.0
    # Distance max pour ranger un colis pres du depot (cm)
    @editable RayonDepot:float = 250.0
    # Ramassage en visant : portee et precision (cm)
    @editable PorteeRamassage:float = 400.0
    @editable RayonVisee:float = 40.0
    # Colis porte : distance devant la camera, hauteur sous la camera (cm)
    @editable DistancePort:float = 130.0
    @editable HauteurPort:float = 60.0
    # Anti-saccade (comme la pizzeria)
    @editable DureeLissage:float = 0.08
    @editable SeuilTeleport:float = 300.0
    @editable Anticipation:float = 0.15

    var Pool:[]colis_avion = array{}
    var Menu:?menu_pc = false
    var EnAttente:[]ligne_colis = array{}
    var Porte:[player]?colis_avion = map{}
    # evite qu'un meme appui range ET reprenne un colis
    var DerniereAction:[player]float = map{}

    OnBegin<override>()<suspends>:void =
        BoutonDepot.InteractedWithEvent.Subscribe(OnDepot)
        InputColis.PressedEvent.Subscribe(OnInput)
        for (I -> P : PoolBoites, B := PoolBoutons[I]):
            C := colis_avion{Prop := P, Bouton := B}
            set Pool += array{C}
            B.InteractedWithEvent.Subscribe(colis_clic{Manager := Self, LeColis := C}.OnClick)
            P.Hide()
            B.Disable()
        # livre ce qui attend des que l'avion est au sol
        loop:
            Sleep(0.5)
            if (EnAttente.Length > 0, not EnVol[]):
                Commande := EnAttente
                set EnAttente = array{}
                Larguer(Commande)

    EnVol()<transacts><decides>:void =
        V := Vol?
        V.EnVol?

    # Appele par le PC au paiement.
    Commander(LeMenu:menu_pc, Commande:[]ligne_colis):void =
        set Menu = option{LeMenu}
        if (EnVol[]):
            set EnAttente += Commande
        else:
            Larguer(Commande)

    AjouterAuStock(L:ligne_colis):void =
        if (M := Menu?):
            M.AjouterStock(L.Index, L.Unites)

    Larguer(Commande:[]ligne_colis):void =
        if (Livraison := PointLivraison?):
            Base := Livraison.GetTransform().Translation
            var Dernier:?colis_avion = false
            for (Ligne : Commande):
                var Trouve:?colis_avion = false
                for (C : Pool, not Trouve?, not C.Actif?):
                    set Trouve = option{C}
                if (C := Trouve?):
                    set Dernier = option{C}
                    set C.Actif = true
                    set C.Contenu = array{Ligne}
                    Pos := Base + vector3{X := GetRandomFloat(-Eparpillement, Eparpillement), Y := GetRandomFloat(-Eparpillement, Eparpillement), Z := 0.0}
                    Rot := MakeRotation(vector3{X := 0.0, Y := 0.0, Z := 1.0}, GetRandomFloat(0.0, 6.28))
                    if (C.Prop.TeleportTo[Pos, Rot]):
                        C.Prop.Show()
                        set C.AuSol = true
                        if (C.Bouton.TeleportTo[Pos + vector3{Z := 80.0}, Rot]) {}
                        C.Bouton.Enable()
                else if (D := Dernier?):
                    # plus de colis libre : on regroupe dans le dernier
                    set D.Contenu += array{Ligne}
                else:
                    # aucun colis disponible : directement dans le stock
                    AjouterAuStock(Ligne)
        else:
            # pas de point de livraison : directement dans le stock
            for (Ligne : Commande) { AjouterAuStock(Ligne) }

    PeutAgir(P:player)<transacts><decides>:void =
        Derniere := if (T := DerniereAction[P]) then T else -10.0
        GetSimulationElapsedTime() - Derniere > 0.3

    Marquer(P:player):void =
        if (set DerniereAction[P] = GetSimulationElapsedTime()) {}

    Ramasser(Agent:agent, Cible:colis_avion):void =
        if (P := player[Agent], Cible.AuSol?, PeutAgir[P], not Porte[P]?):
            set Cible.AuSol = false
            Cible.Bouton.Disable()
            Marquer(P)
            if (set Porte[P] = option{Cible}):
                spawn{Porter(P, Cible)}

    OnInput(Agent:agent):void =
        if (P := player[Agent]):
            if (Porte[P]?):
                if (FC := P.GetFortCharacter[]):
                    if (Distance(FC.GetTransform().Translation, BoutonDepot.GetTransform().Translation) < RayonDepot):
                        Ranger(P)
            else:
                Vise := ColisVise(P)
                if (C := Vise?):
                    Ramasser(Agent, C)

    OnDepot(Agent:agent):void =
        if (P := player[Agent]):
            Ranger(P)

    # Colis au sol vise precisement (ligne du regard a moins de RayonVisee de son centre)
    ColisVise(P:player):?colis_avion =
        if (FC := P.GetFortCharacter[]):
            CamPos := FC.GetViewLocation()
            Avant := FC.GetViewRotation().RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})
            var Meilleur:?colis_avion = false
            var MeilleurEcart:float = RayonVisee
            for (C : Pool, C.AuSol?):
                Pos := C.Prop.GetTransform().Translation
                Dir := Pos - CamPos
                T := Avant.X * Dir.X + Avant.Y * Dir.Y + Avant.Z * Dir.Z
                Ecart := Distance(CamPos + Avant * T, Pos)
                if (T > 0.0, T < PorteeRamassage, Ecart < MeilleurEcart):
                    set MeilleurEcart = Ecart
                    set Meilleur = option{C}
            return Meilleur
        false

    RotationPlate(Avant:vector3):rotation =
        Plat := vector3{X := Avant.X, Y := Avant.Y, Z := 0.0}
        if (Plat.Length() > 0.01):
            MakeShortestRotationBetween(vector3{X := 1.0, Y := 0.0, Z := 0.0}, Plat)
        else:
            IdentityRotation()

    Glisser(Prop:creative_prop, Pos:vector3, Rot:rotation, Duree:float)<suspends>:void =
        Prop.MoveTo(Pos, Rot, Duree)

    Porter(P:player, Boite:colis_avion)<suspends>:void =
        if (FC := P.GetFortCharacter[]):
            Suivi := vitesse_porteur{}
            loop:
                if (Tenu := Porte[P]?, Tenu = Boite, FC.IsActive[]):
                    Vitesse := Suivi.Mesurer(FC.GetTransform().Translation)
                    Avant := FC.GetViewRotation().RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})
                    Cible := FC.GetViewLocation() + Avant * DistancePort - vector3{Z := HauteurPort} + Vitesse * Anticipation
                    Rot := RotationPlate(Avant)
                    if (Distance(Boite.Prop.GetTransform().Translation, Cible) > SeuilTeleport):
                        if (Boite.Prop.TeleportTo[Cible, Rot]) {}
                        Sleep(0.0)
                    else:
                        # MoveTo remplace a chaque tick : fluide et colle au joueur
                        race:
                            Glisser(Boite.Prop, Cible, Rot, DureeLissage)
                            Sleep(0.0)
                else:
                    # joueur mort / parti : le colis retombe par terre ici
                    if (Tenu := Porte[P]?, Tenu = Boite):
                        if (set Porte[P] = false) {}
                        set Boite.AuSol = true
                        Boite.Bouton.Enable()
                    break

    Ranger(P:player):void =
        if (PeutAgir[P], Boite := Porte[P]?):
            Marquer(P)
            if (set Porte[P] = false) {}
            Boite.Bouton.Disable()
            spawn{AnimerRangement(Boite)}

    AnimerRangement(Boite:colis_avion)<suspends>:void =
        Sleep(DureeLissage)
        var Dest:transform = Boite.Prop.GetTransform()
        if (Ligne := Boite.Contenu[0], Emplacement := PropsStockage[Ligne.Index]):
            set Dest = Emplacement.GetTransform()
        Boite.Prop.MoveTo(Dest.Translation, Dest.Rotation, 0.8)
        Sleep(0.1)
        for (L : Boite.Contenu) { AjouterAuStock(L) }
        set Boite.Actif = false
        set Boite.Contenu = array{}
        Boite.Prop.Hide()
        if (Boite.Prop.TeleportTo[vector3{Z := -5000.0}, IdentityRotation()]) {}
