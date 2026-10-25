"""INTERIEUR des avions 1 (1 | 1), 2 (2 | 2), 2 Business, 3 (3 | 3 | 3) et le BAS de l'avion 4 :
tous les meubles, CHACUN UN OBJET SEPARE, deja places dans le repere de l'avion (meme origine).

L'avion reste UN seul objet (son GLB ne change pas). Ici, uniquement ce qui se pose dedans :
  - Rangees de sieges : une rangee = 1 objet par cote (Rangee01_G, Rangee01_D...) ; le siege bleu du jeu
  - Ecrans_RangeeXX : les ecrans au dos des sieges d'une rangee (amelioration SCREENS)
  - Business (coques) et First (suites) pour les grands avions
  - CUISINE (galley) : comptoir inox avec 2 chariots, et UN APPAREIL PAR PRODUIT de la boutique SUPPLIES
    (fontaine a eau, machine a soda, vitrine a croissants, frigo a sandwichs, machine a cafe, four a
    burgers, aquarium a homards, coffre-fort a caviar) : la deco "utile", elle apparait quand on
    debloque le produit
  - TOILETTES : cuvette, lavabo, miroir (gauche et droite)
  - ENTREE : plantes, tapis WELCOME, ecran d'accueil
Repere : celui de l'avion (glTF : metres, Y en haut, l'avant de l'avion vers -Z).

Usage : python3 generate_interieurs.py    (ecrit Modeles/Interieurs/Interieur_AvionX.glb + les apercus)
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.transformations import rotation_matrix, scale_matrix, translation_matrix

import generate_etage_salon as S
from generate_etage_salon import M, exporter, palmier, verifier as _v
from generate_siege_business_v2 import bruit, mat, pose, rbox, tex_uni, uv_boite, cylindre

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
SORTIE = os.path.join(MOD, "Interieurs")
POLICE = os.path.join(os.path.dirname(MOD), "Outils", "TitanOne-Regular.ttf")


# ------------------------------------------------------------------ materiaux en plus
def tex_inox(n=512):
    b = bruit(n, 4, 2)
    lignes = np.repeat(np.random.default_rng(1).random((n, 1)), n, 1) * 0.06
    c = np.array([196, 200, 206]) * (0.92 + 0.05 * b + lignes)[..., None]
    return np.clip(c, 0, 255).astype(np.uint8)


def tex_tapis_welcome():
    W, H = 1024, 512
    im = Image.new("RGB", (W, H), (22, 96, 66))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([18, 18, W - 18, H - 18], 40, outline=(214, 184, 128), width=16)
    d.rounded_rectangle([52, 52, W - 52, H - 52], 26, outline=(214, 184, 128), width=5)
    f = ImageFont.truetype(POLICE, 170)
    d.text((W / 2, H / 2 + 6), "WELCOME", font=f, fill=(255, 255, 255), anchor="mm", stroke_width=10,
           stroke_fill=(16, 40, 30))
    a = np.asarray(im).astype(float) * (0.92 + 0.08 * bruit(512, 6, 2)[:, :, None].repeat(2, 1)[:, :W])
    return np.clip(a, 0, 255).astype(np.uint8)


def tex_ecran_accueil():
    W, H = 1024, 576
    g = np.linspace(0, 1, H)[:, None, None]
    c = np.array([18, 120, 80]) * (1 - g) + np.array([8, 50, 34]) * g
    im = Image.fromarray(np.repeat(c, W, 1).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.text((W / 2, H * 0.36), "WELCOME", font=ImageFont.truetype(POLICE, 150), fill="white", anchor="mm",
           stroke_width=9, stroke_fill=(10, 30, 22))
    d.text((W / 2, H * 0.68), "ENJOY YOUR FLIGHT", font=ImageFont.truetype(POLICE, 70), fill=(190, 255, 220),
           anchor="mm", stroke_width=6, stroke_fill=(10, 30, 22))
    return np.asarray(im)


def transparent(nom, rgb, alpha, rough=0.05, emissive=None):
    m = mat(nom, tex_uni(rgb), rough, 0.0, emissive)
    m.alphaMode = "BLEND"
    m.baseColorFactor = [1.0, 1.0, 1.0, alpha]
    return m


M.update({
    "inox": mat("InoxBrosse", tex_inox(), 0.35, 0.9),
    "blanc_mat": mat("PlastiqueBlanc", tex_uni((236, 238, 240)), 0.45),
    "vert_vif": mat("VertBrillant", tex_uni((30, 170, 90)), 0.25),
    "vitre": transparent("VitreClaire", (210, 235, 245), 0.22, 0.02),
    "eau_aquarium": transparent("EauAquarium", (60, 170, 210), 0.45, 0.02, [0.02, 0.10, 0.14]),
    "bleu_eau": mat("BonbonneBleue", tex_uni((90, 170, 230)), 0.05),
    "sable": mat("SableAquarium", tex_uni((222, 200, 160), var=0.15), 0.9),
    "miroir": mat("Miroir", tex_uni((225, 235, 240)), 0.02, 1.0),
    "brun_cafe": mat("Cafe", tex_uni((90, 52, 30)), 0.3),
    "welcome": mat("TapisWelcome", tex_tapis_welcome(), 1.0),
    "accueil": mat("EcranAccueil", tex_ecran_accueil(), 0.1, 0.0, [0.25, 0.4, 0.3]),
})


_CACHE = {}


def charger(chemin):
    if chemin not in _CACHE:
        sc = trimesh.load(chemin, force="scene")
        lst = [(sc.geometry[g], M0) for node in sc.graph.nodes_geometry for M0, g in [sc.graph[node]]]
        for m, _ in lst:
            m.merge_vertices()                       # sommets en double soudes (fichier plus leger)
        _CACHE[chemin] = lst
    return _CACHE[chemin]


# ------------------------------------------------------------------ les meubles d'un avion
class Interieur:
    """Tous les meubles d'un avion. meuble(nom) commence un nouvel objet ; tout ce qui suit lui appartient."""

    def __init__(self, nom):
        self.nom, self.meubles, self.ext, self.courant = nom, {}, {}, None

    def meuble(self, nom):
        assert nom not in self.meubles, nom
        self.courant = nom
        self.meubles[nom], self.ext[nom] = {}, []

    def add(self, k, m, echelle=1.0):
        self.meubles[self.courant].setdefault(k, []).append(uv_boite(m, echelle))

    def boite(self, k, l, h, e, x, y, z, r=0.01, echelle=1.0, rx=0.0, ry=0.0, bombe=0.0):
        n = 3 if (r >= 0.02 or bombe) else 2
        self.add(k, pose(rbox(l, h, e, r, bombe, n), rx, ry, (x, y, z)), echelle)

    def cyl(self, k, r, h, x, y, z, axe=(0, 1, 0), sec=24, echelle=1.0):
        self.add(k, cylindre(r, h, (x, y, z), axe, sec), echelle)

    def quad(self, k, coins):
        """Rectangle texture (image entiere) : coins = 4 points (bas-gauche, bas-droite, haut-droite, haut-gauche)."""
        v = np.array(coins, float)
        m = trimesh.Trimesh(v, [[0, 1, 2], [0, 2, 3]], process=False)
        n = np.repeat(m.face_normals[:1], 4, 0)
        m.metadata["uv"] = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
        m.metadata["normales"] = n
        self.meubles[self.courant].setdefault(k, []).append(m)

    def externe(self, chemin, T):
        """Copie d'un modele : la geometrie est recopiee, les MATERIAUX (et leurs images) sont partages,
        pour que le fichier ne contienne chaque texture qu'une fois."""
        for m0, M0 in charger(chemin):
            m = trimesh.Trimesh(trimesh.transform_points(m0.vertices, T @ M0), m0.faces, process=False)
            m.visual = trimesh.visual.TextureVisuals(uv=m0.visual.uv, material=m0.visual.material) \
                if getattr(m0.visual, "uv", None) is not None else m0.visual.copy()
            self.ext[self.courant].append(m)

    def sommets(self, nom):
        v = [p.vertices for lst in self.meubles[nom].values() for p in lst] + [m.vertices for m in self.ext[nom]]
        return np.vstack(v)

    def scene(self):
        sc = trimesh.Scene()
        for nom, pieces in self.meubles.items():
            for k, lst in pieces.items():
                m = trimesh.util.concatenate(lst)
                m = trimesh.Trimesh(m.vertices, m.faces, process=False,
                                    vertex_normals=np.vstack([p.metadata["normales"] for p in lst]))
                m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([p.metadata["uv"] for p in lst]), material=M[k])
                m.merge_vertices()
                sc.add_geometry(m, node_name=f"{nom}__{M[k].name}", geom_name=f"{nom}__{M[k].name}")
            for i, m in enumerate(self.ext[nom]):
                sc.add_geometry(m, node_name=f"{nom}__ext{i}", geom_name=f"{nom}__ext{i}")
        return sc


