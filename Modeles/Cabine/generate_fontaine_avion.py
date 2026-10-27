"""FONTAINE A L'AVION (lobby) : fontaine de place en pierre, "ressemblante" :
- grand bassin rond (pierre claire, margelle arrondie, fond et parois interieures en mosaique bleue), marche autour
- colonne moulee + vasque haute ; l'eau deborde de la vasque en rideau
- 8 jets d'eau en arc depuis la margelle vers la vasque
- au sommet : statue d'un avion de ligne qui decolle (aluminium poli, derive verte), porte par une
  trainee argentee qui monte en spirale
Repere : centre au sol, Y en haut, 1 unite = 1 m (bassin de 9 m de large, statue a ~7,5 m).
Sortie : Modeles/Lobby/Fontaine_Avion.glb        Usage : python3 generate_fontaine_avion.py [--apercu]
"""
import math
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Fontaine_Avion.glb")
APERCU = "--apercu" in sys.argv
PBR = trimesh.visual.material.PBRMaterial
rng = np.random.default_rng(12)


def lin(rgb, a=255):
    c = np.asarray(rgb, float) / 255.0
    if not APERCU:
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return list(np.round(c * 255).astype(int)) + [a]


# ------------------------------------------------------------------ textures
def tex_pierre(base, var=10, n=512, joints=False):
    a = np.zeros((n, n, 3)) + base
    g = rng.normal(0, 1, (n // 8, n // 8))
    g = np.asarray(Image.fromarray(((g - g.min()) / np.ptp(g) * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC), float) / 255 - 0.5
    a += g[..., None] * var * 2.2
    a += rng.normal(0, var * 0.5, (n, n, 1))
    for _ in range(140):                                   # petits grains
        x, y = rng.integers(0, n, 2)
        a[max(0, y - 1):y + 2, max(0, x - 1):x + 2] += rng.uniform(-25, 15)
    if joints:                                             # joints entre les blocs de pierre (1 bloc = 1 tuile)
        a[:6, :] *= 0.72
        a[:, :6] *= 0.72
        a[n // 2 - 3:n // 2 + 3, :] *= 0.78
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))


def tex_mosaique(n=512):
    img = Image.new("RGB", (n, n), (230, 236, 238))
    d = ImageDraw.Draw(img)
    c = 32
    for i in range(n // c):
        for j in range(n // c):
            t = rng.uniform(0, 1)
            col = (int(40 + 40 * t), int(140 + 50 * t), int(185 + 40 * t))
            d.rectangle([i * c + 2, j * c + 2, i * c + c - 2, j * c + c - 2], fill=col)
    return img.filter(ImageFilter.GaussianBlur(0.7))


def tex_eau(n=512):
    a = np.zeros((n, n, 3)) + (40, 150, 185)
    yy, xx = np.mgrid[0:n, 0:n] / n
    for k in range(6):
        fx, fy, ph = rng.uniform(4, 12), rng.uniform(4, 12), rng.uniform(0, 6)
        a += (np.sin(xx * fx * 6.28 + np.sin(yy * fy * 6.28 + ph) * 1.5) * 9)[..., None] * np.array([0.6, 0.9, 1.0])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def mat_tex(nom, img, rugo, alpha=None):
    m = PBR(name=nom, baseColorTexture=img, roughnessFactor=rugo, metallicFactor=0.0)
    if alpha is not None:
        m.baseColorFactor = [255, 255, 255, alpha]
        m.alphaMode = "BLEND"
    return m


M = {
    "pierre": mat_tex("FontainePierre", tex_pierre((214, 207, 194), joints=True), 0.75),
    "pierre_sombre": mat_tex("FontainePierreSombre", tex_pierre((150, 150, 152), 9), 0.8),
    "mosaique": mat_tex("FontaineMosaique", tex_mosaique(), 0.3),
    "eau": mat_tex("FontaineEau", tex_eau(), 0.04),
    "jet": PBR(name="FontaineJet", baseColorFactor=lin((215, 240, 255), 150), roughnessFactor=0.05, metallicFactor=0.0,
               alphaMode="BLEND"),
    "alu": PBR(name="StatueAlu", baseColorFactor=lin((222, 226, 232)), roughnessFactor=0.28, metallicFactor=0.65),
    "vert": PBR(name="StatueVert", baseColorFactor=lin((30, 160, 88)), roughnessFactor=0.25, metallicFactor=0.3),
    "sombre": PBR(name="StatueVitres", baseColorFactor=lin((30, 40, 58)), roughnessFactor=0.1, metallicFactor=0.2),
    "trainee": PBR(name="StatueTrainee", baseColorFactor=lin((236, 240, 246)), roughnessFactor=0.18, metallicFactor=0.85),
    "bronze": PBR(name="FontaineBronze", baseColorFactor=lin((150, 110, 70)), roughnessFactor=0.35, metallicFactor=1.0),
}
TEXTURES = {"pierre": 1.2, "pierre_sombre": 1.2, "mosaique": 0.9, "eau": 3.0}


# ------------------------------------------------------------------ outils
def tour(profil, sections=96):
    """solide de revolution autour de Y ; profil = liste (rayon, hauteur) de l'interieur vers l'exterieur, ferme"""
    m = trimesh.creation.revolve([(r, h) for r, h in profil], sections=sections)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    if m.is_watertight and m.volume < 0:
        m.invert()
    return m


def uv_monde(m, tuile):
    m = m.copy()
    m.unmerge_vertices()
    v, n = m.vertices, m.face_normals
    uv = np.zeros((len(v), 2))
    for fi, f in enumerate(m.faces):
        ax = np.argmax(np.abs(n[fi]))
        p = v[f]
        uv[f] = np.c_[p[:, 2], p[:, 1]] if ax == 0 else (np.c_[p[:, 0], p[:, 2]] if ax == 1 else np.c_[p[:, 0], p[:, 1]])
    return m, uv / tuile


def tube(points, rayons, sec=14):
    pts = np.asarray(points, float)
    rayons = np.broadcast_to(np.asarray(rayons, float), (len(pts),))
    V, F = [], []
    prev = None
    for i, p in enumerate(pts):
        t = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        t /= np.linalg.norm(t)
        if prev is None:
            a = np.cross(t, [0, 1, 0]) if abs(t[1]) < 0.9 else np.cross(t, [1, 0, 0])
        else:
            a = prev - t * np.dot(prev, t)
        a /= np.linalg.norm(a)
        prev = a
        b = np.cross(t, a)
        for j in range(sec):
            u = 2 * np.pi * j / sec
            V.append(p + (a * np.cos(u) + b * np.sin(u)) * rayons[i])
    n = len(pts)
    for i in range(n - 1):
        for j in range(sec):
            q, w = i * sec + j, i * sec + (j + 1) % sec
            F += [[q, w, q + sec], [w, w + sec, q + sec]]
    V = np.array(V)
    c0, c1 = len(V), len(V) + 1
    V = np.vstack([V, pts[0], pts[-1]])
    for j in range(sec):
        F += [[c0, (j + 1) % sec, j], [c1, (n - 1) * sec + j, (n - 1) * sec + (j + 1) % sec]]
    m = trimesh.Trimesh(V, F, process=False)
    if m.volume < 0:
        m.invert()
    return m


# ------------------------------------------------------------------ la fontaine
R_BASSIN = 4.5
Y_EAU = 0.48


def bassin(P):
    # marche / dallage autour
    P.setdefault("pierre_sombre", []).append(tour([(0.0, -0.10), (R_BASSIN + 1.6, -0.10), (R_BASSIN + 1.6, 0.06),
                                                    (R_BASSIN + 1.55, 0.08), (R_BASSIN + 1.1, 0.08), (R_BASSIN + 1.1, 0.14),
                                                    (R_BASSIN + 1.05, 0.16), (0.0, 0.16)]))
    # moulure (boudin) sur la face exterieure du bassin
    prof_m = [(R_BASSIN - 0.02, 0.22)] + [(R_BASSIN + 0.06 * math.sin(math.pi * k / 8), 0.22 + 0.10 * k / 8) for k in range(9)] + \
             [(R_BASSIN - 0.02, 0.32)]
    P.setdefault("pierre", []).append(tour(prof_m))
    # mur du bassin avec margelle arrondie (profil ferme : interieur -> exterieur)
    ri, re = R_BASSIN - 0.38, R_BASSIN
    prof = [(ri, 0.15), (re, 0.15), (re, 0.52), (re + 0.06, 0.55)]
    for k in range(9):                                       # arrondi de la margelle
        a = math.pi * k / 8
        prof.append((re - 0.16 + 0.22 * math.cos(a), 0.62 + 0.09 * math.sin(a)))
    prof += [(ri - 0.06, 0.62), (ri - 0.04, 0.56), (ri, 0.54)]
    P.setdefault("pierre", []).append(tour(prof))
    # interieur : fond + paroi en mosaique (un peu sous l'eau)
    P.setdefault("mosaique", []).append(tour([(0.0, 0.19), (ri - 0.01, 0.19), (ri - 0.01, 0.53), (ri - 0.02, 0.53), (ri - 0.02, 0.21), (0.0, 0.21)]))
    # l'eau
    P.setdefault("eau", []).append(tour([(0.0, Y_EAU - 0.02), (ri - 0.015, Y_EAU - 0.02), (ri - 0.015, Y_EAU), (0.0, Y_EAU)]))


def tour_module(rayon, y0, y1, n_y=24, sections=160, motif=None):
    """surface de revolution dont le rayon varie avec l'angle (cannelures, godrons) ; rayon(t) avec t de 0 a 1"""
    th = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    V = []
    for i in range(n_y + 1):
        t = i / n_y
        y = y0 + (y1 - y0) * t
        r = rayon(t) * (motif(th, t) if motif else 1.0)
        V.append(np.c_[r * np.cos(th), np.full(sections, y), r * np.sin(th)])
    V = np.vstack(V + [[[0, y0, 0]], [[0, y1, 0]]])
    F = []
    for i in range(n_y):
        for j in range(sections):
            a, b = i * sections + j, i * sections + (j + 1) % sections
            F += [[a, a + sections, b], [b, a + sections, b + sections]]
    c0, c1 = len(V) - 2, len(V) - 1
    last = n_y * sections
    for j in range(sections):
        F += [[c0, j, (j + 1) % sections], [c1, last + (j + 1) % sections, last + j]]
    m = trimesh.Trimesh(V, F, process=False)
    if m.volume < 0:
        m.invert()
    return m


def colonne(P):
    # pied mouluré, fut cannele (approx. par un profil), chapiteau, vasque
    pied = [(0.0, 0.14), (1.05, 0.14), (1.05, 0.30), (0.95, 0.36), (0.95, 0.44), (0.78, 0.52), (0.62, 0.60),
            (0.56, 0.68), (0.56, 0.74), (0.0, 0.74)]
    P.setdefault("pierre", []).append(tour(pied))
    # fut cannele (20 cannelures)
    P["pierre"].append(tour_module(lambda t: 0.53 - 0.03 * t, 0.72, 2.12, 20, 200,
                                   lambda th, t: 1 - 0.045 * np.clip(np.cos(th * 20), 0, 1) ** 0.6))
    chap = [(0.0, 2.10), (0.53, 2.10), (0.58, 2.18), (0.68, 2.28), (0.64, 2.36), (0.42, 2.42), (0.0, 2.42)]
    P["pierre"].append(tour(chap))
    # godrons sous la vasque (bosses rayonnantes)
    P["pierre"].append(tour_module(lambda t: 0.45 + 1.30 * t ** 1.15, 2.36, 2.98, 16, 192,
                                   lambda th, t: 1 + 0.035 * np.abs(np.sin(th * 12)) * np.sin(np.pi * t)))
    # vasque : coupe evasee avec levre
    vas = [(0.0, 2.35), (0.42, 2.35), (0.9, 2.50), (1.45, 2.78), (1.80, 3.02), (1.92, 3.10), (1.92, 3.18), (1.82, 3.18),
           (1.72, 3.08), (1.20, 2.86), (0.60, 2.70), (0.0, 2.68)]
    P["pierre"].append(tour(vas))
    P.setdefault("eau", []).append(tour([(0.0, 3.04), (1.74, 3.04), (1.74, 3.08), (0.0, 3.08)]))
    # rideau d'eau qui deborde de la levre et retombe dans le bassin (fin, legerement evase)
    rideau = []
    for k, (r, y) in enumerate([(1.95, 3.14), (2.05, 2.95), (2.12, 2.4), (2.16, 1.6), (2.18, 0.9), (2.20, Y_EAU)]):
        rideau.append((r, y))
    pts = [(r, y) for r, y in rideau] + [(r - 0.025, y) for r, y in reversed(rideau)]
    P.setdefault("jet", []).append(tour(pts, 96))
    # petites gouttes / eclaboussures au pied du rideau (anneau d'ecume)
    P["jet"].append(tour([(2.05, Y_EAU + 0.008), (2.38, Y_EAU + 0.008), (2.34, Y_EAU + 0.05), (2.10, Y_EAU + 0.06)], 96))
    # socle de la statue au centre de la vasque
    P["pierre"].append(tour([(0.0, 2.68), (0.42, 2.68), (0.42, 3.25), (0.36, 3.32), (0.0, 3.32)]))
    P.setdefault("bronze", []).append(tour([(0.0, 3.32), (0.37, 3.32), (0.37, 3.36), (0.0, 3.36)]))


def jets(P):
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        r0 = R_BASSIN - 0.30
        pts = []
        for k in range(26):
            t = k / 25
            r = r0 - t * (r0 - 2.25)
            y = 0.70 + 2.1 * t * (1 - t) * 2.0 + (Y_EAU - 0.70) * t ** 3
            pts.append([r * math.cos(a), y, r * math.sin(a)])
        P.setdefault("jet", []).append(tube(pts, np.linspace(0.045, 0.07, 26), 10))
        # buse en bronze sur la margelle
        b = trimesh.creation.cylinder(radius=0.07, height=0.12, sections=16)
        b.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
        b.apply_translation([r0 * math.cos(a), 0.66, r0 * math.sin(a)])
        P.setdefault("bronze", []).append(b)


def statue(P):
    import generate_avion_decor as AV
    AV.RES = 0.75
    parts = AV.parts(False)
    corres = {"av_blanc": "alu", "av_aile": "alu", "av_chrome": "alu", "av_porte": "alu", "av_pneu": "sombre",
              "av_vert": "alu", "av_vert_fonce": "alu", "av_vitre": "sombre", "av_sombre": "sombre",
              "av_feu_rouge": "sombre", "av_feu_vert": "sombre", "av_feu_blanc": "sombre"}
    ech = 0.135
    # l'avion monte (cabre 18 deg) en virage leger (inclinaison 14 deg), nez vers -Z
    T = translation_matrix([0.0, 6.4, 0.6]) @ rotation_matrix(math.radians(-14), [0, 0, 1]) @ \
        rotation_matrix(math.radians(18), [1, 0, 0]) @ np.diag([ech, ech, ech, 1]) @ translation_matrix([0, -3.7, -1.0])
    for k, ms in parts.items():
        if k == "av_logo":
            continue
        for m in ms:
            m = m.copy()
            m.apply_transform(T)
            P.setdefault(corres.get(k, "alu"), []).append(m)
    # tige elegante et effilee (comme une trainee) : part du socle, une seule courbe douce, jusqu'au ventre de l'avion
    pts, ray = [], []
    for k in range(50):
        t = k / 49
        x = 0.35 * math.sin(t * math.pi) * (1 - t)
        z = 0.65 * t ** 1.6 - 0.25 * math.sin(t * math.pi)
        y = 3.34 + t * (6.05 - 3.34)
        pts.append([x, y, z])
        ray.append(0.17 - 0.10 * t ** 0.8)
    P.setdefault("trainee", []).append(tube(pts, ray, 20))


def construire():
    P = {}
    bassin(P)
    colonne(P)
    jets(P)
    statue(P)
    return P


def exporter(P, chemin, nom="Fontaine_Avion"):
    sc = trimesh.Scene()
    for k, ms in P.items():
        m = trimesh.util.concatenate(ms)
        if k in TEXTURES:
            m, uv = uv_monde(m, TEXTURES[k])
            m.visual = trimesh.visual.TextureVisuals(uv=uv, material=M[k])
        else:
            m.visual = trimesh.visual.TextureVisuals(material=M[k])
        sc.add_geometry(m, node_name=f"{nom}__{k}", geom_name=f"{nom}__{k}")
    sc.export(chemin)
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
    print(chemin, round(os.path.getsize(chemin) / 1e6, 2), "Mo", sum(len(m.faces) for ms in P.values() for m in ms), "triangles")


if __name__ == "__main__":
    out = SORTIE if not APERCU else os.path.join(os.environ.get("APERCU_DIR", "/tmp"), "fontaine_apercu.glb")
    exporter(construire(), out)
