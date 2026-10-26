"""ENCLOS DU LOBBY, theme aeroport (comme Infinity Tower Tycoon, mais a l'aeroport).
Dedans : une grande pelouse fermee par un grillage d'aeroport (on ne peut pas sortir).
Dehors (decor) : la piste d'atterrissage, le terminal avec des avions gares, la tour de controle, des hangars.
La plateforme de spawn (Plateforme_Spawn.glb) se pose au centre (0, 0, 0).
Chaque element est un objet separe. Origine : centre de l'enclos, au sol. Y en haut, 1 unite = 1 m.
Sortie : Modeles/Lobby/Enclos_Aeroport.glb     Usage : python3 generate_enclos_lobby.py
"""
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import Point, Polygon
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Enclos_Aeroport.glb")
DEMI = 60.0          # enclos de 120 x 120 m
H_GRILLE = 3.2
rng = np.random.default_rng(11)
PBR = trimesh.visual.material.PBRMaterial


# ------------------------------------------------------------------ textures
def bruit(img, s):
    a = np.asarray(img).astype(np.int16)
    a[..., :3] += rng.normal(0, s, a.shape[:2] + (1,)).astype(np.int16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def tex_pelouse():
    n = 512
    img = Image.new("RGB", (n, n))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, n // 2, n], fill=(98, 190, 72))      # bandes de tonte
    d.rectangle([n // 2, 0, n, n], fill=(86, 176, 64))
    return bruit(img, 6).filter(ImageFilter.GaussianBlur(1.0))


def tex_uni(rgb, s=5, n=256):
    return bruit(Image.new("RGB", (n, n), rgb), s).filter(ImageFilter.GaussianBlur(0.8))


def tex_grillage():
    n = 128
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = (70, 76, 86, 255)
    for k in (-n, 0, n):
        d.line([(k, 0), (k + n, n)], fill=c, width=7)
        d.line([(k + n, 0), (k, n)], fill=c, width=7)
    return img


def tex_vitres():
    n = 256
    img = Image.new("RGB", (n, n), (235, 240, 245))
    d = ImageDraw.Draw(img)
    for i in range(2):
        for j in range(2):
            x0, y0 = i * 128 + 8, j * 128 + 8
            for y in range(y0, y0 + 112):
                t = (y - y0) / 112
                d.line([(x0, y), (x0 + 112, y)], fill=(int(90 + 70 * t), int(170 + 40 * t), int(225 + 20 * t)))
            d.line([(x0 + 20, y0 + 90), (x0 + 60, y0 + 20)], fill=(205, 235, 250), width=6)    # reflet
    return img


M = {
    "pelouse": PBR(name="Pelouse", baseColorTexture=tex_pelouse(), roughnessFactor=0.95, metallicFactor=0.0),
    "tarmac": PBR(name="Tarmac", baseColorTexture=tex_uni((120, 124, 132), 6), roughnessFactor=0.9, metallicFactor=0.0),
    "piste": PBR(name="Piste", baseColorTexture=tex_uni((62, 66, 74), 6), roughnessFactor=0.9, metallicFactor=0.0),
    "grillage": PBR(name="Grillage", baseColorTexture=tex_grillage(), alphaMode="MASK", alphaCutoff=0.5,
                    doubleSided=True, roughnessFactor=0.6, metallicFactor=0.3),
    "vitres": PBR(name="VitresTerminal", baseColorTexture=tex_vitres(), roughnessFactor=0.15, metallicFactor=0.1),
}


def col(nom, rgb, rugo=0.7, em=None):
    return PBR(name=nom, baseColorFactor=[*rgb, 255], roughnessFactor=rugo, metallicFactor=0.0,
               emissiveFactor=em)


M.update({
    "blanc": col("BlancCartoon", (244, 246, 248), 0.5),
    "beton": col("Beton", (196, 200, 206), 0.85),
    "poteau": col("PoteauGris", (150, 156, 166), 0.5),
    "vert": col("VertArgent", (40, 185, 100), 0.45),
    "vert_fonce": col("VertFonce", (22, 120, 66), 0.5),
    "sombre": col("ContourSombre", (36, 42, 58), 0.6),
    "marquage": col("MarquageBlanc", (250, 250, 250), 0.6),
    "feu_blanc": col("FeuBlanc", (255, 255, 255), 0.3, [1.0, 1.0, 1.0]),
    "feu_vert": col("FeuVert", (90, 255, 140), 0.3, [0.3, 1.0, 0.5]),
    "feu_rouge": col("FeuRouge", (255, 70, 70), 0.3, [1.0, 0.25, 0.25]),
    "hublot": col("Hublot", (40, 60, 90), 0.1),
    "orange": col("ManchetteOrange", (255, 110, 50), 0.6),
    "haie": col("Haie", (52, 150, 62), 0.9),
    "feuillage": col("Feuillage", (70, 178, 74), 0.9),
    "feuillage_fonce": col("FeuillageFonce", (46, 140, 58), 0.9),
    "tronc": col("Tronc", (120, 82, 56), 0.9),
})


# ------------------------------------------------------------------ geometrie
def uv_monde(m, tuile):
    m = m.copy()
    m.unmerge_vertices()
    v, n = m.vertices, m.face_normals
    uv = np.zeros((len(v), 2))
    for fi, f in enumerate(m.faces):
        ax = np.argmax(np.abs(n[fi]))
        p = v[f]
        uv[f] = np.c_[p[:, 2], p[:, 1]] if ax == 0 else (np.c_[p[:, 0], p[:, 2]] if ax == 1 else np.c_[p[:, 0], p[:, 1]])
    uv /= tuile
    return m, uv


class Objets:
    def __init__(self):
        self.sc = trimesh.Scene()
        self.parts = {}
        self.ordre = []

    def add(self, objet, k, m, tuile=None):
        if objet not in self.parts:
            self.parts[objet] = {}
            self.ordre.append(objet)
        self.parts[objet].setdefault((k, tuile), []).append(m)

    def exporter(self, chemin):
        for o in self.ordre:
            for (k, tuile), ms in self.parts[o].items():
                m = trimesh.util.concatenate(ms)
                mat = M[k]
                if tuile:
                    m, uv = uv_monde(m, tuile)
                    m.visual = trimesh.visual.TextureVisuals(uv=uv, material=mat)
                else:
                    m.visual = trimesh.visual.TextureVisuals(material=mat)
                self.sc.add_geometry(m, node_name=f"{o}__{k}", geom_name=f"{o}__{k}")
        self.sc.export(chemin)
        # regroupe les primitives par objet (un noeud = un objet)
        import json
        import struct
        b = open(chemin, "rb").read()
        lj = struct.unpack("<I", b[12:16])[0]
        js = json.loads(b[20:20 + lj])
        rest = b[20 + lj:]
        nouveaux_mesh, nouveaux_noeuds, index = [], [], {}
        for nd in js["nodes"]:
            if "mesh" not in nd:
                continue
            o = nd["name"].split("__")[0]
            if o not in index:
                index[o] = len(nouveaux_mesh)
                nouveaux_mesh.append({"name": o, "primitives": []})
                nouveaux_noeuds.append({"name": o, "mesh": index[o]})
            nouveaux_mesh[index[o]]["primitives"] += js["meshes"][nd["mesh"]]["primitives"]
        js["meshes"] = nouveaux_mesh
        js["nodes"] = nouveaux_noeuds
        js["scenes"] = [{"nodes": list(range(len(nouveaux_noeuds)))}]
        js["scene"] = 0
        s = json.dumps(js, separators=(",", ":")).encode()
        s += b" " * ((4 - len(s) % 4) % 4)
        out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(s) + len(rest)) + struct.pack("<II", len(s), 0x4E4F534A) + s + rest
        open(chemin, "wb").write(out)
        return self.ordre


def boite(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box((x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def cyl(r, h, x, y, z, sections=24):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    m.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([x, y + h / 2, z])
    return m


def tronc_cone(r0, r1, h, x, y, z, sections=48):
    a = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    bas = np.c_[r0 * np.cos(a), np.zeros(sections), r0 * np.sin(a)]
    haut = np.c_[r1 * np.cos(a), np.full(sections, h), r1 * np.sin(a)]
    m = trimesh.convex.convex_hull(np.vstack([bas, haut]))
    m.apply_translation([x, y, z])
    return m


def extrusion(poly, y0, y1):
    if hasattr(poly, "geoms"):
        return trimesh.util.concatenate([extrusion(p, y0, y1) for p in poly.geoms if p.area > 0.01])
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_translation([0, y0, 0])
    return m


def quad(p0, p1, h, y0=0.0):
    """panneau vertical de p0 a p1 (x, z), hauteur h, deux faces, UV en metres"""
    (x0, z0), (x1, z1) = p0, p1
    v = np.array([[x0, y0, z0], [x1, y0, z1], [x1, y0 + h, z1], [x0, y0 + h, z0]])
    L = math.hypot(x1 - x0, z1 - z0)
    m = trimesh.Trimesh(v, [[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]], process=False)
    return m, np.array([[0, 0], [L, 0], [L, h], [0, h]])


# ------------------------------------------------------------------ elements
def sols(O):
    O.add("Sol_Pelouse", "pelouse", boite(-DEMI, -0.1, -DEMI, DEMI, 0.0, DEMI), 12.0)
    dehors = Polygon([(-260, -260), (260, -260), (260, 260), (-260, 260)]).difference(
        Polygon([(-DEMI, -DEMI), (DEMI, -DEMI), (DEMI, DEMI), (-DEMI, DEMI)]))
    from shapely.ops import unary_union
    from shapely.geometry import box as rect
    tar = unary_union([rect(-115, 66, 115, 150),            # parking avions devant le terminal
                       rect(-150, -50, -64, 50),             # devant les hangars
                       rect(-150, -78, -130, 150),           # taxiway ouest vers la piste
                       rect(64, -78, 84, 150),               # taxiway est
                       Point(95, -40).buffer(12, 48)])       # pied de la tour
    tar = tar.difference(Polygon([(-DEMI, -DEMI), (DEMI, -DEMI), (DEMI, DEMI), (-DEMI, DEMI)]))
    O.add("Sol_Tarmac", "tarmac", extrusion(tar, -0.08, -0.01), 8.0)
    O.add("Sol_Herbe_Dehors", "pelouse", extrusion(dehors.difference(tar), -0.12, -0.02), 12.0)
    for x in np.arange(-110, 111, 6):                        # ligne de guidage du parking
        O.add("Sol_Tarmac", "marquage", boite(x, -0.01, 71.6, x + 3, 0.0, 72.0))
    for z in np.arange(-74, 148, 6):
        for xc in (-140, 74):
            O.add("Sol_Tarmac", "marquage", boite(xc - 0.2, -0.01, z, xc + 0.2, 0.0, z + 3))


def grillage(O):
    pas = 4.0
    coins = [(-DEMI, -DEMI), (DEMI, -DEMI), (DEMI, DEMI), (-DEMI, DEMI)]
    panneaux, uvs = [], []
    for c in range(4):
        (xa, za), (xb, zb) = coins[c], coins[(c + 1) % 4]
        L = math.hypot(xb - xa, zb - za)
        n = int(round(L / pas))
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            p0 = (xa + (xb - xa) * t0, za + (zb - za) * t0)
            p1 = (xa + (xb - xa) * t1, za + (zb - za) * t1)
            m, uv = quad(p0, p1, H_GRILLE - 0.35, 0.35)
            panneaux.append((m, uv / 0.5))
            O.add("Grillage_Poteaux", "poteau", cyl(0.07, H_GRILLE + 0.3, p0[0], 0.0, p0[1], 12))
            O.add("Grillage_Poteaux", "vert", cyl(0.1, 0.12, p0[0], H_GRILLE + 0.3, p0[1], 12))
        # rail du haut + muret beton bas
        dx, dz = (xb - xa) / L, (zb - za) / L
        rail = trimesh.creation.cylinder(radius=0.05, height=L, sections=10)
        rail.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], [dx, 0, dz]))
        rail.apply_translation([(xa + xb) / 2, H_GRILLE, (za + zb) / 2])
        O.add("Grillage_Poteaux", "poteau", rail)
        ex, ez = abs(dz) * 0.15, abs(dx) * 0.15
        O.add("Grillage_Muret", "beton", boite(min(xa, xb) - ex - 0.15, 0.0, min(za, zb) - ez - 0.15,
                                               max(xa, xb) + ex + 0.15, 0.35, max(za, zb) + ez + 0.15))
        O.add("Grillage_Muret", "vert", boite(min(xa, xb) - ex - 0.16, 0.28, min(za, zb) - ez - 0.16,
                                              max(xa, xb) + ex + 0.16, 0.35, max(za, zb) + ez + 0.16))
    m = trimesh.util.concatenate([p for p, _ in panneaux])
    m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([u for _, u in panneaux]), material=M["grillage"])
    O.sc.add_geometry(m, node_name="Grillage__grillage", geom_name="Grillage__grillage")


def piste(O):
    z0, z1, x0, x1 = -125.0, -80.0, -240.0, 240.0          # au nord, derriere le grillage
    zc = (z0 + z1) / 2
    O.add("Piste", "piste", boite(x0, -0.02, z0, x1, 0.02, z1), 10.0)
    for x in np.arange(x0 + 50, x1 - 50, 24):              # ligne centrale en tirets
        O.add("Piste", "marquage", boite(x, 0.02, zc - 0.5, x + 12, 0.04, zc + 0.5))
    for z in (z0 + 1.5, z1 - 1.5):                          # lignes de bord
        O.add("Piste", "marquage", boite(x0 + 4, 0.02, z - 0.4, x1 - 4, 0.04, z + 0.4))
    for xs, sgn in ((x0 + 6, 1), (x1 - 6, -1)):            # "piano" de seuil + zones de toucher
        for k in range(-5, 6):
            if k == 0:
                continue
            z = zc + k * 3.4
            O.add("Piste", "marquage", boite(min(xs, xs + sgn * 30), 0.02, z - 1.0, max(xs, xs + sgn * 30), 0.04, z + 1.0))
        for k in (-1, 1):
            xa = xs + sgn * 70
            O.add("Piste", "marquage", boite(min(xa, xa + sgn * 22), 0.02, zc + k * 7 - 1.6, max(xa, xa + sgn * 22), 0.04, zc + k * 7 + 1.6))
    for x in np.arange(x0 + 4, x1, 15):                     # feux de bord
        for z in (z0 + 0.4, z1 - 0.4):
            O.add("Piste_Feux", "poteau", cyl(0.12, 0.3, x, 0.0, z, 8))
            O.add("Piste_Feux", "feu_blanc", trimesh.creation.icosphere(1, 0.22).apply_translation([x, 0.42, z]))
    for xs, k in ((x0 + 2, "feu_vert"), (x1 - 2, "feu_rouge")):
        for z in np.arange(z0 + 3, z1 - 2, 3):
            O.add("Piste_Feux", k, trimesh.creation.icosphere(1, 0.25).apply_translation([xs, 0.3, z]))


def avion(O, nom, x, z, cap, s=3.0, alt=0.0, tangage=0.0):
    """avion cartoon (blanc + vert argent), nez vers -Z avant rotation de cap degres"""
    R = rotation_matrix(math.radians(cap), [0, 1, 0]) @ rotation_matrix(math.radians(tangage), [1, 0, 0])

    def T(m):
        m.apply_transform(R)
        m.apply_translation([x, alt, z])
        O.add(nom, k_courant[0], m)

    k_courant = ["blanc"]

    def put(k, m):
        k_courant[0] = k
        T(m)

    y = 1.15 * s
    fus = trimesh.creation.capsule(height=6.0 * s, radius=0.9 * s, count=[32, 24])
    fus.apply_translation([0, y, 0])
    put("blanc", fus)
    b = trimesh.creation.cylinder(radius=0.915 * s, height=6.0 * s, sections=48)
    b.apply_scale([1, 0.18, 1])
    b.apply_translation([0, y - 0.25 * s, 0])
    put("vert", b)

    def aile(points, ep, yy, k):
        m = trimesh.creation.extrude_polygon(Polygon(points), ep)
        m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
        m.apply_transform(np.diag([1, 1, -1, 1]))
        m.invert()
        m.apply_translation([0, yy, 0])
        put(k, m)
    aile([(0, -1.2 * s), (4.6 * s, 0.9 * s), (4.6 * s, 1.5 * s), (0, 1.0 * s), (-4.6 * s, 1.5 * s), (-4.6 * s, 0.9 * s)],
         0.22 * s, y - 0.45 * s, "blanc")
    aile([(0, 3.2 * s), (1.9 * s, 4.0 * s), (1.9 * s, 4.35 * s), (0, 4.1 * s), (-1.9 * s, 4.35 * s), (-1.9 * s, 4.0 * s)],
         0.16 * s, y + 0.2 * s, "vert")
    der = trimesh.creation.extrude_polygon(Polygon([(2.9 * s, 0), (4.3 * s, 0), (4.5 * s, 2.1 * s), (3.9 * s, 2.1 * s)]), 0.2 * s)
    der.apply_transform(rotation_matrix(-np.pi / 2, [0, 1, 0]))
    der.apply_translation([0.1 * s, y + 0.4 * s, 0])
    put("vert", der)
    for xx in (-2.3, 2.3):
        r = trimesh.creation.capsule(height=1.1 * s, radius=0.42 * s, count=[16, 12])
        r.apply_translation([xx * s, y - 0.85 * s, -0.4 * s])
        put("vert", r)
        e = trimesh.creation.cylinder(radius=0.3 * s, height=0.05 * s, sections=24)
        e.apply_translation([xx * s, y - 0.85 * s, -1.38 * s])
        put("sombre", e)
    for zz in np.arange(-2.3, 2.4, 0.5):
        for xx in (-1, 1):
            h = trimesh.creation.icosphere(2, 0.17 * s)
            h.apply_scale([0.35, 1.0, 1.0])
            h.apply_translation([xx * 0.89 * s, y + 0.2 * s, zz * s])
            put("hublot", h)
    pare = trimesh.creation.icosphere(2, 0.55 * s)
    pare.apply_scale([1.1, 0.42, 0.65])
    pare.apply_translation([0, y + 0.42 * s, -3.15 * s])
    put("hublot", pare)
    for zz, xx in (((-2.6, 0), (0.4, -1.0), (0.4, 1.0)) if alt == 0 else ()):     # train d'atterrissage
        put("sombre", cyl(0.12 * s, y - 0.35 * s, xx * s, 0.35 * s, zz * s, 10))
        roue = trimesh.creation.cylinder(radius=0.35 * s, height=0.3 * s, sections=20)
        roue.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
        roue.apply_translation([xx * s, 0.35 * s, zz * s])
        put("sombre", roue)


def terminal(O):
    z0, z1, x0, x1, H = 108.0, 138.0, -95.0, 95.0, 15.0     # au sud
    O.add("Terminal", "beton", boite(x0, 0, z0 + 2, x1, 1.0, z1))
    O.add("Terminal", "vitres", boite(x0 + 1, 1.0, z0 + 2, x1 - 1, H - 1.5, z1 - 2), 4.0)
    for x in np.arange(x0 + 1, x1, 16):                     # piliers blancs
        O.add("Terminal", "blanc", boite(x - 0.5, 1.0, z0 + 1.6, x + 0.5, H - 1.5, z0 + 2.6))
    O.add("Terminal", "vert", boite(x0, H - 1.5, z0 + 1.5, x1, H - 0.4, z1))   # bandeau vert
    # toit en vague (arc)
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        z = z0 - 4 + (z1 - z0 + 8) * t
        pts.append((z, H - 0.4 + 3.2 * math.sin(math.pi * t)))
    prof = Polygon(pts + [(p[0], p[1] + 0.8) for p in reversed(pts)][:1] +
                   [(p[0], p[1] + 0.8) for p in reversed(pts)][1:])
    toit = trimesh.creation.extrude_polygon(prof, x1 - x0 + 8)
    toit.apply_transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]))
    toit.invert()
    toit.apply_translation([x0 - 4, 0, 0])
    O.add("Terminal", "blanc", toit)
    # passerelles (jet bridges) vers les avions
    for xa in (-55, 0, 55):
        O.add("Terminal_Passerelles", "beton", boite(xa - 1.6, 4.0, 86, xa + 1.6, 7.0, z0 + 2))
        O.add("Terminal_Passerelles", "vert", boite(xa - 1.65, 6.2, 86, xa + 1.65, 6.6, z0 + 2))
        O.add("Terminal_Passerelles", "poteau", cyl(0.35, 4.0, xa, 0, 92))
    # lettres "AIRPORT" vertes sur le toit (blocs simples)
    lettres(O, "AIRPORT", 0.0, H + 3.6, z0 + 6, 5.0)