# ------------------------------------------------------------------ sieges
SIEGE = os.path.join(MOD, "siege.glb")                       # le siege bleu du jeu (0,6 m de large)
DEMI_TOUR = rotation_matrix(np.pi, [0, 1, 0])                  # le modele regarde +Z : on le tourne vers l'avant (-Z)
PAS = 0.80                                                     # distance entre 2 rangees (eco)
AV_SIEGE, AR_SIEGE = -0.27, 0.37                               # avant / arriere du siege tourne (z)


def dos_siege():
    """Point et normale du dos du siege (tourne vers l'avant), a 0,95 m : la ou va l'ecran."""
    m = trimesh.load(SIEGE, force="scene").to_geometry()
    m.apply_transform(DEMI_TOUR)
    from trimesh.ray.ray_pyembree import RayMeshIntersector
    loc, _, tri = RayMeshIntersector(m).intersects_location([[0, 0.95, 2.0]], [[0, 0, -1]], multiple_hits=False)
    return loc[0], m.face_normals[tri[0]]


DOS, NORMALE_DOS = dos_siege()


def rangees(I, zone, xs, n_max=99, ecrans=True, num0=1):
    """Rangees eco de zone = (z avant, z arriere) en glTF ; xs = centres des sieges d'un cote (x > 0)."""
    z_av, z_ar = zone
    i = 0
    num = num0
    while True:
        zc = z_av + 0.36 - AV_SIEGE + i * PAS
        if zc + AR_SIEGE > z_ar - 0.08 or i >= n_max:
            break
        for cote, s in (("G", -1), ("D", 1)):
            I.meuble(f"Rangee{num:02d}_{cote}")
            for x in xs:
                I.externe(SIEGE, translation_matrix([s * x, 0, zc]) @ DEMI_TOUR)
        if ecrans:
            I.meuble(f"Ecrans_Rangee{num:02d}")
            for s in (-1, 1):
                for x in xs:
                    ecran_dos(I, s * x, zc)
        i += 1
        num += 1
    return num


