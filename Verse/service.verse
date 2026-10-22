using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Verse.org/Simulation }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }

# Flight Attendant Tycoon - le galley : prendre, porter, poser (comme la pizzeria).
#
#   CHARIOT : E sur un stockage EN TENANT le chariot -> le produit se range TOUT SEUL dans la case
#   libre suivante du plateau du chariot (les plats sur une assiette). Sans tenir le chariot, le
#   produit va dans la main comme avant. TOUCHE en tenant un produit, chariot a cote -> il va aussi
#   dans une case.
#   Pour servir : le chariot a cote d'un passager qui commande, on le vise, TOUCHE de la feuille
#   (feuille_mission) -> on choisit le produit du chariot sur l'ecran.
#
#   E sur un stockage (son bouton)  -> le produit apparait EN MAIN (1ere personne, a droite).
#   E sur la pile d'assiettes      -> une assiette en main.
#   TOUCHE (InputPoser) en tenant quelque chose :
#       - assiette / boisson (eau, soda, cafe) : se pose sur un plan de travail,
#         la ou est l'hologramme ;
#       - plat (croissant, sandwich, burger, homard, caviar) : se pose UNIQUEMENT sur une
#         assiette vide (l'hologramme apparait sur l'assiette visee).
#   TOUCHE les mains vides : reprend l'objet vise (une assiette garnie revient avec son plat).
#   Ce qui est pose sur le chariot bouge avec le chariot.
#
# Pourquoi 2 touches : E (Interagir) sert aux boutons (stockages, assiettes, chariot) ;
# tout ce qu'on tient se gere avec la TOUCHE du Declencheur d'entree. Plus de conflit.
#
# Ordre des produits (le meme que la boutique) :
#   0 Eau, 1 Soda, 2 Croissant, 3 Sandwich, 4 Cafe, 5 Burger, 6 Homard, 7 Caviar
#
# Dans l'editeur :
#   Menu             : le device menu_pc (pour le stock).
#   ModelesProduits  : 8 lignes dans l'ordre ci-dessus : le modele (asset) de chaque produit.
#   BoutonsStockage  : 8 boutons, un sur chaque prop de stockage, dans le meme ordre.
#   ModeleAssiette   : le modele de l'assiette ; BoutonAssiettes : le bouton sur la pile.
#   InputPoser       : un Declencheur d'entree (la touche pour poser / reprendre).
#   Planches         : des props plats (invisibles en jeu) sur les plans de travail du galley.
#   Chariots         : tes chariot_device (avec leur Plateau rempli : le centre du dessus du chariot).
#   MateriauEau      : ton materiau pour la bouteille d'eau.
#   MateriauHologramme : le materiau de l'hologramme.

produit_service := class<concrete>:
    @editable Modele:creative_prop_asset = DefaultCreativePropAsset
    # Monte (+) / descend (-) le produit quand il est pose (cm), si son pivot n'est pas en bas
    @editable DecalagePose:float = 0.0
    # Tourne le produit a plat quand il est pose / en main (degres)
    @editable Rotation:float = 0.0

# Un objet du galley : une assiette (Index = -1) ou un produit (Index = 0..7).
objet_service := class<unique>:
    Index:int
    Prop:creative_prop
    # le plat pose sur cette assiette
    var Dessus:?objet_service = false
    # accroche au chariot (si pose dessus)
    var Attache:?attache_chariot = false
    var ChariotIndex:int = -1
    # la case du plateau du chariot (-1 = pas sur un chariot)
    var Casier:int = -1

cible_pose := struct:
    Position:vector3
    Rotation:rotation
    ChariotIndex:int
    Assiette:?objet_service

point_planche := struct:
    Point:vector3
    Haut:vector3
    ChariotIndex:int

# Ce que le joueur tient
tenu_service := class<unique>:
    Objet:objet_service
    Holo:?creative_prop
    var Visible:logic = false

