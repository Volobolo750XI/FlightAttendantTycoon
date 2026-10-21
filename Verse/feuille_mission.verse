using { /Fortnite.com/Devices }
using { /Fortnite.com/Characters }
using { /Fortnite.com/UI }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /Verse.org/Colors }
using { /Verse.org/Assets }
using { /UnrealEngine.com/Temporary/SpatialMath }
using { /UnrealEngine.com/Temporary/UI }

# Flight Attendant Tycoon - la feuille de mission (une nouvelle à chaque trajet) et les billets.
#
# LA FEUILLE : elle est accrochée au mur (Modeles/Feuille/FeuilleMur.glb + un bouton dessus).
# E dessus -> elle s'ouvre en gros plan : tout ce qu'il y a à faire, cases cochées, ce que ça
# rapporte, bouton CLOSE. À chaque START BOARDING, une nouvelle feuille est tirée au hasard
# (MaxMissions au maximum) :
#   AVANT LE DÉCOLLAGE (ratées si pas faites au TAKE OFF)
#     - fermer tous les coffres à bagages (après l'embarquement)
#     - accueillir les passagers à la porte (rester près de la porte pendant l'embarquement)
#     - démonstration de sécurité (rester sur RepereDemo)
#     - tour de cabine : aller au fond de l'allée une fois tout le monde assis
#     - contrôler N billets (possible jusqu'à l'atterrissage)
#   EN VOL (ratées si pas faites à l'atterrissage)
#     - annonce de bienvenue : E sur l'Interphone
#     - inspecter un endroit (toilettes, cockpit... : Inspections)
#     - mettre N objets sur le chariot (galley)
#     - commander des fournitures sur le PC (SUPPLIES)
#   SURPRISES (rares, au milieu du vol)
#     - FAUX BILLET : la photo du fraudeur apparaît sur la feuille -> le trouver, regarder son
#       billet, REFUSE
#     - objet perdu : il apparaît dans une cachette, marcher dessus
#     - TURBULENCES : rejoindre SiegeEquipage en moins de DelaiTurbulence secondes
#     - passager malade (photo + siège) : lui donner une bouteille d'eau (TOUCHE du galley)
#
# LES PAPIERS : quand on vise un passager, "[F] CHECK PASSPORT & TICKET" s'affiche. La touche
# ouvre ses papiers en gros : son vrai visage à gauche, son billet au milieu, son passeport à
# droite, et en haut la date du jour + le vol en cours. Il faut vérifier que tout correspond, puis
# cliquer VALID ou REFUSE (tampon). À la porte pendant l'embarquement, les passagers s'arrêtent
# devant toi (poste de contrôle, device passagers) ; refusé, il repart par la passerelle.
# Un "cerveau" (Fabriquer) fabrique les papiers et glisse parfois UNE erreur, de plus en plus
# subtile avec les destinations et selon ta forme. REFUSE sur des faux = attrapé (bonus).
# REFUSE sur des vrais = plainte. VALID sur des faux = il voyage gratis (et le cerveau s'en
# souvient : ce type d'erreur reviendra).
#
# ARGENT : tout dépend de la VALEUR DU VOL (pc_destinations.ValeurVol : environ la moitié du prix
# de la destination suivante). Au début ça rapporte un peu, avec les grosses destinations beaucoup.
#   mission = PartMission x valeur, fraudeur = PartFraudeur x valeur, feuille parfaite =
#   PartParfait x valeur ; billets (device passagers) = PartBillets x valeur x sièges occupés / sièges.
#
# Dans le Tiroir à contenu, dossier "FeuilleMission" : importe tout Textures/FeuilleMission
# (FondFeuille, Billet, Passeport, Case, CaseCochee, CaseRatee, TamponOk, TamponRefus, Photo1 ... Photo5).
# Dans le device passagers, règle "Photo" de chaque modèle.

point_inspection := class<concrete>:
    # Nom court affiché sur la feuille (ex : TOILETS, COCKPIT, GALLEY).
    @editable Nom:string = "TOILETS"
    @editable Repere:creative_prop = creative_prop{}

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
    # 0 coffres, 1 billets, 2 accueil, 3 démo, 4 tour de cabine,
    # 5 annonce, 6 inspection, 7 chariot, 8 fournitures,
    # 9 faux billet, 10 objet perdu, 11 turbulences, 12 malade
    Genre:int
    var Fait:logic = false
    var Rate:logic = false
    var Visible:logic = true
    var Compte:int = 0
    var Objectif:int = 1
    # inspection : numéro du point ; objet perdu : numéro de l'objet
    var Numero:int = -1
    # temps passé sur place
    var Chrono:float = 0.0
    # surprise : secondes après le décollage où elle arrive
    var Apparition:float = -1.0
    # turbulences : heure limite
    var Limite:float = 0.0
    # fraudeur / malade
    var Cible:?passager = false

clic_feuille := class:
    Feuille:feuille_mission
    Action:int
    Clique(Clic:widget_message):void = Feuille.Agir(Action)