def ecran_dos(I, x, z):
    """Ecran noir encastre dans le dos d'un siege (cadre noir + dalle), incline comme le dossier."""
    p = DOS + [x, 0, z]
    ang = np.degrees(np.arctan2(NORMALE_DOS[1], NORMALE_DOS[2]))      # inclinaison du dossier
    for k, (l, h, e, dz) in (("noir", (0.27, 0.18, 0.02, 0.008)), ("ecran", (0.245, 0.155, 0.004, 0.019))):
        b = rbox(l, h, e, 0.008 if k == "noir" else 0.003, 0, 2)
        b.apply_transform(rotation_matrix(np.radians(-ang), [1, 0, 0]))
        b.apply_translation(p + NORMALE_DOS * dz)
        I.add(k, b)


def business(I, zone, xs_cotes, pas=1.95):
    """Coques Business (siege_business_*.glb) : xs_cotes = [(x, 'droite'/'gauche'), ...]."""
    z_av, z_ar = zone
    n = 0
    z = z_av + 0.15 + 0.875
    while z + 0.875 < z_ar - 0.05:
        for x, cote in xs_cotes:
            n += 1
            I.meuble(f"Business{n:02d}")
            I.externe(os.path.join(HERE, f"siege_business_{cote}_leger.glb"), translation_matrix([x, 0, z]))
        z += pas


def first(I, z_rangees, suites):
    n = 0
    for z in z_rangees:
        for x, cote in suites:
            n += 1
            I.meuble(f"First{n:02d}")
            I.externe(os.path.join(HERE, f"suite_first_{cote}.glb"), translation_matrix([x, 0, z]))


# ------------------------------------------------------------------ cuisine : comptoir + appareils
def chariot(I, x, z):
    """Chariot de service (modele du jeu), range dans le comptoir, poignee vers l'allee."""
    I.externe(os.path.join(MOD, "Chariot", "Chariot.glb"),
              translation_matrix([x, 0, z]) @ rotation_matrix(np.pi / 2 * np.sign(x), [0, 1, 0]))


def produit(I, nom, taille, x, y, z, ry=0.0):
    """Pose un produit du jeu (Modeles/Produits) a la bonne taille (taille = sa plus grande dimension)."""
    chemin = os.path.join(MOD, "Produits", nom + ".glb")
    sc = trimesh.load(chemin, force="scene")
    b = sc.bounds
    k = taille / float((b[1] - b[0]).max())
    centre = (b[0] + b[1]) / 2
    T = translation_matrix([x, y, z]) @ rotation_matrix(np.radians(ry), [0, 1, 0]) @ scale_matrix(k) @ \
        translation_matrix([-centre[0], -b[0][1], -centre[2]])
    I.externe(chemin, T)


def cuisine(I, z_av, z_ar, fx, sens=1):
    """Galley contre la paroi (cote sens) : x de sens*(fx-0.62) a sens*fx ; z de z_av (avant) a z_ar."""
    xi, xm = sens * (fx - 0.62), sens * (fx - 0.31)          # bord interieur, milieu du comptoir
    L = z_ar - z_av
    zc = (z_av + z_ar) / 2
    H = 0.95
    # --- comptoir inox : caissons, plan de travail ; une baie ouverte pour 2 chariots, une niche pour le coffre
    baie, niche = (z_av + 0.02, z_av + 0.84), (z_ar - 0.60, z_ar - 0.04)
    I.meuble("Comptoir")
    meuble_bas(I, z_av, z_ar, fx, sens, [baie, niche], H)
    for k in range(2):
        I.meuble(f"Chariot_{k + 1}")
        chariot(I, sens * (fx - 0.32), baie[0] + 0.21 + k * 0.40)
    # --- coffre-fort (CAVIAR) dans sa niche
    zs = (niche[0] + niche[1]) / 2
    I.meuble("CoffreFort")
    I.boite("vert_vif", 0.50, 0.62, 0.50, xm - sens * 0.02, 0.37, zs, 0.03, 0.5)
    I.boite("noir", 0.02, 0.50, 0.40, xi + sens * 0.04 - sens * 0.01, 0.37, zs, 0.01)
    I.boite("vert_vif", 0.02, 0.46, 0.36, xi + sens * 0.04 - sens * 0.02, 0.37, zs, 0.01)
    I.cyl("or", 0.065, 0.03, xi, 0.42, zs + 0.06, axe=(1, 0, 0), sec=32)
    I.cyl("noir", 0.03, 0.035, xi, 0.42, zs + 0.06, axe=(1, 0, 0))
    I.boite("or", 0.03, 0.025, 0.12, xi, 0.30, zs - 0.08, 0.008)
    # liasses de billets posees sur le coffre
    for j in range(3):
        I.boite("vert_vif", 0.14, 0.03, 0.07, xm - sens * 0.02, 0.695 + j * 0.032, zs + 0.06 * (j - 1), 0.004)
        I.boite("blanc_mat", 0.03, 0.031, 0.072, xm - sens * 0.02, 0.695 + j * 0.032, zs + 0.06 * (j - 1), 0.002)
    # --- les appareils sur le plan de travail, de l'avant vers l'arriere
    y0 = H + 0.04
    z = z_av + 0.04
    largeurs = [("MachineCafe", 0.34), ("FontaineEau", 0.30), ("MachineSoda", 0.42), ("VitrineCroissants", 0.48),
                ("FrigoSandwichs", 0.46), ("FourBurgers", 0.50)]
    reste = L - 0.08 - sum(w for _, w in largeurs)
    gap = reste / (len(largeurs) - 1)
    for nom, w in largeurs:
        I.meuble(nom)
        APPAREILS[nom](I, xm - sens * 0.02, y0, z + w / 2, sens)
        z += w + gap