GLYPHES = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
}


def lettres(O, mot, xc, y0, z, h):
    px = h / 7
    larg = len(mot) * 6 * px - px
    x = xc + larg / 2                                        # vu depuis l'enclos (on regarde vers +Z), la droite est -X
    for ch in mot:
        g = GLYPHES[ch]
        for r, ligne in enumerate(g):
            for c, b in enumerate(ligne):
                if b == "1":
                    xa = x - (c + 1) * px
                    O.add("Terminal_Enseigne", "vert", boite(xa, y0 + (6 - r) * px, z, xa + px * 1.02, y0 + (7 - r) * px * 1.0, z + 0.6))
                    O.add("Terminal_Enseigne", "blanc", boite(xa - 0.08, y0 + (6 - r) * px - 0.08, z + 0.6, xa + px + 0.1, y0 + (7 - r) * px + 0.08, z + 0.9))
        x -= 6 * px
    O.add("Terminal_Enseigne", "poteau", boite(xc - larg / 2, y0 - 3.6, z + 0.2, xc + larg / 2, y0, z + 0.7))


def tour(O):
    x, z = 95.0, -40.0                                       # a l'est, pres de la piste
    O.add("Tour_Controle", "beton", cyl(6.0, 3.0, x, 0, z, 48))
    O.add("Tour_Controle", "blanc", tronc_cone(3.6, 2.8, 30.0, x, 3.0, z))
    for y in (10.0, 20.0):
        O.add("Tour_Controle", "vert", cyl(3.3 - y * 0.026, 0.8, x, y, z, 48))
    O.add("Tour_Controle", "blanc", tronc_cone(3.0, 6.0, 2.5, x, 33.0, z))
    O.add("Tour_Controle", "vitres", tronc_cone(6.0, 6.8, 4.5, x, 35.5, z), 4.0)
    O.add("Tour_Controle", "vert", tronc_cone(7.2, 3.5, 1.8, x, 40.0, z))
    O.add("Tour_Controle", "poteau", cyl(0.15, 6.0, x, 41.8, z, 8))
    O.add("Tour_Controle", "feu_rouge", trimesh.creation.icosphere(1, 0.4).apply_translation([x, 48.0, z]))
    r = trimesh.creation.icosphere(2, 1.6)                   # radar
    r.apply_scale([1, 0.5, 1])
    r.apply_translation([x + 2.5, 42.6, z])
    O.add("Tour_Controle", "blanc", r)


