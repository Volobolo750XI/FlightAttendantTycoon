"""Etage du haut de l'avion 4 amenage en SALON DE LUXE (style tycoon) : un fichier GLB par objet a acheter.

Chaque objet est deja place dans le repere de avion_niveau4.glb : on l'importe et on le pose a la MEME
position que l'avion (meme origine), il tombe pile a sa place sur le pont superieur.

De l'avant (cinema) vers l'arriere (escalier), en z glTF (l'avant de l'avion est vers -Z) :
  09 Cinema          z -9.4 .. -4.9   grand ecran sur la cloison avant, rideaux, 4 canapes inclinables
  07 Piano           z -3.5 .. -1.4   piano a queue blanc et or + banquette (cote gauche)
  08 Casino          z -3.8 .. -1.7   table de poker, 6 chaises, jetons et cartes (cote droit)
  06 Statue Dollar   z -0.65.. -0.05  "$" geant en or sur socle de marbre
  04 Piscine         z  0.4 ..  5.1   bassin sureleve en mosaique, margelle en marbre, echelle, marches
  05 Transats        z  0.45..  4.75  4 transats + serviettes, de chaque cote de la piscine
  03 Salon           z  5.4 ..  9.3   2 canapes velours, 4 fauteuils, tables basses, tapis, lampes
  02 Bar             z  9.8 .. 14.0   bar central en ilot (marbre / noyer / or), colonne a bouteilles, 9 tabourets
  01 Salon Escalier  z 15.2 .. 20.6   2 canapes de chaque cote de l'escalier, tables, lampes
  10 Lustres         4 lustres en cristal au plafond (escalier, salon, piscine, piano / casino)
  11 Plantes         8 palmiers en pots dores
Repere : metres, Y en haut ; le plancher du pont superieur est a y = UP (3,70).

Usage : python3 generate_etage_salon.py   (ecrit les GLB dans Modeles/Etage/, dont
        Etage_Complet_Tout_Place.glb : les 11 objets ensemble, deja places, en un seul fichier)
"""
import os

import numpy as np
import trimesh
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from trimesh.transformations import rotation_matrix

from generate_siege_business_v2 import bruit, tex_tissu, tex_cuir, tex_uni, mat, uv_boite, rbox, pose, cylindre
from generate_siege_first import tex_noyer, tex_capitonne, M as M_FIRST

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Etage")
UP = 3.70

# profil interieur du pont superieur (x, y) : paroi puis plafond (generate_avion_niveau4.section_haute x 1,05)
PAROI = np.array([(2.73, 0.00), (2.83, 0.35), (2.90, 0.80), (2.91, 1.20), (2.88, 1.52), (2.78, 1.84),
                  (2.57, 2.06), (2.22, 2.16)]) * 1.05
PLAFOND = np.array([(2.22, 2.16), (2.12, 2.27), (1.85, 2.39), (1.40, 2.46), (0.90, 2.49), (0.0, 2.51)]) * 1.05


def x_paroi(y):
    return float(np.interp(y, PAROI[:, 1], PAROI[:, 0]))


def y_plafond(x):
    x = abs(x)
    return float(np.interp(x, PLAFOND[::-1, 0], PLAFOND[::-1, 1]))


# ------------------------------------------------------------------ textures
def tex_marbre(n=512):
    x, y = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n))
    b = bruit(n, 96, 5)
    v1 = np.abs(np.sin((x * 3 + y * 2 + b * 4) * np.pi))
    v2 = np.abs(np.sin((x * 7 - y * 3 + bruit(n, 48, 4) * 6) * np.pi))
    veines = np.exp(-(v1 / 0.05) ** 2) * 0.55 + np.exp(-(v2 / 0.03) ** 2) * 0.25
    base = np.array([242, 240, 236]) * (0.97 + 0.04 * bruit(n, 32, 3))[..., None]
    c = base * (1 - veines[..., None]) + np.array([150, 150, 156]) * veines[..., None]
    return np.clip(c, 0, 255).astype(np.uint8)