def meuble_bas(I, z0, z1, fx, sens, ouvertures, H=0.95):
    """Meuble bas inox contre la paroi (profondeur 0,62 m) : caissons avec portes, plan de travail,
    plinthe ; les ouvertures [(za, zb)] restent vides (fond sombre, sol, montants) pour les chariots etc."""
    xm, xi = sens * (fx - 0.31), sens * (fx - 0.62)
    I.boite("inox", 0.64, 0.04, z1 - z0, xm - sens * 0.01, H + 0.02, (z0 + z1) / 2, 0.006, 0.6)
    bornes = [z0] + [v for o in sorted(ouvertures) for v in o] + [z1]
    for a, b in zip(bornes[0::2], bornes[1::2]):                     # caissons pleins
        if b - a < 0.05:
            continue
        I.boite("inox", 0.60, H - 0.06, b - a, xm, (H - 0.06) / 2 + 0.06, (a + b) / 2, 0.008, 0.6)
        I.boite("noir", 0.56, 0.06, b - a - 0.02, xm, 0.03, (a + b) / 2, 0.004)
        for zz in np.arange(a, b - 0.2, 0.42):
            zp = min(zz + 0.42, b)
            I.boite("noir", 0.004, 0.72, 0.004, xi - sens * 0.002, 0.46, zp - 0.002, 0.001)
            I.boite("chrome", 0.025, 0.012, 0.14, xi - sens * 0.016, 0.82, (zz + zp) / 2, 0.004)
    for a, b in ouvertures:                                           # baies ouvertes
        I.boite("noir", 0.02, H - 0.02, b - a, sens * (fx - 0.03), (H - 0.02) / 2, (a + b) / 2, 0.004)
        I.boite("inox", 0.60, 0.02, b - a, xm, 0.01, (a + b) / 2, 0.004)
        for zz in (a, b):
            I.boite("inox", 0.60, H, 0.02, xm, H / 2, zz, 0.004)


def rangement_chariots(I, z0, z1, fx, sens, k):
    """Meuble inox bas contre la paroi : 2 chariots ranges dedans, plan de travail, bac a glace."""
    xm = sens * (fx - 0.31)
    zc = (z0 + z1) / 2
    meuble_bas(I, z0, z1, fx, sens, [(zc - 0.41, zc + 0.41)], 0.95)
    for j in range(2):
        chariot(I, sens * (fx - 0.32), zc - 0.20 + j * 0.40)
    I.boite("inox", 0.40, 0.10, 0.50, xm, 1.04, zc, 0.01, 0.6)                         # bac a glace
    I.boite("vitre", 0.36, 0.02, 0.46, xm, 1.08, zc, 0.006)


def machine_cafe(I, x, y, z, s):
    I.boite("noir", 0.40, 0.42, 0.32, x, y + 0.21, z, 0.03)
    I.boite("inox", 0.38, 0.08, 0.30, x, y + 0.46, z, 0.02, 0.5)
    I.boite("inox", 0.02, 0.10, 0.20, x - s * 0.205, y + 0.33, z, 0.008)              # tete
    for dz in (-0.05, 0.05):
        I.cyl("chrome", 0.012, 0.05, x - s * 0.22, y + 0.25, z + dz)
    I.boite("chrome", 0.14, 0.01, 0.22, x - s * 0.17, y + 0.02, z, 0.004)              # grille
    I.cyl("blanc_mat", 0.035, 0.08, x - s * 0.20, y + 0.07, z)                         # tasse
    I.cyl("brun_cafe", 0.031, 0.002, x - s * 0.20, y + 0.110, z)
    I.boite("ecran", 0.005, 0.06, 0.12, x - s * 0.203, y + 0.40, z, 0.002)
    for dz in (-0.08, 0.08):
        I.cyl("vert_vif", 0.012, 0.01, x - s * 0.205, y + 0.30, z + dz, axe=(1, 0, 0))