feuille_mission := class(creative_device):
    @editable Passagers:passagers = passagers{}
    @editable DeviceAvion:avion_tycoon = avion_tycoon{}
    @editable DevicePC:?pc_destinations = false
    @editable Service:?service_device = false
    @editable Menu:?menu_pc = false
    # Un Appareil Bouton posé sur la feuille accrochée au mur (texte "Read").
    @editable BoutonFeuille:button_device = button_device{}
    # Un Déclencheur d'entrée : la touche pour regarder les papiers du passager visé,
    # et le nom de cette touche (affiché à l'écran quand on vise un passager).
    @editable InputBillet:input_trigger_device = input_trigger_device{}
    @editable NomTouche:string = "F"
    # (facultatif) Appareil Bouton sur le téléphone de cabine : l'annonce de bienvenue.
    @editable Interphone:?button_device = false
    @editable RepereDemo:?creative_prop = false
    @editable SiegeEquipage:?creative_prop = false
    @editable Inspections:[]point_inspection = array{}
    @editable ObjetsPerdus:[]creative_prop = array{}
    @editable Cachettes:[]creative_prop = array{}
    @editable MessageHUD:?hud_message_device = false
    @editable SonMission:?audio_player_device = false
    @editable SonErreur:?audio_player_device = false
    @editable SonAnnonce:?audio_player_device = false
    @editable SonTurbulence:?audio_player_device = false
    @editable SonTampon:?audio_player_device = false

    # ===== Le hasard de la feuille (chances en %) =====
    @editable MaxMissions:int = 6
    @editable ChanceCoffres:int = 90
    @editable ChanceBillets:int = 85
    @editable ChanceAccueil:int = 55
    @editable ChanceDemo:int = 50
    @editable ChanceTourCabine:int = 45
    @editable ChanceAnnonce:int = 55
    @editable ChanceInspection:int = 50
    @editable ChanceChariot:int = 35
    @editable ChanceFournitures:int = 30
    @editable ChanceFraudeur:int = 15
    @editable ChanceObjetPerdu:int = 18
    @editable ChanceTurbulence:int = 15
    @editable ChanceMalade:int = 15
    # Chance que des papiers regardés soient faux (+5 par niveau du cerveau ; en plus de la surprise)
    @editable ChanceBilletFaux:int = 10
    @editable BilletsMin:int = 2
    @editable BilletsMax:int = 4
    @editable ObjetsChariotMin:int = 2
    @editable ObjetsChariotMax:int = 4
    # Temps à rester sur place (démo, inspection), à la porte (accueil), et distance (cm)
    @editable DureeSurPlace:float = 4.0
    @editable DureeAccueil:float = 8.0
    @editable RayonSurPlace:float = 200.0
    @editable DelaiTurbulence:float = 25.0
    # Viser un passager : précision (cm) et portée (cm)
    @editable RayonVisee:float = 70.0
    @editable PorteeVisee:float = 450.0
    # ===== Gains (part de la valeur du vol) =====
    @editable PartMission:float = 0.07
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
    TextesTaches:[]string = array{"Close all overhead bins", "", "Greet passengers at the door", "Safety demonstration (front)", "Walk to the back of the cabin", "Welcome announcement (phone)", "", "", "Order supplies on the PC", "ALERT: passenger with fake papers", "A passenger lost something: find it", "TURBULENCE: go to your crew seat!", "Sick passenger: bring water"}
    PaysNoms:[]string = array{"FRANCE", "GERMANY", "ITALY", "SPAIN", "JAPAN", "BRAZIL", "CANADA", "EGYPT", "INDIA", "MEXICO", "NIGERIA", "POLAND", "TURKEY", "KOREA", "SWEDEN", "USA", "MOROCCO", "PORTUGAL"}
    PaysCodes:[]string = array{"FRA", "DEU", "ITA", "ESP", "JPN", "BRA", "CAN", "EGY", "IND", "MEX", "NGA", "POL", "TUR", "KOR", "SWE", "USA", "MAR", "PRT"}
    MoisNoms:[]string = array{"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"}
    Raisons:[]string = array{"", "WRONG DESTINATION", "WRONG FLIGHT", "NOT THE SAME FACE", "WRONG DATE ON TICKET", "PASSPORT EXPIRED", "NAMES DON'T MATCH", "WRONG SEX ON PASSPORT", "PASSPORT No. DOESN'T MATCH", "NAME MISSPELLED"}
    # Les papiers à l'écran : Billet.png (1800 x 720) en 900 x 360, Passeport.png (1260 x 1000)
    # en 630 x 500. Les positions des valeurs sont celles de Outils/feuille_mission.py.
    BilletX:float = 330.0
    BilletY:float = 250.0
    BilletK:float = 0.5
    PassX:float = 1250.0
    PassY:float = 190.0
    PassK:float = 0.5

    var Taches:[]tache_feuille = array{}
    var Billets:[]billet_passager = array{}
    var EnCours:logic = false
    var Bilan:logic = false
    var DebutVol:float = -1.0
    var DebutTrajet:float = 0.0
    var NumeroVol:string = ""
    var Porte:string = ""
    var Embarquement:string = ""
    var GainsMissions:int = 0
    var FraudeursRates:int = 0
    var Plaintes:int = 0
    var Rangs:[]int = array{}
    var PointPorte:?vector3 = false
    var PointFond:?vector3 = false
    # La date du jour (un trajet = un jour)
    var AujAn:int = 2026
    var AujMois:int = 3
    var AujJour:int = 2
    # Le cerveau : la forme du joueur et, pour chaque erreur (1..9), combien il en a attrapé / raté
    var Forme:int = 0
    var Attrapes:[]int = array{0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
    var Rates:[]int = array{0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
    # Le message quand on vise un passager
    var Invite:?canvas = false
    TexteInvite:text_block = text_block{DefaultTextColor := NamedColors.White, DefaultJustification := text_justification.Center, DefaultShadowColor := NamedColors.Black, DefaultShadowOpacity := 0.9, DefaultShadowOffset := option{vector2{X := 2.0, Y := 2.0}}}

    # L'écran ouvert : 0 rien, 1 la feuille, 2 un billet
    var Page:int = 0
    var Joueur:?player = false
    var Base:?canvas = false
    var Dynamiques:[]widget = array{}
    var BilletOuvert:?billet_passager = false

    OnBegin<override>()<suspends>:void =
        if (R := RepereDemo?) { R.Hide() }
        if (R := SiegeEquipage?) { R.Hide() }
        for (P : Inspections) { P.Repere.Hide() }
        for (O : ObjetsPerdus) { O.Hide() }
        for (C : Cachettes) { C.Hide() }
        BoutonFeuille.InteractedWithEvent.Subscribe(OnFeuille)
        InputBillet.PressedEvent.Subscribe(OnBillet)
        if (I := Interphone?) { I.InteractedWithEvent.Subscribe(OnInterphone) }
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
                Verifier(0.2)

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
        set DebutVol = -1.0
        set DebutTrajet = GetSimulationElapsedTime()
        MesurerCabine()
        # 1. on tire les missions du jour, puis on en garde MaxMissions au hasard
        var Liste:[]tache_feuille = array{}
        if (Passagers.PortesCoffres.Length > 0, Chance[ChanceCoffres]):
            set Liste += array{tache_feuille{Genre := 0}}
        if (PointPorte?, Chance[ChanceAccueil]):
            set Liste += array{tache_feuille{Genre := 2}}
        if (RepereDemo?, Chance[ChanceDemo]):
            set Liste += array{tache_feuille{Genre := 3}}
        if (PointFond?, Chance[ChanceTourCabine]):
            set Liste += array{tache_feuille{Genre := 4}}
        if (Chance[ChanceBillets]):
            T := tache_feuille{Genre := 1}
            set T.Objectif = GetRandomInt(Max(1, BilletsMin), Max(BilletsMin, BilletsMax))
            set Liste += array{T}
        if (Interphone?, Chance[ChanceAnnonce]):
            set Liste += array{tache_feuille{Genre := 5}}
        if (Inspections.Length > 0, Chance[ChanceInspection]):
            T := tache_feuille{Genre := 6}
            set T.Numero = GetRandomInt(0, Inspections.Length - 1)
            set Liste += array{T}
        if (Service?, Chance[ChanceChariot]):
            T := tache_feuille{Genre := 7}
            set T.Objectif = GetRandomInt(Max(1, ObjetsChariotMin), Max(ObjetsChariotMin, ObjetsChariotMax))
            set Liste += array{T}
        if (Menu?, Chance[ChanceFournitures]):
            T := tache_feuille{Genre := 8}
            set T.Compte = SommeStock()
            set Liste += array{T}
        set Liste = GarderAuHasard(Liste, Max(1, MaxMissions))
        # 2. les surprises (rares) : entre 15 % et 60 % du vol
        var Surprises:[]int = array{}
        if (Chance[ChanceFraudeur]) { set Surprises += array{9} }
        if (ObjetsPerdus.Length > 0, Chance[ChanceObjetPerdu]) { set Surprises += array{10} }
        if (SiegeEquipage?, Chance[ChanceTurbulence]) { set Surprises += array{11} }
        if (Service?, Chance[ChanceMalade]) { set Surprises += array{12} }
        Duree := DureeVolPrevue()
        for (G : Surprises):
            T := tache_feuille{Genre := G}
            set T.Visible = false
            set T.Apparition = Duree * GetRandomFloat(0.15, 0.6)
            if (G = 10) { set T.Numero = GetRandomInt(0, ObjetsPerdus.Length - 1) }
            set Liste += array{T}
        set Taches = Liste
        set EnCours = true
        Message("New flight briefing on the wall!")
        Rafraichir()

    GarderAuHasard(Liste:[]tache_feuille, N:int):[]tache_feuille =
        var Reste:[]tache_feuille = Liste
        loop:
            if (Reste.Length <= N) { break }
            Retire := GetRandomInt(0, Reste.Length - 1)
            set Reste = for (I -> T : Reste, I <> Retire) { T }
        Reste

    # La porte (bout du chemin, dans l'allée), le fond de la cabine (place la plus loin)
    # et le rang de chaque place (le siège le plus proche dans les rangées du device avion).
    MesurerCabine():void =
        if (Fin := Passagers.Chemin[Passagers.Chemin.Length - 1]):
            Depart := Fin.GetTransform().Translation
            set PointPorte = option{Depart}
            var Loin:float = 0.0
            for (P : Passagers.Places):
                A := P.Allee.GetTransform().Translation
                D := Distance(A, Depart)
                if (D > Loin):
                    set Loin = D
                    set PointFond = option{A}
        set Rangs = for (P : Passagers.Places) { RangDe(P) }

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
        set DebutVol = GetSimulationElapsedTime()
        for (T : Taches, not T.Fait?, T.Genre = 0 or T.Genre = 2 or T.Genre = 3 or T.Genre = 4):
            set T.Rate = true
        Rafraichir()

    Atterrissage():void =
        if (EnCours?):
            set EnCours = false
            for (T : Taches, not T.Fait?):
                set T.Rate = true
                if (T.Genre = 10, O := ObjetsPerdus[T.Numero]) { O.Hide() }
            Visibles := for (T : Taches, T.Visible?) { T }
            Reussies := for (T : Visibles, T.Fait?) { T }
            if (Visibles.Length > 0, Reussies.Length = Visibles.Length):
                Payer(Gain(PartParfait), "PERFECT FLIGHT!")
            Passes := for (B : Billets, B.Probleme > 0, B.Decision <> 2) { B }
            set FraudeursRates = Passes.Length
            # revenu moyen du trajet (billets + missions) pour le cadre "/Sec"
            Duree := GetSimulationElapsedTime() - DebutTrajet
            Total := Passagers.DernierGainBillets + GainsMissions
            if (Duree > 1.0, R := Round[Total * 1.0 / Duree]):
                set DeviceAvion.RevenuParSeconde = R
                DeviceAvion.MettreAJourUI()
            set Bilan = true
            Message("Flight complete! Check your briefing sheet.")
            Rafraichir()

    # ---------- vérifications (toutes les 0.2 s) ----------
    Verifier(Pas:float):void =
        Etat := Passagers.EtatBouton
        Maintenant := GetSimulationElapsedTime()
        Ecoule := Maintenant - DebutVol
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
                    Reussir(T, "PAPERS CHECKED")
                    set Change = true
            else if (T.Genre = 2):
                if (Etat = 1, Pos := PointPorte?):
                    Ok := SurPlace(T, Pos, DureeAccueil, Pas)
                    if (Ok?):
                        Reussir(T, "PASSENGERS WELCOMED")
                        set Change = true
            else if (T.Genre = 3):
                if (Etat >= 2, R := RepereDemo?):
                    Ok := SurPlace(T, R.GetTransform().Translation, DureeSurPlace, Pas)
                    if (Ok?):
                        Reussir(T, "SAFETY DEMO DONE")
                        set Change = true
            else if (T.Genre = 4):
                if (Etat >= 2, Pos := PointFond?):
                    Ok := SurPlace(T, Pos, 0.4, Pas)
                    if (Ok?):
                        Reussir(T, "CABIN CHECKED")
                        set Change = true
            else if (T.Genre = 6):
                if (Etat = 3, P := Inspections[T.Numero]):
                    Ok := SurPlace(T, P.Repere.GetTransform().Translation, DureeSurPlace, Pas)
                    if (Ok?):
                        Reussir(T, "{P.Nom} INSPECTED")
                        set Change = true
            else if (T.Genre = 7):
                N := ObjetsSurChariot()
                if (N <> T.Compte):
                    set T.Compte = N
                    set Change = true
                if (N >= T.Objectif):
                    Reussir(T, "TROLLEY READY")
                    set Change = true
            else if (T.Genre = 8):
                Stock := SommeStock()
                if (Stock > T.Compte):
                    Reussir(T, "SUPPLIES ORDERED")
                    set Change = true
            else if (T.Genre = 10):
                if (O := ObjetsPerdus[T.Numero], Proche[O.GetTransform().Translation, 150.0]):
                    O.Hide()
                    Reussir(T, "LOST ITEM FOUND")
                    set Change = true
            else if (T.Genre = 11):
                if (R := SiegeEquipage?, Proche[R.GetTransform().Translation, RayonSurPlace]):
                    Reussir(T, "SAFE DURING TURBULENCE")
                    set Change = true
                else if (Maintenant > T.Limite):
                    set T.Rate = true
                    Erreur("Too late! A passenger got hurt.")
                    set Change = true
        if (Change?) { Rafraichir() }

    # true quand le proprio est resté Duree secondes près du point
    # (le chrono repart à 0 s'il s'en va). À appeler HORS d'une condition (sinon le chrono est annulé).
    SurPlace(T:tache_feuille, Position:vector3, Duree:float, Pas:float):logic =
        if (Proche[Position, RayonSurPlace]):
            set T.Chrono += Pas
        else:
            set T.Chrono = 0.0
        if (T.Chrono >= Duree) then true else false

    Proche(Position:vector3, Rayon:float)<transacts><decides>:void =
        Proprio := DeviceAvion.Proprio?
        Perso := Proprio.GetFortCharacter[]
        Distance(Perso.GetTransform().Translation, Position) < Rayon

    ObjetsSurChariot():int =
        if (S := Service?):
            Sur := for (O : S.Poses, O.ChariotIndex >= 0) { O }
            Sur.Length
        else:
            0

    SommeStock():int =
        var Total:int = 0
        if (M := Menu?):
            for (N : M.Stock) { set Total += N }
        Total

    # ---------- les surprises en vol ----------
    Surprise(T:tache_feuille):void =
        Assis := for (P : Passagers.EnCours, P.Etat = 2, P.Corps?) { P }
        if (T.Genre = 9):
            # de préférence quelqu'un qui a déjà un faux billet pas encore vu, sinon un inconnu
            DejaFaux := for (B : Billets, B.Probleme > 0, B.Decision = 0, B.Passager.Etat = 2) { B.Passager }
            Inconnus := for (P : Assis, not ABillet[P]) { P }
            Choix := if (DejaFaux.Length > 0) then DejaFaux else Inconnus
            if (P := Choix[GetRandomInt(0, Choix.Length - 1)]):
                if (not ABillet[P]) { Fabriquer(P, true) }
                set T.Cible = option{P}
                set T.Visible = true
                Erreur("ALERT: a passenger has fake papers! See the briefing.")
            else:
                set T.Rate = true
        else if (T.Genre = 10, O := ObjetsPerdus[T.Numero]):
            if (C := Cachettes[GetRandomInt(0, Cachettes.Length - 1)]):
                if (O.TeleportTo[C.GetTransform().Translation, O.GetTransform().Rotation]) {}
            O.Show()
            set T.Visible = true
            Message("A passenger lost something in the cabin!")
        else if (T.Genre = 11):
            set T.Limite = GetSimulationElapsedTime() + DelaiTurbulence
            set T.Visible = true
            if (S := SonTurbulence?) { S.Play() }
            Erreur("TURBULENCE! Go to your crew seat!")
        else if (T.Genre = 12):
            Libres := for (P : Assis, not EstCible[P]) { P }
            if (P := Libres[GetRandomInt(0, Libres.Length - 1)]):
                set T.Cible = option{P}
                set T.Visible = true
                Siege := SiegeDe(P)
                Erreur("A passenger feels sick at seat {Siege}! Bring water.")
            else:
                set T.Rate = true
        else:
            set T.Rate = true

    EstCible(P:passager)<transacts><decides>:void =
        var Oui:logic = false
        for (T : Taches, C := T.Cible?, C = P) { set Oui = true }
        Oui?

    # ---------- l'eau pour le malade (appelé par le service_device) ----------
    # true = on a donné l'objet tenu (il disparaît de la main).
    Donner(Agent:agent, Index:int):logic =
        Vise := PassagerVise(Agent)
        if (Index = 0, P := Vise?):
            for (T : Taches, T.Genre = 12, T.Visible?, not T.Fait?, not T.Rate?, C := T.Cible?, C = P):
                Reussir(T, "PASSENGER FEELS BETTER")
                Rafraichir()
                return true
        false

    # ---------- l'annonce ----------
    OnInterphone(Agent:agent):void =
        if (S := SonAnnonce?) { S.Play() }
        if (Passagers.EtatBouton = 3):
            for (T : Taches, T.Genre = 5, not T.Fait?, not T.Rate?):
                Reussir(T, "WELCOME ANNOUNCEMENT")
                Rafraichir()

    # ---------- les papiers (passeport + billet) ----------
    # Viser un passager + la touche -> ses papiers en gros. Marche à la porte (le passager attend
    # devant le poste de contrôle) comme une fois assis.
    OnBillet(Agent:agent):void =
        Vise := PassagerVise(Agent)
        if (Page = 0, EstProprio[Agent], P := Vise?, J := player[Agent]):
            B := BilletDe(P)
            Ouvrir(J, 2)
            set BilletOuvert = option{B}
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
        Chances := ChanceBilletFaux + (NiveauActuel() - 1) * 5
        Fabriquer(P, if (Chance[Chances]) then true else false)

    # ----- le cerveau des faux papiers -----
    # Il fabrique des papiers cohérents (nom, sexe et âge qui vont avec le visage, passeport valide,
    # billet pour CE vol, CE jour), puis, si ce sont des faux, il glisse UNE erreur dedans :
    #   facile    1 mauvaise destination   2 mauvais numéro de vol   3 photo de quelqu'un d'autre
    #   moyen     4 date du billet ≠ aujourd'hui   5 passeport expiré   6 prénoms différents
    #             7 mauvais sexe sur le passeport
    #   difficile 8 n° de passeport ≠ celui de la bande du bas   9 nom mal écrit sur le billet
    # Le niveau dépend de la destination (les grosses destinations = erreurs plus subtiles) et de
    # la forme du joueur (il réussit tout -> plus dur ; il se trompe -> plus facile). Il choisit
    # surtout les erreurs que le joueur a déjà laissé passer ou qu'il n'a encore jamais vues.
    Fabriquer(P:passager, Faux:logic):billet_passager =
        Vraie := P.Modele.Photo
        PhotoOk := if (Vraie > 0) then true else false
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
        Defaut := if (Faux?) then ChoisirProbleme(PhotoOk) else 0
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
        else if (Defaut = 3):
            for (Essai := 1..10, PhotoB = Vraie) { set PhotoB = GetRandomInt(1, PhotosPassagers.Length) }
        else if (Defaut = 4):
            set JourBillet = if (AujJour > 3) then AujJour - GetRandomInt(1, 3) else AujJour + GetRandomInt(1, 3)
        else if (Defaut = 5):
            if (AujMois > 1, GetRandomInt(0, 1) = 0):
                set ExpA = AujAn
                set ExpM = GetRandomInt(1, AujMois - 1)
            else:
                set ExpA = AujAn - GetRandomInt(1, 4)
        else if (Defaut = 6):
            Liste := if (Homme?) then PrenomsH else PrenomsF
            for (Essai := 1..10, PrenomB = PrenomVrai) { set PrenomB = Choisir(Liste) }
        else if (Defaut = 7):
            set SexePasseport = if (Homme?) then "F" else "M"
        else if (Defaut = 8):
            Autres := GetRandomInt(1000000, 9999999)
            set NumeroBande = "{L1}{L2}{Autres}"
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
            DateBillet := DateTexte(JourBillet, AujMois, AujAn)
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
            Mrz1 := Remplir("P<{Code}{NomVrai}<<{PrenomVrai}", 44)
            Mrz2 := Remplir("{NumeroBande}<{Code}{NaissMrz}{SexePasseport}{Expire}", 44)
            Probleme := Defaut
        if (Defaut > 0) { set P.Fraudeur = true }
        set Billets += array{B}
        B

    # Le niveau des erreurs : 1 facile, 2 moyen, 3 difficile.
    NiveauActuel():int =
        var NiveauBase:int = 1
        if (Ordi := DevicePC?):
            if (Ordi.Active >= 7):
                set NiveauBase = 3
            else if (Ordi.Active >= 2):
                set NiveauBase = 2
        Bonus := if (Forme >= 6) then 1 else if (Forme <= -3) then -1 else 0
        Max(1, Min(3, NiveauBase + Bonus))

    NiveauDe(Code:int)<transacts>:int =
        if (Code <= 3) then 1 else if (Code <= 7) then 2 else 3

    ChoisirProbleme(PhotoOk:logic):int =
        N := NiveauActuel()
        var Codes:[]int = array{}
        var Poids:[]float = array{}
        for (C := 1..9, NiveauDe(C) <= N, (C <> 3 and C <> 7) or PhotoOk?):
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
                for (T : Taches, T.Genre = 9, not T.Fait?, Q := T.Cible?, Q = P):
                    set T.Fait = true
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

    # Le passager que le joueur vise (son corps), à portée.
    PassagerVise(Agent:agent):?passager =
        var Vise:?passager = false
        if (FC := Agent.GetFortCharacter[]):
            CamPos := FC.GetViewLocation()
            Avant := FC.GetViewRotation().RotateVector(vector3{X := 1.0, Y := 0.0, Z := 0.0})
            var Meilleur:float = RayonVisee
            for (P : Passagers.EnCours, P.Controle <> 2, C := P.Corps?):
                Pos := C.GetTransform().Translation + vector3{Z := 60.0}
                D := Pos - CamPos
                T := D.X * Avant.X + D.Y * Avant.Y + D.Z * Avant.Z
                Ecart := Distance(CamPos + Avant * T, Pos)
                if (T > 0.0, T < PorteeVisee, Ecart < Meilleur):
                    set Meilleur = Ecart
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
                if (P := Vise?):
                    Texte := if (DejaControle[P]) then "DOCUMENTS CHECKED" else "[{NomTouche}]  CHECK PASSPORT & TICKET"
                    TexteInvite.SetText(Msg(Texte))
                    TexteInvite.SetVisibility(widget_visibility.Visible)
                else:
                    TexteInvite.SetVisibility(widget_visibility.Collapsed)

    CreerInvite(J:player):void =
        if (UI := GetPlayerUI[J]):
            C := canvas{Slots := array{Bloc(TexteInvite, 560.0, 640.0, 800.0, 40.0, 0)}}
            UI.AddWidget(C)
            TexteInvite.SetVisibility(widget_visibility.Collapsed)
            set Invite = option{C}

    # ---------- le vol en cours, les dates, les noms ----------
    VilleDepart():string =
        if (Ordi := DevicePC?, D := Ordi.ListeDestinations[Ordi.Active]):
            if (Ordi.Retour?) then D.Ville2 else D.Ville1
        else:
            "PARIS"

    VilleArrivee():string =
        if (Ordi := DevicePC?, D := Ordi.ListeDestinations[Ordi.Active]):
            if (Ordi.Retour?) then D.Ville1 else D.Ville2
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

    GainTache(T:tache_feuille):int = Gain(if (T.Genre = 9) then PartFraudeur else PartMission)

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

    DureeVolPrevue():float =
        if (Ordi := DevicePC?) then Ordi.DureeVolActive() else Passagers.DureeVolSansPC

    PhotoDe(N:int)<transacts><decides>:texture = PhotosPassagers[N - 1]

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

    # 1 VALID, 2 REFUSE, 3 fermer le billet, 10 fermer la feuille
    Agir(Action:int):void =
        if (Action = 1 or Action = 2):
            Decider(Action)
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
            Slots := if (Page = 1) then PageFeuille() else if (B := BilletOuvert?) then PageBillet(B) else array{}
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
        set S += array{Bloc(Vignette(FeuilleMission.FondFeuille, 820.0, 1000.0), 550.0, 40.0, 820.0, 1000.0, 1)}
        set S += BoutonEcran("CLOSE", "374151", 1170.0, 950.0, 150.0, 42.0, 10)
        if (Taches.Length = 0):
            set S += array{Bloc(Ecrit("No flight yet: press START BOARDING.", "334155", text_justification.Center), 600.0, 400.0, 720.0, 40.0, 3)}
            return S
        Visibles := for (T : Taches, T.Visible?) { T }
        Faites := for (T : Visibles, T.Fait?) { T }
        set S += array{Bloc(Ecrit("FLIGHT {NumeroVol}   {VilleDepart()} > {VilleArrivee()}", "1E293B", text_justification.Left), 640.0, 205.0, 520.0, 36.0, 3)}
        set S += array{Bloc(Ecrit("{Faites.Length}/{Visibles.Length}", "244A8C", text_justification.Right), 1160.0, 205.0, 140.0, 36.0, 3)}
        var Y:float = 252.0
        for (Section := 0..1):
            Liste := for (T : Visibles, DansSection[T, Section]) { T }
            if (Liste.Length > 0):
                Titre := if (Section = 0) then "BEFORE TAKE OFF" else "IN FLIGHT"
                set S += array{Bloc(Ecrit(Titre, "244A8C", text_justification.Left), 640.0, Y, 400.0, 34.0, 3)}
                set Y += 40.0
                for (T : Liste):
                    Coche := if (T.Fait?) then FeuilleMission.CaseCochee else if (T.Rate?) then FeuilleMission.CaseRatee else FeuilleMission.Case
                    Couleur := if (T.Rate?) then "9CA3AF" else if (T.Genre >= 9) then "B91C1C" else "111827"
                    CouleurPrix := if (T.Rate?) then "9CA3AF" else "16A34A"
                    set S += array{Bloc(Vignette(Coche, 38.0, 38.0), 640.0, Y, 38.0, 38.0, 3)}
                    set S += array{Bloc(Ecrit(TexteTache(T), Couleur, text_justification.Left), 692.0, Y + 4.0, 470.0, 34.0, 3)}
                    set S += array{Bloc(Ecrit("+{Prix(GainTache(T))}", CouleurPrix, text_justification.Right), 1160.0, Y + 4.0, 140.0, 34.0, 3)}
                    set Y += 54.0
                set Y += 8.0
        if (Bilan?):
            set S += PageBilan()
        else:
            # les avis de recherche : faux billet et malade, avec la photo
            var X:float = 640.0
            for (T : Visibles, not T.Fait?, not T.Rate?, T.Genre = 9 or T.Genre = 12, P := T.Cible?):
                set S += Alerte(T, P, X, 800.0)
                set X += 340.0
        S

    DansSection(T:tache_feuille, Section:int)<transacts><decides>:void =
        Avant := if (T.Genre <= 4) then 0 else 1
        Avant = Section

    Alerte(T:tache_feuille, P:passager, X:float, Y:float):[]canvas_slot =
        var S:[]canvas_slot = array{}
        if (Tex := PhotoDe[P.Modele.Photo]):
            set S += array{Bloc(Vignette(Tex, 110.0, 110.0), X, Y, 110.0, 110.0, 3)}
        else:
            set S += array{Bloc(color_block{DefaultColor := MakeColorFromHex("CBD5E1"), DefaultOpacity := 1.0}, X, Y, 110.0, 110.0, 3)}
            set S += array{Bloc(Ecrit("?", "334155", text_justification.Center), X, Y + 36.0, 110.0, 40.0, 4)}
        Titre := if (T.Genre = 9) then "FAKE PAPERS!" else "SICK PASSENGER"
        Ligne1 := if (T.Genre = 9) then "Find this face," else "Seat {SiegeDe(P)}"
        Ligne2 := if (T.Genre = 9) then "check and REFUSE" else "Bring water"
        set S += array{Bloc(Ecrit(Titre, "B91C1C", text_justification.Left), X + 122.0, Y + 4.0, 210.0, 32.0, 3)}
        set S += array{Bloc(Ecrit(Ligne1, "1E293B", text_justification.Left), X + 122.0, Y + 40.0, 210.0, 30.0, 3)}
        set S += array{Bloc(Ecrit(Ligne2, "1E293B", text_justification.Left), X + 122.0, Y + 72.0, 210.0, 30.0, 3)}
        S

    PageBilan():[]canvas_slot =
        GainBillets := Passagers.DernierGainBillets
        Total := GainBillets + GainsMissions
        var S:[]canvas_slot = array{}
        set S += array{Bloc(Ecrit("FLIGHT COMPLETE", "244A8C", text_justification.Left), 640.0, 760.0, 400.0, 34.0, 3)}
        set S += array{Bloc(Ecrit("Tickets ({Passagers.DerniersPayants} passengers)", "1E293B", text_justification.Left), 640.0, 798.0, 480.0, 32.0, 3)}
        set S += array{Bloc(Ecrit("+{Prix(GainBillets)}", "16A34A", text_justification.Right), 1160.0, 798.0, 140.0, 32.0, 3)}
        set S += array{Bloc(Ecrit("Missions", "1E293B", text_justification.Left), 640.0, 834.0, 480.0, 32.0, 3)}
        set S += array{Bloc(Ecrit("+{Prix(GainsMissions)}", "16A34A", text_justification.Right), 1160.0, 834.0, 140.0, 32.0, 3)}
        set S += array{Bloc(Ecrit("TOTAL", "111827", text_justification.Left), 640.0, 874.0, 480.0, 34.0, 3)}
        set S += array{Bloc(Ecrit("+{Prix(Total)}", "15803D", text_justification.Right), 1160.0, 874.0, 140.0, 34.0, 3)}
        if (FraudeursRates > 0 or Plaintes > 0):
            set S += array{Bloc(Ecrit("Fraudsters missed: {FraudeursRates}   Complaints: {Plaintes}", "B91C1C", text_justification.Left), 640.0, 912.0, 520.0, 30.0, 3)}
        S

    TexteTache(T:tache_feuille):string =
        if (T.Genre = 1) then "Check passengers' papers {Min(T.Compte, T.Objectif)}/{T.Objectif}" else if (T.Genre = 6, P := Inspections[T.Numero]) then "Inspect the {P.Nom}" else if (T.Genre = 7) then "Put items on the trolley {Min(T.Compte, T.Objectif)}/{T.Objectif}" else if (Texte := TextesTaches[T.Genre]) then Texte else "?"

    # ---------- les papiers en gros plan ----------
    # À gauche le vrai visage du passager, au milieu le billet, à droite le passeport.
    PageBillet(B:billet_passager):[]canvas_slot =
        var S:[]canvas_slot = array{}
        P := B.Passager
        set S += array{Bloc(color_block{DefaultColor := NamedColors.Black, DefaultOpacity := 0.65}, 0.0, 0.0, 1920.0, 1080.0, 0)}
        # aujourd'hui et le vol en cours, pour comparer
        set S += array{Bloc(Ecrit("TODAY  {Aujourdhui()}        FLIGHT  {NumeroVol}        {VilleDepart()} > {VilleArrivee()}", "FFFFFF", text_justification.Center), 0.0, 110.0, 1920.0, 40.0, 3)}
        # le vrai visage
        set S += array{Bloc(Ecrit("PASSENGER", "E2E8F0", text_justification.Center), 60.0, 215.0, 240.0, 30.0, 3)}
        if (Tex := PhotoDe[P.Modele.Photo]):
            set S += array{Bloc(Vignette(Tex, 240.0, 240.0), 60.0, 250.0, 240.0, 240.0, 2)}
        else:
            set S += array{Bloc(Ecrit("?", "FFFFFF", text_justification.Center), 60.0, 350.0, 240.0, 40.0, 3)}
        # le billet
        set S += array{Bloc(Vignette(FeuilleMission.Billet, 900.0, 360.0), BilletX, BilletY, 900.0, 360.0, 1)}
        set S += array{SurBillet(B.NomBillet, 60.0, 205.0, 900.0)}
        set S += array{SurBillet(VilleDepart(), 60.0, 345.0, 360.0)}
        set S += array{SurBillet(B.Vers, 720.0, 345.0, 320.0)}
        set S += array{SurBillet(B.DateBillet, 1050.0, 205.0, 270.0)}
        set S += array{SurBillet(B.Seq, 1050.0, 345.0, 200.0)}
        set S += array{SurBillet(B.Vol, 60.0, 535.0, 240.0)}
        set S += array{SurBillet(Porte, 320.0, 535.0, 220.0)}
        set S += array{SurBillet(B.Siege, 560.0, 535.0, 220.0)}
        set S += array{SurBillet(Embarquement, 800.0, 535.0, 220.0)}
        set S += array{SurBillet(B.Vol, 1390.0, 205.0, 380.0)}
        set S += array{SurBillet(B.Siege, 1390.0, 345.0, 380.0)}
        set S += array{SurBillet(B.Vers, 1390.0, 455.0, 380.0)}
        # le passeport
        set S += array{Bloc(Vignette(FeuilleMission.Passeport, 630.0, 500.0), PassX, PassY, 630.0, 500.0, 1)}
        if (Tex := PhotoDe[B.Photo]):
            Cote := 360.0 * PassK
            set S += array{Bloc(Vignette(Tex, Cote, Cote), PassX + 60.0 * PassK, PassY + 190.0 * PassK, Cote, Cote, 2)}
        set S += array{SurPasseport(B.Nom, 470.0, 228.0, 420.0)}
        set S += array{SurPasseport(B.Numero, 900.0, 228.0, 340.0)}
        set S += array{SurPasseport(B.Prenom, 470.0, 348.0, 700.0)}
        set S += array{SurPasseport(B.Pays, 470.0, 468.0, 420.0)}
        set S += array{SurPasseport(B.Sexe, 900.0, 468.0, 200.0)}
        set S += array{SurPasseport(B.Naissance, 470.0, 588.0, 420.0)}
        set S += array{SurPasseport(B.Expiration, 900.0, 588.0, 340.0)}
        set S += array{SurPasseport(B.Mrz1, 60.0, 800.0, 1140.0)}
        set S += array{SurPasseport(B.Mrz2, 60.0, 880.0, 1140.0)}
        # le tampon, ou les boutons
        if (B.Decision = 1):
            set S += array{Bloc(Vignette(FeuilleMission.TamponOk, 400.0, 228.0), 460.0, 316.0, 400.0, 228.0, 6)}
        else if (B.Decision = 2):
            set S += array{Bloc(Vignette(FeuilleMission.TamponRefus, 400.0, 228.0), 460.0, 316.0, 400.0, 228.0, 6)}
        if (B.Decision = 0):
            set S += BoutonEcran("VALID", "16A34A", 620.0, 760.0, 300.0, 70.0, 1)
            set S += BoutonEcran("REFUSE", "DC2626", 1000.0, 760.0, 300.0, 70.0, 2)
            set S += Regles()
        else:
            set S += array{Bloc(Ecrit("Documents already checked.", "CBD5E1", text_justification.Center), 0.0, 780.0, 1920.0, 30.0, 3)}
        set S += BoutonEcran("CLOSE", "374151", 1700.0, 30.0, 180.0, 48.0, 3)
        S

    # Le règlement affiché sous les boutons : ce qu'il faut comparer. Seules les règles du niveau
    # actuel du cerveau sont montrées (au début : visage, vol, destination).
    Regles():[]canvas_slot =
        N := NiveauActuel()
        Toutes := array:
            "1. FACE: passport photo = the passenger"
            "2. FLIGHT: ticket flight = this flight"
            "3. DESTINATION: ticket TO = this flight"
            "4. DATE: ticket date = today"
            "5. NAMES: ticket name = passport name"
            "6. PASSPORT: not expired, right sex"
            "7. PASSPORT No. = number in the bottom strip"
        Niveaux := array{1, 1, 1, 2, 2, 2, 3}
        Visibles := for (I -> R : Toutes, Nv := Niveaux[I], Nv <= N) { R }
        var S:[]canvas_slot = array{}
        Rangees := if (Q := Quotient[Visibles.Length + 1, 2]) then Q * 1.0 else 1.0
        set S += array{Bloc(color_block{DefaultColor := MakeColorFromHex("0F172A"), DefaultOpacity := 0.85}, 460.0, 850.0, 1000.0, 50.0 + Rangees * 30.0, 1)}
        set S += array{Bloc(Ecrit("CHECK THAT EVERYTHING MATCHES - ONE MISTAKE = REFUSE", "FBBF24", text_justification.Center), 460.0, 856.0, 1000.0, 30.0, 3)}
        for (I -> R : Visibles):
            Colonne := if (Mod[I, 2] = 0) then 0.0 else 500.0
            Ligne := if (L := Quotient[I, 2]) then L * 1.0 else 0.0
            set S += array{Bloc(Ecrit(R, "E2E8F0", text_justification.Left), 490.0 + Colonne, 890.0 + Ligne * 30.0, 480.0, 30.0, 3)}
        S

    # Une valeur écrite sur le billet / le passeport (X, Y en pixels de l'image).
    SurBillet(Texte:string, X:float, Y:float, L:float):canvas_slot =
        Bloc(Ecrit(Texte, "111827", text_justification.Left), BilletX + X * BilletK, BilletY + Y * BilletK, L * BilletK, 30.0, 3)

    SurPasseport(Texte:string, X:float, Y:float, L:float):canvas_slot =
        Bloc(Ecrit(Texte, "1F2937", text_justification.Left), PassX + X * PassK, PassY + Y * PassK, L * PassK, 30.0, 3)