def hangars(O):
    for i, zc in enumerate((-25.0, 25.0)):                  # a l'ouest
        x0, x1, r = -125.0, -90.0, 17.0
        nom = f"Hangar_{i + 1}"
        a = np.linspace(0, np.pi, 33)
        arc = [(zc + r * math.cos(t), 0.9 * r * math.sin(t)) for t in a]
        coque = Polygon([(zc - r, 0)] + [(p[0], p[1]) for p in reversed(arc)] + [(zc + r, 0)])
        m = trimesh.creation.extrude_polygon(coque, x1 - x0)
        m.apply_transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]))
        m.invert()
        m.apply_translation([x0, 0, 0])
        O.add(nom, "blanc", m)
        # grande porte verte avec bandes, face a l'enclos (+X)
        porte = Polygon([(zc - r * 0.75, 0)] + [(zc + r * 0.75 * math.cos(t), 0.9 * r * 0.75 * math.sin(t))
                                                for t in np.linspace(np.pi, 0, 25)] + [(zc + r * 0.75, 0)])
        p = trimesh.creation.extrude_polygon(porte.buffer(0), 0.3)
        p.apply_transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]))
        p.invert()
        p.apply_translation([x1, 0, 0])
        O.add(nom, "vert", p)
        for k in range(1, 6):
            zz = zc - r * 0.75 + k * (1.5 * r * 0.75 / 6)
            hmax = 0.9 * r * 0.75 * math.sqrt(max(0, 1 - ((zz - zc) / (r * 0.75)) ** 2))
            O.add(nom, "vert_fonce", boite(x1 + 0.3, 0, zz - 0.15, x1 + 0.45, hmax - 0.3, zz + 0.15))
        lettres_bloc = boite(x1 + 0.05, 0.9 * r * 0.95, zc - 3, x1 + 0.4, 0.9 * r * 0.95 + 0.6, zc + 3)
        O.add(nom, "vert", lettres_bloc)