def fontaine_eau(I, x, y, z, s):
    I.boite("blanc_mat", 0.36, 0.30, 0.28, x, y + 0.15, z, 0.03)
    I.boite("noir", 0.02, 0.10, 0.16, x - s * 0.18, y + 0.16, z, 0.01)
    I.cyl("chrome", 0.010, 0.04, x - s * 0.17, y + 0.19, z - 0.04)
    I.cyl("chrome", 0.010, 0.04, x - s * 0.17, y + 0.19, z + 0.04)
    I.boite("chrome", 0.10, 0.01, 0.18, x - s * 0.15, y + 0.05, z, 0.003)
    I.cyl("bleu_eau", 0.11, 0.30, x, y + 0.46, z, sec=32)                              # bonbonne
    I.cyl("bleu_eau", 0.04, 0.05, x, y + 0.325, z)
    I.cyl("blanc_mat", 0.112, 0.02, x, y + 0.53, z, sec=32)


def machine_soda(I, x, y, z, s):
    I.boite("vert_vif", 0.44, 0.56, 0.40, x, y + 0.28, z, 0.03)
    I.boite("blanc_mat", 0.02, 0.18, 0.34, x - s * 0.22, y + 0.43, z, 0.01)            # panneau
    I.boite("noir", 0.02, 0.16, 0.30, x - s * 0.225, y + 0.16, z, 0.01)                # niche
    for dz in (-0.09, 0.0, 0.09):
        I.cyl("chrome", 0.012, 0.05, x - s * 0.19, y + 0.215, z + dz)
        I.cyl("rouge", 0.025, 0.01, x - s * 0.232, y + 0.40, z + dz, axe=(1, 0, 0))
    I.boite("chrome", 0.14, 0.01, 0.32, x - s * 0.16, y + 0.03, z, 0.003)
    for dz in (-0.06, 0.06):
        produit(I, "Canette_Soda", 0.11, x - s * 0.17, y + 0.04, z + dz)


def vitrine_croissants(I, x, y, z, s):
    I.boite("noyer", 0.44, 0.05, 0.44, x, y + 0.025, z, 0.01, 0.6)
    I.boite("vitre", 0.42, 0.005, 0.42, x, y + 0.27, z, 0.002)
    for dx in (-1, 1):                                                                   # vitres
        I.boite("vitre", 0.004, 0.22, 0.42, x + dx * 0.21, y + 0.16, z, 0.001)
        I.boite("vitre", 0.42, 0.22, 0.004, x, y + 0.16, z + dx * 0.21, 0.001)
    I.boite("chrome", 0.44, 0.012, 0.44, x, y + 0.276, z, 0.003)
    I.boite("blanc_mat", 0.36, 0.01, 0.36, x, y + 0.055, z, 0.003)
    for i, (dx, dz, a) in enumerate(((-0.09, -0.09, 20), (0.08, -0.08, -30), (-0.08, 0.09, 60), (0.09, 0.08, 10),
                                     (0.0, 0.0, 90))):
        produit(I, "Croissant", 0.12, x + dx, y + 0.06, z + dz, a)


def frigo_sandwichs(I, x, y, z, s):
    # caisson creux (dos, cotes, dessus, dessous) ouvert devant, porte vitree
    I.boite("inox", 0.04, 0.50, 0.44, x + s * 0.21, y + 0.25, z, 0.01, 0.5)
    for dz in (-1, 1):
        I.boite("inox", 0.46, 0.50, 0.03, x, y + 0.25, z + dz * 0.205, 0.01, 0.5)
    I.boite("inox", 0.46, 0.06, 0.44, x, y + 0.47, z, 0.01, 0.5)
    I.boite("inox", 0.46, 0.04, 0.44, x, y + 0.02, z, 0.01, 0.5)
    I.boite("noir", 0.40, 0.42, 0.38, x + s * 0.18, y + 0.25, z, 0.004)          # fond sombre
    I.boite("vitre", 0.006, 0.40, 0.38, x - s * 0.226, y + 0.25, z, 0.002)
    I.boite("lumiere", 0.30, 0.008, 0.34, x, y + 0.465, z, 0.002)
    for yy in (0.08, 0.25):
        I.boite("chrome", 0.38, 0.008, 0.38, x - s * 0.02, y + yy, z, 0.002)
        for dz in (-0.11, 0.0, 0.11):
            produit(I, "Sandwich", 0.10, x - s * 0.08, y + yy + 0.005, z + dz)
    I.boite("chrome", 0.02, 0.24, 0.02, x - s * 0.25, y + 0.25, z + 0.15, 0.008)


