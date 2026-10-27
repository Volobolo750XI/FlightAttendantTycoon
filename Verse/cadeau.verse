using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }
using { /Fortnite.com/UI }

# Flight Attendant Tycoon - le CADEAU du lobby (Playtime Reward).
# Reste MinutesRequises minutes sur la map -> le cadeau est pret. On interagit avec : une fenetre
# cartoon s'ouvre (FREE GIFT, compte a rebours, barre arc-en-ciel, bouton OPEN!). On clique OPEN! :
# on gagne MinutesDeGain minutes de son revenu (au moins GainMinimum), le couvercle saute, et le
# compteur repart a zero.
#
# Installation dans UEFN :
#   - importe Modeles/Lobby/Cadeau.glb (2 objets : Cadeau_Boite et Cadeau_Couvercle), Convert to Prop ;
#   - importe le dossier Textures/InterfaceCadeau a la racine du projet (comme InterfacePC) ;
#   - pose la boite, puis le couvercle dessus ;
#   - pose un appareil "Bouton" (Button) devant le cadeau (texte d'interaction : GIFT) ;
#   - pose ce device, et dans ses Details : Bouton, Couvercle, Avions (tes avion_tycoon).
#   TestRapide : le cadeau est pret en 10 secondes (pour tester). A DECOCHER avant de publier !

clic_cadeau := class:
    Cadeau:cadeau_device
    Joueur:player
    Action:int
    Clique(Clic:widget_message):void = Cadeau.Agir(Joueur, Action)