def manche_a_air(O):
    x, z = 40.0, -48.0                                       # pres d un coin de l'enclos
    O.add("Manche_A_Air", "poteau", cyl(0.12, 7.0, x, 0, z, 12))
    O.add("Manche_A_Air", "beton", cyl(0.6, 0.3, x, 0, z, 24))
    for i in range(5):
        r0, r1 = 0.65 - i * 0.08, 0.65 - (i + 1) * 0.08
        c = tronc_cone(r0, r1, 0.9, 0, 0, 0, 20)
        c.apply_transform(rotation_matrix(-np.pi / 2, [0, 0, 1]))
        c.apply_transform(rotation_matrix(math.radians(10), [0, 0, 1]))
        c.apply_translation([x + 0.2 + i * 0.9, 6.5 - i * 0.16, z])
        O.add("Manche_A_Air", "orange" if i % 2 == 0 else "blanc", c)


def lampadaires(O):
    for x in (-DEMI + 3.4, DEMI - 3.4):
        for z in np.arange(-45, 46, 30):
            O.add("Lampadaires", "poteau", cyl(0.12, 6.0, x, 0, z, 12))
            sgn = 1 if x < 0 else -1
            O.add("Lampadaires", "poteau", boite(min(x, x + sgn * 1.4), 5.85, z - 0.08, max(x, x + sgn * 1.4), 6.0, z + 0.08))
            O.add("Lampadaires", "sombre", boite(x + sgn * 1.0, 5.6, z - 0.3, x + sgn * 1.7, 5.85, z + 0.3))
            O.add("Lampadaires", "feu_blanc", boite(x + sgn * 1.05, 5.55, z - 0.25, x + sgn * 1.65, 5.6, z + 0.25))