def four_burgers(I, x, y, z, s):
    I.boite("inox", 0.48, 0.38, 0.46, x, y + 0.19, z, 0.02, 0.5)
    I.boite("noir", 0.02, 0.26, 0.32, x - s * 0.235, y + 0.17, z - 0.04, 0.01)
    I.boite("vitre", 0.005, 0.20, 0.26, x - s * 0.245, y + 0.17, z - 0.04, 0.002)
    I.boite("lumiere", 0.30, 0.005, 0.24, x, y + 0.27, z - 0.04, 0.002)
    I.boite("chrome", 0.025, 0.02, 0.26, x - s * 0.255, y + 0.32, z - 0.04, 0.006)
    I.boite("noir", 0.01, 0.30, 0.08, x - s * 0.24, y + 0.19, z + 0.17, 0.004)
    for yy in (0.28, 0.20, 0.12):
        I.cyl("chrome", 0.018, 0.02, x - s * 0.25, y + yy, z + 0.17, axe=(1, 0, 0))
    I.boite("ecran", 0.004, 0.03, 0.06, x - s * 0.247, y + 0.34, z + 0.17, 0.001)


def aquarium_homards(I, x0, z0, fx, sens):
    """Aquarium a homards sur son meuble, contre la paroi (cote sens), longueur 0,9 m en z."""
    x = sens * (fx - 0.27)
    I.boite("noyer", 0.50, 0.70, 0.92, x, 0.35, z0, 0.02, 0.6)
    I.boite("or", 0.51, 0.02, 0.93, x, 0.70, z0, 0.006)
    I.boite("noir", 0.50, 0.03, 0.92, x, 0.725, z0, 0.006)
    for dx in (-1, 1):
        I.boite("vitre", 0.006, 0.46, 0.90, x + dx * 0.245, 0.97, z0, 0.002)
    for dz in (-1, 1):
        I.boite("vitre", 0.49, 0.46, 0.006, x, 0.97, z0 + dz * 0.447, 0.002)
    I.boite("eau_aquarium", 0.48, 0.38, 0.88, x, 0.93, z0, 0.004, 1.0)
    I.boite("sable", 0.48, 0.05, 0.88, x, 0.765, z0, 0.01, 0.5)
    I.boite("noir", 0.52, 0.05, 0.94, x, 1.225, z0, 0.01)
    I.boite("lumiere", 0.30, 0.005, 0.70, x, 1.198, z0, 0.002)
    for i, (dx, dz, a) in enumerate(((0.05, -0.2, 30), (-0.06, 0.18, -40))):
        produit(I, "Homard", 0.32, x + dx, 0.80, z0 + dz, a)
    for dx, dz, r in ((0.10, 0.30, 0.07), (-0.08, -0.33, 0.06), (0.12, -0.05, 0.045)):  # rochers
        roc = trimesh.creation.icosphere(1, r)
        roc.apply_scale([1.0, 0.65, 1.2])
        roc.apply_translation([x + dx, 0.80, z0 + dz])
        I.add("noir" if r < 0.05 else "inox", roc, 0.3)
    for k in range(5):                                                                  # algues
        za = z0 - 0.30 + k * 0.15
        xa = x + sens * 0.13
        V, F = [], []
        for t in np.linspace(0, 1, 8):
            c = np.array([xa + 0.02 * np.sin(t * 6 + k), 0.79 + 0.30 * t, za + 0.02 * np.cos(t * 5 + k)])
            w = 0.018 * (1 - t) + 0.004
            V += [c - [0, 0, w], c + [0, 0, w]]
        for j in range(7):
            q = 2 * j
            F += [[q, q + 1, q + 3], [q, q + 3, q + 2], [q, q + 3, q + 1], [q, q + 2, q + 3]]
        I.add("feuille", trimesh.Trimesh(np.array(V), np.array(F), process=False), 0.3)
    for i in range(10):                                                                # bulles
        b = trimesh.creation.icosphere(1, 0.008 + 0.004 * (i % 3))
        b.apply_translation([x - sens * 0.12, 0.82 + i * 0.035, z0 + 0.32 + 0.01 * np.sin(i)])
        I.add("vitre", b)
    I.boite("noir", 0.04, 0.14, 0.04, x - sens * 0.12, 0.84, z0 + 0.32, 0.01)


APPAREILS = {"MachineCafe": machine_cafe, "FontaineEau": fontaine_eau, "MachineSoda": machine_soda,
             "VitrineCroissants": vitrine_croissants, "FrigoSandwichs": frigo_sandwichs, "FourBurgers": four_burgers}


# ------------------------------------------------------------------ toilettes
def toilettes(I, z_av, z_ar):
    """2 cabines : x de -1,24 a 0 et de 0 a 1,24 ; z_av = face de la cloison avant, z_ar = paroi arriere."""
    for cx, cote in ((-0.62, "G"), (0.62, "D")):
        s = np.sign(cx)
        I.meuble(f"WC_{cote}")
        x = cx + 0.15 if cx < 0 else cx - 0.15
        I.externe(os.path.join(HERE, "toilettes.glb"),
                  translation_matrix([x, 0.0, z_ar - 0.60]) @ rotation_matrix(np.pi, [0, 1, 0]) @ scale_matrix(0.09))
        I.meuble(f"Lavabo_{cote}")
        zl = z_ar - 0.55
        I.externe(os.path.join(MOD, "Lavabo", "Lavabo.glb"),
                  translation_matrix([s * 1.21, 0, zl]) @ rotation_matrix(-np.pi / 2 * s, [0, 1, 0]))
        I.meuble(f"Miroir_{cote}")
        I.boite("chrome", 0.02, 0.50, 0.46, s * 1.20, 1.38, zl, 0.008)
        I.boite("miroir", 0.006, 0.46, 0.42, s * 1.19, 1.38, zl, 0.003)
        I.boite("lumiere", 0.03, 0.02, 0.36, s * 1.19, 1.645, zl, 0.005)


