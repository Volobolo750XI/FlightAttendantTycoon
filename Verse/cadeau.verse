using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }
using { /Fortnite.com/UI }
using { /Verse.org/Assets }

# Flight Attendant Tycoon - les CADEAUX du lobby (Playtime Rewards), A L'INFINI.
# On interagit avec le cadeau 3D : une fenetre cartoon FREE GIFTS montre 21 cadeaux pas encore ouverts,
# chacun avec son temps. TOUS LES TEMPS TOURNENT EN MEME TEMPS depuis l'arrivee du joueur sur la map :
# avec les Delais par defaut, GIFT 1 est pret a 5 min, GIFT 2 a 15 min (5 + 10), GIFT 3 a 30 min...
# Meme si on n'ouvre pas, les suivants continuent : plusieurs cadeaux peuvent etre prets en meme temps.
# Un cadeau pret devient la carte verte avec le bouton OPEN (le seul endroit cliquable).
# Apres le dernier delai de la liste, ca STAGNE : chaque cadeau suivant arrive ce dernier delai plus tard.
# Le gain = PartDuGain x (le delai de ce cadeau) de ton revenu, et au moins GainMinimum.
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Cadeau.glb (2 objets : Cadeau_Boite et Cadeau_Couvercle), Convert to Prop ;
#   - importe le dossier Textures/InterfaceCadeau a la racine du projet (comme InterfacePC) ;
#   - pose la boite, puis le couvercle dessus ;
#   - pose un appareil "Bouton" (Button) devant le cadeau (texte d'interaction : GIFTS) ;
#   - pose ce device, et dans ses Details : Bouton, Couvercle, Avions (tes avion_tycoon).
#   TestRapide (decoche par defaut) : les delais en SECONDES au lieu de minutes, seulement pour tester vite.

clic_cadeau := class:
    Cadeau:cadeau_device
    Joueur:player
    Action:int
    Numero:int
    Clique(Clic:widget_message):void = Cadeau.Agir(Joueur, Action, Numero)