def haies(O):
    """haie bombee tout le long du grillage, cote interieur (comme Infinity Tower)"""
    for c in range(4):
        for t in np.arange(-DEMI + 1.6, DEMI - 1.5, 1.7):
            x, z = [(t, -DEMI + 1.6), (DEMI - 1.6, t), (t, DEMI - 1.6), (-DEMI + 1.6, t)][c]
            b = trimesh.creation.icosphere(2, 1.0)
            b.apply_scale([1.15 + rng.uniform(0, 0.2), 0.85 + rng.uniform(0, 0.25), 1.15 + rng.uniform(0, 0.2)])
            b.apply_translation([x, 0.55, z])
            O.add("Haies", "haie", b)
        O.add("Haies", "beton", boite(*[(-DEMI + 0.4, 0, -DEMI + 0.4, DEMI - 0.4, 0.25, -DEMI + 2.9),
                                         (DEMI - 2.9, 0, -DEMI + 0.4, DEMI - 0.4, 0.25, DEMI - 0.4),
                                         (-DEMI + 0.4, 0, DEMI - 2.9, DEMI - 0.4, 0.25, DEMI - 0.4),
                                         (-DEMI + 0.4, 0, -DEMI + 0.4, -DEMI + 2.9, 0.25, DEMI - 0.4)][c]))