def tex_mosaique(n=512, pas=32):
    x, y = np.meshgrid(np.arange(n), np.arange(n))
    cellule = (x // pas) * 1000 + (y // pas)
    rng = np.random.default_rng(3)
    teinte = rng.random(cellule.max() + 1)[cellule]
    c = np.array([40, 170, 190]) * (1 - teinte[..., None]) + np.array([20, 120, 160]) * teinte[..., None]
    joint = ((x % pas) < 2) | ((y % pas) < 2)
    c = np.where(joint[..., None], np.array([225, 235, 235]), c)
    return np.clip(c, 0, 255).astype(np.uint8)


def tex_eau(n=512):
    b = bruit(n, 48, 4)
    caust = np.abs(np.sin(b * 18)) ** 6
    c = np.array([40, 190, 205]) * (0.85 + 0.15 * b)[..., None] + np.array([200, 255, 255]) * caust[..., None] * 0.35
    return np.clip(c, 0, 255).astype(np.uint8)


def tex_touches(n=512):
    """Clavier vu du dessus : touches blanches separees par des traits fins (52 touches sur la largeur)."""
    x = np.arange(n)[None, :].repeat(n, 0)
    pas = n / 26
    trait = (x % pas) < 2
    c = np.where(trait[..., None], np.array([90, 90, 90]), np.array([246, 244, 238]))
    return c.astype(np.uint8)


def tex_tapis(n=512):
    """Tapis creme a motif de losanges emeraude tres doux."""
    x, y = np.meshgrid(np.arange(n), np.arange(n))
    u, v = (x + y) % 128 / 128, (x - y) % 128 / 128
    motif = (np.minimum(u, 1 - u) < 0.03) | (np.minimum(v, 1 - v) < 0.03)
    c = np.where(motif[..., None], np.array([60, 120, 92]), np.array([234, 226, 206]))
    c = c * (0.93 + 0.08 * bruit(n, 8, 2))[..., None]
    return np.clip(c, 0, 255).astype(np.uint8)


def tex_feuille(n=256):
    y = np.linspace(0, 1, n)[:, None].repeat(n, 1)
    x = np.linspace(0, 1, n)[None, :].repeat(n, 0)
    nervure = np.exp(-((x - 0.5) / 0.02) ** 2)
    c = np.array([38, 120, 52]) * (0.8 + 0.3 * y)[..., None] * (0.9 + 0.1 * bruit(n, 16, 2))[..., None]
    c = c * (1 - 0.3 * nervure[..., None]) + np.array([150, 190, 110]) * 0.3 * nervure[..., None]
    return np.clip(c, 0, 255).astype(np.uint8)


def tex_tronc(n=256):
    y = np.arange(n)[:, None].repeat(n, 1)
    anneau = ((y % 32) < 5)
    c = np.where(anneau[..., None], np.array([92, 66, 40]), np.array([138, 104, 70]))
    c = c * (0.85 + 0.2 * bruit(n, 16, 3))[..., None]
    return np.clip(c, 0, 255).astype(np.uint8)


M = dict(M_FIRST)
M.update({
    "marbre": mat("MarbreBlanc", tex_marbre(), 0.15),
    "mosaique": mat("MosaiquePiscine", tex_mosaique(), 0.2),
    "eau": mat("EauPiscine", tex_eau(), 0.02, 0.0, [0.02, 0.12, 0.14]),
    "velours": mat("VeloursEmeraude", tex_tissu((22, 98, 68)), 0.95),
    "tissu": mat("TissuIvoire", tex_tissu((230, 222, 204)), 0.9),
    "feutre": mat("FeutreCasino", tex_tissu((18, 110, 60)), 1.0),
    "piano": mat("LaqueBlanchePiano", tex_uni((246, 245, 242), var=0.01), 0.08),
    "touches": mat("ToucheBlanches", tex_touches(), 0.3),
    "tapis": mat("TapisCreme", tex_tapis(), 1.0),
    "feuille": mat("FeuillePalmier", tex_feuille(), 0.7),
    "tronc": mat("TroncPalmier", tex_tronc(), 0.9),
    "rouge": mat("JetonRouge", tex_uni((190, 30, 40)), 0.4),
    "blanc": mat("JetonBlanc", tex_uni((240, 240, 240)), 0.4),
    "ambre": mat("VerreAmbre", tex_uni((150, 80, 20)), 0.05),
    "bouteille": mat("VerreVert", tex_uni((30, 90, 50)), 0.05),
    "chrome": mat("Chrome", tex_uni((215, 218, 222)), 0.08, 1.0),
    "neon": mat("NeonVert", tex_uni((120, 255, 180)), 0.3, 0.0, [0.3, 1.0, 0.6]),
})


# ------------------------------------------------------------------ objet a acheter
class Objet:
    """Un objet a acheter (ex. Transats), fait de plusieurs MEUBLES (ex. Transat_1 ... Transat_4).
    Chaque meuble devient un maillage separe dans le GLB (un noeud = un meuble, plusieurs materiaux)."""

    def __init__(self, nom, principal=None):
        self.nom, self.meubles, self.compte = nom, {}, {}
        if principal:
            self.meuble(principal)

    def meuble(self, nom):
        """Tout ce qui est ajoute ensuite appartient a un nouveau meuble (numerote : Fauteuil_1, Fauteuil_2...)."""
        n = self.compte.get(nom, 0) + 1
        self.compte[nom] = n
        self.courant = (nom, n)
        self.meubles[self.courant] = {}

    def nom_meuble(self, cle):
        nom, n = cle
        return nom if self.compte[nom] == 1 else f"{nom}_{n}"

    @property
    def pieces(self):
        d = {}
        for m in self.meubles.values():
            for k, lst in m.items():
                d.setdefault(k, []).extend(lst)
        return d

    def add(self, k, m, echelle=1.0):
        self.meubles[self.courant].setdefault(k, []).append(uv_boite(m, echelle))

    def boite(self, k, l, h, e, x, y, z, r=0.01, echelle=1.0, rx=0.0, ry=0.0, bombe=0.0):
        n = 3 if (r >= 0.02 or bombe) else 2
        self.add(k, pose(rbox(l, h, e, r, bombe, n), rx, ry, (x, y, z)), echelle)

    def cyl(self, k, r, h, x, y, z, axe=(0, 1, 0), sec=24, echelle=1.0):
        self.add(k, cylindre(r, h, (x, y, z), axe, sec), echelle)

    def extrusion(self, k, poly, y0, y1, echelle=1.0):
        m = trimesh.creation.extrude_polygon(poly, y1 - y0)          # poly dans (x, z) -> extrude vers +Y
        m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))   # (x, y, h) -> (x, h, -y)
        m.apply_transform(np.diag([1, 1, -1, 1]))                   # -> (x, h, y)
        m.invert()
        m.apply_translation([0, y0, 0])
        self.add(k, m, echelle)

    def scene(self, sc=None):
        """Un noeud par (meuble, materiau), nomme "<meuble>__<materiau>" ; exporter() regroupe par meuble."""
        sc = sc if sc is not None else trimesh.Scene()
        prefixe = self.nom.split("_")[0].replace("Etage", "E")
        for cle, pieces in self.meubles.items():
            for k, lst in pieces.items():
                m = trimesh.util.concatenate(lst)
                uv = np.vstack([p.metadata["uv"] for p in lst])
                vn = np.vstack([p.metadata["normales"] for p in lst])
                m = trimesh.Trimesh(m.vertices + [0, UP, 0], m.faces, vertex_normals=vn, process=False)
                m.visual = trimesh.visual.TextureVisuals(uv=uv, material=M[k])
                m.merge_vertices()
                nom = f"{prefixe}_{self.nom_meuble(cle)}__{M[k].name}"
                sc.add_geometry(m, node_name=nom, geom_name=nom)
        return sc

    def sommets(self):
        return np.vstack([p.vertices for lst in self.pieces.values() for p in lst])


def stade(lx, lz, cx=0.0, cz=0.0):
    """Rectangle aux bouts arrondis (vue de dessus), lx < lz."""
    r = lx / 2
    return LineString([(cx, cz - lz / 2 + r), (cx, cz + lz / 2 - r)]).buffer(r, 32)


