"""OBJETS 3D CARTOON du lobby (style du HUD : couleurs franches, gros contour sombre) :
- Liasse_Cartoon.glb   : une liasse de billets verts avec sa bande blanche "$"
- Pile_Liasses.glb     : une pile de liasses (pyramide) pour decorer, comme a Infinity Tower
- Rebirth_3D.glb       : le symbole REBIRTH (deux fleches rondes, rose + blanc) en 3D
Le contour noir cartoon est une "coque inversee" (une copie un peu plus grosse, faces retournees) :
ca marche dans UEFN sans materiau special.
Repere : face avant vers -Z, Y en haut, pose au sol (y = 0).  Usage : python3 generate_objets_cartoon.py
"""
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Polygon, box as rect
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(HERE))
LOBBY = os.path.join(os.path.dirname(HERE), "Lobby")
POLICE = os.path.join(RACINE, "Outils", "TitanOne-Regular.ttf")
PBR = trimesh.visual.material.PBRMaterial
CONTOUR = (22, 27, 48)


def lin(rgb):
    c = np.asarray(rgb, float) / 255.0
    return list(np.round(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4) * 255).astype(int)) + [255]


def col(nom, rgb, rugo=0.45, em=None):
    return PBR(name=nom, baseColorFactor=lin(rgb), roughnessFactor=rugo, metallicFactor=0.0, emissiveFactor=em)


# ------------------------------------------------------------------ textures
def tex_billet():
    W, H = 1024, 448
    img = Image.new("RGB", (W, H), (70, 175, 85))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([14, 14, W - 14, H - 14], 30, outline=(30, 110, 55), width=14)
    d.rounded_rectangle([46, 46, W - 46, H - 46], 22, fill=(120, 210, 120), outline=(40, 135, 65), width=6)
    d.ellipse([W / 2 - 150, H / 2 - 150, W / 2 + 150, H / 2 + 150], fill=(70, 175, 85), outline=(30, 110, 55), width=10)
    f = ImageFont.truetype(POLICE, 230)
    d.text((W / 2, H / 2 + 6), "$", font=f, fill=(225, 255, 225), anchor="mm", stroke_width=10, stroke_fill=(30, 110, 55))
    f2 = ImageFont.truetype(POLICE, 90)
    for x, y in ((120, 110), (W - 120, 110), (120, H - 110), (W - 120, H - 110)):
        d.text((x, y), "100", font=f2, fill=(30, 110, 55), anchor="mm")
    return img


def tex_tranche():
    """le cote de la liasse : plein de feuilles empilees"""
    W, H = 512, 128
    img = Image.new("RGB", (W, H), (205, 240, 200))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 8):
        d.line([(0, y), (W, y)], fill=(95, 180, 100), width=3)
    return img


def tex_bande():
    W, H = 256, 512
    img = Image.new("RGB", (W, H), (248, 250, 246))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 18, H], fill=(30, 140, 75))
    d.rectangle([W - 18, 0, W, H], fill=(30, 140, 75))
    d.text((W / 2, H / 2), "$", font=ImageFont.truetype(POLICE, 190), fill=(30, 150, 80), anchor="mm")
    return img


M = {
    "billet": PBR(name="BilletDessus", baseColorTexture=tex_billet(), roughnessFactor=0.55, metallicFactor=0.0),
    "tranche": PBR(name="BilletTranche", baseColorTexture=tex_tranche(), roughnessFactor=0.6, metallicFactor=0.0),
    "bande": PBR(name="BilletBande", baseColorTexture=tex_bande(), roughnessFactor=0.5, metallicFactor=0.0),
    "contour": col("ContourCartoon", CONTOUR, 0.7),
    "rose": col("RebirthRose", (240, 92, 168), 0.35),
    "rose_clair": col("RebirthRoseClair", (255, 160, 210), 0.3),
    "blanc": col("RebirthBlanc", (246, 244, 255), 0.35),
    "lavande": col("RebirthLavande", (205, 200, 245), 0.35),
    "etincelle": col("RebirthEtincelle", (255, 230, 250), 0.3, [0.9, 0.75, 0.9]),
}


# ------------------------------------------------------------------ outils
def coque(m, ep):
    """contour cartoon : copie gonflee le long des normales, faces retournees"""
    c = m.copy()
    c.merge_vertices()
    c.vertices = c.vertices + c.vertex_normals * ep
    c.invert()
    return c


def avec_uv(m, uv, k):
    m.visual = trimesh.visual.TextureVisuals(uv=uv, material=M[k])
    return m


