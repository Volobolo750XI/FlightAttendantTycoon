using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - la feuille de mission (une nouvelle à chaque trajet).
#
# Au START BOARDING, une feuille "FLIGHT BRIEFING" apparaît à droite de l'écran du proprio,
# tirée au hasard (comme un petit cerveau) :
#   - souvent    : fermer tous les coffres à bagages (après l'embarquement, avant TAKE OFF) ;
#   - souvent    : contrôler les billets de quelques passagers (viser + TOUCHE) ;
#   - souvent    : la démonstration de sécurité (rester quelques secondes sur le repère) ;
#   - parfois    : une inspection en vol (toilettes, cockpit... : aller sur le repère) ;
#   - RARE, en vol : "un passager voyage sans billet" avec SA PHOTO -> le trouver et
#                  contrôler son billet (viser + TOUCHE). Attention aux sosies !
#   - RARE, en vol : un objet perdu apparaît quelque part -> marcher dessus pour le ramasser.
# Coffres et démo non faits au décollage = ratés. Le reste doit être fait avant l'atterrissage.
# Chaque mission rapporte BonusMission x multiplicateur de la destination ; tout réussir rapporte
# BonusFeuilleComplete en plus. À l'atterrissage, la feuille affiche le bilan puis disparaît.
#
# Dans le Tiroir à contenu, dossier "FeuilleMission" : importe FondFeuille et Photo1 ... Photo5
# (Textures/FeuilleMission). Dans le device passagers, règle "Photo" de chaque modèle.
#
# Dans l'éditeur :
#   Passagers, DeviceAvion, DevicePC : tes devices.
#   InputBillet      : un Déclencheur d'entrée (la touche pour contrôler un billet). Ça peut être
#                      le même que celui du galley.
#   InputFeuille     : (facultatif) un Déclencheur d'entrée pour cacher / montrer la feuille.
#   RepereDemo       : (facultatif) un petit prop à l'avant de l'allée : la démo de sécurité.
#   Inspections      : (facultatif) des endroits à inspecter : un nom court + un repère.
#   ObjetsPerdus     : (facultatif) des props (téléphone, doudou...) posés n'importe où, cachés au début.
#   Cachettes        : (facultatif) des repères où l'objet perdu peut apparaître.
#   MessageHUD       : (facultatif) Appareil Message HUD pour "+$..." et "Ticket OK".
#   SonMission       : (facultatif) Lecteur audio joué quand une mission est réussie.

point_inspection := class<concrete>:
    # Nom court affiché sur la feuille (ex : TOILETS, COCKPIT, GALLEY).
    @editable Nom:string = "TOILETS"
    @editable Repere:creative_prop = creative_prop{}

# Une ligne de la feuille.
tache_feuille := class<unique>:
    # 0 coffres, 1 billets, 2 démo, 3 inspection, 4 fraudeur, 5 objet perdu
    Genre:int
    var Fait:logic = false
    var Rate:logic = false
    var Visible:logic = true
    var Compte:int = 0
    var Objectif:int = 1
    # inspection : numéro du point ; objet perdu : numéro de l'objet
    var Numero:int = -1
    # temps passé sur place (démo, inspection)
    var Chrono:float = 0.0
    # surprise en vol : secondes après le décollage où la ligne apparaît (-1 = visible tout de suite)
    var Apparition:float = -1.0
    var Fraudeur:?passager = false

