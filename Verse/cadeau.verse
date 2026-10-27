using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }
using { /Fortnite.com/UI }

# Flight Attendant Tycoon - les CADEAUX du lobby (Playtime Rewards), A L'INFINI.
# On interagit avec le cadeau 3D : une fenetre cartoon FREE GIFTS montre les 6 prochains cadeaux
# DANS L'ORDRE, chacun avec son temps (le temps total avant de pouvoir l'ouvrir).
# Le premier devient la carte verte OPEN! quand il est pret -> on clique dessus -> on gagne de l'argent,
# le couvercle saute, et la liste avance d'un cadeau.
# Chaque cadeau attend un peu plus que le precedent (Delais, en minutes). Apres le dernier
# delai de la liste, ca STAGNE : tous les cadeaux suivants attendent ce dernier delai.
# Le gain = PartDuGain x (le temps attendu) de ton revenu, et au moins GainMinimum.
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Cadeau.glb (2 objets : Cadeau_Boite et Cadeau_Couvercle), Convert to Prop ;
#   - importe le dossier Textures/InterfaceCadeau a la racine du projet (comme InterfacePC) ;
#   - pose la boite, puis le couvercle dessus ;
#   - pose un appareil "Bouton" (Button) devant le cadeau (texte d'interaction : GIFTS) ;
#   - pose ce device, et dans ses Details : Bouton, Couvercle, Avions (tes avion_tycoon).
#   TestRapide : les delais sont en SECONDES au lieu de minutes (pour tester). A DECOCHER avant de publier !

clic_cadeau := class:
    Cadeau:cadeau_device
    Joueur:player
    Action:int
    Clique(Clic:widget_message):void = Cadeau.Agir(Joueur, Action)