# ------------------------------------------------------------------ meubles reutilises
def canape(o, x, z, longueur, sens, prof=0.85, k="velours", coussin="tissu"):
    """Canape le long de Z ; sens = +1 : le dossier est cote +X (contre la paroi droite)."""
    xb = x + sens * (prof / 2 - 0.11)                                   # dossier
    o.boite(k, prof, 0.30, longueur, x, 0.22, z, 0.05, 0.5)             # socle
    o.boite(k, 0.22, 0.52, longueur, xb, 0.55, z, 0.07, 0.5, bombe=0.02)
    for s in (-1, 1):                                                    # accoudoirs
        o.boite(k, prof, 0.40, 0.18, x, 0.47, z + s * (longueur / 2 - 0.09), 0.07, 0.5)
    n = max(2, int(round((longueur - 0.36) / 0.7)))
    lc = (longueur - 0.36) / n
    for i in range(n):                                                   # coussins d'assise et de dos
        zc = z - longueur / 2 + 0.18 + lc * (i + 0.5)
        o.boite(coussin, prof - 0.26, 0.14, lc - 0.02, x - sens * 0.08, 0.44, zc, 0.05, 0.4, bombe=0.02)
        o.boite(coussin, 0.14, 0.40, lc - 0.04, xb - sens * 0.17, 0.70, zc, 0.06, 0.4, ry=0, bombe=0.03)
    o.boite("velours", 0.12, 0.30, 0.34, x - sens * 0.05, 0.66, z - longueur / 2 + 0.45, 0.05, 0.3, bombe=0.03)
    o.boite("cuir", 0.12, 0.30, 0.34, x - sens * 0.05, 0.66, z + longueur / 2 - 0.45, 0.05, 0.3, bombe=0.03)
    for dz in (-1, 1):                                                   # pieds dores
        for dx in (-1, 1):
            o.cyl("or", 0.025, 0.08, x + dx * (prof / 2 - 0.08), 0.04, z + dz * (longueur / 2 - 0.08))


def fauteuil(o, x, z, angle, k="velours"):
    """Fauteuil club ; angle (deg) : 0 = il regarde vers +X."""
    def p(m):
        m.apply_transform(rotation_matrix(np.radians(angle), [0, 1, 0]))
        m.apply_translation([x, 0, z])
        return m
    o.add(k, p(pose(rbox(0.72, 0.30, 0.72, 0.06, 0, 3), 0, 0, (0, 0.24, 0))), 0.5)
    o.add(k, p(pose(rbox(0.18, 0.50, 0.72, 0.07, 0.02, 3), 0, 0, (-0.27, 0.56, 0))), 0.5)
    for s in (-1, 1):
        o.add(k, p(pose(rbox(0.66, 0.30, 0.14, 0.06, 0, 3), 0, 0, (0.0, 0.48, s * 0.29))), 0.5)
    o.add("tissu", p(pose(rbox(0.50, 0.12, 0.44, 0.05, 0.02, 3), 0, 0, (0.05, 0.44, 0))), 0.4)
    for dx in (-1, 1):
        for dz in (-1, 1):
            o.add("or", p(cylindre(0.022, 0.09, (dx * 0.28, 0.045, dz * 0.28))))


def table_ronde(o, x, z, r, h, k="marbre"):
    o.cyl(k, r, 0.04, x, h - 0.02, z, sec=48, echelle=0.8)
    o.cyl("or", r + 0.006, 0.012, x, h - 0.042, z, sec=48)
    o.cyl("or", 0.035, h - 0.06, x, (h - 0.06) / 2 + 0.02, z)
    o.cyl("or", r * 0.55, 0.02, x, 0.01, z, sec=36)


def lampe(o, x, z, y0, haute=0.42):
    o.cyl("or", 0.06, 0.015, x, y0 + 0.008, z)
    o.cyl("or", 0.01, haute, x, y0 + haute / 2, z)
    abat = trimesh.creation.cylinder(radius=1.0, height=0.22, sections=32)   # abat-jour tronconique
    v = abat.vertices
    v[:, :2] *= np.where(v[:, 2] > 0, 0.085, 0.135)[:, None]
    abat = trimesh.Trimesh(v[:, [0, 2, 1]] * [1, 1, -1], abat.faces, process=True)
    abat.fix_normals()
    abat.apply_translation([x, y0 + haute + 0.06, z])
    o.add("lumiere", abat)


def verre(o, x, y, z, k="cristal"):
    o.cyl(k, 0.03, 0.006, x, y + 0.003, z)
    o.cyl(k, 0.005, 0.09, x, y + 0.05, z, sec=8)
    o.cyl(k, 0.032, 0.07, x, y + 0.13, z)


def bouteille(o, x, y, z, k="bouteille", h=0.30):
    o.cyl(k, 0.04, h * 0.65, x, y + h * 0.325, z, sec=16)
    o.cyl(k, 0.014, h * 0.30, x, y + h * 0.80, z, sec=10)
    o.cyl("or", 0.016, 0.04, x, y + h * 0.97, z, sec=10)


# ------------------------------------------------------------------ 01 salon de l'escalier
def salon_escalier():
    o = Objet("Etage01_SalonEscalier")
    for s in (-1, 1):
        o.meuble("Canape")
        canape(o, s * 2.36, 17.9, 3.0, s)
        o.meuble("TableBasse")
        table_ronde(o, s * 1.38, 17.9, 0.36, 0.42)
        for dz in (-0.12, 0.12):
            verre(o, s * 1.38 + dz * 0.5, 0.42, 17.9 + dz)
        o.meuble("Lampe")
        o.cyl("or", 0.20, 0.55, s * 2.45, 0.275, 16.05, sec=32)        # gueridon-colonne sous la lampe
        lampe(o, s * 2.45, 16.05, 0.55)
    return o