def arbre(O, nom, x, z, h=1.0):
    O.add(nom, "tronc", tronc_cone(0.35 * h, 0.22 * h, 3.2 * h, x, 0, z, 12))
    for dx, dy, dz, r, k in ((0, 4.2, 0, 2.2, "feuillage"), (1.3, 3.6, 0.6, 1.5, "feuillage_fonce"),
                             (-1.2, 3.7, -0.5, 1.6, "feuillage_fonce"), (0.3, 5.4, -0.3, 1.5, "feuillage")):
        b = trimesh.creation.icosphere(2, r * h)
        b.apply_scale([1, 0.85, 1])
        b.apply_translation([x + dx * h, dy * h, z + dz * h])
        O.add(nom, k, b)


def arbres(O):
    pos = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (DEMI - 7), sz * (DEMI - 7)
            pos += [(cx, cz, 1.3), (cx - sx * 7, cz, 1.0), (cx, cz - sz * 7, 1.0)]
    for a in (-30, 30):
        for x, z in ((a, -DEMI + 6), (a, DEMI - 6), (-DEMI + 6, a), (DEMI - 6, a)):
            pos.append((x, z, 0.9))
    for i, (x, z, h) in enumerate(pos):
        if abs(x - 50) < 4 and abs(z + 50) < 4:
            continue
        arbre(O, f"Arbre_{i + 1:02d}", x, z, h)


if __name__ == "__main__":
    O = Objets()
    sols(O)
    grillage(O)
    piste(O)
    terminal(O)
    for i, xa in enumerate((-55, 0, 55)):
        avion(O, f"Avion_Gare_{i + 1}", xa, 88.0, 0.0)
    avion(O, "Avion_Piste", -150.0, -102.5, -90.0, 4.0)       # un avion pret a decoller sur la piste
    avion(O, "Avion_Decollage", 70.0, -102.5, -90.0, 4.0, alt=24.0, tangage=12.0)   # un avion qui decolle
    tour(O)
    hangars(O)
    manche_a_air(O)
    lampadaires(O)
    haies(O)
    arbres(O)
    noms = O.exporter(SORTIE)
    print(SORTIE, round(os.path.getsize(SORTIE) / 1e6, 2), "Mo", len(noms) + 1, "objets")
