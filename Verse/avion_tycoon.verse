using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - un avion (une parcelle).
# Pose ce device une fois par avion et remplis ses sous-parties dans l'éditeur.
#
# 1. CLAIM   : dans la passerelle, on marche sur la plaque -> l'avion est à nous
#              et on est téléporté dedans. Ensuite la plaque re-téléporte le proprio.
# 2. RANGEES : dans l'avion, on marche sur la plaque d'une rangée -> ses sièges
#              apparaissent. Les rangées se débloquent dans l'ordre de la liste.
#              Au 1er achat, les 3 cadres de gauche apparaissent (argent, /sec, rebirths).
# 3. INTERFACE : importe tes 3 images dans un dossier "Interface" du Tiroir à contenu
#              et nomme-les FondArgent, FondRevenu, FondRebirth.
#
# Argent : on démarre à 0 $ (mets Prix = 0 sur la 1re rangée, panneau "FREE").
# On gagne à chaque atterrissage (un billet par siège occupé, device passagers)
# et avec les missions de la feuille du trajet (device feuille_mission).

Msg<localizes>(Texte:string):message = "{Texte}"

# Les joueurs qui ont déjà un avion (pour qu'on ne puisse pas en prendre deux).
var JoueursAvecAvion:weak_map(session, []agent) = map{}

# ---------- 1. CLAIM ----------
reglages_claim := class<concrete>:
    # Le prop de la plaque dans la passerelle.
    @editable Plaque:creative_prop = creative_prop{}
    # Le prop du panneau CLAIM au-dessus (il suit le joueur le plus proche).
    @editable Panneau:creative_prop = creative_prop{}
    # Un petit prop repère dans l'avion (caché en jeu) :
    # sa position = où on arrive, sa rotation = où on regarde en arrivant.
    @editable Arrivee:creative_prop = creative_prop{}

# ---------- 2. UNE RANGEE DE SIEGES ----------
reglages_rangee := class<concrete>:
    # Prix de la rangée (0 = gratuit, panneau "FREE").
    @editable Prix:int = 0
    # Le prop de la plaque où on marche pour acheter.
    @editable Plaque:creative_prop = creative_prop{}
    # Le prop du panneau au-dessus (ex : "SEAT ROW / FREE"), il suit le joueur.
    @editable Panneau:creative_prop = creative_prop{}
    # Les sièges de la rangée (et tout ce qui doit apparaître avec : PNJ, écrans...).
    @editable Sieges:[]creative_prop = array{}
    # Argent gagné EN PLUS chaque seconde DE VOL, une fois cette dalle achetée (ex : 10).
    @editable Revenu:int = 0
    # DALLE "WIDER CABIN" (changer d'avion) : mets ici le repère d'arrivée dans le nouvel avion.
    # A l'achat, le joueur y est téléporté et la plaque de la passerelle l'y ramène ensuite.
    # Dans Sieges, mets les sièges / toilettes du NOUVEL avion déjà achetés avant (ils apparaissent).
    # Les dalles suivantes de la liste Rangees = celles du nouvel avion, dans l'ordre.
    @editable ArriveeNouvelAvion:?creative_prop = false

# ---------- 3. REGLAGES ----------
reglages_generaux := class<concrete>:
    # Distance (cm) autour du centre d'une plaque pour compter qu'on est dessus.
    @editable RayonPlaque:float = 150.0
    # Distance (cm) jusqu'à laquelle les panneaux suivent un joueur.
    @editable DistanceSuivi:float = 3000.0
    # Si les panneaux montrent leur dos ou leur côté, mets 180 ou 90 ici.
    @editable DecalageAngle:float = 0.0
    # Douceur de la rotation : 0.05 = très doux, 0.3 = rapide, 1.0 = instantané.
    @editable Lissage:float = 0.12
    # Flottement des panneaux : hauteur (cm) et allers-retours par seconde (0 = aucun).
    @editable Flottement:float = 8.0
    @editable VitesseFlottement:float = 0.5