cadeau_device := class(creative_device):
    @editable Bouton : button_device = button_device{}
    @editable Couvercle : ?creative_prop = false
    @editable Avions : []avion_tycoon = array{}
    # temps (en minutes) entre un cadeau et le suivant ; apres le dernier, on garde le dernier pour toujours
    @editable Delais : []float = array{5.0, 10.0, 15.0, 20.0, 30.0, 45.0, 60.0}
    @editable PartDuGain : float = 0.5
    @editable GainMinimum : int = 1000
    @editable TestRapide : logic = false

    Ecriture:ecriture_cartoon = ecriture_cartoon{}

    var Debuts : [player]float = map{}             # arrivee du joueur : tous les temps partent de la
    var Ouverts : [player][int]logic = map{}       # cadeaux deja ouverts
    var Listes : [player][]int = map{}             # numeros des 21 cadeaux affiches
    var Toiles : [player]canvas = map{}
    var Temps : [player][][]widget = map{}         # lettres des 21 temps (pour les changer)
    var PretsAffiches : [player]int = map{}        # nombre de cartes vertes dessinees
    var Ouvertures : [player]logic = map{}

    OnBegin<override>()<suspends>:void =
        Bouton.InteractedWithEvent.Subscribe(OnBouton)
        loop:
            Maintenant := GetSecondsSinceEpoch()
            for (P : GetPlayspace().GetPlayers(), not Debuts[P]):
                if (set Debuts[P] = Maintenant) {}
            for (P -> T : Toiles):
                Rafraichir(P, T)
            Sleep(0.5)

    # temps entre le cadeau N-1 et le cadeau N, en secondes
    Delai(N:int):float =
        Unite := if (TestRapide?) then 1.0 else 60.0
        if (D := Delais[N - 1]) then D * Unite
        else if (D := Delais[Delais.Length - 1]) then D * Unite
        else 60.0 * Unite

    # moment ou le cadeau N est pret (secondes depuis l'arrivee du joueur)
    Deblocage(N:int):float =
        var Total : float = 0.0
        for (I := 1..N) { set Total += Delai(I) }
        Total

    # secondes passees depuis l'arrivee du joueur
    Ecoule(P:player):float =
        Maintenant := GetSecondsSinceEpoch()
        Debut := if (D := Debuts[P]) then D else Maintenant
        Maintenant - Debut

    EstOuvert(P:player, N:int)<transacts><decides>:void =
        O := Ouverts[P]
        O[N]?

    # les 21 premiers cadeaux pas encore ouverts
    Prochains(P:player):[]int =
        var Liste : []int = array{}
        var N : int = 1
        loop:
            if (Liste.Length >= 21):
                break
            if (not EstOuvert[P, N]):
                set Liste += array{N}
            set N += 1
        Liste

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

    Clic(P:player, Action:int, Num:int, X:float, Y:float, L:float, H:float):canvas_slot =
        B := button_quiet{DefaultText := Msg("")}
        B.OnClick().Subscribe(clic_cadeau{Cadeau := Self, Joueur := P, Action := Action, Numero := Num}.Clique)
        Bloc(B, X, Y, L, H, 30)

    # 21 cartes : 3 lignes de 7, chaque carte fait 140 x 140
    CarteX(K:int):float = 398.0 + 164.0 * (if (V := Mod[K, 7]) then V else 0)
    CarteY(K:int):float = 372.0 + 166.0 * (if (V := Quotient[K, 7]) then V else 0)

    Couleur(N:int):texture =
        case (if (V := Mod[N - 1, 6]) then V else 0):
            0 => InterfaceCadeau.Carte_1
            1 => InterfaceCadeau.Carte_2
            2 => InterfaceCadeau.Carte_3
            3 => InterfaceCadeau.Carte_4
            4 => InterfaceCadeau.Carte_5
            _ => InterfaceCadeau.Carte_6

    # (re)dessine toute la fenetre : a l'ouverture, quand un cadeau devient pret, et apres en avoir ouvert un
    Construire(P:player):void =
        Retirer(P)
        if (UI := GetPlayerUI[P]):
            Liste := Prochains(P)
            Ecoule0 := Ecoule(P)
            var Prets : int = 0
            var Slots : []canvas_slot = array:
                Bloc(Image(InterfaceCadeau.Fenetre_Cadeaux, 1440.0, 720.0), 240.0, 180.0, 1440.0, 720.0, 1)
                Bloc(Image(InterfacePC.Fermer, 80.0, 80.0), 1612.0, 236.0, 80.0, 80.0, 5)
                Clic(P, 0, 0, 1620.0, 244.0, 64.0, 64.0)
            for (K -> N : Liste):
                X := CarteX(K)
                Y := CarteY(K)
                Moment := Deblocage(N)
                Pret := if (Ecoule0 >= Moment) then true else false
                Fond := if (Pret?) then InterfaceCadeau.Carte_Prete else Couleur(N)
                set Slots += array:
                    Bloc(Image(Fond, 140.0, 140.0), X, Y, 140.0, 140.0, 2)
                    Bloc(Image(InterfaceCadeau.Icone_Cadeau, 80.0, 80.0), X + 30.0, Y + 30.0, 80.0, 80.0, 3)
                Titre := Ecriture.Ecrire("GIFT {N}", "FFFFFF", text_justification.Center, X + 22.0, Y + 14.0, 96.0, 20.0, 4)
                set Slots += Titre
                # cadeau pret : le bouton OPEN est le SEUL endroit cliquable
                if (Pret?):
                    set Prets += 1
                    set Slots += array:
                        # image AU-DESSUS de la zone de clic : sinon le voile gris du bouton Fortnite la ternit
                        Bloc(Image(InterfaceCadeau.Bouton_Open, 100.0, 50.0), X + 20.0, Y + 86.0, 100.0, 50.0, 31)
                        Clic(P, 1, N, X + 24.0, Y + 90.0, 92.0, 36.0)
            T := canvas{Slots := Slots}
            UI.AddWidget(T, player_ui_slot{InputMode := ui_input_mode.All})
            if (set Toiles[P] = T, set Listes[P] = Liste, set PretsAffiches[P] = Prets, set Temps[P] = array{}) {}
            Rafraichir(P, T)

    Retirer(P:player):void =
        if (T := Toiles[P], UI := GetPlayerUI[P]):
            UI.RemoveWidget(T)
        var Tx : [player]canvas = map{}
        for (Cle -> V : Toiles, Cle <> P) { if (set Tx[Cle] = V) {} }
        set Toiles = Tx

    # met a jour les 21 temps ; redessine tout si un nouveau cadeau est devenu pret
    Rafraichir(P:player, T:canvas):void =
        Liste := if (L := Listes[P]) then L else array{}
        E := Ecoule(P)
        var Prets : int = 0
        for (N : Liste):
            Moment := Deblocage(N)
            if (E >= Moment) { set Prets += 1 }
        Avant := if (A := PretsAffiches[P]) then A else 0
        if (Prets <> Avant):
            Construire(P)
        else:
            Anciens := if (A := Temps[P]) then A else array{}
            var Nouveaux : [][]widget = array{}
            for (K -> N : Liste):
                Reste := Deblocage(N) - E
                Texte := if (Reste <= 0.0) then "" else Duree(Reste)
                Vieilles := if (V := Anciens[K]) then V else array{}
                set Nouveaux += array:
                    Ecriture.Remplacer(T, Vieilles, Texte, "FFFFFF", text_justification.Center,
                                       CarteX(K) + 14.0 - 960.0, CarteY(K) + 101.0 - 540.0, 112.0, 22.0, 4, vector2{X := 0.5, Y := 0.5})
            if (set Temps[P] = Nouveaux) {}

    Duree(Secondes:float):string =
        Total := if (V := Ceil[Secondes]) then V else 0
        H := if (V := Quotient[Total, 3600]) then V else 0
        Mi := if (V := Quotient[Total - H * 3600, 60]) then V else 0
        Se := Total - H * 3600 - Mi * 60
        if (H > 0) then "{H}:{Deux(Mi)}:{Deux(Se)}" else "{Deux(Mi)}:{Deux(Se)}"

    Deux(N:int):string = if (N < 10) then "0{N}" else "{N}"

    # Action 0 : fermer ; 1 : ouvrir le cadeau numero Num (s'il est pret)
    Agir(P:player, Action:int, Num:int):void =
        E := Ecoule(P)
        Moment := Deblocage(Num)
        Pret := if (E >= Moment) then true else false
        if (Action = 0):
            Retirer(P)
        else if (Pret?, not EstOuvert[P, Num], not Ouvertures[P]?):
            if (set Ouvertures[P] = true) {}
            spawn{ OuvrirCadeau(P, Num) }

    OuvrirCadeau(P:player, N:int)<suspends>:void =
        var Affiche : string = "{GainMinimum}"
        for (Av : Avions, J := Av.Proprio?, J = P):
            Brut := Av.RevenuDeBase() * Delai(N) * PartDuGain
            Montant := Max(GainMinimum, if (V := Floor[Brut]) then V else 0)
            Av.Gagner(Montant, 2)
            set Affiche = Av.Abreger(Montant)
        Avant := if (O := Ouverts[P]) then O else map{}
        if (set Ouverts[P] = ConcatenateMaps(Avant, map{N => true})) {}
        if (T := Toiles[P]):
            Gros := Ecriture.Ecrire("+${Affiche}!", "FDE047", text_justification.Center, 260.0, 440.0, 1400.0, 180.0, 20)
            for (Slot : Gros):
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