# ------------------------------------------------------------------ 02 bar
def bar():
    o = Objet("Etage02_Bar", "Bar")
    zc, lx, lz = 12.15, 1.50, 3.40
    corps = stade(lx, lz, 0, zc)
    o.extrusion("noir", stade(lx - 0.10, lz - 0.10, 0, zc), 0.0, 0.10)                 # socle en retrait
    o.extrusion("neon", stade(lx - 0.06, lz - 0.06, 0, zc).difference(stade(lx - 0.12, lz - 0.12, 0, zc)), 0.10, 0.115)
    o.extrusion("noyer", corps, 0.10, 0.98, 0.8)
    o.extrusion("or", stade(lx + 0.10, lz + 0.10, 0, zc), 0.98, 1.00)
    o.extrusion("marbre", stade(lx + 0.24, lz + 0.24, 0, zc), 1.00, 1.05, 0.9)
    o.extrusion("or", stade(lx + 0.25, lz + 0.25, 0, zc).difference(stade(lx + 0.22, lz + 0.22, 0, zc)), 1.002, 1.048)
    # cannelures dorees verticales tout autour du comptoir
    bord = corps.exterior
    for d in np.arange(0, bord.length, 0.16):
        p, q = bord.interpolate(d), bord.interpolate(d + 0.01)
        ang = np.degrees(np.arctan2(q.x - p.x, q.y - p.y))
        o.boite("or", 0.012, 0.70, 0.02, p.x, 0.55, p.y, 0.004, ry=ang)
    # repose-pieds en laiton tout autour
    rp = stade(lx + 0.22, lz + 0.22, 0, zc).exterior
    pts = [rp.interpolate(d) for d in np.linspace(0, rp.length, 120)]
    for a, b in zip(pts[:-1], pts[1:]):
        o.add("or", cylindre(0.018, max(1e-3, a.distance(b)) + 0.004, ((a.x + b.x) / 2, 0.25, (a.y + b.y) / 2),
                             axe=(b.x - a.x, 0, b.y - a.y), sec=10))
    # colonne centrale a bouteilles jusqu'au plafond : etageres en verre, bouteilles, chapiteau dore
    h_pl = y_plafond(0.6) - 0.002
    o.cyl("or", 0.14, h_pl - 1.05, 0, 1.05 + (h_pl - 1.05) / 2, zc, sec=32)
    o.cyl("or", 0.55, 0.06, 0, h_pl - 0.03, zc, sec=48)
    o.cyl("neon", 0.52, 0.01, 0, h_pl - 0.065, zc, sec=48)
    rng = np.random.default_rng(5)
    for y in (1.05, 1.42, 1.79):
        if y > 1.05:
            o.cyl("cristal", 0.48, 0.02, 0, y, zc, sec=48)
            o.cyl("or", 0.485, 0.008, 0, y - 0.014, zc, sec=48)
        for a in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            k = ("ambre", "bouteille", "cristal")[int(rng.integers(3))]
            bouteille(o, 0.36 * np.cos(a), y + 0.01, zc + 0.36 * np.sin(a), k, 0.26 + 0.06 * rng.random())
    # sur le comptoir : verres, seau a glace, shaker
    for z in (10.75, 11.25, 13.05, 13.55):
        for s in (-1, 1):
            verre(o, s * 0.80, 1.05, z)
    o.cyl("or", 0.10, 0.20, -0.62, 1.15, 12.15)
    bouteille(o, -0.62, 1.12, 12.15, "bouteille", 0.30)
    o.cyl("chrome", 0.04, 0.20, 0.62, 1.15, 12.15)
    # tabourets : 4 de chaque cote, 1 a chaque bout
    places = [(s * 1.17, z) for s in (-1, 1) for z in (10.95, 11.75, 12.55, 13.35)] + [(0, 9.98)]          # rien devant l'arrivee de l'escalier
    for x, z in places:
        o.meuble("Tabouret")
        o.cyl("or", 0.21, 0.02, x, 0.01, z, sec=32)
        o.cyl("or", 0.03, 0.72, x, 0.38, z)
        o.add("or", trimesh.creation.annulus(0.17, 0.19, 0.02, sections=32).apply_transform(
            rotation_matrix(np.pi / 2, [1, 0, 0])).apply_translation([x, 0.30, z]))
        o.cyl("cuir_vert", 0.21, 0.09, x, 0.78, z, sec=32)
        o.cyl("or", 0.212, 0.012, x, 0.738, z, sec=32)
        dx, dz = -x, 12.15 - z                                            # dossier bas, dos au comptoir
        n = np.hypot(dx, dz)
        o.boite("cuir_vert", 0.34, 0.20, 0.05, x - dx / n * 0.17, 0.95, z - dz / n * 0.17, 0.02,
                ry=np.degrees(np.arctan2(dx, dz)))
    return o


# ------------------------------------------------------------------ 03 salon
def salon():
    o = Objet("Etage03_Salon")
    zc = 7.35
    for s in (-1, 1):
        o.meuble("Tapis")
        o.boite("or", 2.30, 0.008, 3.40, s * 1.62, 0.004, zc, 0.002)
        o.boite("tapis", 2.22, 0.012, 3.32, s * 1.62, 0.008, zc, 0.003, 1.6)
        o.meuble("Canape")
        canape(o, s * 2.36, zc, 2.4, s)
        o.meuble("TableBasse")
        table_ronde(o, s * 1.50, zc, 0.40, 0.42)
        # sur la table basse : plateau dore, livres, bougie
        o.boite("or", 0.30, 0.01, 0.20, s * 1.50, 0.425, zc - 0.12, 0.004)
        o.boite("cuir_vert", 0.22, 0.04, 0.16, s * 1.50, 0.44, zc + 0.15, 0.005)
        o.boite("cuir", 0.20, 0.03, 0.15, s * 1.50, 0.475, zc + 0.15, 0.005)
        o.cyl("lumiere", 0.035, 0.08, s * 1.50, 0.47, zc - 0.12)
        for dz in (-0.65, 0.65):
            o.meuble("Fauteuil")
            fauteuil(o, s * 0.80, zc + dz * 1.0, 180 if s > 0 else 0)
        for dz in (-1.6, 1.6):
            o.meuble("Lampe")
            table_ronde(o, s * 2.45, zc + dz, 0.20, 0.55)
            lampe(o, s * 2.45, zc + dz, 0.55)
    return o


# ------------------------------------------------------------------ 04 piscine
PISC = (2.60, 4.40, 2.60, 0.55)           # largeur (x), longueur (z), centre z, hauteur du bord