def uni(m, k):
    m.visual = trimesh.visual.TextureVisuals(material=M[k])
    return m


def boite_uv(w, h, l, k_dessus, k_cote, rep_cote=(1.0, 1.0)):
    """boite (w en X, h en Y, l en Z) posee sur y=0 : dessus/dessous texture k_dessus, tour texture k_cote"""
    x, y, z = w / 2, h, l / 2
    faces = []
    # dessus (y = h) et dessous (y = 0)
    for yy, s in ((y, 1), (0, -1)):
        v = [[-x, yy, -z], [x, yy, -z], [x, yy, z], [-x, yy, z]]
        uv = [[1, 1], [0, 1], [0, 0], [1, 0]]
        f = [[0, 2, 1], [0, 3, 2]] if s > 0 else [[0, 1, 2], [0, 2, 3]]
        faces.append((k_dessus, v, uv, f))
    # 4 cotes
    cotes = [([[-x, 0, -z], [x, 0, -z], [x, y, -z], [-x, y, -z]], w), ([[x, 0, z], [-x, 0, z], [-x, y, z], [x, y, z]], w),
             ([[x, 0, -z], [x, 0, z], [x, y, z], [x, y, -z]], l), ([[-x, 0, z], [-x, 0, -z], [-x, y, -z], [-x, y, z]], l)]
    for v, L in cotes:
        uv = [[0, 0], [rep_cote[0] * L, 0], [rep_cote[0] * L, rep_cote[1]], [0, rep_cote[1]]]
        faces.append((k_cote, v, uv, [[0, 2, 1], [0, 3, 2]]))
    out = {}
    for k, v, uv, f in faces:
        m = trimesh.Trimesh(np.array(v, float), np.array(f), process=False)
        if np.dot(m.face_normals[0], m.triangles_center[0] - [0, h / 2, 0]) < 0:
            m.invert()
        out.setdefault(k, []).append(avec_uv(m, np.array(uv, float), k))
    return out


def fusion(*ds):
    out = {}
    for d in ds:
        for k, ms in d.items():
            out.setdefault(k, []).extend(ms)
    return out


def transformer(d, T):
    out = {}
    for k, ms in d.items():
        for m in ms:
            m = m.copy()
            m.apply_transform(T)
            out.setdefault(k, []).append(m)
    return out


def exporter(d, chemin, nom):
    sc = trimesh.Scene()
    for k, ms in d.items():
        m = trimesh.util.concatenate(ms)
        if k in ("billet", "tranche", "bande"):
            m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([x.visual.uv for x in ms]), material=M[k])
        else:
            m.visual = trimesh.visual.TextureVisuals(material=M[k])
        sc.add_geometry(m, node_name=f"{nom}__{k}", geom_name=f"{nom}__{k}")
    sc.export(chemin)
    # un seul objet
    import json
    import struct
    b = open(chemin, "rb").read()
    lj = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + lj])
    rest = b[20 + lj:]
    prims = [p for nd in js["nodes"] if "mesh" in nd for p in js["meshes"][nd["mesh"]]["primitives"]]
    js["meshes"], js["nodes"] = [{"name": nom, "primitives": prims}], [{"name": nom, "mesh": 0}]
    js["scenes"], js["scene"] = [{"nodes": [0]}], 0
    s = json.dumps(js, separators=(",", ":")).encode()
    s += b" " * ((4 - len(s) % 4) % 4)
    open(chemin, "wb").write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(s) + len(rest)) + struct.pack("<II", len(s), 0x4E4F534A) + s + rest)
    nb = sum(len(m.faces) for ms in d.values() for m in ms)
    print(chemin, round(os.path.getsize(chemin) / 1e3), "Ko", nb, "triangles")


# ------------------------------------------------------------------ liasse
def liasse():
    W, H, L = 0.62, 0.14, 0.28
    corps = boite_uv(W, H, L, "billet", "tranche", (1.0, 1.0))
    # bande au milieu (un peu plus grosse)
    bande = boite_uv(0.13, H + 0.012, L + 0.012, "bande", "bande", (1.0 / 0.28, 1.0))
    bande = transformer(bande, translation_matrix([0, -0.006, 0]))
    d = fusion(corps, bande)
    # contour cartoon autour de la liasse
    tout = trimesh.util.concatenate([m for ms in corps.values() for m in ms])
    d["contour"] = [coque(tout, 0.012)]
    return d


