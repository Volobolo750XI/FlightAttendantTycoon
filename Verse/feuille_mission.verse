using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - la feuille de mission (une nouvelle à chaque trajet) et les papiers.
#
# LA FEUILLE : elle est accrochée au mur (Modeles/Feuille/FeuilleMur.glb + un bouton dessus).
# E dessus -> elle s'ouvre en gros plan : ce qu'il y a à faire, cases cochées, ce que ça rapporte,
# bouton CLOSE. À chaque START BOARDING, une nouvelle feuille (3 missions) :
#   AVANT LE DÉCOLLAGE
#     - fermer tous les coffres à bagages (une fois tout le monde assis ; ratée si pas faite au TAKE OFF)
#     - contrôler les papiers de N passagers (possible jusqu'à l'atterrissage)
#   EN VOL
#     - servir N passagers (leurs commandes, device demandes)
#
# SERVIR : une flèche flotte au-dessus d'un passager qui commande. On amène le chariot à côté
# (chargé au galley), on le vise : "[E] TAKE ORDER". La touche -> on est figé face à lui, sa
# commande s'affiche dans une bulle sur l'écran (l'icône du produit), et en dessous ce qu'il y a
# sur le chariot : on clique le bon produit. Bon = servi et payé ; mauvais = "Wrong order!".
#
# LES PAPIERS : quand on vise un passager, "[F] CHECK PASSPORT & TICKET" s'affiche. La touche
# ouvre ses papiers en gros : son vrai visage à gauche, son billet au milieu, son passeport à
# droite, et en haut la date du jour + le vol en cours. Il faut vérifier que tout correspond, puis
# cliquer VALID ou REFUSE (tampon). À la porte pendant l'embarquement, les passagers s'arrêtent
# devant toi (poste de contrôle, device passagers) ; refusé, il repart par la passerelle.
# La plupart des papiers sont bons. Un "cerveau" (Fabriquer) glisse parfois UNE erreur
# (ChanceBilletFaux, rare), de plus en plus subtile avec les destinations et selon ta forme.
#   REFUSE sur des faux  = fraudeur attrapé, tu gagnes de l'argent.
#   VALID sur des vrais  = c'est bon (compte pour la mission).
#   REFUSE sur des vrais = plainte (le passager s'en va si c'est à la porte).
#   VALID sur des faux   = il voyage gratis (le cerveau s'en souvient : cette erreur reviendra).
#
# ARGENT : tout dépend de la VALEUR DU VOL (pc_destinations.ValeurVol : environ la moitié du prix
# de la destination suivante). Au début ça rapporte un peu, avec les grosses destinations beaucoup.
#   mission = PartMission x valeur, fraudeur = PartFraudeur x valeur, feuille parfaite =
#   PartParfait x valeur ; passagers (device passagers) = PartParPassager x valeur par passager assis, gagné seconde par seconde en vol.
#
# Dans le Tiroir à contenu, dossier "FeuilleMission" : importe tout Textures/FeuilleMission
# (FondFeuille, Billet, Passeport, Case, CaseCochee, CaseRatee, TamponOk, TamponRefus, Photo1 ... Photo5).
# Dans le device passagers, règle "Photo" de chaque modèle.

# Les papiers d'un passager : son billet + son passeport (fabriqués la première fois qu'on les
# regarde, par Fabriquer dans feuille_mission).
billet_passager := class<unique>:
    Passager:passager
    # le billet
    NomBillet:string
    Vers:string
    Vol:string
    DateBillet:string
    Siege:string
    Seq:string
    # le passeport
    Nom:string
    Prenom:string
    Pays:string
    Sexe:string
    Naissance:string
    Numero:string
    Expiration:string
    Photo:int
    Mrz1:string
    Mrz2:string
    # 0 = papiers en règle, sinon l'erreur glissée dedans (voir Fabriquer)
    Probleme:int
    # 0 pas encore décidé, 1 VALID, 2 REFUSE
    var Decision:int = 0

# Une ligne de la feuille.
tache_feuille := class<unique>:
    # 0 fermer les coffres, 1 contrôler les papiers, 2 servir les passagers
    Genre:int
    var Fait:logic = false
    var Rate:logic = false
    var Compte:int = 0
    var Objectif:int = 1
    # servir : nombre de passagers déjà servis (compteur du device demandes) au début du trajet
    var Depart:int = 0

clic_feuille := class:
    Feuille:feuille_mission
    Action:int
    Clique(Clic:widget_message):void = Feuille.Agir(Action)