def piscine():
    o = Objet("Etage04_Piscine", "Piscine")
    lx, lz, zc, h = PISC
    ext = Polygon([(-lx / 2, zc - lz / 2), (lx / 2, zc - lz / 2), (lx / 2, zc + lz / 2), (-lx / 2, zc + lz / 2)])
    inte = ext.buffer(-0.15, join_style=2)
    o.extrusion("marbre", ext.difference(inte), 0.0, h - 0.05, 0.9)                     # muret
    o.extrusion("mosaique", inte, 0.0, 0.04, 0.5)                                       # fond
    o.extrusion("mosaique", inte.difference(inte.buffer(-0.01, join_style=2)), 0.04, h - 0.05, 0.5)
    o.extrusion("eau", inte.buffer(-0.01, join_style=2), 0.40, 0.42, 1.5)              # eau
    o.extrusion("marbre", ext.buffer(0.10, join_style=2).difference(inte), h - 0.05, h, 0.9)   # margelle
    o.extrusion("or", ext.buffer(0.105, join_style=2).difference(ext.buffer(0.09, join_style=2)), h - 0.052, h - 0.008)
    # liseret lumineux sous la margelle + spots sous l'eau
    o.extrusion("neon", ext.buffer(0.09, join_style=2).difference(ext.buffer(0.0, join_style=2)), h - 0.07, h - 0.055)
    for s in (-1, 1):
        for z in (zc - 1.2, zc, zc + 1.2):
            o.cyl("lumiere", 0.05, 0.01, s * (lx / 2 - 0.155), 0.25, z, axe=(1, 0, 0))
    # 2 marches en marbre au bout arriere, echelle chromee
    z1 = zc + lz / 2 + 0.10
    o.boite("marbre", 1.0, 0.20, 0.32, 0, 0.10, z1 + 0.16, 0.01, 0.9)
    o.boite("marbre", 1.0, 0.18, 0.16, 0, 0.29, z1 + 0.08, 0.01, 0.9)
    for s in (-1, 1):
        x = s * 0.25
        pts = [(x, 0.95, z1 - 0.08), (x, h + 0.05, z1 - 0.08), (x, h + 0.25, z1 - 0.28),
               (x, h + 0.15, zc + lz / 2 - 0.30), (x, 0.10, zc + lz / 2 - 0.30)]
        pts[0] = (x, 0.40, z1 + 0.05)
        for a, b in zip(pts[:-1], pts[1:]):
            a, b = np.array(a), np.array(b)
            o.add("chrome", cylindre(0.02, np.linalg.norm(b - a) + 0.02, (a + b) / 2, axe=b - a, sec=12))
    for y in (0.15, 0.30):
        o.boite("chrome", 0.50, 0.02, 0.06, 0, y, zc + lz / 2 - 0.30, 0.008)
    # bouee et ballon (ambiance tycoon) poses sur l'eau
    o.meuble("Bouee")
    bouee = trimesh.creation.torus(0.28, 0.08, major_sections=32, minor_sections=12)
    bouee.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    bouee.apply_translation([-0.45, 0.44, zc - 0.9])
    o.add("blanc", bouee)
    for i, a in enumerate(np.linspace(0, 2 * np.pi, 4, endpoint=False)):
        t = trimesh.creation.torus(0.28, 0.082, major_sections=8, minor_sections=12)
        t.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
        t.apply_transform(rotation_matrix(a, [0, 1, 0]))
        t = t.slice_plane([0, 0, 0], [np.cos(a + 0.2), 0, -np.sin(a + 0.2)])
        t = t.slice_plane([0, 0, 0], [-np.cos(a + 0.6), 0, np.sin(a + 0.6)])
        t.apply_translation([-0.45, 0.44, zc - 0.9])
        o.add("rouge", t)
    o.meuble("Ballon")
    ballon = trimesh.creation.icosphere(3, 0.16)
    ballon.apply_translation([0.5, 0.48, zc + 0.8])
    o.add("blanc", ballon)
    return o


# ------------------------------------------------------------------ 05 transats
def transat(o, x, z):
    """Transat le long de Z, tete vers +Z (vers les marches)."""
    for s in (-1, 1):
        o.boite("laque", 0.04, 0.05, 1.90, x + s * 0.32, 0.28, z, 0.015)
    for dz in (-0.85, 0.85):
        for s in (-1, 1):
            o.boite("laque", 0.05, 0.28, 0.05, x + s * 0.32, 0.14, z + dz, 0.015)
    o.boite("laque", 0.66, 0.04, 1.30, x, 0.31, z - 0.30, 0.015)
    o.boite("cuir", 0.62, 0.08, 1.24, x, 0.37, z - 0.30, 0.035, 0.5, bombe=0.01)
    o.boite("laque", 0.66, 0.04, 0.66, x, 0.52, z + 0.62, 0.015, rx=-38)
    o.boite("cuir", 0.62, 0.08, 0.62, x, 0.56, z + 0.60, 0.035, 0.5, rx=-38, bombe=0.01)
    o.boite("plaid", 0.42, 0.05, 0.30, x, 0.43, z - 0.60, 0.02, 0.5)       # serviette pliee
    o.cyl("velours", 0.07, 0.40, x, 0.66, z + 0.72, axe=(1, 0, 0))         # coussin rouleau


def transats():
    o = Objet("Etage05_Transats")
    for s in (-1, 1):
        for z in (1.45, 3.80):
            o.meuble("Transat")
            transat(o, s * 2.12, z)
        o.meuble("PetiteTable")
        table_ronde(o, s * 2.30, 2.62, 0.18, 0.45)
        verre(o, s * 2.30, 0.45, 2.62)
    return o


