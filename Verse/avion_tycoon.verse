using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
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
# L'argent n'est pas encore branché : on démarre à 0 $, donc mets Prix = 0
# sur la 1re rangée (panneau "FREE").

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

    var Proprio:?agent = false
    var Argent:int = 0
    var RevenuParSeconde:int = 0
    var Rebirths:int = 0
    var UICree:logic = false
    TexteArgent:text_block = text_block{DefaultTextColor := NamedColors.White}
    TexteRevenu:text_block = text_block{DefaultTextColor := NamedColors.White}
    TexteRebirth:text_block = text_block{DefaultTextColor := NamedColors.White}

    OnBegin<override>()<suspends>:void =
        # Tout est caché au départ, sauf le claim.
        Claim.Arrivee.Hide()
        for (R : Rangees):
            R.Plaque.Hide()
            R.Panneau.Hide()
            for (S : R.Sieges) { S.Hide() }

        # 1. Claim
        race:
            block:
                Joueur := AttendreSurPlaque(Claim.Plaque, false)
                set Proprio = option{Joueur}
            SuivreRegard(Claim.Panneau)
        Claim.Panneau.Hide()
        if (Joueur := Proprio?):
            Teleporter(Joueur)
        spawn{BoucleRetourAvion()}

        # 2. Rangées, dans l'ordre
        for (R : Rangees):
            AcheterRangee(R)

    # ---------- Téléportation ----------
    Teleporter(Joueur:agent):void =
        Destination := Claim.Arrivee.GetTransform()
        if (Perso := Joueur.GetFortCharacter[]):
            if (Perso.TeleportTo[Destination.Translation, Destination.Rotation]) {}

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
        if (not UICree?):
            set UICree = true
            CreerUI()
        MettreAJourUI()

    AttendrePaiement(R:reglages_rangee)<suspends>:void =
        loop:
            AttendreSurPlaque(R.Plaque, Proprio)
            if (Argent >= R.Prix):
                set Argent -= R.Prix
                break
            # Pas assez d'argent : on réessaie dans 1 seconde.
            Sleep(1.0)

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
        loop:
            Sleep(0.0)
            if (Cible := JoueurLePlusProche[Position]):
                YawCible := ArcTan(Cible.Y - Position.Y, Cible.X - Position.X) * 180.0 / PiFloat + Reglages.DecalageAngle
                set Yaw += AngleLePlusCourt(YawCible - Yaw) * Reglages.Lissage
            Hauteur := Sin(GetSimulationElapsedTime() * Reglages.VitesseFlottement * 2.0 * PiFloat) * Reglages.Flottement
            NouvellePosition := Position + vector3{X := 0.0, Y := 0.0, Z := Hauteur}
            if (Panneau.TeleportTo[NouvellePosition, MakeRotationFromYawPitchRollDegrees(Yaw, 0.0, 0.0)]) {}

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