cadeau_device := class(creative_device):
    @editable Bouton : button_device = button_device{}
    @editable Couvercle : ?creative_prop = false
    @editable Avions : []avion_tycoon = array{}
    @editable MinutesRequises : float = 15.0
    @editable MinutesDeGain : float = 10.0
    @editable GainMinimum : int = 1000
    @editable TestRapide : logic = true

    Ecriture:ecriture_cartoon = ecriture_cartoon{}

    var Debuts : [player]float = map{}            # depuis quand le joueur attend son cadeau
    var Toiles : [player]canvas = map{}
    var Lettres : [player][]widget = map{}
    var Barres : [player]widget = map{}
    var Boutons : [player]widget = map{}
    var PretAffiche : [player]logic = map{}
    var Ouvertures : [player]logic = map{}

    OnBegin<override>()<suspends>:void =
        Bouton.InteractedWithEvent.Subscribe(OnBouton)
        loop:
            Maintenant := GetSecondsSinceEpoch()
            for (P : GetPlayspace().GetPlayers(), not Debuts[P]):
                if (set Debuts[P] = Maintenant) {}
            for (P -> T : Toiles):
                Rafraichir(P, T)
            Sleep(0.25)

    Attente():float = if (TestRapide?) then 10.0 else MinutesRequises * 60.0

    Restant(P:player):float =
        Debut := if (D := Debuts[P]) then D else GetSecondsSinceEpoch()
        Max(0.0, Attente() - (GetSecondsSinceEpoch() - Debut))

    OnBouton(Agent:agent):void =
        if (P := player[Agent], not Toiles[P]):
            Ouvrir(P)

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

    Ouvrir(P:player):void =
        if (UI := GetPlayerUI[P]):
            T := canvas:
                Slots := array:
                    Bloc(Image(InterfaceCadeau.Fenetre_Cadeau, 1100.0, 900.0), 410.0, 90.0, 1100.0, 900.0, 1)
                    Bloc(Image(InterfaceCadeau.Icone_Cadeau, 380.0, 380.0), 770.0, 260.0, 380.0, 380.0, 2)
                    Bloc(Image(InterfaceCadeau.Barre_Fond, 900.0, 110.0), 500.0, 700.0, 900.0, 110.0, 2)
                    Bloc(Image(InterfacePC.Fermer, 130.0, 130.0), 1400.0, 70.0, 130.0, 130.0, 5)
                    Clic(P, 0, 1413.0, 83.0, 104.0, 104.0)
                    Clic(P, 1, 708.0, 858.0, 504.0, 128.0)
            UI.AddWidget(T, player_ui_slot{InputMode := ui_input_mode.All})
            if (set Toiles[P] = T, set Lettres[P] = array{}, set PretAffiche[P] = false) {}
            Rafraichir(P, T)
            # bouton dessine au premier passage (pret ou pas)
            DessinerBouton(P, T, Restant(P) <= 0.0)

    Fermer(P:player):void =
        if (T := Toiles[P], UI := GetPlayerUI[P]):
            UI.RemoveWidget(T)
        var Tx : [player]canvas = map{}
        for (Cle -> V : Toiles, Cle <> P) { if (set Tx[Cle] = V) {} }
        set Toiles = Tx
        var Br : [player]widget = map{}
        for (Cle -> V : Barres, Cle <> P) { if (set Br[Cle] = V) {} }
        set Barres = Br
        var Bo : [player]widget = map{}
        for (Cle -> V : Boutons, Cle <> P) { if (set Bo[Cle] = V) {} }
        set Boutons = Bo

    DessinerBouton(P:player, T:canvas, Pret:logic):void =
        if (Ancien := Boutons[P]) { T.RemoveWidget(Ancien) }
        Img := if (Pret?) then InterfaceCadeau.Bouton_Open else InterfaceCadeau.Bouton_Attente
        W := Image(Img, 560.0, 190.0)
        T.AddWidget(Bloc(W, 680.0, 830.0, 560.0, 190.0, 6))
        if (set Boutons[P] = W, set PretAffiche[P] = Pret) {}

    Rafraichir(P:player, T:canvas):void =
        R := Restant(P)
        Pret := if (R <= 0.0) then true else false
        # texte : READY IN 04:32 / READY!
        Texte := if (Pret?) then "READY!" else "READY IN {MinSec(R)}"
        Couleur := if (Pret?) then "86EFAC" else "FFFFFF"
        Anciennes := if (L := Lettres[P]) then L else array{}
        Nouvelles := Ecriture.Remplacer(T, Anciennes, Texte, Couleur, text_justification.Center,
                                        500.0 - 960.0, 618.0 - 540.0, 900.0, 66.0, 4, vector2{X := 0.5, Y := 0.5})
        if (set Lettres[P] = Nouvelles) {}
        # barre arc-en-ciel
        if (Ancienne := Barres[P]) { T.RemoveWidget(Ancienne) }
        Part := Min(1.0, Max(0.0, 1.0 - R / Attente()))
        if (Part > 0.0):
            Largeur := Max(110.0, 900.0 * Part)
            W := Image(InterfaceCadeau.Barre_Plein, Largeur, 110.0)
            T.AddWidget(Bloc(W, 500.0, 700.0, Largeur, 110.0, 3))
            if (set Barres[P] = W) {}
        # le bouton change d'image quand le cadeau devient pret
        if (Avant := PretAffiche[P], Avant <> Pret):
            DessinerBouton(P, T, Pret)

    MinSec(Secondes:float):string =
        Total := if (V := Ceil[Secondes]) then V else 0
        Mi := if (V := Quotient[Total, 60]) then V else 0
        Se := Total - Mi * 60
        "{Deux(Mi)}:{Deux(Se)}"

    Deux(N:int):string = if (N < 10) then "0{N}" else "{N}"

    # Action 0 : fermer ; 1 : OPEN!
    Agir(P:player, Action:int):void =
        if (Action = 0):
            Fermer(P)
        else if (Restant(P) <= 0.0, not Ouvertures[P]?):
            if (set Ouvertures[P] = true) {}
            spawn{ OuvrirCadeau(P) }

    OuvrirCadeau(P:player)<suspends>:void =
        var Montant : int = GainMinimum
        var Affiche : string = "{GainMinimum}"
        for (Av : Avions, J := Av.Proprio?, J = P):
            Brut := Av.RevenuDeBase() * MinutesDeGain * 60.0
            set Montant = Max(GainMinimum, if (V := Floor[Brut]) then V else 0)
            Av.Gagner(Montant, 2)
            set Affiche = Av.Abreger(Montant)
        if (set Debuts[P] = GetSecondsSinceEpoch()) {}
        # gros texte du gain par-dessus la fenetre
        if (T := Toiles[P]):
            Texte := "+${Affiche}!"
            for (Slot : Ecriture.Ecrire(Texte, "FDE047", text_justification.Center, 460.0, 400.0, 1000.0, 150.0, 20)):
                T.AddWidget(Slot)
        spawn{ SauterCouvercle() }
        Sleep(2.0)
        Fermer(P)
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
