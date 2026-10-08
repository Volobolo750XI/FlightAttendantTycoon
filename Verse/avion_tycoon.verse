using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - un avion = une parcelle.
# Pose ce device une fois par avion et remplis ses props dans l'éditeur.
# (Il remplace passerelle_embarquement : il fait la passerelle ET les achats.)
#
# 1. CLAIM   : dans la passerelle, on marche sur la plaque -> l'avion est à nous
#              et on est téléporté dedans. Ensuite, la plaque ne téléporte plus
#              que le propriétaire.
# 2. ACHATS  : dans l'avion, les plaques d'achat apparaissent une par une, dans
#              l'ordre de la liste. On marche dessus -> les objets (sièges...)
#              apparaissent.
# 3. INTERFACE : au premier achat, les 3 cadres à gauche apparaissent
#              (argent, argent/seconde, rebirths). Importe tes 3 images dans un
#              dossier "Interface" du Tiroir à contenu, nommées
#              FondArgent, FondRevenu, FondRebirth.

Msg<localizes>(Texte:string):message = "{Texte}"

# Les joueurs qui ont déjà un avion (pour qu'on ne puisse pas en prendre deux).
var JoueursAvecAvion:weak_map(session, []agent) = map{}

# ---------- UN ACHAT (ex : une rangée de sièges) ----------
reglages_achat := class<concrete>:
    @editable Prix:int = 0
    # Argent/seconde ajouté par cet achat (on s'en servira pour l'argent).
    @editable ArgentParSeconde:int = 0
    # Le prop de la plaque où on marche pour acheter.
    @editable Plaque:creative_prop = creative_prop{}
    # Le prop du panneau au-dessus (nom en haut, prix en dessous).
    @editable Panneau:creative_prop = creative_prop{}
    # Les objets qui apparaissent à l'achat : les sièges de la rangée, etc.
    # Clique sur + puis prends-les à la pipette.
    @editable Objets:[]creative_prop = array{}