feuille_mission := class(creative_device):
    @editable Passagers:passagers = passagers{}
    @editable DeviceAvion:avion_tycoon = avion_tycoon{}
    @editable DevicePC:?pc_destinations = false
    # Le device des commandes des passagers (mission "servir").
    @editable Demandes:?demandes_device = false
    # Le galley (service_device) : le chariot et ce qu'il y a dessus (pour servir).
    @editable Service:?service_device = false
    # Un Appareil Bouton posé sur la feuille accrochée au mur (texte "Read").
    @editable BoutonFeuille:button_device = button_device{}
    # Un Déclencheur d'entrée : la touche pour regarder les papiers du passager visé,
    # et le nom de cette touche (affiché à l'écran quand on vise un passager).
    @editable InputBillet:input_trigger_device = input_trigger_device{}
    @editable NomTouche:string = "F"
    @editable MessageHUD:?hud_message_device = false
    @editable SonMission:?audio_player_device = false
    @editable SonErreur:?audio_player_device = false
    @editable SonTampon:?audio_player_device = false

    # Chance (%) que des papiers soient faux. Peu : la plupart des passagers sont en règle.
    # +2 par niveau du cerveau (grosses destinations).
    @editable ChanceBilletFaux:int = 8
    # Nombre de passagers à contrôler / à servir (au hasard entre les deux)
    @editable BilletsMin:int = 3
    @editable BilletsMax:int = 6
    @editable ServisMin:int = 2
    @editable ServisMax:int = 5
    # Viser un passager : précision (cm) et portée (cm)
    @editable RayonVisee:float = 70.0
    @editable PorteeVisee:float = 450.0
    # ===== Gains (part de la valeur du vol) =====
    @editable PartMission:float = 0.1
    @editable PartFraudeur:float = 0.12
    @editable PartParfait:float = 0.1
    # Valeur du vol s'il n'y a pas de DevicePC
    @editable ValeurSansPC:float = 100.0

    PhotosPassagers:[]texture = array{FeuilleMission.Photo1, FeuilleMission.Photo2, FeuilleMission.Photo3, FeuilleMission.Photo4, FeuilleMission.Photo5}
    # Noms des billets : un prénom au hasard + un nom de famille, soit pris dans la liste, soit
    # inventé (un début + une fin de nom : des centaines de noms différents à chaque vol).
    PrenomsH:[]string = array{"JAMES", "LUCAS", "OMAR", "HUGO", "ARTHUR", "DAVID", "MARCO", "LEO", "SAMUEL", "VICTOR", "NOAH", "ETHAN", "KARIM", "IVAN", "MATEO", "YUKI", "LIAM", "FELIX", "PABLO", "ANDRE", "THEO", "ADAM", "RAFAEL", "MILO", "OSCAR", "JONAS", "AMIR", "LORENZO", "ERIK", "BRUNO", "KENJI", "DIEGO", "SACHA", "MALIK", "TOM", "NICO", "HENRI", "PIOTR", "AXEL", "JULES"}
    PrenomsF:[]string = array{"EMMA", "SOFIA", "CLARA", "MARIA", "LINA", "JULIA", "ROSE", "NORA", "ALICE", "MAYA", "CHLOE", "INES", "LEA", "ZOE", "AMIRA", "HANA", "ELENA", "MIA", "LUNA", "OLIVIA", "SARA", "YASMINE", "ANNA", "LUCIE", "CAMILA", "AIKO", "NADIA", "EVA", "LOLA", "IRIS", "PAULA", "MARGOT", "ELSA", "LAYLA", "AGATHE", "VERA", "NINA", "JADE", "SELMA", "OLGA"}
    NomsFamille:[]string = array{"SMITH", "MARTIN", "GARCIA", "ROSSI", "MULLER", "DUBOIS", "SILVA", "NOVAK", "TANAKA", "JOHNSON", "LOPEZ", "PETIT", "NGUYEN", "KOWALSKI", "FERREIRA", "SCHMIDT", "MORENO", "BROWN", "LAURENT", "YILMAZ", "IVANOV", "KIM", "OKAFOR", "HANSEN", "BIANCHI", "MENDES", "WILSON", "SATO", "KHAN", "DIALLO", "FISCHER", "ROUX", "COSTA", "PATEL", "LEROY", "JANSEN", "ORTEGA", "WEBER", "HAMDI", "CHEN"}
    DebutsNom:[]string = array{"BER", "KAL", "MOR", "SAN", "VAL", "DOR", "LAR", "MAL", "TOR", "RIV", "GAR", "SOL", "FER", "LIND", "HAR", "BEL", "CAS", "NOV", "OST", "WIL", "MAR", "ROS", "BRAN", "KOV", "DEL", "AND", "PET", "STRO", "VAN", "MON"}
    FinsNom:[]string = array{"SSON", "OVA", "ELLI", "ANDEZ", "BERG", "OWSKI", "MANN", "IER", "AKIS", "ENKO", "AUD", "ESCU", "SEN", "OTTI", "ARD", "EIRA", "OGLU", "IC", "STEIN", "WOOD", "INI", "OS", "ANT", "EAU", "OV", "HOLM", "AZ", "ETTE", "UCCI", "ER"}
    AutresVilles:[]string = array{"PARIS", "LONDON", "TOKYO", "ROME", "DUBAI", "MIAMI", "OSLO", "LIMA", "SEOUL", "CAIRO", "SYDNEY", "MADRID"}
    Lettres:[]string = array{"A", "B", "C", "D", "E", "F", "G", "H", "J", "K"}
    PaysNoms:[]string = array{"FRANCE", "GERMANY", "ITALY", "SPAIN", "JAPAN", "BRAZIL", "CANADA", "EGYPT", "INDIA", "MEXICO", "NIGERIA", "POLAND", "TURKEY", "KOREA", "SWEDEN", "USA", "MOROCCO", "PORTUGAL"}
    PaysCodes:[]string = array{"FRA", "DEU", "ITA", "ESP", "JPN", "BRA", "CAN", "EGY", "IND", "MEX", "NGA", "POL", "TUR", "KOR", "SWE", "USA", "MAR", "PRT"}
    MoisNoms:[]string = array{"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"}
    Raisons:[]string = array{"", "WRONG DESTINATION", "WRONG FLIGHT", "NOT THE SAME FACE", "WRONG DATE ON TICKET", "PASSPORT EXPIRED", "NAMES DON'T MATCH", "WRONG SEX ON PASSPORT", "PASSPORT No. DOESN'T MATCH", "NAME MISSPELLED"}
    # Les papiers à l'écran : le dessin du billet (1800 x 720) en 1116 x 446, celui du passeport
    # (1260 x 1000) en 756 x 600 (assez grand pour la taille du texte de Fortnite). Les images sont en puissance de 2 avec du vide autour : on les
    # affiche donc plus grandes et décalées pour que le dessin tombe ici.
    # Les positions des valeurs sont celles de Outils/feuille_mission.py.
    BilletX:float = 20.0
    BilletY:float = 165.0
    BilletK:float = 0.62
    PassX:float = 1144.0
    PassY:float = 165.0
    PassK:float = 0.6

    TextesTaches:[]string = array{"Close the overhead bins", "", ""}

    var Taches:[]tache_feuille = array{}
    var Billets:[]billet_passager = array{}
    var EnCours:logic = false
    var Bilan:logic = false
    var DebutTrajet:float = 0.0
    var NumeroVol:string = ""
    var Porte:string = ""
    var Embarquement:string = ""
    var GainsMissions:int = 0
    var FraudeursRates:int = 0
    var Plaintes:int = 0
    var Rangs:[]int = array{}
    # La date du jour (un trajet = un jour)
    var AujAn:int = 2026
    var AujMois:int = 3
    var AujJour:int = 2
    # Le cerveau : la forme du joueur et, pour chaque erreur (1..9), combien il en a attrapé / raté
    var Forme:int = 0
    var Attrapes:[]int = array{0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
    var Rates:[]int = array{0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
    # Le message quand on vise un passager, et le point au milieu de l'écran
    var Invite:?canvas = false
    PointDiscret:color_block = color_block{DefaultColor := NamedColors.White, DefaultOpacity := 0.45}
    PointActif:color_block = color_block{DefaultColor := NamedColors.White, DefaultOpacity := 1.0}
    TexteInvite:text_block = text_block{DefaultTextColor := NamedColors.White, DefaultJustification := text_justification.Center, DefaultShadowColor := NamedColors.Black, DefaultShadowOpacity := 0.9, DefaultShadowOffset := option{vector2{X := 2.0, Y := 2.0}}}

    # L'écran ouvert : 0 rien, 1 la feuille, 2 des papiers
    var Page:int = 0
    var Joueur:?player = false
    var Base:?canvas = false
    var Dynamiques:[]widget = array{}
    var BilletOuvert:?billet_passager = false
    # L'écran de service (page 3) : la commande, le chariot utilisé, et si le joueur est figé.
    var CommandeOuverte:?demande = false
    var ChariotOuvert:int = -1
    var Fige:logic = false
    var MessageService:string = ""

    OnBegin<override>()<suspends>:void =
        BoutonFeuille.InteractedWithEvent.Subscribe(OnFeuille)
        InputBillet.PressedEvent.Subscribe(OnBillet)
        spawn{BoucleInvite()}
        var Avant:int = Passagers.EtatBouton
        loop:
            Sleep(0.2)
            Etat := Passagers.EtatBouton
            if (Etat <> Avant):
                # 3 -> 0 : atterrissage (et si l'embarquement est déjà relancé, nouvelle feuille aussi)
                if (Avant = 3):
                    Atterrissage()
                if (Etat = 1, Avant = 0 or Avant = 3):
                    NouvelleFeuille()
                else if (Etat = 3):
                    Decollage()
                set Avant = Etat
            if (EnCours?):
                Verifier()

    # ---------- une nouvelle feuille (START BOARDING) ----------
    NouvelleFeuille():void =
        AvancerJour()
        set NumeroVol = NumeroAuHasard()
        LettrePorte := Choisir(Lettres)
        set Porte = "{LettrePorte}{GetRandomInt(1, 24)}"
        Heure := GetRandomInt(6, 22)
        Minutes := GetRandomInt(0, 11) * 5
        set Embarquement = if (Minutes < 10) then "{Heure}:0{Minutes}" else "{Heure}:{Minutes}"
        set Billets = array{}
        set GainsMissions = 0
        set FraudeursRates = 0
        set Plaintes = 0
        set Bilan = false
        set DebutTrajet = GetSimulationElapsedTime()
        set Rangs = for (P : Passagers.Places) { RangDe(P) }
        var Liste:[]tache_feuille = array{}
        if (Passagers.PortesCoffres.Length > 0):
            set Liste += array{tache_feuille{Genre := 0}}
        Papiers := tache_feuille{Genre := 1}
        set Papiers.Objectif = GetRandomInt(Max(1, BilletsMin), Max(BilletsMin, BilletsMax))
        set Liste += array{Papiers}
        if (D := Demandes?):
            Servir := tache_feuille{Genre := 2}
            set Servir.Objectif = GetRandomInt(Max(1, ServisMin), Max(ServisMin, ServisMax))
            set Servir.Depart = D.NbServis
            set Liste += array{Servir}
        set Taches = Liste
        set EnCours = true
        Message("New flight briefing on the wall!")
        Rafraichir()

    # Le rang de chaque place (le siège le plus proche dans les rangées du device avion).
    RangDe(Place:place_passager):int =
        Pos := Place.Siege.GetTransform().Translation
        var Meilleur:float = 1000000.0
        var Rang:int = 0
        for (K -> R : DeviceAvion.Rangees, S : R.Sieges):
            D := Distance(S.GetTransform().Translation, Pos)
            if (D < Meilleur):
                set Meilleur = D
                set Rang = K
        Rang

    # "3C" : le numéro du rang + une lettre (dans l'ordre des places de ce rang).
    SiegeDe(P:passager):string =
        if (Rang := Rangs[P.NumeroPlace]):
            var N:int = 0
            for (J := 0..P.NumeroPlace - 1, R := Rangs[J], R = Rang) { set N += 1 }
            Lettre := if (L := Lettres[N]) then L else "K"
            "{Rang + 1}{Lettre}"
        else:
            "--"

    # ---------- décollage / atterrissage ----------
    Decollage():void =
        # les coffres, c'était avant le décollage
        for (T : Taches, not T.Fait?, T.Genre = 0):
            set T.Rate = true
        Rafraichir()

    Atterrissage():void =
        if (EnCours?):
            set EnCours = false
            for (T : Taches, not T.Fait?):
                set T.Rate = true
            Reussies := for (T : Taches, T.Fait?) { T }
            if (Taches.Length > 0, Reussies.Length = Taches.Length):
                Payer(Gain(PartParfait), "PERFECT FLIGHT!")
            Passes := for (B : Billets, B.Probleme > 0, B.Decision <> 2) { B }
            set FraudeursRates = Passes.Length
            set Bilan = true
            Message("Flight complete! Check your briefing sheet.")
            Rafraichir()

    # ---------- vérifications (toutes les 0.2 s) ----------
    Verifier():void =
        Etat := Passagers.EtatBouton
        var Change:logic = false
        for (T : Taches, not T.Fait?, not T.Rate?):
            if (T.Genre = 0):
                Ouverts := for (O : Passagers.CoffresOuverts, O?) { O }
                if (Etat >= 2, Ouverts.Length = 0):
                    Reussir(T, "BINS CLOSED")
                    set Change = true
            else if (T.Genre = 1):
                if (T.Compte >= T.Objectif):
                    Reussir(T, "PAPERS CHECKED")
                    set Change = true
            else if (T.Genre = 2):
                N := if (D := Demandes?) then D.NbServis - T.Depart else 0
                if (N <> T.Compte):
                    set T.Compte = N
                    set Change = true
                if (N >= T.Objectif):
                    Reussir(T, "PASSENGERS SERVED")
                    set Change = true
        if (Change?) { Rafraichir() }

    # ---------- les papiers (passeport + billet) ----------
    # Viser un passager + la touche -> ses papiers en gros. Marche à la porte (le passager attend
    # devant le poste de contrôle) comme une fois assis.
    # La touche : selon le passager visé, ses papiers (pas encore assis, pas encore contrôlé) ou
    # sa commande (il a une flèche au-dessus de la tête, et le chariot est à côté).
    OnBillet(Agent:agent):void =
        Vise := PassagerVise(Agent)
        if (Page = 0, EstProprio[Agent], P := Vise?, J := player[Agent]):
            if (AControler[P]):
                B := BilletDe(P)
                Ouvrir(J, 2)
                set BilletOuvert = option{B}
                Afficher()
            else if (Dem := Demandes?, D := Dem.DemandeDe(P)?):
                Chariot := ChariotPour(Agent)
                if (I := Chariot?):
                    OuvrirService(J, D, I)
                else:
                    Erreur("Bring the trolley to serve this passenger!")

    # Les papiers ne se contrôlent qu'avant d'être assis, et une seule fois.
    AControler(P:passager)<transacts><decides>:void =
        P.Etat <> 2
        P.Controle = 0

    ChariotPour(Agent:agent):?int =
        if (S := Service?) then S.ChariotDe(Agent) else false

    # ---------- l'écran de service ----------
    # Le joueur est figé face au passager, sa commande s'affiche dans une bulle.
    OuvrirService(J:player, D:demande, I:int):void =
        Ouvrir(J, 3)
        set CommandeOuverte = option{D}
        set ChariotOuvert = I
        set MessageService = ""
        if (FC := J.GetFortCharacter[], C := D.Passager.Corps?):
            Pos := FC.GetTransform().Translation
            Vers := C.GetTransform().Translation - Pos
            Lacet := RadiansToDegrees(ArcTan(Vers.Y, Vers.X))
            if (FC.TeleportTo[Pos, MakeRotationFromYawPitchRollDegrees(Lacet, 0.0, 0.0)]) {}
            FC.PutInStasis(stasis_args{AllowTurning := false, AllowFalling := false, AllowEmotes := false})
            set Fige = true
        Afficher()

    # Clic sur un produit du chariot.
    ServirProduit(Article:int):void =
        if (D := CommandeOuverte?, Dem := Demandes?, S := Service?):
            if (Article = D.Choix):
                Retire := S.RetirerDuChariot(ChariotOuvert, Article)
                if (Retire?):
                    Dem.Payer(D)
                    Fermer()
            else:
                Dem.MauvaisProduit()
                set MessageService = "Wrong order! Look at the bubble."
                Afficher()

    ABillet(P:passager)<transacts><decides>:void =
        var Oui:logic = false
        for (B : Billets, B.Passager = P) { set Oui = true }
        Oui?

    DejaControle(P:passager)<transacts><decides>:void =
        var Oui:logic = false
        for (B : Billets, B.Passager = P, B.Decision > 0) { set Oui = true }
        Oui?

    BilletDe(P:passager):billet_passager =
        for (B : Billets, B.Passager = P):
            return B
        # plus on avance dans le jeu, plus il y a de faux papiers
        Chances := ChanceBilletFaux + (NiveauActuel() - 1) * 2
        Fabriquer(P, if (Chance[Chances]) then true else false)

    # ----- le cerveau des faux papiers -----
    # Il fabrique des papiers cohérents (billet pour CE vol, CE jour, même nom que le passeport),
    # puis, si ce sont des faux, il glisse UNE erreur dedans. Il n'y a que 3 choses à vérifier :
    #   1 la destination du billet (TO)   2 le numéro de vol du billet   6/9 le nom (billet = passeport)
    #   6 = prénom différent (facile) ; 9 = nom de famille avec une lettre en moins (plus subtil, il
    #   arrive avec les grosses destinations ou quand le joueur réussit tout).
    # Il choisit surtout les erreurs que le joueur a déjà laissé passer.
    Fabriquer(P:passager, Faux:logic):billet_passager =
        Vraie := PhotoPassager(P)
        SexeVrai := if (Vraie = 1 or Vraie = 4) then "M" else if (Vraie >= 2 and Vraie <= 5) then "F" else if (GetRandomInt(0, 1) = 0) then "M" else "F"
        Homme := if (SexeVrai = "M") then true else false
        PrenomVrai := if (Homme?) then Choisir(PrenomsH) else Choisir(PrenomsF)
        Titre := if (Homme?) then "MR" else if (GetRandomInt(0, 1) = 0) then "MS" else "MRS"
        NomVrai := NomDeFamille()
        IPays := GetRandomInt(0, PaysNoms.Length - 1)
        PaysVrai := if (S := PaysNoms[IPays]) then S else "FRANCE"
        Code := if (S := PaysCodes[IPays]) then S else "FRA"
        AnNaiss := if (Vraie = 1 or Vraie = 3) then GetRandomInt(1938, 1958) else GetRandomInt(1960, 2005)
        MoisNaiss := GetRandomInt(1, 12)
        JourNaiss := GetRandomInt(1, 28)
        L1 := Choisir(Lettres)
        L2 := Choisir(Lettres)
        Chiffres := GetRandomInt(1000000, 9999999)
        NumeroVrai := "{L1}{L2}{Chiffres}"
        # passeport valide (parfois il expire dans quelques mois : piège, il est encore bon)
        var ExpA:int = AujAn + GetRandomInt(1, 9)
        var ExpM:int = GetRandomInt(1, 12)
        if (AujMois < 12, GetRandomInt(1, 100) <= 25):
            set ExpA = AujAn
            set ExpM = GetRandomInt(AujMois + 1, 12)
        ExpJ := GetRandomInt(1, 28)
        Defaut := if (Faux?) then ChoisirProbleme() else 0
        # les valeurs, puis l'erreur éventuelle
        Arrivee := VilleArrivee()
        var VersB:string = Arrivee
        var VolB:string = NumeroVol
        var JourBillet:int = AujJour
        var PhotoB:int = Vraie
        var PrenomB:string = PrenomVrai
        var NomB:string = NomVrai
        var SexePasseport:string = SexeVrai
        var NumeroBande:string = NumeroVrai
        if (Defaut = 1):
            for (Essai := 1..10, VersB = Arrivee) { set VersB = Choisir(AutresVilles) }
        else if (Defaut = 2):
            for (Essai := 1..10, VolB = NumeroVol) { set VolB = NumeroAuHasard() }
        else if (Defaut = 6):
            Liste := if (Homme?) then PrenomsH else PrenomsF
            for (Essai := 1..10, PrenomB = PrenomVrai) { set PrenomB = Choisir(Liste) }
        else if (Defaut = 9):
            set NomB = SansUneLettre(NomVrai)
        NaissMrz := DateMrz(JourNaiss, MoisNaiss, AnNaiss)
        Expire := DateMrz(ExpJ, ExpM, ExpA)
        SeqN := GetRandomInt(1, 189)
        B := billet_passager:
            Passager := P
            NomBillet := "{NomB}/{PrenomB} {Titre}"
            Vers := VersB
            Vol := VolB
            DateBillet := DateCourte(JourBillet, AujMois)
            Siege := SiegeDe(P)
            Seq := "{SeqN}"
            Nom := NomVrai
            Prenom := PrenomVrai
            Pays := PaysVrai
            Sexe := SexePasseport
            Naissance := DateTexte(JourNaiss, MoisNaiss, AnNaiss)
            Numero := NumeroVrai
            Expiration := DateTexte(ExpJ, ExpM, ExpA)
            Photo := PhotoB
            Mrz1 := Remplir("P<{Code}{NomVrai}<<{PrenomVrai}", 30)
            Mrz2 := Remplir("{NumeroBande}<{Code}{NaissMrz}{SexePasseport}{Expire}", 30)
            Probleme := Defaut
        if (Defaut > 0) { set P.Fraudeur = true }
        set Billets += array{B}
        B

    # Le niveau des erreurs : 1 facile, 2 moyen, 3 difficile.
    NiveauActuel():int =
        var NiveauBase:int = 1
        if (Ordi := DevicePC?):
            # niveau de la ligne (1..8) : 6+ = erreurs difficiles, 3+ = moyennes
            if (Ordi.Niveau() >= 6):
                set NiveauBase = 3
            else if (Ordi.Niveau() >= 3):
                set NiveauBase = 2
        Bonus := if (Forme >= 6) then 1 else if (Forme <= -3) then -1 else 0
        Max(1, Min(3, NiveauBase + Bonus))

    NiveauDe(Code:int)<transacts>:int =
        if (Code = 9) then 2 else 1

    ChoisirProbleme():int =
        N := NiveauActuel()
        var Codes:[]int = array{}
        var Poids:[]float = array{}
        for (C : array{1, 2, 6, 9}, NiveauDe(C) <= N):
            Rate := if (R := Rates[C]) then R else 0
            Vu := if (A := Attrapes[C]) then A else 0
            # ce qu'il a laissé passer revient plus souvent ; ce qu'il attrape toujours, moins
            var W:float = (1.0 + 2.0 * Rate) / (1.0 + Vu * 1.0)
            # les erreurs du niveau qu'il vient d'atteindre sont mises en avant
            if (NiveauDe(C) = N) { set W *= 1.5 }
            set Codes += array{C}
            set Poids += array{W}
        var Total:float = 0.0
        for (W : Poids) { set Total += W }
        var Tirage:float = GetRandomFloat(0.0, Total)
        var Choix:int = 1
        var Trouve:logic = false
        for (I -> W : Poids, not Trouve?):
            if (Tirage <= W, C := Codes[I]):
                set Choix = C
                set Trouve = true
            else:
                set Tirage -= W
        if (not Trouve?, C := Codes[Codes.Length - 1]) { set Choix = C }
        Choix

    # Ce que le joueur a fait avec une erreur : attrapée ou ratée (le cerveau s'en souvient).
    Noter(Code:int, Attrape:logic):void =
        if (Attrape?):
            if (A := Attrapes[Code], set Attrapes[Code] = A + 1) {}
            set Forme = Min(10, Forme + 1)
        else:
            if (R := Rates[Code], set Rates[Code] = R + 1) {}
            set Forme = Max(-6, Forme - 2)

    # Décision sur les papiers ouverts : 1 VALID, 2 REFUSE.
    Decider(Choix:int):void =
        if (B := BilletOuvert?, B.Decision = 0):
            set B.Decision = Choix
            if (S := SonTampon?) { S.Play() }
            P := B.Passager
            if (Choix = 1):
                # VALID : il entre (à la porte) ; un faux passe sans qu'on le sache
                set P.Controle = 1
                CompterBillet()
                if (B.Probleme > 0):
                    Noter(B.Probleme, false)
                else:
                    set Forme = Min(10, Forme + 1)
                Message("Documents accepted")
            else if (B.Probleme > 0):
                # REFUSE sur de faux papiers : attrapé !
                Noter(B.Probleme, true)
                set P.Fraudeur = false
                CompterBillet()
                Raison := if (R := Raisons[B.Probleme]) then R else ""
                Payer(Gain(PartFraudeur), "FAKE PAPERS: {Raison}")
                Expulser(P)
            else:
                # REFUSE sur des papiers en règle : il se plaint (et à la porte, il s'en va)
                set Plaintes += 1
                set Forme = Max(-6, Forme - 2)
                Erreur("Those documents were valid! The passenger complains.")
                if (P.Etat <> 2) { set P.Controle = 2 }
            Afficher()
            spawn{FermerBilletApres(B)}

    # Refusé : à la porte il repart par la passerelle (passagers s'en occupe) ;
    # déjà assis, il est escorté hors de l'avion (il disparaît avec son bagage).
    Expulser(P:passager):void =
        if (P.Etat = 2):
            if (Corps := P.Corps?) { Corps.Dispose() }
            if (Bagage := P.Bagage?) { Bagage.Dispose() }
            set Passagers.EnCours = for (X : Passagers.EnCours, X <> P) { X }
        else:
            set P.Controle = 2

    FermerBilletApres(B:billet_passager)<suspends>:void =
        Sleep(1.6)
        if (Page = 2, O := BilletOuvert?, O = B):
            Fermer()

    CompterBillet():void =
        for (T : Taches, T.Genre = 1, not T.Fait?, not T.Rate?):
            set T.Compte += 1

    # Le passager que le joueur vise : n'importe où sur son corps (des pieds à la tête), à portée.
    # Si plusieurs sont dans la visée (une file d'attente), c'est le PLUS PROCHE qui compte.
    PassagerVise(Agent:agent):?passager =
        var Vise:?passager = false
        if (FC := Agent.GetFortCharacter[]):
            CamPos := FC.GetViewLocation()
            Avant := FC.GetViewRotation().RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})
            var PlusProche:float = PorteeVisee
            for (P : Passagers.EnCours, P.Controle <> 2, C := P.Corps?):
                Pieds := C.GetTransform().Translation
                for (Hauteur : array{20.0, 60.0, 100.0, 140.0, 180.0, 210.0}):
                    Pos := Pieds + vector3{Z := Hauteur}
                    D := Pos - CamPos
                    T := D.X * Avant.X + D.Y * Avant.Y + D.Z * Avant.Z
                    Ecart := Distance(CamPos + Avant * T, Pos)
                    if (T > 0.0, T < PlusProche, Ecart < RayonVisee):
                        set PlusProche = T
                        set Vise = option{P}
        Vise

    # ----- le message quand on vise un passager -----
    BoucleInvite()<suspends>:void =
        loop:
            Sleep(0.1)
            if (Proprio := DeviceAvion.Proprio?, J := player[Proprio]):
                if (not Invite?) { CreerInvite(J) }
                var Vise:?passager = false
                if (Page = 0) { set Vise = PassagerVise(Proprio) }
                # ce qu'on peut faire avec le passager visé
                var Texte:string = ""
                ChariotDispo := ChariotPour(Proprio)
                if (P := Vise?):
                    if (AControler[P]):
                        set Texte = "[{NomTouche}]  CHECK PASSPORT & TICKET"
                    else if (Dem := Demandes?, Dem.DemandeDe(P)?):
                        set Texte = if (ChariotDispo?) then "[{NomTouche}]  TAKE ORDER" else "BRING THE TROLLEY"
                if (Texte <> ""):
                    TexteInvite.SetText(Msg(Texte))
                    TexteInvite.SetVisibility(widget_visibility.Visible)
                else:
                    TexteInvite.SetVisibility(widget_visibility.Collapsed)
                    set Vise = false
                # écran de service ouvert mais la commande n'existe plus (il est parti) : on ferme
                if (Page = 3, D := CommandeOuverte?, Dem := Demandes?, not Dem.DemandeDe(D.Passager)?):
                    Fermer()
                # le point au milieu : mi-transparent, tout blanc quand on vise quelque chose
                # d'utile (un passager, la feuille du mur)
                PosFeuille := BoutonFeuille.GetTransform().Translation
                Utile := if (Vise?) then true else if (VisePoint[Proprio, PosFeuille, 60.0, 400.0]) then true else false
                if (Page > 0):
                    PointDiscret.SetVisibility(widget_visibility.Collapsed)
                    PointActif.SetVisibility(widget_visibility.Collapsed)
                else if (Utile?):
                    PointDiscret.SetVisibility(widget_visibility.Collapsed)
                    PointActif.SetVisibility(widget_visibility.Visible)
                else:
                    PointDiscret.SetVisibility(widget_visibility.Visible)
                    PointActif.SetVisibility(widget_visibility.Collapsed)

    # Le joueur vise-t-il ce point (à moins de Rayon cm de sa ligne de visée, à portée) ?
    VisePoint(Agent:agent, Pos:vector3, Rayon:float, Portee:float)<transacts><decides>:void =
        FC := Agent.GetFortCharacter[]
        CamPos := FC.GetViewLocation()
        Avant := FC.GetViewRotation().RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})
        D := Pos - CamPos
        T := D.X * Avant.X + D.Y * Avant.Y + D.Z * Avant.Z
        T > 0.0
        T < Portee
        Distance(CamPos + Avant * T, Pos) < Rayon

    CreerInvite(J:player):void =
        if (UI := GetPlayerUI[J]):
            C := canvas:
                Slots := array:
                    Bloc(TexteInvite, 560.0, 640.0, 800.0, 40.0, 0)
                    Bloc(PointDiscret, 956.0, 536.0, 8.0, 8.0, 0)
                    Bloc(PointActif, 954.0, 534.0, 12.0, 12.0, 0)
            UI.AddWidget(C)
            TexteInvite.SetVisibility(widget_visibility.Collapsed)
            PointActif.SetVisibility(widget_visibility.Collapsed)
            set Invite = option{C}

    # ---------- le vol en cours, les dates, les noms ----------
    VilleDepart():string =
        if (Ordi := DevicePC?):
            Ordi.VilleDepart()
        else:
            "PARIS"

    VilleArrivee():string =
        if (Ordi := DevicePC?):
            Ordi.VilleArrivee()
        else:
            "LONDON"

    # Chaque trajet = le jour suivant.
    AvancerJour():void =
        set AujJour += 1
        if (AujJour > JoursDansMois(AujMois)):
            set AujJour = 1
            set AujMois += 1
            if (AujMois > 12):
                set AujMois = 1
                set AujAn += 1

    JoursDansMois(M:int)<transacts>:int =
        if (M = 2) then 28 else if (M = 4 or M = 6 or M = 9 or M = 11) then 30 else 31

    Aujourdhui():string = DateTexte(AujJour, AujMois, AujAn)

    Deux(N:int):string = if (N < 10) then "0{N}" else "{N}"

    # "05 APR 2027"
    DateTexte(J:int, M:int, A:int):string =
        NomMois := if (S := MoisNoms[M - 1]) then S else "JAN"
        "{Deux(J)} {NomMois} {A}"

    # "05 APR" (date courte, comme sur les vrais billets)
    DateCourte(J:int, M:int):string =
        NomMois := if (S := MoisNoms[M - 1]) then S else "JAN"
        "{Deux(J)} {NomMois}"

    # "270405" (AAMMJJ, comme sur la bande du bas des passeports)
    DateMrz(J:int, M:int, A:int):string =
        AA := if (R := Mod[A, 100]) then R else 0
        "{Deux(AA)}{Deux(M)}{Deux(J)}"

    Remplir(S:string, N:int):string =
        var R:string = S
        loop:
            if (R.Length >= N) { break }
            set R += "<"
        R

    # Le même nom avec une lettre en moins (faute discrète).
    SansUneLettre(S:string):string =
        if (S.Length <= 3):
            S
        else:
            K := GetRandomInt(1, S.Length - 2)
            for (I -> C : S, I <> K) { C }

    # Un nom de famille : de la liste, ou inventé (début + fin).
    NomDeFamille():string =
        if (GetRandomInt(1, 100) <= 40):
            Debut := Choisir(DebutsNom)
            Fin := Choisir(FinsNom)
            "{Debut}{Fin}"
        else:
            Choisir(NomsFamille)

    NumeroAuHasard():string =
        N := GetRandomInt(100, 999)
        "FT{N}"

    Choisir(Liste:[]string):string =
        if (S := Liste[GetRandomInt(0, Liste.Length - 1)]) then S else ""

    # ---------- argent ----------
    # Valeur du vol : ce que rapporte un trajet (dépend de la destination, voir pc_destinations).
    ValeurDuVol():float = if (Ordi := DevicePC?) then Ordi.ValeurVol() else ValeurSansPC

    Gain(Part:float):int =
        V := ValeurDuVol()
        if (G := Round[V * Part]) then Max(1, G) else 1

    GainTache(T:tache_feuille):int = Gain(PartMission)

    Reussir(T:tache_feuille, Texte:string):void =
        set T.Fait = true
        Payer(Gain(PartMission), Texte)

    Payer(Montant:int, Texte:string):void =
        set GainsMissions += Montant
        set DeviceAvion.Argent += Montant
        DeviceAvion.MettreAJourUI()
        if (S := SonMission?) { S.Play() }
        Message("{Texte}  +${DeviceAvion.Abreger(Montant)}")
        if (Page = 1) { Afficher() }

    Message(Texte:string):void =
        if (M := MessageHUD?, Proprio := DeviceAvion.Proprio?):
            M.SetText(Msg(Texte))
            M.Show(Proprio)

    Erreur(Texte:string):void =
        if (S := SonErreur?) { S.Play() }
        Message(Texte)

    # ---------- outils ----------
    Chance(Pourcent:int)<transacts><decides>:void =
        GetRandomInt(1, 100) <= Pourcent

    EstProprio(Agent:agent)<transacts><decides>:void =
        Proprio := DeviceAvion.Proprio?
        Proprio = Agent

    PhotoDe(N:int)<transacts><decides>:texture = PhotosPassagers[N - 1]

    # La photo d'un passager : celle réglée sur son modèle, sinon automatique (n° du modèle).
    PhotoPassager(P:passager)<transacts>:int =
        if (P.Modele.Photo > 0) then P.Modele.Photo
        else if (N := Mod[P.IndexModele, PhotosPassagers.Length]) then N + 1
        else 1

    # ---------- écrans ----------
    OnFeuille(Agent:agent):void =
        if (EstProprio[Agent], J := player[Agent]):
            Ouvrir(J, 1)

    Ouvrir(J:player, NouvellePage:int):void =
        Fermer()
        set Joueur = option{J}
        set Page = NouvellePage
        Afficher()

    Fermer():void =
        if (J := Joueur?, UI := GetPlayerUI[J], C := Base?):
            UI.RemoveWidget(C)
        set Base = false
        set Dynamiques = array{}
        set Page = 0
        set BilletOuvert = false
        set CommandeOuverte = false
        if (Fige?, J := Joueur?, FC := J.GetFortCharacter[]):
            FC.ReleaseFromStasis()
        set Fige = false

    # 1 VALID, 2 REFUSE, 3 fermer le billet, 10 fermer la feuille, 100 + produit : servir
    Agir(Action:int):void =
        if (Action = 1 or Action = 2):
            Decider(Action)
        else if (Action >= 100):
            ServirProduit(Action - 100)
        else:
            Fermer()

    Rafraichir():void =
        if (Page = 1) { Afficher() }

    # L'écran ouvert (on remplace seulement ce qui change : pas de saut de souris).
    Afficher():void =
        if (J := Joueur?, UI := GetPlayerUI[J], Page > 0):
            var Toile:canvas = canvas{}
            if (C := Base?):
                set Toile = C
            else:
                Nouveau := canvas{}
                UI.AddWidget(Nouveau, player_ui_slot{InputMode := ui_input_mode.All})
                set Base = option{Nouveau}
                set Toile = Nouveau
            for (W : Dynamiques) { Toile.RemoveWidget(W) }
            Slots := if (Page = 1) then PageFeuille() else if (Page = 3) then PageService() else if (B := BilletOuvert?) then PageBillet(B) else array{}
            for (S : Slots) { Toile.AddWidget(S) }
            set Dynamiques = for (S : Slots) { S.Widget }

    # Tout est placé comme sur un écran 1920 x 1080 (X, Y = coin haut gauche).
    Bloc(W:widget, X:float, Y:float, L:float, H:float, Couche:type{_X:int where 0 <= _X, _X <= 2147483647}):canvas_slot =
        canvas_slot:
            Anchors := anchors{Minimum := vector2{X := 0.5, Y := 0.5}, Maximum := vector2{X := 0.5, Y := 0.5}}
            Alignment := vector2{X := 0.0, Y := 0.0}
            Offsets := margin{Left := X - 960.0, Top := Y - 540.0, Right := L, Bottom := H}
            SizeToContent := false
            ZOrder := Couche
            Widget := W

    Ecrit(S:string, Hex:string, J:text_justification):text_block =
        text_block{DefaultText := Msg(S), DefaultTextColor := MakeColorFromHex(Hex), DefaultJustification := J}

    Vignette(T:texture, L:float, H:float):texture_block =
        texture_block{DefaultImage := T, DefaultDesiredSize := vector2{X := L, Y := H}}

    BoutonEcran(S:string, Hex:string, X:float, Y:float, L:float, H:float, Action:int):[]canvas_slot =
        B := button_quiet{DefaultText := Msg(S)}
        B.OnClick().Subscribe(clic_feuille{Feuille := Self, Action := Action}.Clique)
        array{Bloc(color_block{DefaultColor := MakeColorFromHex(Hex), DefaultOpacity := 1.0}, X, Y, L, H, 4), Bloc(B, X, Y, L, H, 5)}

    Prix(N:int):string = "${DeviceAvion.Abreger(N)}"

    # ---------- la feuille en gros plan ----------
    PageFeuille():[]canvas_slot =
        var S:[]canvas_slot = array{}
        set S += array{Bloc(color_block{DefaultColor := NamedColors.Black, DefaultOpacity := 0.45}, 0.0, 0.0, 1920.0, 1080.0, 0)}
        set S += array{Bloc(Vignette(FeuilleMission.FondFeuille, 1024.0, 1024.0), 448.0, 28.0, 1024.0, 1024.0, 1)}
        set S += BoutonEcran("CLOSE", "374151", 1150.0, 935.0, 160.0, 46.0, 10)
        if (Taches.Length = 0):
            set S += array{Bloc(Ecrit("No flight yet: press START BOARDING.", "334155", text_justification.Center), 600.0, 400.0, 720.0, 40.0, 3)}
            return S
        Visibles := Taches
        Faites := for (T : Visibles, T.Fait?) { T }
        set S += array{Bloc(Ecrit("FLIGHT {NumeroVol}", "1E293B", text_justification.Left), 640.0, 248.0, 400.0, 40.0, 3)}
        set S += array{Bloc(Ecrit("{Faites.Length}/{Visibles.Length}", "244A8C", text_justification.Right), 1160.0, 248.0, 140.0, 40.0, 3)}
        set S += array{Bloc(Ecrit("{VilleDepart()} > {VilleArrivee()}", "1E293B", text_justification.Left), 640.0, 290.0, 660.0, 40.0, 3)}
        var Y:float = 350.0
        for (Section := 0..1):
            Liste := for (T : Visibles, DansSection[T, Section]) { T }
            if (Liste.Length > 0):
                Titre := if (Section = 0) then "BEFORE TAKE OFF" else "IN FLIGHT"
                set S += array{Bloc(Ecrit(Titre, "244A8C", text_justification.Left), 640.0, Y, 400.0, 40.0, 3)}
                set Y += 46.0
                for (T : Liste):
                    Coche := if (T.Fait?) then FeuilleMission.CaseCochee else if (T.Rate?) then FeuilleMission.CaseRatee else FeuilleMission.Case
                    Couleur := if (T.Rate?) then "9CA3AF" else "111827"
                    CouleurPrix := if (T.Rate?) then "9CA3AF" else "16A34A"
                    set S += array{Bloc(Vignette(Coche, 38.0, 38.0), 640.0, Y, 38.0, 38.0, 3)}
                    set S += array{Bloc(Ecrit(TexteTache(T), Couleur, text_justification.Left), 692.0, Y, 470.0, 40.0, 3)}
                    set S += array{Bloc(Ecrit("+{Prix(GainTache(T))}", CouleurPrix, text_justification.Right), 1160.0, Y, 140.0, 40.0, 3)}
                    set Y += 58.0
                set Y += 16.0
        if (Bilan?):
            set S += PageBilan()
        S

    DansSection(T:tache_feuille, Section:int)<transacts><decides>:void =
        # coffres et papiers : avant le décollage ; servir : en vol
        Avant := if (T.Genre <= 1) then 0 else 1
        Avant = Section

    PageBilan():[]canvas_slot =
        GainBillets := Passagers.DernierGainBillets
        Total := GainBillets + GainsMissions
        var S:[]canvas_slot = array{}
        set S += array{Bloc(Ecrit("FLIGHT COMPLETE", "244A8C", text_justification.Left), 640.0, 700.0, 400.0, 40.0, 3)}
        set S += array{Bloc(Ecrit("Passengers x{Passagers.DerniersPayants}", "1E293B", text_justification.Left), 640.0, 744.0, 480.0, 40.0, 3)}
        set S += array{Bloc(Ecrit("+{Prix(GainBillets)}", "16A34A", text_justification.Right), 1120.0, 744.0, 180.0, 40.0, 3)}
        set S += array{Bloc(Ecrit("Missions", "1E293B", text_justification.Left), 640.0, 786.0, 480.0, 40.0, 3)}
        set S += array{Bloc(Ecrit("+{Prix(GainsMissions)}", "16A34A", text_justification.Right), 1120.0, 786.0, 180.0, 40.0, 3)}
        set S += array{Bloc(Ecrit("TOTAL", "111827", text_justification.Left), 640.0, 830.0, 480.0, 40.0, 3)}
        set S += array{Bloc(Ecrit("+{Prix(Total)}", "15803D", text_justification.Right), 1120.0, 830.0, 180.0, 40.0, 3)}
        if (FraudeursRates > 0 or Plaintes > 0):
            set S += array{Bloc(Ecrit("Missed: {FraudeursRates}   Complaints: {Plaintes}", "B91C1C", text_justification.Left), 640.0, 878.0, 500.0, 40.0, 3)}
        S

    TexteTache(T:tache_feuille):string =
        if (T.Genre = 1) then "Check papers {Min(T.Compte, T.Objectif)}/{T.Objectif}" else if (T.Genre = 2) then "Serve passengers {Min(T.Compte, T.Objectif)}/{T.Objectif}" else if (Texte := TextesTaches[T.Genre]) then Texte else "?"

    # ---------- l'écran de service ----------
    # En haut à droite : la bulle du passager avec l'icône de ce qu'il veut. En bas : ce qu'il y a
    # sur le chariot, une carte par produit (icône + nombre) ; on clique celle qu'il demande.
    PageService():[]canvas_slot =
        var S:[]canvas_slot = array{}
        if (D := CommandeOuverte?, Dem := Demandes?, M := Dem.Menu?, Prod := M.ListeProduits[D.Choix]):
            # la bulle : bord sombre, fond blanc, petite queue en escalier vers le passager
            set S += array{Bloc(Rect("1E293B"), 1046.0, 96.0, 468.0, 348.0, 1)}
            set S += array{Bloc(Rect("FFFFFF"), 1052.0, 102.0, 456.0, 336.0, 2)}
            set S += array{Bloc(Rect("1E293B"), 1086.0, 438.0, 72.0, 40.0, 1)}
            set S += array{Bloc(Rect("FFFFFF"), 1092.0, 432.0, 60.0, 40.0, 2)}
            set S += array{Bloc(Rect("1E293B"), 1062.0, 472.0, 50.0, 34.0, 1)}
            set S += array{Bloc(Rect("FFFFFF"), 1068.0, 466.0, 38.0, 34.0, 2)}
            set S += array{Bloc(Ecrit("I'D LIKE...", "64748B", text_justification.Center), 1052.0, 112.0, 456.0, 40.0, 3)}
            set S += array{Bloc(Vignette(Prod.Image, 210.0, 210.0), 1175.0, 160.0, 210.0, 210.0, 3)}
            set S += array{Bloc(Ecrit(Prod.Nom, "111827", text_justification.Center), 1052.0, 380.0, 456.0, 44.0, 3)}
            # le chariot : un bandeau en bas, une carte par produit (icône, nom, pastille du nombre)
            Contenu := if (Sv := Service?) then Sv.ContenuChariot(ChariotOuvert) else array{}
            Presents := for (K -> N : Contenu, N > 0) { K }
            # le bandeau s'élargit s'il y a beaucoup de produits (8 au maximum)
            Largeur := 210.0
            Ecart := 16.0
            LargeurCartes := Presents.Length * Largeur + Max(0, Presents.Length - 1) * Ecart
            Bandeau := Max(1400.0, LargeurCartes + 60.0)
            set S += array{Bloc(Rect("0F172A"), 960.0 - Bandeau / 2.0, 770.0, Bandeau, 280.0, 1)}
            set S += array{Bloc(Ecrit("YOUR TROLLEY  -  CLICK WHAT THE PASSENGER WANTS", "FBBF24", text_justification.Center), 260.0, 780.0, 1400.0, 44.0, 3)}
            if (Presents.Length = 0):
                set S += array{Bloc(Ecrit("Your trolley is empty. Load it at the galley (E on the storage).", "E2E8F0", text_justification.Center), 260.0, 910.0, 1400.0, 44.0, 3)}
            else:
                # cartes centrées
                Debut := 960.0 - LargeurCartes / 2.0
                for (N -> K : Presents, P2 := M.ListeProduits[K], Nb := Contenu[K]):
                    X := Debut + N * (Largeur + Ecart)
                    set S += array{Bloc(Rect("FFFFFF"), X, 836.0, Largeur, 200.0, 2)}
                    set S += array{Bloc(Vignette(P2.Image, 120.0, 120.0), X + 24.0, 846.0, 120.0, 120.0, 3)}
                    set S += array{Bloc(Ecrit(P2.Nom, "1E293B", text_justification.Center), X, 976.0, Largeur, 44.0, 3)}
                    set S += array{Bloc(Rect("244A8C"), X + Largeur - 62.0, 842.0, 56.0, 40.0, 3)}
                    set S += array{Bloc(Ecrit("x{Nb}", "FFFFFF", text_justification.Center), X + Largeur - 62.0, 842.0, 56.0, 40.0, 4)}
                    set S += array{ZoneClic(X, 836.0, Largeur, 200.0, 100 + K)}
            if (MessageService <> ""):
                set S += array{Bloc(Rect("7F1D1D"), 560.0, 712.0, 800.0, 48.0, 1)}
                set S += array{Bloc(Ecrit(MessageService, "FFFFFF", text_justification.Center), 560.0, 714.0, 800.0, 44.0, 3)}
        set S += BoutonEcran("CLOSE", "374151", 1700.0, 20.0, 180.0, 50.0, 10)
        S

    Rect(Hex:string):color_block = color_block{DefaultColor := MakeColorFromHex(Hex), DefaultOpacity := 1.0}

    # Zone cliquable invisible (au-dessus d'une carte).
    ZoneClic(X:float, Y:float, L:float, H:float, Action:int):canvas_slot =
        B := button_quiet{DefaultText := Msg("")}
        B.OnClick().Subscribe(clic_feuille{Feuille := Self, Action := Action}.Clique)
        Bloc(B, X, Y, L, H, 5)

    # ---------- les papiers en gros plan ----------
    # En haut le jour et le vol en cours, à gauche le billet, à droite le passeport, en dessous
    # le vrai visage du passager, les boutons et les règles.
    PageBillet(B:billet_passager):[]canvas_slot =
        var S:[]canvas_slot = array{}
        P := B.Passager
        set S += array{Bloc(color_block{DefaultColor := NamedColors.Black, DefaultOpacity := 0.75}, 0.0, 0.0, 1920.0, 1080.0, 0)}
        # aujourd'hui et le vol en cours, pour comparer
        set S += array{Bloc(Ecrit("TODAY  {Aujourdhui()}      FLIGHT  {NumeroVol}      {VilleDepart()} > {VilleArrivee()}", "FFFFFF", text_justification.Center), 0.0, 95.0, 1920.0, 44.0, 3)}
        # le billet (image en puissance de 2 : affichée plus grande et décalée)
        set S += array{Bloc(Vignette(FeuilleMission.Billet, 2048.0 * BilletK, 1024.0 * BilletK), BilletX - 124.0 * BilletK, BilletY - 152.0 * BilletK, 2048.0 * BilletK, 1024.0 * BilletK, 1)}
        # on cache le petit avion et l'étiquette "SEQ No." de l'image pour laisser la place aux villes
        set S += array{CacheBillet(430.0, 330.0, 220.0, 100.0)}
        set S += array{CacheBillet(1040.0, 290.0, 260.0, 120.0)}
        set S += array{SurBillet(B.NomBillet, 60.0, 205.0, 980.0)}
        set S += array{SurBillet(B.DateBillet, 1050.0, 205.0, 260.0)}
        set S += array{SurBillet(VilleDepart(), 60.0, 345.0, 640.0)}
        set S += array{SurBillet(B.Vers, 720.0, 345.0, 590.0)}
        set S += array{SurBillet(B.Vol, 60.0, 535.0, 250.0)}
        set S += array{SurBillet(Porte, 320.0, 535.0, 230.0)}
        set S += array{SurBillet(B.Siege, 560.0, 535.0, 230.0)}
        set S += array{SurBillet(Embarquement, 800.0, 535.0, 240.0)}
        set S += array{SurBillet(B.Vol, 1390.0, 205.0, 410.0)}
        set S += array{SurBillet(B.Siege, 1390.0, 345.0, 410.0)}
        set S += array{SurBillet(B.Vers, 1390.0, 455.0, 410.0)}
        # le passeport
        set S += array{Bloc(Vignette(FeuilleMission.Passeport, 2048.0 * PassK, 1024.0 * PassK), PassX - 394.0 * PassK, PassY - 12.0 * PassK, 2048.0 * PassK, 1024.0 * PassK, 1)}
        # pas de photo : on cache le cadre photo et la signature de l'image
        set S += array{Bloc(color_block{DefaultColor := MakeColorFromHex("ECF0E2"), DefaultOpacity := 1.0}, PassX + 40.0 * PassK, PassY + 172.0 * PassK, 405.0 * PassK, 500.0 * PassK, 2)}
        set S += array{SurPasseport(B.Nom, 470.0, 228.0, 430.0)}
        set S += array{SurPasseport(B.Numero, 900.0, 228.0, 340.0)}
        set S += array{SurPasseport(B.Prenom, 470.0, 348.0, 760.0)}
        set S += array{SurPasseport(B.Pays, 470.0, 468.0, 430.0)}
        set S += array{SurPasseport(B.Sexe, 900.0, 468.0, 340.0)}
        set S += array{SurPasseport(B.Naissance, 470.0, 588.0, 430.0)}
        set S += array{SurPasseport(B.Expiration, 900.0, 588.0, 340.0)}
        set S += array{SurPasseport(B.Mrz1, 60.0, 800.0, 1170.0)}
        set S += array{SurPasseport(B.Mrz2, 60.0, 880.0, 1170.0)}
        # le tampon, ou les boutons
        if (B.Decision = 1):
            set S += array{Bloc(Vignette(FeuilleMission.TamponOk, 600.0, 300.0), 129.0, 238.0, 600.0, 300.0, 6)}
        else if (B.Decision = 2):
            set S += array{Bloc(Vignette(FeuilleMission.TamponRefus, 600.0, 300.0), 129.0, 238.0, 600.0, 300.0, 6)}
        if (B.Decision = 0):
            set S += BoutonEcran("VALID", "15803D", 180.0, 680.0, 330.0, 80.0, 1)
            set S += BoutonEcran("REFUSE", "B91C1C", 630.0, 680.0, 330.0, 80.0, 2)
        else:
            set S += array{Bloc(Ecrit("Documents already checked.", "CBD5E1", text_justification.Center), 20.0, 700.0, 1100.0, 40.0, 3)}
        set S += Regles()
        set S += BoutonEcran("CLOSE", "374151", 1700.0, 20.0, 180.0, 50.0, 3)
        S

    # Le règlement en bas : les 3 choses à comparer.
    Regles():[]canvas_slot =
        Toutes := array{"1. FLIGHT No. = this flight", "2. TO = this flight's city", "3. NAME: ticket = passport"}
        var S:[]canvas_slot = array{}
        set S += array{Bloc(color_block{DefaultColor := MakeColorFromHex("0F172A"), DefaultOpacity := 0.95}, 150.0, 850.0, 1620.0, 110.0, 1)}
        set S += array{Bloc(Ecrit("CHECK THESE 3 THINGS  -  ONE MISTAKE = REFUSE", "FBBF24", text_justification.Center), 150.0, 858.0, 1620.0, 40.0, 3)}
        for (I -> R : Toutes):
            set S += array{Bloc(Ecrit(R, "E2E8F0", text_justification.Center), 150.0 + I * 540.0, 906.0, 540.0, 40.0, 3)}
        S

    # Une valeur écrite sur le billet / le passeport (X, Y en pixels de l'image).
    SurBillet(Texte:string, X:float, Y:float, L:float):canvas_slot =
        Bloc(Ecrit(Texte, "111827", text_justification.Left), BilletX + X * BilletK, BilletY + Y * BilletK, L * BilletK, 40.0, 3)

    # Un rectangle blanc posé sur le billet (cache une partie de l'image).
    CacheBillet(X:float, Y:float, L:float, H:float):canvas_slot =
        Bloc(color_block{DefaultColor := NamedColors.White, DefaultOpacity := 1.0}, BilletX + X * BilletK, BilletY + Y * BilletK, L * BilletK, H * BilletK, 2)

    SurPasseport(Texte:string, X:float, Y:float, L:float):canvas_slot =
        Bloc(Ecrit(Texte, "1F2937", text_justification.Left), PassX + X * PassK, PassY + Y * PassK, L * PassK, 40.0, 3)