avion_tycoon := class(creative_device):
    @editable Claim:reglages_claim = reglages_claim{}
    @editable Rangees:[]reglages_rangee = array{}
    @editable Reglages:reglages_generaux = reglages_generaux{}
    # Son joué à chaque achat de rangée (même gratuite) : un Appareil Lecteur audio.
    @editable SonAchat:?audio_player_device = false
    # (facultatif) Lecteurs audio : chaque gain (commande, mission, fraudeur attrapé), chaque
    # perte (faux billet raté), et le petit "tic" du récap de fin de vol qui compte l'argent.
    @editable SonArgent:?audio_player_device = false
    @editable SonPerte:?audio_player_device = false
    @editable SonCompteur:?audio_player_device = false
    # (facultatif) Appareils Panneau d'affichage (Billboard) posés devant l'écran blanc d'un
    # objet 3D (ATM, borne...) : ils affichent l'argent du joueur en direct.
    @editable EcransArgent:[]billboard_device = array{}
    # TEST : argent infini (coche pour tester, DECOCHE avant de publier).
    @editable TestArgentInfini:logic = false

    var Proprio:?agent = false
    var Argent:int = 0
    # Nombre de rangées achetées (utilisé par le device passagers).
    var RangeesAchetees:int = 0
    # Index (dans Rangees) de la 1re dalle de l'avion actuel : les sièges d'avant = ancien avion.
    var DebutAvionActuel:int = 0
    var Arrivee:?creative_prop = false
    # Argent par seconde pendant le vol : dalles achetées (RevenuAchats) + passagers assis.
    # (c'est le device passagers qui verse l'argent, seconde par seconde, seulement en vol)
    var RevenuParSeconde:int = 0
    var RevenuAchats:int = 0
    var RevenuVol:int = 0
    var Rebirths:int = 0
    # Bonus des AMELIORATIONS du PC (calcules par menu_pc, lus par passagers et demandes).
    var MultiBillet:float = 1.0
    var MultiService:float = 1.0
    var MultiRepas:float = 1.0
    var MultiPatience:float = 1.0
    var MultiRebirth:float = 1.0
    var UICree:logic = false
    # Le device passagers de cet avion (il s'inscrit tout seul au démarrage).
    var Passagers:?passagers = false
    # Les comptes du vol, pour le récap de fin de vol (remis à 0 à chaque récap).
    var StatBillets:int = 0
    var StatService:int = 0
    var StatMissions:int = 0
    var StatFraudeurs:int = 0
    var StatPertes:int = 0
    var StatDepenses:int = 0
    var NumeroPopup:int = 0
    var NumeroRecap:int = 0
    var EcranRecap:?canvas = false
    TexteArgent:text_block = text_block{DefaultTextColor := NamedColors.White, DefaultShadowColor := NamedColors.Black, DefaultShadowOpacity := 0.85, DefaultShadowOffset := option{vector2{X := 2.0, Y := 2.0}}}
    TexteRevenu:text_block = text_block{DefaultTextColor := NamedColors.White, DefaultShadowColor := NamedColors.Black, DefaultShadowOpacity := 0.85, DefaultShadowOffset := option{vector2{X := 2.0, Y := 2.0}}}
    TexteRebirth:text_block = text_block{DefaultTextColor := NamedColors.White, DefaultShadowColor := NamedColors.Black, DefaultShadowOpacity := 0.85, DefaultShadowOffset := option{vector2{X := 2.0, Y := 2.0}}}

    OnBegin<override>()<suspends>:void =
        Print("Avion : device démarré")
        # Tout est caché au départ, sauf le claim.
        Claim.Arrivee.Hide()
        set Arrivee = option{Claim.Arrivee}
        for (R : Rangees):
            if (A := R.ArriveeNouvelAvion?) { A.Hide() }
            R.Plaque.Hide()
            R.Panneau.Hide()
            for (S : R.Sieges) { S.Hide() }

        # 1. Claim
        race:
            block:
                Joueur := AttendreSurPlaque(Claim.Plaque, false)
                set Proprio = option{Joueur}
                Print("Avion : claim OK")
                if (TestArgentInfini?) { set Argent = 1000000000000000 }
            SuivreRegard(Claim.Panneau)
        Claim.Panneau.Hide()
        if (Joueur := Proprio?):
            Teleporter(Joueur)
        spawn{BoucleRetourAvion()}

        # 2. Rangées, dans l'ordre
        for (R : Rangees):
            AcheterRangee(R)

    # ---------- Téléportation ----------
    # TeleportTo échoue sans rien dire si l'endroit est bloqué (collision, sol trop proche).
    # On essaie donc à la position du repère, puis un peu plus haut, et on l'écrit dans le journal.
    Teleporter(Joueur:agent):void =
        Repere := if (A := Arrivee?) then A else Claim.Arrivee
        Destination := Repere.GetTransform()
        if (Perso := Joueur.GetFortCharacter[]):
            var Reussi:logic = false
            for (Hauteur : array{0.0, 50.0, 100.0, 150.0}, not Reussi?):
                Position := Destination.Translation + vector3{X := 0.0, Y := 0.0, Z := Hauteur}
                if (Perso.TeleportTo[Position, Destination.Rotation]):
                    set Reussi = true
                    Print("Avion : téléporté (+{Hauteur} cm)")
            if (not Reussi?):
                Print("Avion : téléportation IMPOSSIBLE, l'arrivée est bloquée par une collision")

    # Après le claim, la plaque de la passerelle ramène le proprio dans son avion.
    BoucleRetourAvion()<suspends>:void =
        loop:
            Joueur := AttendreSurPlaque(Claim.Plaque, Proprio)
            Teleporter(Joueur)
            Sleep(1.0)

    # ---------- Achat d'une rangée ----------
    AcheterRangee(R:reglages_rangee)<suspends>:void =
        R.Plaque.Show()
        R.Panneau.Show()
        race:
            AttendrePaiement(R)
            SuivreRegard(R.Panneau)
        R.Plaque.Hide()
        R.Panneau.Hide()
        for (S : R.Sieges) { S.Show() }
        set RangeesAchetees += 1
        set RevenuAchats += R.Revenu
        # Dalle "WIDER CABIN" : on passe dans le nouvel avion.
        if (A := R.ArriveeNouvelAvion?):
            set DebutAvionActuel = RangeesAchetees - 1
            set Arrivee = option{A}
            if (Joueur := Proprio?) { Teleporter(Joueur) }
        if (not UICree?):
            set UICree = true
            CreerUI()
        MettreAJourUI()

    AttendrePaiement(R:reglages_rangee)<suspends>:void =
        loop:
            AttendreSurPlaque(R.Plaque, Proprio)
            if (R.ArriveeNouvelAvion?, not AuSolEtVide[]):
                # WIDER CABIN : seulement entre deux vols (pas en vol, pas pendant l'embarquement)
                Avertir("FINISH THE FLIGHT FIRST!")
                Sleep(3.0)
            else if (Argent >= R.Prix):
                Depenser(R.Prix)
                if (Son := SonAchat?) { Son.Play() }
                break
            else:
                # Pas assez d'argent : on réessaie dans 1 seconde.
                Sleep(1.0)

    # Entre deux vols : pas d'embarquement en cours, pas de vol, plus personne à bord.
    AuSolEtVide()<transacts><decides>:void =
        P := Passagers?
        P.EtatBouton = 0
        P.EnCours.Length = 0

    # ---------- Plaques ----------
    # Attend qu'un joueur soit sur la plaque. Si Seul est rempli, seul ce joueur compte.
    # Pour le claim, un joueur qui a déjà un avion ne compte pas.
    AttendreSurPlaque(Plaque:creative_prop, Seul:?agent)<suspends>:agent =
        Centre := Plaque.GetTransform().Translation
        loop:
            Sleep(0.1)
            var Trouve:?agent = false
            for (Joueur : GetPlayspace().GetPlayers(), Perso := Joueur.GetFortCharacter[]):
                if (Distance(Perso.GetTransform().Translation, Centre) < Reglages.RayonPlaque):
                    if (S := Seul?):
                        if (S = Joueur) { set Trouve = option{Joueur} }
                    else if (not ADejaUnAvion[Joueur]):
                        set Trouve = option{Joueur}
            if (J := Trouve?):
                if (not Seul?) { EnregistrerAvion(J) }
                return J

    ADejaUnAvion(Joueur:agent)<transacts><decides>:void =
        Liste := JoueursAvecAvion[GetSession()]
        Liste.Find[Joueur]

    EnregistrerAvion(Joueur:agent):void =
        Liste := JoueursAvecAvion[GetSession()] or array{}
        if (set JoueursAvecAvion[GetSession()] = Liste + array{Joueur}) {}

    # ---------- Panneaux qui suivent le joueur, sans à-coups ----------
    # À chaque frame : on vise le joueur le plus proche, on tourne d'un petit
    # pourcentage vers lui (lissage) et on fait flotter le panneau.
    SuivreRegard(Panneau:creative_prop)<suspends>:void =
        Depart := Panneau.GetTransform()
        Position := Depart.Translation
        var Yaw:float = if (Y := Depart.Rotation.GetYawPitchRollDegrees()[0]) then Y else 0.0
        # MoveTo par petits pas de 0.1 s (fluide en réseau) au lieu d'un TeleportTo à chaque image,
        # qui faisait sauter / bugger le panneau.
        loop:
            Sleep(0.0)
            if (Cible := JoueurLePlusProche[Position]):
                YawCible := ArcTan(Cible.Y - Position.Y, Cible.X - Position.X) * 180.0 / PiFloat + Reglages.DecalageAngle
                set Yaw += AngleLePlusCourt(YawCible - Yaw) * Reglages.Lissage
            Hauteur := Sin(GetSimulationElapsedTime() * Reglages.VitesseFlottement * 2.0 * PiFloat) * Reglages.Flottement
            NouvellePosition := Position + vector3{X := 0.0, Y := 0.0, Z := Hauteur}
            Panneau.MoveTo(NouvellePosition, MakeRotationFromYawPitchRollDegrees(Yaw, 0.0, 0.0), 0.1)

    JoueurLePlusProche(Position:vector3)<decides><transacts>:vector3 =
        var PlusProche:float = Reglages.DistanceSuivi
        var Cible:?vector3 = false
        for (Joueur : GetPlayspace().GetPlayers(), Perso := Joueur.GetFortCharacter[]):
            PosJoueur := Perso.GetTransform().Translation
            Dist := Distance(PosJoueur, Position)
            if (Dist < PlusProche):
                set PlusProche = Dist
                set Cible = option{PosJoueur}
        Cible?

    # Ramène un écart d'angle entre -180 et 180 (tourner par le chemin le plus court).
    AngleLePlusCourt(Angle:float):float =
        var A:float = Angle
        loop:
            if (A > 180.0):
                set A -= 360.0
            else if (A < -180.0):
                set A += 360.0
            else:
                break
        A

    # ---------- Interface à gauche de l'écran ----------
    # Un cadre = ton image en fond + le texte centré dessus.
    Cadre(Image:texture, Texte:text_block):stack_box_slot =
        stack_box_slot:
            Padding := margin{Bottom := 10.0}
            HorizontalAlignment := horizontal_alignment.Left
            Widget := overlay:
                Slots := array:
                    overlay_slot:
                        Widget := texture_block{DefaultImage := Image, DefaultDesiredSize := vector2{X := 256.0, Y := 64.0}}
                    overlay_slot:
                        Widget := Texte
                        # centré sur la barre seulement, à droite de l'icône
                        Padding := margin{Left := 44.0, Right := 4.0}
                        HorizontalAlignment := horizontal_alignment.Center
                        VerticalAlignment := vertical_alignment.Center

    CreerUI():void =
        if (Joueur := Proprio?, P := player[Joueur], UI := GetPlayerUI[P]):
            Ecran := canvas:
                Slots := array:
                    canvas_slot:
                        Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.5}, Maximum := vector2{X := 0.0, Y := 0.5}}
                        Alignment := vector2{X := 0.0, Y := 0.5}
                        Offsets := margin{Left := 20.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
                        SizeToContent := true
                        Widget := stack_box:
                            Orientation := orientation.Vertical
                            Slots := array:
                                Cadre(Interface.FondArgent, TexteArgent)
                                Cadre(Interface.FondRevenu, TexteRevenu)
                                Cadre(Interface.FondRebirth, TexteRebirth)
            UI.AddWidget(Ecran)

    MettreAJourUI():void =
        set RevenuParSeconde = RevenuVol
        TexteArgent.SetText(Msg("${Abreger(Argent)}"))
        for (E : EcransArgent) { E.SetText(Msg("${Abreger(Argent)}")) }
        TexteRevenu.SetText(Msg("${Abreger(RevenuParSeconde)}/Sec"))
        TexteRebirth.SetText(Msg("{Rebirths} Rebirths"))

    # 2500000000 -> "2.5B", 1400000 -> "1.4M", 76000 -> "76.0K" ; au-delà du milliard :
    # T (mille milliards), Qa (million de milliards), Qi (milliard de milliards).
    Abreger(N:int):string =
        if (N >= 1000000000000000000, A := Quotient[N, 1000000000000000000], B := Quotient[Mod[N, 1000000000000000000], 100000000000000000]):
            "{A}.{B}Qi"
        else if (N >= 1000000000000000, A := Quotient[N, 1000000000000000], B := Quotient[Mod[N, 1000000000000000], 100000000000000]):
            "{A}.{B}Qa"
        else if (N >= 1000000000000, A := Quotient[N, 1000000000000], B := Quotient[Mod[N, 1000000000000], 100000000000]):
            "{A}.{B}T"
        else if (N >= 1000000000, A := Quotient[N, 1000000000], B := Quotient[Mod[N, 1000000000], 100000000]):
            "{A}.{B}B"
        else if (N >= 1000000, A := Quotient[N, 1000000], B := Quotient[Mod[N, 1000000], 100000]):
            "{A}.{B}M"
        else if (N >= 1000, A := Quotient[N, 1000], B := Quotient[Mod[N, 1000], 100]):
            "{A}.{B}K"
        else:
            "{N}"

    # ---------- l'argent qui rentre et qui sort ----------
    # Cat : 0 billets (argent par seconde du vol : pas d'animation), 1 commandes servies,
    # 2 missions, 3 fraudeurs attrapés.
    Gagner(Montant:int, Cat:int):void =
        if (Montant > 0):
            set Argent += Montant
            if (Cat = 0):
                set StatBillets += Montant
            else if (Cat = 1):
                set StatService += Montant
            else if (Cat = 2):
                set StatMissions += Montant
            else:
                set StatFraudeurs += Montant
            MettreAJourUI()
            if (Cat > 0):
                if (Son := SonArgent?) { Son.Play() }
                Popup("+${Abreger(Montant)}", "86EFAC")

    # Une perte (faux billet laissé passer...) : l'argent ne descend pas sous 0.
    Perdre(Montant:int, Texte:string):void =
        Perte := Min(Montant, Argent)
        if (Perte > 0):
            set Argent -= Perte
            set StatPertes += Perte
            MettreAJourUI()
            if (Son := SonPerte?) { Son.Play() }
            Popup("-${Abreger(Perte)}  {Texte}", "FCA5A5")

    # Un achat (dalle, ligne, produits, amélioration) : compté dans les dépenses du récap.
    Depenser(Montant:int):void =
        set Argent -= Montant
        set StatDepenses += Montant
        MettreAJourUI()

    # Un message rouge qui saute à l'écran (même animation que les gains, sans billets).
    Avertir(Texte:string):void =
        if (Son := SonPerte?) { Son.Play() }
        Popup(Texte, "FCA5A5")

    # ---------- l'icône d'argent qui saute à côté du compteur ----------
    Popup(Texte:string, Couleur:string):void =
        if (Joueur := Proprio?, P := player[Joueur], UI := GetPlayerUI[P]):
            set NumeroPopup += 1
            # plusieurs gains d'affilée : ils se décalent un peu pour ne pas se cacher
            Decalage := if (D := Mod[NumeroPopup, 3]) then D * 56.0 else 0.0
            spawn{AnimerPopup(UI, Texte, Couleur, Decalage)}

    AnimerPopup(UI:player_ui, Texte:string, Couleur:string, Decalage:float)<suspends>:void =
        Toile := canvas{}
        UI.AddWidget(Toile)
        Icone := texture_block{DefaultImage := InterfacePC.IconeArgent, DefaultDesiredSize := vector2{X := 96.0, Y := 96.0}}
        Ecrit := text_block:
            DefaultText := Msg(Texte)
            DefaultTextColor := MakeColorFromHex(Couleur)
            DefaultShadowColor := MakeColorFromHex("052E16")
            DefaultShadowOpacity := 1.0
            DefaultShadowOffset := option{vector2{X := 3.0, Y := 3.0}}
        var Slots:[]canvas_slot = array{}
        Etapes := 45
        for (K := 0..Etapes):
            T := K * 1.0 / (Etapes * 1.0)
            # pop (grossit, rebondit), puis monte doucement, puis rétrécit et disparaît
            Taille := if (T < 0.12) then 96.0 * 1.3 * T / 0.12 else if (T < 0.22) then 96.0 * (1.3 - 0.3 * (T - 0.12) / 0.1) else if (T > 0.85) then 96.0 * Max(0.0, 1.0 - (T - 0.85) / 0.15) else 96.0
            Monte := -Decalage - 70.0 * T
            for (S : Slots) { Toile.RemoveWidget(S.Widget) }
            set Slots = array:
                PlaceGauche(Icone, 300.0 + 48.0 - Taille / 2.0, Monte - Taille / 2.0, Taille, Taille)
                PlaceGauche(Ecrit, 404.0, Monte - 20.0, 700.0, 44.0)
            if (T > 0.9) { set Slots = array{PlaceGauche(Icone, 300.0 + 48.0 - Taille / 2.0, Monte - Taille / 2.0, Taille, Taille)} }
            for (S : Slots) { Toile.AddWidget(S) }
            Sleep(0.033)
        UI.RemoveWidget(Toile)

    # Un widget placé depuis le milieu du bord gauche de l'écran (là où est le compteur d'argent).
    PlaceGauche(W:widget, X:float, Y:float, L:float, H:float):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.5}, Maximum := vector2{X := 0.0, Y := 0.5}}
            Alignment := vector2{X := 0.0, Y := 0.0}
            Offsets := margin{Left := X, Top := Y, Right := L, Bottom := H}
            SizeToContent := false
            Widget := W

    # ---------- le récap de fin de vol ----------
    # Appelé par le device passagers juste après l'atterrissage (le temps que la feuille de
    # mission compte les faux billets ratés).
    RecapApres(Delai:float)<suspends>:void =
        Sleep(Delai)
        AfficherRecap()

    AfficherRecap():void =
        if (Joueur := Proprio?, P := player[Joueur], UI := GetPlayerUI[P]):
            FermerRecap()
            set NumeroRecap += 1
            Valeurs := array{StatBillets, StatService, StatMissions, StatFraudeurs, StatPertes, StatDepenses}
            set StatBillets = 0
            set StatService = 0
            set StatMissions = 0
            set StatFraudeurs = 0
            set StatPertes = 0
            set StatDepenses = 0
            spawn{AnimerRecap(P, UI, Valeurs, NumeroRecap)}

    FermerRecap():void =
        if (C := EcranRecap?, Joueur := Proprio?, P := player[Joueur], UI := GetPlayerUI[P]):
            UI.RemoveWidget(C)
        set EcranRecap = false

    AnimerRecap(P:player, UI:player_ui, Valeurs:[]int, Numero:int)<suspends>:void =
        Noms := array{"TICKETS", "ORDERS SERVED", "MISSIONS", "FAKE TICKETS CAUGHT", "FAKE TICKETS MISSED", "SPENT"}
        # les 4 premières lignes ajoutent, les 2 dernières enlèvent
        Toile := canvas:
            Slots := array:
                # fond cartoon multicolore sur tout l'écran
                canvas_slot:
                    Anchors := anchors{Minimum := vector2{X := 0.0, Y := 0.0}, Maximum := vector2{X := 1.0, Y := 1.0}}
                    Offsets := margin{Left := 0.0, Top := 0.0, Right := 0.0, Bottom := 0.0}
                    SizeToContent := false
                    Widget := texture_block{DefaultImage := InterfacePC.FondRecap}
                PlaceRecap(texture_block{DefaultImage := InterfacePC.PanneauRecap, DefaultDesiredSize := vector2{X := 760.0, Y := 760.0}}, 580.0, 210.0, 760.0, 760.0, 1)
                PlaceRecap(texture_block{DefaultImage := InterfacePC.Ruban, DefaultDesiredSize := vector2{X := 900.0, Y := 225.0}}, 510.0, 110.0, 900.0, 225.0, 3)
                PlaceRecap(TexteRecap("FLIGHT COMPLETE!", "FFFFFF", text_justification.Center), 510.0, 190.0, 900.0, 44.0, 4)
        UI.AddWidget(Toile, player_ui_slot{InputMode := ui_input_mode.All})
        set EcranRecap = option{Toile}
        spawn{ScintillerEtoiles(Toile, Numero)}
        var Total:int = 0
        for (I -> Valeur : Valeurs, Nom := Noms[I]):
            if (Numero <> NumeroRecap) { return }
            Moins := if (I >= 4) then true else false
            Y := 330.0 + I * 66.0
            Couleur := if (Moins?) then "FCA5A5" else "86EFAC"
            Chiffre := TexteRecap("", Couleur, text_justification.Right)
            Toile.AddWidget(PlaceRecap(TexteRecapGauche(Nom), 650.0, Y, 400.0, 44.0, 4))
            Toile.AddWidget(PlaceRecap(Chiffre, 1010.0, Y, 260.0, 44.0, 4))
            # ça monte vite au début puis ralentit, comme une machine à sous
            Etapes := 10
            for (K := 1..Etapes):
                F := K * 1.0 / (Etapes * 1.0)
                Montre := if (V := Round[Valeur * (1.0 - (1.0 - F) * (1.0 - F))]) then V else Valeur
                Signe := if (Moins?) then "-" else "+"
                Chiffre.SetText(Msg("{Signe}${Abreger(Montre)}"))
                if (Mod[K, 2] = 0, Son := SonCompteur?) { Son.Play() }
                Sleep(0.03)
            if (Moins?):
                set Total -= Valeur
            else:
                set Total += Valeur
            Sleep(0.06)
        if (Numero <> NumeroRecap) { return }
        # le total, plus gros, avec l'icône d'argent
        Toile.AddWidget(PlaceRecap(color_block{DefaultColor := MakeColorFromHex("BBF7D0"), DefaultOpacity := 0.6}, 650.0, 735.0, 620.0, 4.0, 4))
        Toile.AddWidget(PlaceRecap(texture_block{DefaultImage := InterfacePC.IconeArgent, DefaultDesiredSize := vector2{X := 110.0, Y := 110.0}}, 640.0, 745.0, 110.0, 110.0, 5))
        Toile.AddWidget(PlaceRecap(TexteRecapGauche("TOTAL"), 760.0, 778.0, 250.0, 44.0, 5))
        CouleurTotal := if (Total >= 0) then "FFFFFF" else "FCA5A5"
        Grand := TexteRecap("", CouleurTotal, text_justification.Right)
        Toile.AddWidget(PlaceRecap(Grand, 990.0, 778.0, 280.0, 44.0, 5))
        EtapesTotal := 16
        Absolu := if (Total >= 0) then Total else -Total
        for (K := 1..EtapesTotal):
            F := K * 1.0 / (EtapesTotal * 1.0)
            Montre := if (V := Round[Absolu * (1.0 - (1.0 - F) * (1.0 - F) * (1.0 - F))]) then V else Absolu
            SigneTotal := if (Total >= 0) then "+" else "-"
            Grand.SetText(Msg("{SigneTotal}${Abreger(Montre)}"))
            if (Mod[K, 2] = 0, Son := SonCompteur?) { Son.Play() }
            Sleep(0.03)
        if (Son := SonArgent?) { Son.Play() }
        # le bouton CONTINUE (ou ça se ferme tout seul après 10 secondes)
        Toile.AddWidget(PlaceRecap(texture_block{DefaultImage := InterfacePC.BoutonVert, DefaultDesiredSize := vector2{X := 300.0, Y := 150.0}}, 810.0, 870.0, 300.0, 120.0, 6))
        Toile.AddWidget(PlaceRecap(TexteRecap("CONTINUE", "FFFFFF", text_justification.Center), 810.0, 908.0, 300.0, 44.0, 7))
        Bouton := button_quiet{DefaultText := Msg("")}
        Bouton.OnClick().Subscribe(clic_recap{Device := Self}.Clique)
        Toile.AddWidget(PlaceRecap(Bouton, 810.0, 870.0, 300.0, 120.0, 30))
        Sleep(6.0)
        if (Numero = NumeroRecap) { FermerRecap() }

    # Les étoiles du fond du récap : chacune grossit puis rapetisse à son propre rythme.
    ScintillerEtoiles(Toile:canvas, Numero:int)<suspends>:void =
        # des étoiles autour du panneau (pas dessus)
        var Etoiles:[]tuple(float, float, float, int, int) = array{}
        for (I := 0..21):
            Gauche := if (Mod[I, 2] = 0) then true else false
            X := if (Gauche?) then GetRandomFloat(40.0, 520.0) else GetRandomFloat(1400.0, 1880.0)
            Y := GetRandomFloat(40.0, 1040.0)
            Taille := GetRandomFloat(30.0, 70.0)
            Periode := GetRandomInt(14, 30)
            Decale := GetRandomInt(0, 30)
            set Etoiles += array{(X, Y, Taille, Periode, Decale)}
        Images := for (E : Etoiles) { texture_block{DefaultImage := InterfacePC.Etoile, DefaultDesiredSize := vector2{X := 64.0, Y := 64.0}} }
        var Places:[]canvas_slot = array{}
        var K:int = 0
        loop:
            if (Numero <> NumeroRecap or not EcranRecap?) { break }
            for (S : Places) { Toile.RemoveWidget(S.Widget) }
            set Places = for (I -> E : Etoiles, Img := Images[I]):
                # aller-retour 0 -> 1 -> 0 (triangle), la taille varie entre 15 % et 100 %
                Pas := if (M := Mod[K + E(4), E(3)]) then M * 1.0 / (E(3) * 1.0) else 0.0
                Vague := if (Pas < 0.5) then Pas * 2.0 else (1.0 - Pas) * 2.0
                T := E(2) * (0.15 + 0.85 * Vague)
                PlaceRecap(Img, E(0) - T / 2.0, E(1) - T / 2.0, T, T, 1)
            for (S : Places) { Toile.AddWidget(S) }
            set K += 1
            Sleep(0.05)

    # Placé comme sur un écran 1920 x 1080 (X, Y = coin haut gauche).
    PlaceRecap(W:widget, X:float, Y:float, L:float, H:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.5}, Maximum := vector2{X := 0.5, Y := 0.5}}
            Alignment := vector2{X := 0.0, Y := 0.0}
            Offsets := margin{Left := X - 960.0, Top := Y - 540.0, Right := L, Bottom := H}
            SizeToContent := false
            ZOrder := Couche
            Widget := W

    TexteRecap(S:string, Couleur:string, J:text_justification):text_block =
        text_block:
            DefaultText := Msg(S)
            DefaultTextColor := MakeColorFromHex(Couleur)
            DefaultJustification := J
            DefaultShadowColor := MakeColorFromHex("052E16")
            DefaultShadowOpacity := 1.0
            DefaultShadowOffset := option{vector2{X := 3.0, Y := 3.0}}

    TexteRecapGauche(S:string):text_block =
        text_block:
            DefaultText := Msg(S)
            DefaultTextColor := NamedColors.White
            DefaultJustification := text_justification.Left
            DefaultShadowColor := MakeColorFromHex("052E16")
            DefaultShadowOpacity := 1.0
            DefaultShadowOffset := option{vector2{X := 3.0, Y := 3.0}}

# Le bouton CONTINUE du récap.
clic_recap := class:
    Device:avion_tycoon
    Clique(Clic:widget_message):void = Device.FermerRecap()