# ------------------------------------------------------------------ pile de liasses
def pile():
    r = np.random.default_rng(4)
    d = {}
    niveaux = [(4, 3), (3, 2), (2, 1), (1, 1)]
    for n, (nx, nz) in enumerate(niveaux):
        for i in range(nx):
            for j in range(nz):
                x = (i - (nx - 1) / 2) * 0.66 + r.uniform(-0.04, 0.04)
                z = (j - (nz - 1) / 2) * 0.32 + r.uniform(-0.03, 0.03)
                T = translation_matrix([x, n * 0.15, z]) @ rotation_matrix(math.radians(r.uniform(-8, 8)), [0, 1, 0])
                d = fusion(d, transformer(liasse(), T))
    return d


# ------------------------------------------------------------------ rebirth
def tube_arc(R, r_w, r_d, a0, a1, n=40, m=16):
    """tube (section ellipse r_w dans le plan, r_d en profondeur) le long d'un arc de cercle du plan XY"""
    V, F = [], []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        c = np.array([R * math.cos(a), R * math.sin(a), 0.0])
        rad = np.array([math.cos(a), math.sin(a), 0.0])
        # pointe arrondie au depart : la section se reduit un peu
        s = min(1.0, 0.55 + 0.45 * (i / 4)) if i < 4 else 1.0
        for j in range(m):
            t = 2 * math.pi * j / m
            V.append(c + rad * math.cos(t) * r_w * s + np.array([0, 0, 1.0]) * math.sin(t) * r_d * s)
    for i in range(n):
        for j in range(m):
            a, b = i * m + j, i * m + (j + 1) % m
            F += [[a, b, a + m], [b, b + m, a + m]]
    V = np.array(V)
    c0, c1 = len(V), len(V) + 1
    V = np.vstack([V, V[:m].mean(0), V[-m:].mean(0)])
    for j in range(m):
        F += [[c0, (j + 1) % m, j], [c1, n * m + j, n * m + (j + 1) % m]]
    t = trimesh.Trimesh(V, np.array(F), process=True)
    trimesh.repair.fix_normals(t)
    return t


def tete_fleche(R, a, larg, long, ep, sens=1):
    """triangle epais au bout de l'arc (angle a), pointe dans le sens de rotation"""
    c = np.array([R * math.cos(a), R * math.sin(a)])
    rad = np.array([math.cos(a), math.sin(a)])
    tan = np.array([-math.sin(a), math.cos(a)]) * sens
    p = [c + rad * larg / 2, c - rad * larg / 2, c + tan * long]
    m = trimesh.creation.extrude_polygon(Polygon(p).buffer(0.035, 4), ep)
    m.apply_translation([0, 0, -ep / 2])
    return m


def rebirth():
    R, rw, rd = 0.62, 0.15, 0.11
    d = {}
    for k, k2, a0, a1 in (("rose", "rose_clair", math.radians(205), math.radians(345 + 25)),
                          ("blanc", "lavande", math.radians(25), math.radians(165 + 25))):
        tube = tube_arc(R, rw, rd, a0, a1)
        tete = tete_fleche(R, a1, 0.55, 0.36, 0.24)
        d.setdefault(k, []).extend([tube, tete])
        # reflet sur le dessus (petit tube plus clair, decale vers l'avant)
        reflet = tube_arc(R + 0.04, 0.035, 0.02, a0 + 0.35, a0 + (a1 - a0) * 0.6, 24, 8)
        reflet.apply_translation([0, 0, -rd * 0.85])
        d.setdefault(k2, []).append(reflet)
        d.setdefault("contour", []).extend([coque(tube, 0.035), coque(tete, 0.035)])
    # etincelle (etoile a 4 branches) en haut a droite
    pts = []
    for i in range(8):
        a = math.pi / 2 + i * math.pi / 4
        rr = 0.17 if i % 2 == 0 else 0.05
        pts.append((0.78 + rr * math.cos(a), 0.78 + rr * math.sin(a)))
    e = trimesh.creation.extrude_polygon(Polygon(pts), 0.06)
    e.apply_translation([0, 0, -0.03])
    d.setdefault("etincelle", []).append(e)
    d.setdefault("contour", []).append(coque(e, 0.02))
    # debout, pose au sol : centre a 1 m de haut
    return transformer(d, translation_matrix([0, 1.0, 0]))


if __name__ == "__main__":
    exporter(liasse(), os.path.join(LOBBY, "Liasse_Cartoon.glb"), "Liasse_Cartoon")
    exporter(pile(), os.path.join(LOBBY, "Pile_Liasses.glb"), "Pile_Liasses")
    exporter(rebirth(), os.path.join(LOBBY, "Rebirth_3D.glb"), "Rebirth_3D")