avion_tycoon := class(creative_device):
    # ---------- Passerelle ----------
    @editable PlaqueClaim:creative_prop = creative_prop{}
    @editable PanneauClaim:creative_prop = creative_prop{}
    # Petit prop repère dans l'avion (caché en jeu) : position + direction d'arrivée.
    @editable Arrivee:creative_prop = creative_prop{}

    # ---------- Achats, dans l'ordre ----------
    @editable Achats:[]reglages_achat = array{}

    # ---------- Réglages ----------
    # Distance (cm) autour du centre d'une plaque pour compter qu'on est dessus.
    @editable RayonPlaque:float = 150.0
    # Distance (cm) jusqu'à laquelle les panneaux suivent un joueur.
    @editable DistanceSuivi:float = 3000.0
    # Si les panneaux montrent leur dos ou leur côté, mets 180 ou 90 ici.
    @editable DecalageAngle:float = 0.0
    # Douceur de la rotation : 0.05 = très doux, 0.3 = rapide, 1.0 = instantané.
    @editable Lissage:float = 0.12
    # Flottement des panneaux : hauteur (cm) et allers-retours par seconde.
    @editable Flottement:float = 8.0
    @editable VitesseFlottement:float = 0.5

    var Proprio:?agent = false
    var Argent:int = 0
    var RevenuParSeconde:int = 0
    var Rebirths:int = 0
    var UICreee:logic = false
    TexteArgent:text_block = text_block{DefaultTextColor := NamedColors.White}
    TexteRevenu:text_block = text_block{DefaultTextColor := NamedColors.White}
    TexteRebirth:text_block = text_block{DefaultTextColor := NamedColors.White}

    OnBegin<override>()<suspends>:void =
        Arrivee.Hide()
        for (A : Achats):
            A.Plaque.Hide()
            A.Panneau.Hide()
            for (O : A.Objets) { O.Hide() }

        # Le panneau de la passerelle suit les joueurs pendant toute la partie.
        spawn{SuivreRegard(PanneauClaim)}

        # 1. Claim : le premier joueur sans avion qui marche sur la plaque.
        Joueur := AttendreSurPlaque(PlaqueClaim, false)
        set Proprio = option{Joueur}
        Teleporter(Joueur)
        # Ensuite la plaque sert d'entrée pour le propriétaire seulement.
        spawn{BoucleEntree()}

        # 2. Achats, un par un
        for (A : Achats):
            Acheter(A)

    # ---------- Téléportation dans l'avion ----------
    Teleporter(Joueur:agent):void =
        Destination := Arrivee.GetTransform()
        if (Perso := Joueur.GetFortCharacter[]):
            if (Perso.TeleportTo[Destination.Translation, Destination.Rotation]) {}

    BoucleEntree()<suspends>:void =
        loop:
            Joueur := AttendreSurPlaque(PlaqueClaim, Proprio)
            Teleporter(Joueur)
            Sleep(1.0)

    # ---------- Un achat ----------
    Acheter(A:reglages_achat)<suspends>:void =
        A.Plaque.Show()
        A.Panneau.Show()
        race:
            AttendrePaiement(A)
            SuivreRegard(A.Panneau)
        A.Plaque.Hide()
        A.Panneau.Hide()
        for (O : A.Objets) { O.Show() }
        set RevenuParSeconde += A.ArgentParSeconde
        # Au tout premier achat, l'interface apparaît.
        if (not UICreee?):
            set UICreee = true
            CreerUI()
        MettreAJourUI()

    AttendrePaiement(A:reglages_achat)<suspends>:void =
        loop:
            AttendreSurPlaque(A.Plaque, Proprio)
            if (Argent >= A.Prix):
                set Argent -= A.Prix
                break
            # Pas assez d'argent : on réessaie dans 1 seconde.
            Sleep(1.0)

    # ---------- Plaques ----------
    # Attend qu'un joueur soit sur la plaque. Si Seul est rempli, seul ce joueur compte.
    # Sinon (claim), un joueur qui a déjà un avion ne compte pas.
    AttendreSurPlaque(Plaque:creative_prop, Seul:?agent)<suspends>:agent =
        Centre := Plaque.GetTransform().Translation
        loop:
            Sleep(0.1)
            var Trouve:?agent = false
            for (Joueur : GetPlayspace().GetPlayers(), Perso := Joueur.GetFortCharacter[]):
                if (Distance(Perso.GetTransform().Translation, Centre) < RayonPlaque):
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

    # ---------- Panneaux qui suivent le regard, sans à-coups ----------
    SuivreRegard(Panneau:creative_prop)<suspends>:void =
        Depart := Panneau.GetTransform()
        Position := Depart.Translation
        var Yaw:float = if (Y := Depart.Rotation.GetYawPitchRollDegrees()[0]) then Y else 0.0
        loop:
            Sleep(0.0)
            if (Cible := JoueurLePlusProche[Position]):
                YawCible := ArcTan(Cible.Y - Position.Y, Cible.X - Position.X) * 180.0 / PiFloat + DecalageAngle
                set Yaw += AngleLePlusCourt(YawCible - Yaw) * Lissage
            Hauteur := Sin(GetSimulationElapsedTime() * VitesseFlottement * 2.0 * PiFloat) * Flottement
            NouvellePosition := Position + vector3{X := 0.0, Y := 0.0, Z := Hauteur}
            if (Panneau.TeleportTo[NouvellePosition, MakeRotationFromYawPitchRollDegrees(Yaw, 0.0, 0.0)]) {}

    JoueurLePlusProche(Position:vector3)<decides><transacts>:vector3 =
        var PlusProche:float = DistanceSuivi
        var Cible:?vector3 = false
        for (Joueur : GetPlayspace().GetPlayers(), Perso := Joueur.GetFortCharacter[]):
            PosJoueur := Perso.GetTransform().Translation
            Dist := Distance(PosJoueur, Position)
            if (Dist < PlusProche):
                set PlusProche = Dist
                set Cible = option{PosJoueur}
        Cible?

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
        TexteArgent.SetText(Msg("${Abreger(Argent)}"))
        TexteRevenu.SetText(Msg("${Abreger(RevenuParSeconde)}/Sec"))
        TexteRebirth.SetText(Msg("{Rebirths} Rebirths"))

    # 1400000 -> "1.4M", 76000 -> "76.0K"
    Abreger(N:int):string =
        if (N >= 1000000, A := Quotient[N, 1000000], B := Quotient[Mod[N, 1000000], 100000]):
            "{A}.{B}M"
        else if (N >= 1000, A := Quotient[N, 1000], B := Quotient[Mod[N, 1000], 100]):
            "{A}.{B}K"
        else:
            "{N}"