feuille_mission := class(creative_device):
    @editable Passagers:passagers = passagers{}
    @editable DeviceAvion:avion_tycoon = avion_tycoon{}
    @editable DevicePC:?pc_destinations = false
    @editable InputBillet:input_trigger_device = input_trigger_device{}
    @editable InputFeuille:?input_trigger_device = false
    @editable RepereDemo:?creative_prop = false
    @editable Inspections:[]point_inspection = array{}
    @editable ObjetsPerdus:[]creative_prop = array{}
    @editable Cachettes:[]creative_prop = array{}
    @editable MessageHUD:?hud_message_device = false
    @editable SonMission:?audio_player_device = false

    # ===== Le hasard de la feuille (chances en %) =====
    @editable ChanceCoffres:int = 90
    @editable ChanceBillets:int = 75
    @editable ChanceDemo:int = 60
    @editable ChanceInspection:int = 50
    @editable ChanceFraudeur:int = 15
    @editable ChanceObjetPerdu:int = 20
    # Nombre de billets à contrôler (au hasard entre les deux)
    @editable BilletsMin:int = 2
    @editable BilletsMax:int = 4
    # Temps à rester sur place (démo, inspection) et distance (cm) pour compter qu'on y est
    @editable DureeSurPlace:float = 4.0
    @editable RayonSurPlace:float = 200.0
    # Viser un passager pour son billet : précision (cm) et portée (cm)
    @editable RayonVisee:float = 70.0
    @editable PorteeVisee:float = 450.0
    # ===== Gains (x multiplicateur de la destination) =====
    @editable BonusMission:int = 20
    @editable BonusFraudeur:int = 60
    @editable BonusFeuilleComplete:int = 50

    PhotosPassagers:[]texture = array{FeuilleMission.Photo1, FeuilleMission.Photo2, FeuilleMission.Photo3, FeuilleMission.Photo4, FeuilleMission.Photo5}
    NbLignes:int = 8

    var Taches:[]tache_feuille = array{}
    var Controles:[]passager = array{}
    var EnCours:logic = false
    var DebutVol:float = -1.0
    var NumeroTrajet:int = 0
    var GainsMissions:int = 0
    var Cachee:logic = false
    var Racine:?canvas = false
    var Lignes:[]text_block = array{}
    Entete:text_block = text_block{DefaultTextColor := NamedColors.DarkBlue}
    Photo:texture_block = texture_block{DefaultImage := FeuilleMission.Photo1, DefaultDesiredSize := vector2{X := 110.0, Y := 110.0}}

    OnBegin<override>()<suspends>:void =
        if (R := RepereDemo?) { R.Hide() }
        for (P : Inspections) { P.Repere.Hide() }
        for (O : ObjetsPerdus) { O.Hide() }
        for (C : Cachettes) { C.Hide() }
        InputBillet.PressedEvent.Subscribe(OnBillet)
        if (I := InputFeuille?) { I.PressedEvent.Subscribe(OnBasculer) }
        var Avant:int = Passagers.EtatBouton
        loop:
            Sleep(0.2)
            Etat := Passagers.EtatBouton
            if (Etat <> Avant):
                # 3 -> 0 : atterrissage (et si on a déjà relancé l'embarquement, nouvelle feuille aussi)
                if (Avant = 3):
                    spawn{AAtterrissage()}
                if (Etat = 1, Avant = 0 or Avant = 3):
                    NouvelleFeuille()
                else if (Etat = 3):
                    AuDecollage()
                set Avant = Etat
            if (EnCours?):
                Verifier(0.2)

    # ---------- une nouvelle feuille (START BOARDING) ----------
    NouvelleFeuille():void =
        set NumeroTrajet += 1
        set Controles = array{}
        set GainsMissions = 0
        set DebutVol = -1.0
        var Liste:[]tache_feuille = array{}
        if (Passagers.PortesCoffres.Length > 0, Chance[ChanceCoffres]):
            set Liste += array{tache_feuille{Genre := 0}}
        if (Chance[ChanceBillets]):
            T := tache_feuille{Genre := 1}
            set T.Objectif = GetRandomInt(Max(1, BilletsMin), Max(BilletsMin, BilletsMax))
            set Liste += array{T}
        if (RepereDemo?, Chance[ChanceDemo]):
            set Liste += array{tache_feuille{Genre := 2}}
        if (Inspections.Length > 0, Chance[ChanceInspection]):
            T := tache_feuille{Genre := 3}
            set T.Numero = GetRandomInt(0, Inspections.Length - 1)
            set Liste += array{T}
        # surprises en vol (rares) : elles apparaissent entre 15 % et 60 % du vol
        if (Chance[ChanceFraudeur]):
            T := tache_feuille{Genre := 4}
            set T.Visible = false
            set T.Apparition = DureeVolPrevue() * GetRandomFloat(0.15, 0.6)
            set Liste += array{T}
        if (ObjetsPerdus.Length > 0, Chance[ChanceObjetPerdu]):
            T := tache_feuille{Genre := 5}
            set T.Visible = false
            set T.Numero = GetRandomInt(0, ObjetsPerdus.Length - 1)
            set T.Apparition = DureeVolPrevue() * GetRandomFloat(0.15, 0.6)
            set Liste += array{T}
        # jamais une feuille vide : au minimum les coffres
        if (Liste.Length = 0, Passagers.PortesCoffres.Length > 0):
            set Liste += array{tache_feuille{Genre := 0}}
        set Taches = Liste
        set EnCours = true
        Afficher()
        Rafraichir()

    # ---------- décollage / atterrissage ----------
    AuDecollage():void =
        set DebutVol = GetSimulationElapsedTime()
        # coffres et démo : c'était avant le décollage
        for (T : Taches, not T.Fait?, T.Genre = 0 or T.Genre = 2):
            set T.Rate = true
        Rafraichir()

    AAtterrissage()<suspends>:void =
        if (EnCours?):
            set EnCours = false
            for (T : Taches, not T.Fait?):
                set T.Rate = true
                if (T.Genre = 5, O := ObjetsPerdus[T.Numero]) { O.Hide() }
            Visibles := for (T : Taches, T.Visible?) { T }
            Reussies := for (T : Visibles, T.Fait?) { T }
            if (Visibles.Length > 0, Reussies.Length = Visibles.Length):
                Gagner(BonusFeuilleComplete, "PERFECT FLIGHT!")
            Rafraichir()
            # bilan en bas de la feuille
            Billets := Passagers.DerniersPayants
            AfficherLigne(NbLignes - 2, "TICKETS {Billets}: +${DeviceAvion.Abreger(Passagers.DernierGainBillets)}")
            AfficherLigne(NbLignes - 1, "MISSIONS {Reussies.Length}/{Visibles.Length}: +${DeviceAvion.Abreger(GainsMissions)}")
            Numero := NumeroTrajet
            Sleep(10.0)
            # (si un nouveau trajet a commencé entre-temps, on ne cache rien)
            if (Numero = NumeroTrajet, not EnCours?):
                if (C := Racine?) { C.SetVisibility(widget_visibility.Collapsed) }

    # ---------- vérifications (toutes les 0.2 s) ----------
    Verifier(Pas:float):void =
        Etat := Passagers.EtatBouton
        Ecoule := GetSimulationElapsedTime() - DebutVol
        var Change:logic = false
        for (T : Taches, not T.Fait?, not T.Rate?):
            if (not T.Visible?):
                if (DebutVol >= 0.0, Ecoule >= T.Apparition):
                    Surprise(T)
                    set Change = true
            else if (T.Genre = 0):
                Ouverts := for (O : Passagers.CoffresOuverts, O?) { O }
                if (Etat >= 2, Ouverts.Length = 0):
                    Reussir(T, "BINS CLOSED")
                    set Change = true
            else if (T.Genre = 1):
                if (T.Compte >= T.Objectif):
                    Reussir(T, "TICKETS CHECKED")
                    set Change = true
            else if (T.Genre = 2):
                if (R := RepereDemo?, Etat >= 2):
                    Ok := SurPlace(T, R, Pas)
                    if (Ok?):
                        Reussir(T, "SAFETY DEMO DONE")
                        set Change = true
            else if (T.Genre = 3):
                if (Etat = 3, P := Inspections[T.Numero]):
                    Ok := SurPlace(T, P.Repere, Pas)
                    if (Ok?):
                        Reussir(T, "{P.Nom} INSPECTED")
                        set Change = true
            else if (T.Genre = 5):
                if (O := ObjetsPerdus[T.Numero]):
                    Pres := Proche(O.GetTransform().Translation, 150.0)
                    if (Pres?):
                        O.Hide()
                        Reussir(T, "LOST ITEM FOUND")
                        set Change = true
        if (Change?) { Rafraichir() }

    # Le proprio reste DureeSurPlace secondes près du repère (le chrono repart à 0 s'il s'en va).
    SurPlace(T:tache_feuille, Repere:creative_prop, Pas:float):logic =
        Pres := Proche(Repere.GetTransform().Translation, RayonSurPlace)
        if (Pres?):
            set T.Chrono += Pas
        else:
            set T.Chrono = 0.0
        if (T.Chrono >= DureeSurPlace) then true else false

    Proche(Position:vector3, Rayon:float)<transacts>:logic =
        if (Joueur := DeviceAvion.Proprio?, Perso := Joueur.GetFortCharacter[]):
            if (Distance(Perso.GetTransform().Translation, Position) < Rayon) then true else false
        else:
            false

    # Une surprise en vol arrive : le fraudeur est choisi parmi les passagers assis,
    # l'objet perdu apparaît dans une cachette.
    Surprise(T:tache_feuille):void =
        if (T.Genre = 4):
            Assis := for (P : Passagers.EnCours, P.Etat = 2, P.Corps?) { P }
            # de préférence quelqu'un dont on n'a pas encore vu le billet
            PasVus := for (P : Assis, not DejaControle[P]) { P }
            Choix := if (PasVus.Length > 0) then PasVus else Assis
            if (P := Choix[GetRandomInt(0, Choix.Length - 1)]):
                set P.Fraudeur = true
                set T.Fraudeur = option{P}
                set T.Visible = true
                Message("ALERT: a passenger has no ticket!")
            else:
                # personne à bord : pas de fraudeur ce trajet
                set T.Rate = true
        else if (T.Genre = 5, O := ObjetsPerdus[T.Numero]):
            if (C := Cachettes[GetRandomInt(0, Cachettes.Length - 1)]):
                if (O.TeleportTo[C.GetTransform().Translation, O.GetTransform().Rotation]) {}
            O.Show()
            set T.Visible = true
            Message("A passenger lost something!")
        else:
            set T.Rate = true

    # ---------- contrôle des billets (viser un passager + TOUCHE) ----------
    OnBillet(Agent:agent):void =
        Vise := PassagerVise(Agent)
        if (EnCours?, P := Vise?):
            if (P.Fraudeur?):
                # pris ! il est emmené (il disparaît avec son bagage)
                set P.Fraudeur = false
                if (C := P.Corps?) { C.Dispose() }
                if (B := P.Bagage?) { B.Dispose() }
                set Passagers.EnCours = for (X : Passagers.EnCours, X <> P) { X }
                for (T : Taches, T.Genre = 4, not T.Fait?):
                    set T.Fraudeur = false
                    set T.Fait = true
                    Gagner(BonusFraudeur, "NO TICKET! FRAUDSTER CAUGHT")
                CompterBillet()
            else if (DejaControle[P]):
                Message("Already checked")
            else:
                Message("Ticket OK")
                CompterBillet()
            set Controles += array{P}
            Rafraichir()

    CompterBillet():void =
        for (T : Taches, T.Genre = 1, not T.Fait?, not T.Rate?):
            set T.Compte += 1

    DejaControle(P:passager)<transacts><decides>:void =
        var Trouve:logic = false
        for (X : Controles, X = P) { set Trouve = true }
        Trouve?

    # Le passager que le joueur vise (son corps), à portée.
    PassagerVise(Agent:agent):?passager =
        var Vise:?passager = false
        if (FC := Agent.GetFortCharacter[]):
            CamPos := FC.GetViewLocation()
            Avant := FC.GetViewRotation().RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})
            var Meilleur:float = RayonVisee
            for (P : Passagers.EnCours, C := P.Corps?):
                Pos := C.GetTransform().Translation + vector3{Z := 60.0}
                D := Pos - CamPos
                T := D.X * Avant.X + D.Y * Avant.Y + D.Z * Avant.Z
                Ecart := Distance(CamPos + Avant * T, Pos)
                if (T > 0.0, T < PorteeVisee, Ecart < Meilleur):
                    set Meilleur = Ecart
                    set Vise = option{P}
        Vise

    # ---------- gains ----------
    Reussir(T:tache_feuille, Texte:string):void =
        set T.Fait = true
        Gagner(BonusMission, Texte)

    Gagner(Bonus:int, Texte:string):void =
        Multi := if (PC := DevicePC?) then PC.MultiplicateurActif() else 1.0
        Gain := if (G := Round[Bonus * Multi]) then Max(0, G) else 0
        set GainsMissions += Gain
        set DeviceAvion.Argent += Gain
        DeviceAvion.MettreAJourUI()
        if (S := SonMission?) { S.Play() }
        Message("{Texte}  +${DeviceAvion.Abreger(Gain)}")

    Message(Texte:string):void =
        if (M := MessageHUD?, Joueur := DeviceAvion.Proprio?):
            M.SetText(Msg(Texte))
            M.Show(Joueur)

    # ---------- outils ----------
    Chance(Pourcent:int)<transacts><decides>:void =
        GetRandomInt(1, 100) <= Pourcent

    DureeVolPrevue():float =
        if (PC := DevicePC?) then PC.DureeVolActive() else Passagers.DureeVolSansPC

    # ---------- affichage ----------
    TexteTache(T:tache_feuille):string =
        Coche := if (T.Fait?) then "[X] " else if (T.Rate?) then "[-] " else "[  ] "
        Fin := if (T.Rate?) then " (MISSED)" else ""
        Phrase := if (T.Genre = 0) then "Close all overhead bins" else if (T.Genre = 1) then "Check tickets {Min(T.Compte, T.Objectif)}/{T.Objectif}" else if (T.Genre = 2) then "Safety demo (front)" else if (T.Genre = 3, P := Inspections[T.Numero]) then "In flight: inspect {P.Nom}" else if (T.Genre = 4) then "NO TICKET! Find this face:" else "Find the lost item"
        "{Coche}{Phrase}{Fin}"

    AfficherLigne(I:int, Contenu:string):void =
        if (L := Lignes[I]) { L.SetText(Msg(Contenu)) }

    Rafraichir():void =
        Visibles := for (T : Taches, T.Visible?) { T }
        for (I -> L : Lignes):
            if (T := Visibles[I]) then L.SetText(Msg(TexteTache(T))) else L.SetText(Msg(""))
        # photo du fraudeur (tant qu'il n'est pas attrapé)
        var Image:?texture = false
        for (T : Taches, T.Visible?, not T.Fait?, not T.Rate?, P := T.Fraudeur?, Tex := PhotosPassagers[P.Modele.Photo - 1]):
            set Image = option{Tex}
        if (Tex := Image?):
            Photo.SetImage(Tex)
            Photo.SetVisibility(widget_visibility.Visible)
        else:
            Photo.SetVisibility(widget_visibility.Collapsed)
        Entete.SetText(Msg("FLIGHT #{NumeroTrajet}  {Trajet()}"))

    Trajet():string =
        if (PC := DevicePC?, D := PC.ListeDestinations[PC.Active]):
            if (PC.Retour?) then "{D.Ville2} > {D.Ville1}" else "{D.Ville1} > {D.Ville2}"
        else:
            ""

    OnBasculer(Agent:agent):void =
        set Cachee = if (Cachee?) then false else true
        if (C := Racine?, EnCours?):
            C.SetVisibility(if (Cachee?) then widget_visibility.Collapsed else widget_visibility.Visible)

    # La feuille à droite de l'écran du proprio (créée une seule fois).
    Afficher():void =
        if (C := Racine?):
            if (not Cachee?) { C.SetVisibility(widget_visibility.Visible) }
        else if (Joueur := DeviceAvion.Proprio?, P := player[Joueur], UI := GetPlayerUI[P]):
            set Lignes = for (I := 1..NbLignes) { text_block{DefaultTextColor := NamedColors.Black} }
            LignesSlots := for (L : Lignes):
                stack_box_slot:
                    Padding := margin{Bottom := 8.0}
                    HorizontalAlignment := horizontal_alignment.Left
                    Widget := L
            Contenu := stack_box:
                Orientation := orientation.Vertical
                Slots := array{stack_box_slot{Padding := margin{Bottom := 14.0}, HorizontalAlignment := horizontal_alignment.Left, Widget := Entete}} + LignesSlots + array{stack_box_slot{HorizontalAlignment := horizontal_alignment.Center, Widget := Photo}}
            Ecran := canvas:
                Slots := array:
                    canvas_slot:
                        Anchors := anchors{Minimum := vector2{X := 1.0, Y := 0.5}, Maximum := vector2{X := 1.0, Y := 0.5}}
                        Alignment := vector2{X := 1.0, Y := 0.5}
                        Offsets := margin{Left := -20.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
                        SizeToContent := true
                        Widget := overlay:
                            Slots := array:
                                overlay_slot:
                                    Widget := texture_block{DefaultImage := FeuilleMission.FondFeuille, DefaultDesiredSize := vector2{X := 380.0, Y := 560.0}}
                                overlay_slot:
                                    Widget := Contenu
                                    Padding := margin{Left := 42.0, Top := 112.0, Right := 40.0, Bottom := 30.0}
                                    HorizontalAlignment := horizontal_alignment.Left
                                    VerticalAlignment := vertical_alignment.Top
            UI.AddWidget(Ecran)
            set Racine = option{Ecran}
            if (Cachee?) { Ecran.SetVisibility(widget_visibility.Collapsed) }