clic_stockage := class:
    Service:service_device
    Index:int
    Clic(Agent:agent):void = Service.ClicStockage(Agent, Index)

service_device := class(creative_device):
    @editable Menu:?menu_pc = false
    @editable ModelesProduits:[]produit_service = array{}
    @editable BoutonsStockage:[]button_device = array{}
    @editable ModeleAssiette:creative_prop_asset = DefaultCreativePropAsset
    @editable BoutonAssiettes:?button_device = false
    @editable EchelleAssiette:float = 1.0
    # Hauteur du dessus de l'assiette au-dessus de son pivot (cm) : la ou le plat est pose
    @editable HauteurAssiette:float = 2.0
    @editable InputPoser:input_trigger_device = input_trigger_device{}
    @editable Planches:[]creative_prop = array{}
    @editable Chariots:[]chariot_device = array{}
    # Le device des demandes : viser un passager qui attend avec le bon objet = le servir.
    @editable Demandes:?demandes_device = false
    @editable MateriauEau:?material = false
    @editable MateriauHologramme:?material = false
    @editable NombreSlotsHolo:int = 2

    # ===== Le chariot =====
    # Distance (cm) du chariot pour y charger un produit sans le tenir.
    @editable DistanceChargement:float = 350.0
    # Les cases du plateau : colonnes x rangees, espacees de EcartChariot cm, centrees sur le Plateau.
    @editable ColonnesChariot:int = 3
    @editable RangeesChariot:int = 2
    @editable EcartChariot:float = 20.0
    # Sans Plateau sur le chariot : hauteur du dessus du chariot au-dessus de son pivot (cm).
    @editable HauteurChariot:float = 100.0
    # ===== Zone de pose (comme la pizzeria) =====
    # Taille du mesh de la planche a l'echelle 1 (cm) : vraie taille = TailleBase x Echelle du prop
    @editable TailleBasePlancheX:float = 100.0
    @editable TailleBasePlancheY:float = 100.0
    # Hauteur de la surface par rapport au pivot de la planche (cm, a l'echelle 1)
    @editable HauteurSurfacePlanche:float = 0.0
    @editable PlancheVisible:logic = false
    @editable PorteeMax:float = 400.0
    # Precision pour viser un objet pose / une assiette (cm)
    @editable RayonRamassage:float = 40.0
    # Affiche dans le journal pourquoi on ne peut pas poser / reprendre (pour regler les planches)
    @editable ModeDebug:logic = true

    # ===== En main (repere de la camera) =====
    @editable DistanceEnMain:float = 70.0
    @editable DecalageMainDroite:float = 28.0
    @editable DecalageMainBas:float = 25.0

    # ===== Anti-saccade =====
    @editable DureeLissage:float = 0.08
    @editable SeuilTeleport:float = 300.0
    @editable DelaiEntreActions:float = 0.3

    # Echelle de chaque produit (dans l'ordre) et plats qui vont sur une assiette.
    Echelles:[]float = array{0.25, 0.2, 0.00065, 0.25, 1.0, 1.0, 0.025, 1.0}
    Plats:[]logic = array{false, false, true, true, false, true, true, true}

    var EnMain:[player]?tenu_service = map{}
    var Poses:[]objet_service = array{}
    var DerniereAction:[player]float = map{}

    OnBegin<override>()<suspends>:void =
        for (I -> B : BoutonsStockage):
            B.InteractedWithEvent.Subscribe(clic_stockage{Service := Self, Index := I}.Clic)
        if (B := BoutonAssiettes?):
            B.InteractedWithEvent.Subscribe(clic_stockage{Service := Self, Index := -1}.Clic)
        InputPoser.PressedEvent.Subscribe(OnTouche)
        if (not PlancheVisible?):
            for (P : Planches) { P.Hide() }

    # ---------- petits outils ----------
    PeutAgir(P:player)<transacts><decides>:void =
        Derniere := if (T := DerniereAction[P]) then T else -10.0
        GetSimulationElapsedTime() - Derniere > DelaiEntreActions

    Marquer(P:player):void =
        if (set DerniereAction[P] = GetSimulationElapsedTime()) {}

    MainsLibres(P:player)<transacts><decides>:void =
        not EnMain[P]?

    EstPlat(Index:int)<transacts><decides>:void =
        Plats[Index]?

    Echelle(Index:int)<transacts>:vector3 =
        E := if (Index < 0) then EchelleAssiette else if (V := Echelles[Index]) then V else 1.0
        vector3{X := E, Y := E, Z := E}

    Modele(Index:int)<transacts>:creative_prop_asset =
        if (Index < 0) then ModeleAssiette else if (P := ModelesProduits[Index]) then P.Modele else DefaultCreativePropAsset

    DecalagePose(Index:int)<transacts>:float =
        if (P := ModelesProduits[Index]) then P.DecalagePose else 0.0

    RotationProduit(Index:int)<transacts>:float =
        if (P := ModelesProduits[Index]) then P.Rotation else 0.0

    Haut()<transacts>:vector3 = vector3{X := 0.0, Y := 0.0, Z := 1.0}

    Scalaire(A:vector3, B:vector3)<transacts>:float = A.X * B.X + A.Y * B.Y + A.Z * B.Z

    Absolu(V:float)<transacts>:float = if (V < 0.0) then -V else V

    # Rotation a plat dans la direction du regard (+ correction du produit)
    RotationPlate(Avant:vector3, Degres:float)<transacts>:rotation =
        Plat := vector3{X := Avant.X, Y := Avant.Y, Z := 0.0}
        Base := if (Plat.Length() > 0.01) then MakeShortestRotationBetween(vector3{X := 1.0, Y := 0.0, Z := 0.0}, Plat) else IdentityRotation()
        Base.RotateBy(MakeRotationFromYawPitchRollDegrees(Degres, 0.0, 0.0))

    Regard(FC:fort_character)<transacts>:vector3 =
        FC.GetViewRotation().RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})

    PositionEnMain(FC:fort_character)<transacts>:vector3 =
        Avant := Regard(FC)
        Plat := RotationPlate(Avant, 0.0)
        FC.GetViewLocation() + Avant * DistanceEnMain + Plat.RotateVector(vector3{X := 0.0, Y := DecalageMainDroite, Z := 0.0}) - vector3{Z := DecalageMainBas}

    # ---------- prendre ----------
    ClicStockage(Agent:agent, Index:int):void =
        Tenu := ChariotTenu(Agent)
        if (P := player[Agent], PeutAgir[P], I := Tenu?, Index >= 0, MainsLibres[P]):
            # on tient le chariot : le produit va directement dans une case du plateau
            Marquer(P)
            ChargerChariot(I, Index)
        else if (P := player[Agent], MainsLibres[P], PeutAgir[P]):
            if (Index < 0):
                Marquer(P)
                CreerEnMain(P, -1)
            else if (M := Menu?, M.RetirerUn[Index]):
                Marquer(P)
                CreerEnMain(P, Index)
            else:
                Annoncer("Out of stock! Buy more on the PC.")

    CreerEnMain(P:player, Index:int):void =
        if (FC := P.GetFortCharacter[]):
            Rot := RotationPlate(Regard(FC), if (Index >= 0) then RotationProduit(Index) else 0.0)
            Depart := transform{Translation := PositionEnMain(FC), Rotation := Rot, Scale := Echelle(Index)}
            Resultat := SpawnProp(Modele(Index), Depart)
            if (Prop := Resultat(0)?):
                if (Prop.TeleportTo[Depart]) {}
                if (Index = 0, Mat := MateriauEau?) { Prop.SetMaterial(Mat) }
                MettreEnMain(P, objet_service{Index := Index, Prop := Prop})
            else:
                Print("Galley : impossible de creer l'objet (modele vide ?)")

    MettreEnMain(P:player, O:objet_service):void =
        var Holo:?creative_prop = false
        Resultat := SpawnProp(Modele(O.Index), transform{Translation := vector3{Z := -5000.0}, Rotation := IdentityRotation(), Scale := Echelle(O.Index)})
        if (H := Resultat(0)?):
            Placer(H, O.Index, vector3{Z := -5000.0}, IdentityRotation())
            if (Mat := MateriauHologramme?):
                for (Slot := 0..NombreSlotsHolo - 1) { H.SetMaterial(Mat, ?Index := Slot) }
            H.Hide()
            set Holo = option{H}
        T := tenu_service{Objet := O, Holo := Holo}
        if (set EnMain[P] = option{T}):
            spawn{BoucleMain(P, T)}
            spawn{BoucleHolo(P, T)}

    Tient(P:player, T:tenu_service)<transacts><decides>:void =
        Actuel := EnMain[P]?
        Actuel = T

    # Place un objet a sa TAILLE (Echelle du produit) : Fortnite ne garde pas l'echelle au spawn.
    Placer(Prop:creative_prop, Index:int, Pos:vector3, Rot:rotation)<transacts>:void =
        if (Prop.TeleportTo[transform{Translation := Pos, Rotation := Rot, Scale := Echelle(Index)}]) {}

    Glisser(Prop:creative_prop, Index:int, Pos:vector3, Rot:rotation)<suspends>:void =
        if (Distance(Prop.GetTransform().Translation, Pos) > SeuilTeleport):
            Placer(Prop, Index, Pos, Rot)
        else:
            Prop.MoveTo(transform{Translation := Pos, Rotation := Rot, Scale := Echelle(Index)}, DureeLissage)

    GlisserDessus(O:objet_service, Pos:vector3, Rot:rotation)<suspends>:void =
        if (D := O.Dessus?):
            Glisser(D.Prop, D.Index, Pos + vector3{Z := HauteurAssiette + DecalagePose(D.Index)}, Rot.RotateBy(MakeRotationFromYawPitchRollDegrees(RotationProduit(D.Index), 0.0, 0.0)))
        else:
            Sleep(DureeLissage)

    BoucleMain(P:player, T:tenu_service)<suspends>:void =
        loop:
            if (not Tient[P, T]) { break }
            if (FC := P.GetFortCharacter[], FC.IsActive[]):
                O := T.Objet
                Pos := PositionEnMain(FC)
                Rot := RotationPlate(Regard(FC), if (O.Index >= 0) then RotationProduit(O.Index) else 0.0)
                race:
                    sync:
                        Glisser(O.Prop, O.Index, Pos, Rot)
                        GlisserDessus(O, Pos, Rot)
                    Sleep(0.0)
            else:
                # joueur mort ou parti : l'objet disparait
                if (set EnMain[P] = false) {}
                Detruire(T.Objet)
                break
        if (H := T.Holo?) { H.Dispose() }

    BoucleHolo(P:player, T:tenu_service)<suspends>:void =
        loop:
            Sleep(0.05)
            if (not Tient[P, T]) { break }
            if (H := T.Holo?):
                if (C := Cible(P, T.Objet)?):
                    Placer(H, T.Objet.Index, C.Position, C.Rotation)
                    if (not T.Visible?):
                        H.Show()
                        set T.Visible = true
                else if (T.Visible?):
                    H.Hide()
                    set T.Visible = false

    Detruire(O:objet_service):void =
        if (D := O.Dessus?) { D.Prop.Dispose() }
        O.Prop.Dispose()

    # ---------- ou poser ----------
    # Point vise sur une planche du galley ou sur le plateau d'un chariot
    PointVise(CamPos:vector3, Avant:vector3)<transacts>:?point_planche =
        var Meilleur:?point_planche = false
        var MeilleurT:float = PorteeMax
        # (le chariot n'est plus une surface : on y range dans des cases, voir ChargerChariot)
        Surfaces:[]tuple(creative_prop, int) = for (Pl : Planches) { (Pl, -1) }
        for (S : Surfaces):
            Tr := S(0).GetTransform()
            H := Tr.Rotation.RotateVector(Haut())
            AxeX := Tr.Rotation.RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})
            AxeY := Tr.Rotation.RotateVector(vector3{X := 0.0, Y := 1.0, Z := 0.0})
            Surface := Tr.Translation + H * (HauteurSurfacePlanche * Tr.Scale.Z)
            Den := Scalaire(Avant, H)
            if (Den < -0.05):
                T := Scalaire(Surface - CamPos, H) / Den
                Point := CamPos + Avant * T
                Local := Point - Surface
                if (T > 0.0, T < MeilleurT, Absolu(Scalaire(Local, AxeX)) <= TailleBasePlancheX * Tr.Scale.X / 2.0, Absolu(Scalaire(Local, AxeY)) <= TailleBasePlancheY * Tr.Scale.Y / 2.0):
                    set MeilleurT = T
                    set Meilleur = option{point_planche{Point := Point, Haut := H, ChariotIndex := S(1)}}
        Meilleur

    # Objet pose vise (le plus proche de la ligne du regard)
    ObjetVise(CamPos:vector3, Avant:vector3, AssietteVideSeulement:logic)<transacts>:?objet_service =
        var Meilleur:?objet_service = false
        var MeilleurEcart:float = RayonRamassage
        for (O : Poses):
            Vide := if (O.Index < 0, not O.Dessus?) then true else false
            if (not AssietteVideSeulement? or Vide?):
                Pos := O.Prop.GetTransform().Translation
                T := Scalaire(Pos - CamPos, Avant)
                Ecart := Distance(CamPos + Avant * T, Pos)
                if (T > 0.0, T < PorteeMax, Ecart < MeilleurEcart):
                    set MeilleurEcart = Ecart
                    set Meilleur = option{O}
        Meilleur

    Cible(P:player, O:objet_service)<transacts>:?cible_pose =
        if (FC := P.GetFortCharacter[]):
            CamPos := FC.GetViewLocation()
            Avant := Regard(FC)
            if (O.Index >= 0, EstPlat[O.Index]):
                # un plat : seulement sur une assiette vide
                if (A := ObjetVise(CamPos, Avant, true)?):
                    Tr := A.Prop.GetTransform()
                    SurAssiette := cible_pose{Position := Tr.Translation + vector3{Z := HauteurAssiette + DecalagePose(O.Index)}, Rotation := Tr.Rotation.RotateBy(MakeRotationFromYawPitchRollDegrees(RotationProduit(O.Index), 0.0, 0.0)), ChariotIndex := A.ChariotIndex, Assiette := option{A}}
                    return option{SurAssiette}
                return false
            if (Pt := PointVise(CamPos, Avant)?):
                Monte := if (O.Index >= 0) then DecalagePose(O.Index) else 0.0
                SurPlanche := cible_pose{Position := Pt.Point + Pt.Haut * Monte, Rotation := RotationPlate(Avant, if (O.Index >= 0) then RotationProduit(O.Index) else 0.0), ChariotIndex := Pt.ChariotIndex, Assiette := false}
                return option{SurPlanche}
        false

    # Journal : ou tu vises par rapport a chaque planche (X / Y doivent etre dans +-Demi)
    Diagnostic(P:player):void =
        if (FC := P.GetFortCharacter[]):
            CamPos := FC.GetViewLocation()
            Avant := Regard(FC)
            for (I -> Pl : Planches):
                Tr := Pl.GetTransform()
                H := Tr.Rotation.RotateVector(Haut())
                Surface := Tr.Translation + H * (HauteurSurfacePlanche * Tr.Scale.Z)
                Den := Scalaire(Avant, H)
                if (Den < -0.05):
                    T := Scalaire(Surface - CamPos, H) / Den
                    Local := CamPos + Avant * T - Surface
                    LX := Scalaire(Local, Tr.Rotation.RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0}))
                    LY := Scalaire(Local, Tr.Rotation.RotateVector(vector3{X := 0.0, Y := 1.0, Z := 0.0}))
                    Print("Planche {I} : distance {T}  X {LX} / Y {LY}  (demi-taille {TailleBasePlancheX * Tr.Scale.X / 2.0} / {TailleBasePlancheY * Tr.Scale.Y / 2.0})")
                else:
                    Print("Planche {I} : tu ne regardes pas le dessus (vise plus vers le bas)")
            Print("Objets poses : {Poses.Length}")

    # ---------- touche ----------
    OnTouche(Agent:agent):void =
        ChariotProche := ChariotDe(Agent)
        if (P := player[Agent], PeutAgir[P]):
            if (T := EnMain[P]?, I := ChariotProche?, RangerSurChariot[I, T.Objet]):
                Marquer(P)
                if (set EnMain[P] = false) {}
                # le dernier mouvement "en main" peut encore tourner : on le recale apres
                spawn{RecalerSurChariot(T.Objet)}
            else if (T := EnMain[P]?):
                # on vise un passager qui attend ? -> on le sert, sinon on pose
                O := T.Objet
                DessusIndex := if (D := O.Dessus?) then D.Index else -99
                Resultat := if (Dem := Demandes?) then Dem.Servir(P, O.Index, DessusIndex) else 0
                if (Resultat = 1):
                    Marquer(P)
                    if (set EnMain[P] = false) {}
                    Detruire(O)
                else if (Resultat = 0):
                    Poser(P, T)
            else:
                Reprendre(P)
            if (ModeDebug?) { Diagnostic(P) }

    Poser(P:player, T:tenu_service):void =
        O := T.Objet
        if (C := Cible(P, O)?):
            Marquer(P)
            if (set EnMain[P] = false) {}
            Placer(O.Prop, O.Index, C.Position, C.Rotation)
            if (D := O.Dessus?):
                Placer(D.Prop, D.Index, C.Position + vector3{Z := HauteurAssiette + DecalagePose(D.Index)}, C.Rotation)
            spawn{Recaler(O, C)}
            if (A := C.Assiette?):
                set A.Dessus = option{O}
            else:
                set Poses += array{O}
            Accrocher(O, C.ChariotIndex)
            if (D := O.Dessus?) { Accrocher(D, C.ChariotIndex) }

    # le dernier mouvement "en main" peut encore tourner : on recale apres
    Recaler(O:objet_service, C:cible_pose)<suspends>:void =
        Sleep(DureeLissage + 0.05)
        if (O.Attache?):
            # sur un chariot : c'est le chariot qui le place
            return
        Placer(O.Prop, O.Index, C.Position, C.Rotation)
        if (D := O.Dessus?):
            Placer(D.Prop, D.Index, C.Position + vector3{Z := HauteurAssiette + DecalagePose(D.Index)}, C.Rotation)

    Accrocher(O:objet_service, ChariotIndex:int):void =
        if (Ch := Chariots[ChariotIndex]):
            T := O.Prop.GetTransform()
            set O.Attache = option{Ch.Attacher(O.Prop, T.Translation, T.Rotation)}
            set O.ChariotIndex = ChariotIndex

    Decrocher(O:objet_service):void =
        if (A := O.Attache?, Ch := Chariots[O.ChariotIndex]):
            Ch.Detacher(A)
        set O.Attache = false
        set O.ChariotIndex = -1

    Reprendre(P:player):void =
        if (FC := P.GetFortCharacter[]):
            if (O := ObjetVise(FC.GetViewLocation(), Regard(FC), false)?):
                Marquer(P)
                set Poses = for (X : Poses, X <> O) { X }
                Decrocher(O)
                if (D := O.Dessus?) { Decrocher(D) }
                MettreEnMain(P, O)

    # ---------- le chariot : des cases fixes sur le plateau ----------
    # Le chariot tenu par ce joueur, sinon le plus proche a moins de DistanceChargement cm.
    ChariotDe(Agent:agent):?int =
        var Meilleur:?int = false
        var Dist:float = DistanceChargement
        if (FC := Agent.GetFortCharacter[]):
            Pos := FC.GetTransform().Translation
            for (I -> Ch : Chariots):
                if (Porteur := Ch.Porteur?, Porteur = Agent):
                    return option{I}
                D := Distance(Ch.Chariot.GetTransform().Translation, Pos)
                if (D < Dist):
                    set Dist = D
                    set Meilleur = option{I}
        Meilleur

    NombreCases()<transacts>:int = Max(1, ColonnesChariot) * Max(1, RangeesChariot)

    CaseOccupee(I:int, Casier:int)<transacts><decides>:void =
        var Oui:logic = false
        for (O : Poses, O.ChariotIndex = I, O.Casier = Casier) { set Oui = true }
        Oui?

    CaseLibre(I:int)<transacts>:?int =
        for (C := 0..NombreCases() - 1, not CaseOccupee[I, C]):
            return option{C}
        false

    # Position d'une case dans le repere du chariot (centre du plateau + decalage de la case).
    PositionCase(Ch:chariot_device, Casier:int)<transacts>:vector3 =
        Centre := if (C := Ch.CentrePlateau?) then C + vector3{Z := HauteurSurfacePlanche} else vector3{Z := HauteurChariot}
        Col := if (C := Mod[Casier, Max(1, ColonnesChariot)]) then C else 0
        Rang := if (R := Quotient[Casier, Max(1, ColonnesChariot)]) then R else 0
        DX := (Col * 1.0 - (Max(1, ColonnesChariot) - 1) * 0.5) * EcartChariot
        DY := (Rang * 1.0 - (Max(1, RangeesChariot) - 1) * 0.5) * EcartChariot
        Centre + vector3{X := DX, Y := DY, Z := 0.0}

    # Le chariot que ce joueur tient (pour y charger les produits du galley).
    ChariotTenu(Agent:agent)<transacts>:?int =
        for (I -> Ch : Chariots, Porteur := Ch.Porteur?, Porteur = Agent):
            return option{I}
        false

    # Cree un objet (produit ou assiette) DIRECTEMENT dans une case du chariot (position Rel dans le
    # repere du chariot), a sa taille, et l'accroche au chariot.
    CreerDansChariot(I:int, Index:int, Rel:vector3):?objet_service =
        if (Ch := Chariots[I]):
            C := Ch.Chariot.GetTransform()
            Rot := MakeRotationFromYawPitchRollDegrees(if (Index >= 0) then RotationProduit(Index) else 0.0, 0.0, 0.0)
            Monde := transform{Translation := C.Translation + C.Rotation.RotateVector(Rel), Rotation := C.Rotation.RotateBy(Rot), Scale := Echelle(Index)}
            Resultat := SpawnProp(Modele(Index), Monde)
            if (Prop := Resultat(0)?):
                Placer(Prop, Index, Monde.Translation, Monde.Rotation)
                if (Index = 0, Mat := MateriauEau?) { Prop.SetMaterial(Mat) }
                O := objet_service{Index := Index, Prop := Prop}
                set O.Attache = option{Ch.AttacherRelatif(Prop, Rel, Rot)}
                set O.ChariotIndex = I
                return option{O}
        false

    # E sur un stockage en tenant le chariot : un produit du stock va dans la case libre suivante
    # (un plat sur une assiette, s'il y a un modele d'assiette).
    ChargerChariot(I:int, Index:int):void =
        if (Ch := Chariots[I], Casier := CaseLibre(I)?):
            if (M := Menu?, M.RetirerUn[Index]):
                Base := PositionCase(Ch, Casier)
                var Pose:logic = false
                if (EstPlat[Index]):
                    CreeA := CreerDansChariot(I, -1, Base)
                    if (Assiette := CreeA?):
                        set Assiette.Casier = Casier
                        set Poses += array{Assiette}
                        CreeP := CreerDansChariot(I, Index, Base + vector3{Z := HauteurAssiette + DecalagePose(Index)})
                        if (Plat := CreeP?) { set Assiette.Dessus = option{Plat} }
                        set Pose = true
                if (not Pose?):
                    Cree := CreerDansChariot(I, Index, Base + vector3{Z := DecalagePose(Index)})
                    if (O := Cree?):
                        set O.Casier = Casier
                        set Poses += array{O}
                Nom := if (P := M.ListeProduits[Index]) then P.Nom else "Item"
                Annoncer("{Nom} added to the trolley")
            else:
                Annoncer("Out of stock! Buy more on the PC.")
        else:
            Annoncer("Your trolley is full!")

    # TOUCHE avec un objet en main et le chariot a cote : il va dans une case (produit, ou
    # assiette garnie). Une assiette vide reste en main (false).
    RangerSurChariot(I:int, O:objet_service)<transacts><decides>:void =
        ProduitDe(O) >= 0
        Casier := CaseLibre(I)?
        set O.Casier = Casier
        set Poses += array{O}
        MettreDansCaseSur(O, I, Casier)

    MettreDansCaseSur(O:objet_service, I:int, Casier:int)<transacts>:void =
        if (Ch := Chariots[I]):
            Base := PositionCase(Ch, Casier)
            Rot := MakeRotationFromYawPitchRollDegrees(if (O.Index >= 0) then RotationProduit(O.Index) else 0.0, 0.0, 0.0)
            Monte := if (O.Index >= 0) then DecalagePose(O.Index) else 0.0
            set O.Attache = option{Ch.AttacherRelatif(O.Prop, Base + vector3{Z := Monte}, Rot)}
            set O.ChariotIndex = I
            if (D := O.Dessus?):
                RotD := MakeRotationFromYawPitchRollDegrees(RotationProduit(D.Index), 0.0, 0.0)
                set D.Attache = option{Ch.AttacherRelatif(D.Prop, Base + vector3{Z := HauteurAssiette + DecalagePose(D.Index)}, RotD)}
                set D.ChariotIndex = I

    # Combien de chaque produit (0..7) il y a sur le chariot I.
    ContenuChariot(I:int)<transacts>:[]int =
        for (K := 0..7):
            Les := for (O : Poses, O.ChariotIndex = I, ProduitDe(O) = K) { O }
            Les.Length

    # Le produit d'un objet : lui-meme, ou le plat sur l'assiette (-1 = assiette vide).
    ProduitDe(O:objet_service)<transacts>:int =
        if (O.Index >= 0) then O.Index else if (D := O.Dessus?) then D.Index else -1

    # Sert un produit : il est retire du chariot (avec son assiette). false s'il n'y en a pas.
    RetirerDuChariot(I:int, Article:int):logic =
        for (O : Poses, O.ChariotIndex = I, ProduitDe(O) = Article):
            set Poses = for (X : Poses, X <> O) { X }
            Decrocher(O)
            if (D := O.Dessus?) { Decrocher(D) }
            Detruire(O)
            return true
        false

    RecalerSurChariot(O:objet_service)<suspends>:void =
        Sleep(DureeLissage + 0.05)
        if (Ch := Chariots[O.ChariotIndex]):
            if (A := O.Attache?) { Ch.Replacer(A) }
            if (D := O.Dessus?, AD := D.Attache?) { Ch.Replacer(AD) }

    Annoncer(Texte:string):void =
        if (D := Demandes?) then D.Message(Texte) else Print(Texte)