# ------------------------------------------------------------------ 06 statue dollar
def statue():
    o = Objet("Etage06_StatueDollar", "StatueDollar")
    z = -0.35
    o.boite("marbre", 0.62, 0.55, 0.62, 0, 0.275, z, 0.01, 0.9)
    o.boite("or", 0.66, 0.05, 0.66, 0, 0.575, z, 0.01)
    o.boite("or", 0.64, 0.03, 0.64, 0, 0.03, z, 0.01)
    # "$" : un S (deux arcs) + une barre verticale, en or massif, epaisseur 0,16
    r, cy = 0.22, 1.20
    t1 = np.linspace(np.radians(20), np.radians(270), 40)
    haut = [(r * np.cos(t), cy + r + r * np.sin(t)) for t in t1]
    t2 = np.linspace(np.radians(90), np.radians(-160), 40)
    bas = [(r * np.cos(t), cy - r + r * np.sin(t)) for t in t2]
    s = LineString(haut + bas).buffer(0.075, cap_style=1)
    barre = Polygon([(-0.035, cy - 2 * r - 0.17), (0.035, cy - 2 * r - 0.17), (0.035, cy + 2 * r + 0.17),
                     (-0.035, cy + 2 * r + 0.17)])
    glyphe = unary_union([s, barre]).simplify(0.002)
    m = trimesh.creation.extrude_polygon(glyphe, 0.16)
    m.apply_translation([0, 0, z - 0.08])
    o.add("or", m)
    return o


# ------------------------------------------------------------------ 07 piano
def piano():
    o = Objet("Etage07_Piano", "Piano")
    xk, zc = -0.80, -2.45            # bord du clavier (cote allee), centre en z
    L, W = 1.75, 1.45
    # contour vu de dessus : u = distance depuis le clavier (vers -X), v = travers (z)
    u = np.linspace(0, 1, 40)
    droit = [(t * (L - 0.35), W / 2) for t in u]                                 # cote basses, droit
    queue = [(L - 0.35 + 0.35 * np.sin(a), W / 2 - 0.35 + 0.35 * np.cos(a)) for a in np.linspace(0, np.pi / 2, 12)]
    courbe = []                                                                  # cote aigus, en S
    for t in np.linspace(1, 0, 40):
        uu = 0.30 + t * (L - 0.30)
        vv = -W / 2 + (W * 0.55) * (0.5 - 0.5 * np.cos(np.pi * np.clip((uu - 0.30) / (L - 0.30), 0, 1)))
        courbe.append((uu, vv))
    contour = droit + queue[1:] + [(L, W / 2 - 0.35)] + [(L, -W / 2 + W * 0.55)] + courbe + [(0.0, -W / 2)]
    poly = Polygon([(xk - a, zc + b) for a, b in contour]).buffer(0.02).buffer(-0.02)
    o.extrusion("piano", poly, 0.62, 0.95, 0.6)
    o.extrusion("or", poly.buffer(0.008).difference(poly.buffer(-0.01)), 0.62, 0.635)
    # couvercle ouvert (incline de 35 deg) + bequille
    cov = trimesh.creation.extrude_polygon(Polygon([(-(a), b) for a, b in contour]).buffer(-0.01), 0.02)
    cov.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    cov.apply_transform(np.diag([1, 1, -1, 1]))
    cov.invert()
    cov.apply_transform(rotation_matrix(np.radians(35), [1, 0, 0], [0, 0, W / 2]))
    cov.apply_translation([xk, 0.95, zc])
    o.add("piano", cov, 0.6)
    o.cyl("or", 0.01, 0.46, xk - 0.95, 0.95 + 0.23, zc - 0.10, sec=8)                # bequille
    # clavier
    o.boite("piano", 0.30, 0.10, W - 0.06, xk + 0.12, 0.66, zc, 0.01, 0.6)
    o.boite("touches", 0.16, 0.025, W - 0.20, xk + 0.17, 0.72, zc, 0.003, 1.3)
    for i in range(36):
        if i % 7 in (2, 6):
            continue
        z = zc - (W - 0.20) / 2 + (i + 1) * (W - 0.20) / 36.5
        o.boite("noir", 0.09, 0.02, 0.012, xk + 0.135, 0.742, z, 0.002)
    o.boite("piano", 0.04, 0.22, W - 0.30, xk + 0.02, 0.86, zc, 0.01, rx=0)       # pupitre
    o.boite("blanc", 0.005, 0.18, 0.40, xk + 0.045, 0.88, zc, 0.001)               # partition
    # 3 pieds tournes blancs a sabot dore + lyre a pedales
    for a, b in ((0.18, -W / 2 + 0.15), (0.18, W / 2 - 0.15), (L - 0.30, W / 2 - 0.25)):
        o.cyl("piano", 0.045, 0.60, xk - a, 0.31, zc + b)
        o.cyl("or", 0.05, 0.04, xk - a, 0.02, zc + b)
    o.boite("piano", 0.08, 0.50, 0.20, xk - 0.25, 0.30, zc, 0.02)
    for dz in (-0.05, 0, 0.05):
        o.boite("or", 0.10, 0.012, 0.025, xk - 0.18, 0.06, zc + dz, 0.004)
    o.meuble("Banquette")
    o.boite("piano", 0.36, 0.06, 0.80, xk + 0.55, 0.47, zc, 0.02)
    o.boite("cuir", 0.36, 0.06, 0.78, xk + 0.55, 0.52, zc, 0.025, 0.5)
    for dx in (-1, 1):
        for dz in (-1, 1):
            o.cyl("piano", 0.025, 0.44, xk + 0.55 + dx * 0.14, 0.22, zc + dz * 0.34)
    o.meuble("Chandelier")                                                       # pose sur le piano
    o.cyl("or", 0.05, 0.01, xk - 1.10, 0.955, zc + 0.45)
    o.cyl("or", 0.012, 0.22, xk - 1.10, 1.07, zc + 0.45)
    o.cyl("lumiere", 0.015, 0.08, xk - 1.10, 1.22, zc + 0.45)
    return o