# ------------------------------------------------------------------ entree
def plante(I, x, z):
    """Petite plante verte en pot dore (0,9 m)."""
    I.cyl("or", 0.17, 0.32, x, 0.16, z, sec=32)
    an = trimesh.creation.annulus(0.15, 0.18, 0.035, sections=32)
    an.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    an.apply_translation([x, 0.335, z])
    I.add("noir", an)
    I.cyl("tronc", 0.152, 0.02, x, 0.33, z, sec=32)
    rng = np.random.default_rng(int(abs(x * 100 + z * 10)))
    for i in range(14):                                                                # feuilles
        a = rng.uniform(0, 2 * np.pi)
        lg = rng.uniform(0.28, 0.42)
        d = np.array([np.cos(a), 0, np.sin(a)])
        lat = np.cross(d, [0, 1, 0])
        base = np.array([x, 0.34, z])
        V, F = [], []
        for t in np.linspace(0, 1, 7):
            c = base + d * lg * 0.55 * t + np.array([0, lg * (1.2 * t - 0.55 * t * t), 0])
            w = 0.055 * np.sin(np.pi * min(1, t * 1.1)) + 0.004
            V += [c - lat * w, c + lat * w]
        for j in range(6):
            q = 2 * j
            F += [[q, q + 1, q + 3], [q, q + 3, q + 2], [q, q + 3, q + 1], [q, q + 2, q + 3]]
        I.add("feuille", trimesh.Trimesh(np.array(V), np.array(F), process=False), 0.3)


def tapis(I, x, z, l=1.30, p=0.70, retourne=False):
    """Tapis WELCOME ; retourne=True : le texte se lit en venant de l'avant de l'avion."""
    I.boite("noir", l + 0.02, 0.006, p + 0.02, x, 0.003, z, 0.002)
    y = 0.0075
    c = [(x - l / 2, y, z + p / 2), (x + l / 2, y, z + p / 2), (x + l / 2, y, z - p / 2), (x - l / 2, y, z - p / 2)]
    I.quad("welcome", c[2:] + c[:2] if retourne else c)


def ecran_accueil(I, x, z, sens_z=1):
    """Ecran plat sur une cloison, face vers +Z (sens_z=1) ou -Z."""
    l, h, y = 0.80, 0.45, 1.55
    I.boite("noir", l + 0.04, h + 0.04, 0.035, x, y, z + sens_z * 0.0175, 0.01)
    zf = z + sens_z * 0.036
    a, b = (x - l / 2, x + l / 2) if sens_z > 0 else (x + l / 2, x - l / 2)
    I.quad("accueil", [(a, y - h / 2, zf), (b, y - h / 2, zf), (b, y + h / 2, zf), (a, y + h / 2, zf)])


# ------------------------------------------------------------------ les avions
CUISINE_Z = (-14.59, -11.71)            # galley (glTF) : entre les 2 cloisons de la zone equipage
ENTREE_AV = (-11.65, -9.45)             # zone de la porte avant (glTF)


def entree_avant(I, fx, x_porte_cuisine):
    I.meuble("Plante_Avant_G")
    plante(I, -(fx - 0.28), -9.78)
    I.meuble("Plante_Avant_D")
    plante(I, fx - 0.28, -9.78)
    I.meuble("Tapis_Avant")
    tapis(I, 0.0, -10.55)
    I.meuble("Ecran_Accueil")
    xe = 0.55 if x_porte_cuisine < 0 else (1.25 if fx > 2 else 0.0)
    ecran_accueil(I, xe, ENTREE_AV[0], 1)


def entree_arriere(I, z_cabine, z_lav, fx):
    """Zone de la porte arriere : de z_cabine (arriere de la cabine) a z_lav (face des toilettes)."""
    for s, c in ((-1, "G"), (1, "D")):
        I.meuble(f"Plante_Arriere_{c}")
        plante(I, s * (fx - 0.28), z_cabine + 0.33)
    I.meuble("Tapis_Arriere")
    tapis(I, 0.0, (z_cabine + z_lav) / 2, retourne=True)