cadeau_device := class(creative_device):
    @editable Bouton : button_device = button_device{}
    @editable Couvercle : ?creative_prop = false
    @editable Avions : []avion_tycoon = array{}
    # attente de chaque cadeau en minutes ; apres le dernier, on garde le dernier pour toujours
    @editable Delais : []float = array{2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0}
    @editable PartDuGain : float = 0.5
    @editable GainMinimum : int = 1000
    @editable TestRapide : logic = true

    Ecriture:ecriture_cartoon = ecriture_cartoon{}

    var Numeros : [player]int = map{}              # numero du prochain cadeau a ouvrir (1, 2, 3...)
    var Debuts : [player]float = map{}             # quand son attente a commence
    var Toiles : [player]canvas = map{}
    var Temps : [player][][]widget = map{}         # lettres des 6 temps (pour les changer)
    var PretAffiche : [player]logic = map{}
    var Ouvertures : [player]logic = map{}

    OnBegin<override>()<suspends>:void =
        Bouton.InteractedWithEvent.Subscribe(OnBouton)
        loop:
            Maintenant := GetSecondsSinceEpoch()
            for (P : GetPlayspace().GetPlayers(), not Debuts[P]):
                if (set Debuts[P] = Maintenant, set Numeros[P] = 1) {}
            for (P -> T : Toiles):
                Rafraichir(P, T)
            Sleep(0.25)

    # attente du cadeau N, en secondes
    Delai(N:int):float =
        Unite := if (TestRapide?) then 1.0 else 60.0
        if (D := Delais[N - 1]) then D * Unite
        else if (D := Delais[Delais.Length - 1]) then D * Unite
        else 60.0 * Unite

    Numero(P:player):int = if (N := Numeros[P]) then N else 1

    # secondes avant de pouvoir ouvrir le cadeau en cours
    Restant(P:player):float =
        Debut := if (D := Debuts[P]) then D else GetSecondsSinceEpoch()
        Max(0.0, Delai(Numero(P)) - (GetSecondsSinceEpoch() - Debut))

    OnBouton(Agent:agent):void =
        if (P := player[Agent], not Toiles[P]):
            Construire(P)

    # ---------- la fenetre ----------
    Bloc(W:widget, X:float, Y:float, L:float, H:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.5}, Maximum := vector2{X := 0.5, Y := 0.5}}
            Alignment := vector2{X := 0.0, Y := 0.0}
            Offsets := margin{Left := X - 960.0, Top := Y - 540.0, Right := L, Bottom := H}
            SizeToContent := false
            ZOrder := Couche
            Widget := W

    Image(T:texture, L:float, H:float):texture_block =
        texture_block{DefaultImage := T, DefaultDesiredSize := vector2{X := L, Y := H}}

    Clic(P:player, Action:int, X:float, Y:float, L:float, H:float):canvas_slot =
        B := button_quiet{DefaultText := Msg("")}
        B.OnClick().Subscribe(clic_cadeau{Cadeau := Self, Joueur := P, Action := Action}.Clique)
        Bloc(B, X, Y, L, H, 30)

    CarteX(K:int):float = 350.0 + 420.0 * (if (V := Mod[K, 3]) then V else 0)
    CarteY(K:int):float = if (K < 3) then 300.0 else 625.0

    Couleur(N:int):texture =
        case (if (V := Mod[N - 1, 6]) then V else 0):
            0 => InterfaceCadeau.Carte_1
            1 => InterfaceCadeau.Carte_2
            2 => InterfaceCadeau.Carte_3
            3 => InterfaceCadeau.Carte_4
            4 => InterfaceCadeau.Carte_5
            _ => InterfaceCadeau.Carte_6

    # (re)dessine toute la fenetre : au debut, et quand le premier cadeau devient pret ou est ouvert
    Construire(P:player):void =
        Retirer(P)
        if (UI := GetPlayerUI[P]):
            N := Numero(P)
            Pret := if (Restant(P) <= 0.0) then true else false
            var Slots : []canvas_slot = array:
                Bloc(Image(InterfaceCadeau.Fenetre_Cadeaux, 1500.0, 900.0), 210.0, 60.0, 1500.0, 900.0, 1)
                Bloc(Image(InterfacePC.Fermer, 120.0, 120.0), 1590.0, 40.0, 120.0, 120.0, 5)
                Clic(P, 0, 1602.0, 52.0, 96.0, 96.0)
            for (K := 0..5):
                X := CarteX(K)
                Y := CarteY(K)
                Fond := if (K = 0, Pret?) then InterfaceCadeau.Carte_Prete else Couleur(N + K)
                set Slots += array:
                    Bloc(Image(Fond, 360.0, 297.0), X, Y, 360.0, 297.0, 2)
                    Bloc(Image(InterfaceCadeau.Icone_Cadeau, 170.0, 170.0), X + 95.0, Y + 50.0, 170.0, 170.0, 3)
                set Slots += Ecriture.Ecrire("GIFT {N + K}", "FFFFFF", text_justification.Center, X + 40.0, Y + 18.0, 280.0, 44.0, 4)
            if (Pret?):
                set Slots += array{Clic(P, 1, CarteX(0) + 14.0, CarteY(0) + 14.0, 332.0, 268.0)}
            T := canvas{Slots := Slots}
            UI.AddWidget(T, player_ui_slot{InputMode := ui_input_mode.All})
            if (set Toiles[P] = T, set PretAffiche[P] = Pret, set Temps[P] = array{}) {}
            Rafraichir(P, T)

    Retirer(P:player):void =
        if (T := Toiles[P], UI := GetPlayerUI[P]):
            UI.RemoveWidget(T)
        var Tx : [player]canvas = map{}
        for (Cle -> V : Toiles, Cle <> P) { if (set Tx[Cle] = V) {} }
        set Toiles = Tx

    # met a jour les 6 temps (le 1er = son attente, les suivants = attente cumulee)
    Rafraichir(P:player, T:canvas):void =
        R := Restant(P)
        Pret := if (R <= 0.0) then true else false
        if (Avant := PretAffiche[P], Avant <> Pret):
            Construire(P)
        else:
            N := Numero(P)
            Anciens := if (A := Temps[P]) then A else array{}
            var Cumul : float = R
            var Nouveaux : [][]widget = array{}
            for (K := 0..5):
                if (K > 0) { set Cumul += Delai(N + K) }
                Texte := if (K = 0, Pret?) then "OPEN!" else Duree(Cumul)
                Teinte := if (K = 0, Pret?) then "86EFAC" else "FFFFFF"
                Vieilles := if (V := Anciens[K]) then V else array{}
                set Nouveaux += array:
                    Ecriture.Remplacer(T, Vieilles, Texte, Teinte, text_justification.Center,
                                       CarteX(K) + 60.0 - 960.0, CarteY(K) + 226.0 - 540.0, 240.0, 42.0, 4, vector2{X := 0.5, Y := 0.5})
            if (set Temps[P] = Nouveaux) {}

    Duree(Secondes:float):string =
        Total := if (V := Ceil[Secondes]) then V else 0
        H := if (V := Quotient[Total, 3600]) then V else 0
        Mi := if (V := Quotient[Total - H * 3600, 60]) then V else 0
        Se := Total - H * 3600 - Mi * 60
        if (H > 0) then "{H}:{Deux(Mi)}:{Deux(Se)}" else "{Deux(Mi)}:{Deux(Se)}"

    Deux(N:int):string = if (N < 10) then "0{N}" else "{N}"

    # Action 0 : fermer ; 1 : ouvrir le cadeau pret
    Agir(P:player, Action:int):void =
        if (Action = 0):
            Retirer(P)
        else if (Restant(P) <= 0.0, not Ouvertures[P]?):
            if (set Ouvertures[P] = true) {}
            spawn{ OuvrirCadeau(P) }

    OuvrirCadeau(P:player)<suspends>:void =
        N := Numero(P)
        var Affiche : string = "{GainMinimum}"
        for (Av : Avions, J := Av.Proprio?, J = P):
            Brut := Av.RevenuDeBase() * Delai(N) * PartDuGain
            Montant := Max(GainMinimum, if (V := Floor[Brut]) then V else 0)
            Av.Gagner(Montant, 2)
            set Affiche = Av.Abreger(Montant)
        # le cadeau suivant commence a attendre
        if (set Numeros[P] = N + 1, set Debuts[P] = GetSecondsSinceEpoch()) {}
        if (T := Toiles[P]):
            for (Slot : Ecriture.Ecrire("+${Affiche}!", "FDE047", text_justification.Center, 310.0, 420.0, 1300.0, 160.0, 20)):
                T.AddWidget(Slot)
        spawn{ SauterCouvercle() }
        Sleep(1.5)
        if (Toiles[P]):
            Construire(P)
        if (set Ouvertures[P] = false) {}

    SauterCouvercle()<suspends>:void =
        if (C := Couvercle?):
            Repos := C.GetTransform()
            Haut := transform:
                Translation := Repos.Translation + vector3{X := 0.0, Y := 0.0, Z := 160.0}
                Rotation := Repos.Rotation.RotateBy(MakeRotation(vector3{X := 0.0, Y := 0.0, Z := 1.0}, PiFloat))
                Scale := Repos.Scale
            C.MoveTo(Haut, 0.35)
            Sleep(0.6)
            C.MoveTo(Repos, 0.35)