# ------------------------------------------------------------------ 08 casino
def casino():
    o = Objet("Etage08_Casino", "TableCasino")
    xc, zc = 1.62, -2.75
    o.extrusion("noir", stade(1.15, 2.10, xc, zc), 0.70, 0.74)
    o.extrusion("feutre", stade(0.95, 1.90, xc, zc), 0.74, 0.755, 0.8)
    rail = stade(1.15, 2.10, xc, zc).difference(stade(0.95, 1.90, xc, zc))
    o.extrusion("cuir_vert", rail, 0.74, 0.80, 0.4)
    o.extrusion("or", stade(1.17, 2.12, xc, zc).difference(stade(1.13, 2.08, xc, zc)), 0.70, 0.745)
    o.boite("or", 0.40, 0.04, 0.60, xc, 0.68, zc, 0.01)
    o.cyl("noyer", 0.11, 0.62, xc, 0.36, zc - 0.45, sec=24)
    o.cyl("noyer", 0.11, 0.62, xc, 0.36, zc + 0.45, sec=24)
    o.boite("noyer", 0.60, 0.04, 1.30, xc, 0.03, zc, 0.01)
    # cartes + piles de jetons
    for dz in (-0.12, -0.06, 0.0, 0.06, 0.12):
        o.boite("blanc", 0.07, 0.002, 0.05, xc, 0.757, zc + dz, 0.001)
    rng = np.random.default_rng(2)
    for px, pz in ((-0.30, -0.6), (0.30, -0.6), (-0.30, 0.0), (0.30, 0.0), (-0.30, 0.6), (0.30, 0.6), (0.0, -0.3)):
        for j, k in enumerate(("rouge", "noir", "blanc", "cuir_vert")[: 2 + int(rng.integers(3))]):
            n = 3 + int(rng.integers(6))
            o.cyl(k, 0.02, 0.0035 * n, xc + px + 0.045 * j, 0.756 + 0.00175 * n, zc + pz, sec=16)
    # 6 chaises velours, pieds dores
    for s in (-1, 1):
        for dz in (-0.65, 0.0, 0.65):
            x = xc + s * 0.85
            o.meuble("Chaise")
            o.boite("velours", 0.46, 0.10, 0.46, x, 0.47, zc + dz, 0.04, 0.5, bombe=0.01)
            o.boite("velours", 0.08, 0.50, 0.46, x + s * 0.22, 0.75, zc + dz, 0.04, 0.5, bombe=0.02)
            for a in (-1, 1):
                for b in (-1, 1):
                    o.cyl("or", 0.015, 0.42, x + a * 0.19, 0.21, zc + dz + b * 0.19)
    return o


# ------------------------------------------------------------------ 09 cinema
def cinema():
    o = Objet("Etage09_Cinema", "EcranCinema")
    zf = -9.45 + 0.07                     # face de la cloison avant
    lw, hw, yc = 3.20, 1.65, 1.30
    o.boite("or", lw + 0.12, hw + 0.12, 0.04, 0, yc, zf + 0.02, 0.02)
    o.boite("noir", lw + 0.04, hw + 0.04, 0.05, 0, yc, zf + 0.03, 0.01)
    o.boite("ecran", lw, hw, 0.01, 0, yc, zf + 0.06, 0.003)
    # rideaux de velours plisses de chaque cote + cantonniere
    for s in (-1, 1):
        for i in range(7):
            x = s * (lw / 2 + 0.12 + i * 0.075)
            h = min(2.25, y_plafond(x) - 0.06)
            o.cyl("velours", 0.05, h, x, h / 2, zf + 0.10 + 0.03 * (i % 2), sec=12)
        o.boite("or", 0.06, 0.06, 0.18, s * (lw / 2 + 0.38), 1.0, zf + 0.12, 0.02)
    o.boite("velours", lw + 1.10, 0.28, 0.14, 0, min(2.25, y_plafond(lw / 2)) - 0.14, zf + 0.12, 0.04, 0.5)
    o.boite("or", lw + 1.12, 0.03, 0.15, 0, min(2.25, y_plafond(lw / 2)) - 0.29, zf + 0.12, 0.01)
    # 2 rangees de 2 canapes inclinables en cuir creme, tournes vers l'ecran (-Z)
    for z in (-6.85, -5.40):
        for s in (-1, 1):
            x = s * 1.35
            o.meuble("CanapeCinema")
            o.boite("cuir", 2.10, 0.32, 0.95, x, 0.22, z, 0.06, 0.5)
            o.boite("cuir", 2.10, 0.60, 0.22, x, 0.62, z + 0.38, 0.08, 0.5, rx=8, bombe=0.02)
            for b in (-1, 1):
                o.boite("cuir", 0.16, 0.30, 0.90, x + b * 0.97, 0.52, z + 0.02, 0.06, 0.5)
            for i in (-1, 0, 1):
                o.boite("siege", 0.56, 0.12, 0.66, x + i * 0.60, 0.44, z - 0.08, 0.05, 0.45, bombe=0.02)
                o.boite("siege", 0.54, 0.44, 0.14, x + i * 0.60, 0.75, z + 0.24, 0.06, 0.45, rx=8, bombe=0.03)
            o.boite("noir", 2.0, 0.08, 0.02, x, 0.10, z - 0.48, 0.005)
            o.boite("neon", 1.9, 0.01, 0.01, x, 0.06, z - 0.49, 0.003)
    # seau de pop-corn sur les accoudoirs centraux
    for s in (-1, 1):
        o.meuble("PopCorn")
        o.cyl("rouge", 0.07, 0.16, s * 0.38, 0.75, -6.85)
        o.cyl("blanc", 0.071, 0.02, s * 0.38, 0.84, -6.85)
    return o


# ------------------------------------------------------------------ 10 lustres
def lustres():
    o = Objet("Etage10_Lustres")
    for z in (17.90, 7.35, 2.60, -2.75):
        o.meuble("Lustre")
        h = y_plafond(0.2) - 0.002
        o.cyl("or", 0.16, 0.03, 0, h - 0.015, z, sec=32)
        o.cyl("or", 0.012, 0.25, 0, h - 0.15, z, sec=8)
        for r, y in ((0.42, h - 0.40), (0.28, h - 0.52), (0.14, h - 0.62)):
            anneau = trimesh.creation.torus(r, 0.012, major_sections=48, minor_sections=8)
            anneau.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
            anneau.apply_translation([0, y, z])
            o.add("or", anneau)
            n = int(r * 60)
            for a in np.linspace(0, 2 * np.pi, n, endpoint=False):
                for j in range(2):
                    g = trimesh.creation.icosphere(0, 0.022)
                    g.apply_scale([1, 1.8, 1])
                    g.apply_translation([r * np.cos(a), y - 0.06 - j * 0.07, z + r * np.sin(a)])
                    o.add("cristal", g)
            for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):    # bougies
                o.cyl("lumiere", 0.012, 0.06, r * np.cos(a), y + 0.04, z + r * np.sin(a), sec=8)
        for a in np.linspace(0, 2 * np.pi, 6, endpoint=False):
            p0 = np.array([0, h - 0.27, z])
            p1 = np.array([0.42 * np.cos(a), h - 0.40, z + 0.42 * np.sin(a)])
            o.add("or", cylindre(0.006, np.linalg.norm(p1 - p0), (p0 + p1) / 2, axe=p1 - p0, sec=6))
        g = trimesh.creation.icosphere(2, 0.06)
        g.apply_translation([0, h - 0.70, z])
        o.add("cristal", g)
    return o