def avion(nom, fx_cabine, fx_avant, x_porte_cuisine, zones, lav, entree_arr, sens_cuisine=1):
    I = Interieur(nom)
    z_ar_cab = zones["arriere"]
    zones["sieges"](I)
    # cuisine : comptoir contre la paroi droite ; aquarium contre la paroi gauche
    cuisine(I, CUISINE_Z[0] + 0.02, CUISINE_Z[1] - 0.02, fx_avant, sens_cuisine)
    I.meuble("AquariumHomards")
    zq = (CUISINE_Z[0] + CUISINE_Z[1]) / 2
    aquarium_homards(I, 0, zq, fx_avant, -sens_cuisine)
    if fx_avant > 2.0:
        # grande cuisine (gros-porteur) : 2 rangements a chariots de chaque cote de l'aquarium
        for k, (z0, z1) in enumerate(((CUISINE_Z[0] + 0.02, zq - 0.52), (zq + 0.52, CUISINE_Z[1] - 0.02))):
            I.meuble(f"RangementChariots_{k + 1}")
            rangement_chariots(I, z0, z1, fx_avant, -sens_cuisine, k)
    toilettes(I, lav[0], lav[1])
    entree_avant(I, fx_avant, x_porte_cuisine)
    entree_arriere(I, z_ar_cab, lav[0] - 0.06, fx_avant)
    return I


def avion1():
    def sieges(I):
        rangees(I, (-9.45, 0.0), [0.78], ecrans=True)
    return avion("Avion1_1x1", 1.25, 1.25, -0.75, {"sieges": sieges, "arriere": 0.0}, (2.26, 3.80), True)


def avion2():
    def sieges(I):
        rangees(I, (-9.45, 0.0), [0.65, 1.25])
    return avion("Avion2_2x2", 1.625, 1.25, -0.75, {"sieges": sieges, "arriere": 0.0}, (2.26, 3.80), True)


def avion2_business():
    def sieges(I):
        business(I, (-9.45, -0.97), [(-0.80, "gauche"), (0.80, "droite")])
        rangees(I, (-0.91, 8.48), [0.65, 1.25])
    return avion("Avion2_Business", 1.625, 1.25, -0.75, {"sieges": sieges, "arriere": 8.48}, (10.74, 12.28), True)


def avion3(decale_arriere=0.0, nom="Avion3_3x3x3"):
    def sieges(I):
        first(I, (-8.215, -5.845), [(-2.75, "droite"), (-0.645, "gauche"), (0.645, "droite"), (2.75, "gauche")])
        business(I, (-3.03, 5.39), [(-2.70, "gauche"), (-0.42, "droite"), (0.42, "gauche"), (2.70, "droite")])
        rangees(I, (5.45, 14.84), [2.08, 2.68, 3.28])
        # bloc central de 3 sieges : objets a part (Centre)
        z_av = 5.45
        i = 0
        while True:
            zc = z_av + 0.36 - AV_SIEGE + i * PAS
            if zc + AR_SIEGE > 14.84 - 0.08:
                break
            I.meuble(f"Rangee{i + 1:02d}_Centre")
            for x in (-0.60, 0.0, 0.60):
                I.externe(SIEGE, translation_matrix([x, 0, zc]) @ DEMI_TOUR)
            i += 1
        # ecrans du bloc central : ajoutes aux Ecrans_RangeeXX
        i = 0
        while True:
            zc = z_av + 0.36 - AV_SIEGE + i * PAS
            if zc + AR_SIEGE > 14.84 - 0.08:
                break
            I.courant = f"Ecrans_Rangee{i + 1:02d}"
            for x in (-0.60, 0.0, 0.60):
                ecran_dos(I, x, zc)
            i += 1
    lav = (17.10 + decale_arriere, 18.64 + decale_arriere)
    return avion(nom, 3.549, 3.549, 0.0, {"sieges": sieges, "arriere": 14.84 + decale_arriere}, lav, True)


AVIONS = [(avion1, "avion_niveau1_wc_vides.glb"), (avion2, "avion_niveau2.glb"),
          (avion2_business, "avion_niveau2_business.glb"), (avion3, "avion_niveau3.glb"),
          (lambda: avion3(6.0, "Avion4_Bas"), "avion_niveau4.glb")]


def plan(I, chemin):
    """Vue de dessus de tous les meubles (l'avant a gauche), avec le nom des zones."""
    from generate_plans import vue_dessus, police
    sc = I.scene()
    b = sc.bounds
    z0, z1, demi = b[0][2] - 0.4, b[1][2] + 0.4, max(abs(b[0][0]), abs(b[1][0])) + 0.3
    im = vue_dessus([sc], z0, z1, -demi, demi, 2.2)
    fond = Image.new("RGBA", (im.width + 40, im.height + 110), (238, 244, 241, 255))
    fond.alpha_composite(im, (20, 90))
    d = ImageDraw.Draw(fond)
    d.text((20, 18), f"INTERIEUR {I.nom.upper()} - VU DE DESSUS (AVANT A GAUCHE)", font=police(34), fill=(22, 120, 80))
    fond.convert("RGB").save(chemin)


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    for f, glb in AVIONS:
        I = f()
        out = os.path.join(SORTIE, f"Interieur_{I.nom}.glb")
        plan(I, os.path.join(SORTIE, f"Plan_{I.nom}.png"))
        noms = exporter(I.scene(), out)
        print(f"{I.nom:20s} {len(noms):4d} objets  {os.path.getsize(out) / 1e6:5.1f} Mo   (avion : {glb})")