# ------------------------------------------------------------------ 11 plantes
def palmier(o, x, z):
    sens = -np.sign(x)                                                   # le palmier penche vers l'allee
    o.cyl("or", 0.26, 0.44, x, 0.22, z, sec=32)                         # pot dore
    bord = trimesh.creation.annulus(0.235, 0.268, 0.05, sections=32)      # bord noir (anneau, sans face commune)
    bord.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    bord.apply_translation([x, 0.465, z])
    o.add("noir", bord)
    o.cyl("tronc", 0.236, 0.025, x, 0.4575, z, sec=32)                    # terre, en retrait sous le bord
    base = np.array([x, 0.48, z])
    sommet = np.array([x + sens * 0.12, 1.65, z])
    for i in range(6):
        a, b = base + (sommet - base) * i / 6, base + (sommet - base) * (i + 1) / 6
        o.add("tronc", cylindre(0.065 - i * 0.004, np.linalg.norm(b - a) + 0.02, (a + b) / 2, axe=b - a, sec=12), 0.3)
    for i, a in enumerate(np.linspace(0, 2 * np.pi, 9, endpoint=False)):
        lg = 0.85 if i % 2 else 0.70
        d = np.array([np.cos(a), 0, np.sin(a)])
        lat = np.cross(d, [0, 1, 0])
        V, F = [], []
        for t in np.linspace(0, 1, 9):
            c = sommet + d * lg * t + np.array([0, 0.15 * t - 0.55 * t * t, 0])
            w = 0.16 * np.sin(np.pi * min(1, t * 1.15)) + 0.01
            V += [c - lat * w + [0, 0.03 * t, 0], c + lat * w + [0, 0.03 * t, 0]]
        for j in range(8):
            q = 2 * j
            F += [[q, q + 1, q + 3], [q, q + 3, q + 2], [q, q + 3, q + 1], [q, q + 2, q + 3]]
        f = trimesh.Trimesh(np.array(V), np.array(F), process=False)
        o.add("feuille", f, 0.5)


def plantes():
    o = Objet("Etage11_Plantes")
    for s in (-1, 1):
        for z in (19.90, 15.45, 9.62, 0.0):
            o.meuble("Palmier")
            palmier(o, s * 2.30, z)
    return o


OBJETS = [salon_escalier, bar, salon, piscine, transats, statue, piano, casino, cinema, lustres, plantes]


def verifier(o):
    """Rien ne doit traverser la paroi, le plafond, ni tomber dans la tremie de l'escalier."""
    v = o.sommets()
    pb = []
    lim = np.array([x_paroi(y) for y in v[:, 1]])
    hors = np.abs(v[:, 0]) > lim - 0.005
    if hors.any():
        pb.append(f"{hors.sum()} sommets dans la paroi (max {np.max(np.abs(v[:, 0]) - lim):.3f} m)")
    pl = np.array([y_plafond(x) for x in v[:, 0]])
    if (v[:, 1] > pl + 0.001).any():
        pb.append(f"{(v[:, 1] > pl + 0.001).sum()} sommets dans le plafond")
    tremie = (np.abs(v[:, 0]) < 0.68) & (v[:, 2] > 15.07) & (v[:, 2] < 20.76) & (v[:, 1] < 1.1)
    if tremie.any():
        pb.append(f"{tremie.sum()} sommets dans la tremie")
    if (v[:, 2] < -9.38).any() or (v[:, 2] > 20.78).any():
        pb.append("depasse les cloisons avant / arriere")
    if v[:, 1].min() < -0.001:
        pb.append("sous le plancher")
    return pb


def exporter(sc, chemin):
    """Exporte puis REGROUPE dans le GLB : un noeud et un maillage par meuble (avec ses materiaux),
    au lieu d'un noeud par materiau. Dans UEFN chaque meuble devient ainsi un objet separe."""
    import json
    import struct
    sc.export(chemin, include_normals=True)
    data = open(chemin, "rb").read()
    lj = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + lj])
    binaire = data[20 + lj:]
    groupes = {}
    for nd in gltf["nodes"]:
        if "mesh" in nd:
            groupes.setdefault(nd["name"].split("__")[0], []).extend(gltf["meshes"][nd["mesh"]]["primitives"])
    gltf["meshes"] = [{"name": n, "primitives": p} for n, p in groupes.items()]
    gltf["nodes"] = [{"name": n, "mesh": i} for i, n in enumerate(groupes)]
    gltf["scenes"] = [{"nodes": list(range(len(groupes)))}]
    gltf["scene"] = 0
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    total = 12 + 8 + len(js) + len(binaire)
    with open(chemin, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        f.write(binaire)
    return list(groupes)


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    tout = trimesh.Scene()
    noms = []
    for f in OBJETS:
        o = f()
        pb = verifier(o)
        out = os.path.join(SORTIE, o.nom + ".glb")
        meubles = exporter(o.scene(), out)
        o.scene(tout)
        noms += meubles
        print(f"{o.nom:28s} {len(meubles):3d} meubles {os.path.getsize(out) / 1e6:5.1f} Mo  "
              f"{'OK' if not pb else ' / '.join(pb)}  ({', '.join(meubles)})")
    # fichier unique "tout deja place" : les memes meubles, chacun un objet separe
    complet = exporter(tout, os.path.join(SORTIE, "Etage_Complet_Tout_Place.glb"))
    assert len(complet) == len(set(complet)) == len(noms)
    print(f"Etage_Complet_Tout_Place.glb : {len(complet)} meubles separes, "
          f"{os.path.getsize(os.path.join(SORTIE, 'Etage_Complet_Tout_Place.glb')) / 1e6:.1f} Mo")
