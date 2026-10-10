"""Valises cabine et sacs à dos, en plusieurs couleurs (1 static mesh + 1 matériau chacun).

Fichiers créés (dossier Modeles/Bagages) :
  Valise_<Couleur>.glb        valise tenue en main, poignée télescopique sortie.
                              PIVOT = centre de la poignée (là où se pose la main droite).
  ValiseRangee_<Couleur>.glb  la même couchée à plat, poignée rentrée (pour le coffre).
                              PIVOT = centre du dessous.
  Sac_<Couleur>.glb           sac à dos. PIVOT = haut des bretelles, côté dos du passager
                              (le sac s'étend vers l'arrière, -Z).

Y vers le haut, l'avant vers +Z. Unités : mètres.
Usage : python3 bagages.py [dossier_sortie]
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial

VALISES = {
    "Noire": (38, 40, 44), "BleuMarine": (34, 52, 92), "Rouge": (168, 36, 40),
    "Argent": (176, 180, 186), "Vert": (40, 86, 70), "Rose": (214, 140, 160),
}
SACS = {
    "Noir": (36, 36, 40), "Bleu": (44, 84, 150), "Kaki": (110, 112, 78),
    "Brique": (150, 64, 50), "Gris": (120, 124, 130), "Moutarde": (196, 150, 52),
}


def fonce(c, k):
    return tuple(int(v * k) for v in c)


# ---------------------------------------------------------------- géométrie
def superellipsoide(taille, centre, e=0.2, res=(48, 24)):
    """Boîte aux angles arrondis (e petit = plus carré), bien tessellée."""
    a, b, c = np.asarray(taille, float) / 2
    nu, nv = res
    u = np.linspace(-np.pi, np.pi, nu, endpoint=False)
    v = np.linspace(-np.pi / 2, np.pi / 2, nv)
    U, V = np.meshgrid(u, v)
    p = lambda x, k: np.sign(x) * np.abs(x) ** k
    x = a * p(np.cos(V), e) * p(np.cos(U), e)
    z = c * p(np.cos(V), e) * p(np.sin(U), e)
    y = b * p(np.sin(V), e)
    pts = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
    f = []
    for j in range(nv - 1):
        for i in range(nu):
            p0, q = j * nu + i, j * nu + (i + 1) % nu
            f += [[p0, q + nu, q], [p0, p0 + nu, q + nu]]
    m = trimesh.Trimesh(pts, f)
    m.merge_vertices()
    m.fix_normals()
    m.apply_translation(centre)
    return m


def tube(p0, p1, r, sections=12):
    m = trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections)
    return m


def capsule(p0, p1, r):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    h = np.linalg.norm(p1 - p0)
    m = trimesh.creation.capsule(height=h, radius=r, count=[12, 12])
    # capsule créée le long de Z, centrée
    d = (p1 - p0) / h
    m.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d))
    m.apply_translation((p0 + p1) / 2)
    return m


def courbe(points, largeur, epaisseur, n=10):
    """Sangle lisse : ruban aux bords arrondis balayé le long d'une courbe (Catmull-Rom).
    La largeur est le long de X."""
    p = np.asarray(points, float)
    ext = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    pts = [p[0]]
    for k in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[k - 1:k + 3]
        for t in np.linspace(0, 1, n + 1)[1:]:
            pts.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    P = np.array(pts)
    m = 10
    ang = np.linspace(0, 2 * np.pi, m, endpoint=False)
    c, s_ = np.cos(ang), np.sin(ang)
    prof = np.column_stack([np.sign(c) * np.abs(c) ** 0.4 * largeur / 2, np.sign(s_) * np.abs(s_) ** 0.4 * epaisseur / 2])
    X = np.array([1.0, 0, 0])
    V = []
    for k in range(len(P)):
        t = P[min(k + 1, len(P) - 1)] - P[max(k - 1, 0)]
        t /= np.linalg.norm(t)
        nrm = np.cross(t, X)
        nrm /= np.linalg.norm(nrm)
        V.append(P[k] + prof[:, :1] * X + prof[:, 1:] * nrm)
    V = np.vstack(V)
    F = []
    for k in range(len(P) - 1):
        for j in range(m):
            a, b = k * m + j, k * m + (j + 1) % m
            F += [[a, b, b + m], [a, b + m, a + m]]
    V = np.vstack([V, P[0], P[-1]])
    for j in range(m):
        F.append([len(V) - 2, (j + 1) % m, j])
        F.append([len(V) - 1, (len(P) - 1) * m + j, (len(P) - 1) * m + (j + 1) % m])
    r = trimesh.Trimesh(V, F)
    r.fix_normals()
    return r


# ---------------------------------------------------------------- assemblage (palette)
def assembler(pieces):
    couleurs = list(dict.fromkeys(c for c, _ in pieces))
    cell = 8
    img = Image.new("RGB", (cell * len(couleurs), cell))
    for i, c in enumerate(couleurs):
        img.paste(c, (i * cell, 0, (i + 1) * cell, cell))
    ms = []
    for c, m in pieces:
        m = m.copy()
        u = (couleurs.index(c) + 0.5) / len(couleurs)
        m.visual = trimesh.visual.TextureVisuals(uv=np.tile([u, 0.5], (len(m.vertices), 1)))
        ms.append(m)
    out = trimesh.util.concatenate(ms)
    out.visual = trimesh.visual.TextureVisuals(uv=out.visual.uv, material=PBRMaterial(
        baseColorTexture=img, metallicFactor=0.0, roughnessFactor=0.55))
    return out


# ---------------------------------------------------------------- valise cabine (55 x 40 x 20)
L, H, P = 0.40, 0.55, 0.21       # largeur (le long de la marche : Z), hauteur, épaisseur (X)
ROUE = 0.035


def valise(couleur, rangee=False):
    coque, bord = couleur, fonce(couleur, 0.7)
    noir, gris, metal = (24, 24, 26), (70, 72, 76), (150, 154, 160)
    pieces = []
    y0 = 2 * ROUE + 0.01                    # dessous de la coque (au-dessus des roulettes)
    cy = y0 + H / 2
    # coque en deux moitiés (avant / arrière) séparées par la fermeture éclair
    for s in (-1, 1):
        demi = superellipsoide((P / 2 - 0.004, H, L), [s * (P / 4 + 0.002), cy, 0], e=0.22)
        pieces.append((coque, demi))
    pieces.append((noir, superellipsoide((0.012, H - 0.01, L - 0.01), [0, cy, 0], e=0.25, res=(32, 16))))
    # nervures verticales sur les deux faces
    for s in (-1, 1):
        for z in (-0.11, -0.04, 0.04, 0.11):
            pieces.append((bord, superellipsoide((0.012, H - 0.10, 0.022), [s * (P / 2 + 0.001), cy, z], e=0.4, res=(12, 8))))
    # coins renforcés
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                pieces.append((gris, superellipsoide((0.05, 0.05, 0.05), [sx * (P / 2 - 0.02), cy + sy * (H / 2 - 0.02), sz * (L / 2 - 0.02)], e=0.6, res=(10, 6))))
    # poignée du dessus + supports
    yt = y0 + H
    pieces.append((noir, capsule([0, yt + 0.035, -0.07], [0, yt + 0.035, 0.07], 0.012)))
    for z in (-0.075, 0.075):
        pieces.append((gris, superellipsoide((0.03, 0.04, 0.025), [0, yt + 0.012, z], e=0.4, res=(10, 6))))
    # poignée télescopique (à l'arrière de la valise : -X côté coque arrière... on la met en -Z)
    zt = -L / 2 + 0.015
    sortie = 0.0 if rangee else 0.26
    for x in (-0.055, 0.055):
        pieces.append((metal, tube([x, yt - 0.02, zt], [x, yt + 0.02 + sortie, zt], 0.008)))
        pieces.append((noir, tube([x, yt - 0.005, zt], [x, yt + 0.012, zt], 0.012)))
    pieces.append((noir, capsule([-0.07, yt + 0.035 + sortie, zt], [0.07, yt + 0.035 + sortie, zt], 0.016)))
    # roulettes doubles orientables (4)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (P / 2 - 0.035), sz * (L / 2 - 0.04)
            pieces.append((gris, superellipsoide((0.04, 0.03, 0.04), [x, y0 - 0.005, z], e=0.5, res=(10, 6))))
            for dx in (-0.012, 0.012):
                w = trimesh.creation.cylinder(radius=ROUE, height=0.014, sections=16)
                w.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
                w.apply_translation([x + dx, ROUE, z])
                pieces.append((noir, w))
    # étiquette nominative accrochée à la poignée du dessus
    pieces.append(((230, 210, 120), superellipsoide((0.006, 0.07, 0.045), [0.02, yt - 0.01, 0.05], e=0.5, res=(10, 6))))
    m = assembler(pieces)
    if rangee:
        # couchée à plat sur une grande face, pivot au centre du dessous
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
        c = m.bounds.mean(0)
        m.apply_translation([-c[0], -m.bounds[0][1], -c[2]])
    else:
        # pivot = centre de la poignée télescopique (la main droite s'y pose)
        m.apply_translation([0, -(yt + 0.035 + sortie), -zt])
    return m


# ---------------------------------------------------------------- sac à dos (~ 45 x 30 x 18)
def sac(couleur):
    tissu, sombre = couleur, fonce(couleur, 0.72)
    noir, gris, zip_ = (30, 30, 32), (90, 92, 96), (190, 190, 194)
    pieces = []
    W, Hs, D = 0.30, 0.45, 0.16
    cz = -0.03 - D / 2                     # le sac est derrière le dos (-Z)
    cy = -0.06 - Hs / 2                    # sous le haut des bretelles (pivot)
    pieces.append((tissu, superellipsoide((W, Hs, D), [0, cy, cz], e=0.42)))
    pieces.append((sombre, superellipsoide((W - 0.01, 0.07, D - 0.01), [0, cy - Hs / 2 + 0.03, cz], e=0.35, res=(32, 10))))   # fond renforcé
    # poche avant + fermetures
    pieces.append((sombre, superellipsoide((W * 0.78, Hs * 0.42, 0.06), [0, cy - 0.07, cz - D / 2 - 0.01], e=0.4, res=(32, 14))))
    pieces.append((zip_, superellipsoide((W * 0.7, 0.008, 0.01), [0, cy + 0.02, cz - D / 2 - 0.038], e=0.5, res=(12, 4))))
    pieces.append((zip_, superellipsoide((W * 0.9, 0.008, 0.01), [0, cy + Hs / 2 - 0.05, cz - D / 2 + 0.01], e=0.5, res=(12, 4))))
    for x in (0.09, -0.07):  # tirettes
        pieces.append((noir, superellipsoide((0.012, 0.035, 0.006), [x, cy + 0.005, cz - D / 2 - 0.045], e=0.6, res=(8, 5))))
    # poches latérales
    for s in (-1, 1):
        pieces.append((sombre, superellipsoide((0.05, Hs * 0.35, D * 0.7), [s * (W / 2 + 0.005), cy - Hs * 0.22, cz], e=0.45, res=(16, 10))))
    # poignée du dessus
    pieces.append((noir, courbe([[0, cy + Hs / 2 - 0.01, cz + 0.045], [0, cy + Hs / 2 + 0.03, cz + 0.03], [0, cy + Hs / 2 + 0.03, cz - 0.01], [0, cy + Hs / 2 - 0.01, cz - 0.025]], 0.03, 0.008, 6)))
    # dos rembourré
    pieces.append((sombre, superellipsoide((W * 0.8, Hs * 0.8, 0.03), [0, cy, -0.02], e=0.4, res=(24, 12))))
    # bretelles : du haut du dos (pivot) jusqu'en bas du sac, en passant devant (épaules)
    for s in (-1, 1):
        x = s * 0.08
        pieces.append((noir, courbe([[x, -0.07, -0.035], [x, -0.005, -0.01], [x * 1.05, 0.0, 0.05], [x * 1.15, -0.06, 0.11],
                                     [x * 1.3, -0.22, 0.13], [x * 1.4, -0.38, 0.09], [x * 1.4, cy - Hs / 2 + 0.07, -0.025]], 0.055, 0.012, 8)))
        pieces.append((gris, superellipsoide((0.03, 0.02, 0.012), [x * 1.3, -0.42, 0.06], e=0.5, res=(8, 5))))
    return assembler(pieces)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Modeles", "Bagages")
    os.makedirs(out, exist_ok=True)
    for nom, c in VALISES.items():
        for rangee, pref in ((False, "Valise"), (True, "ValiseRangee")):
            m = valise(c, rangee)
            m.export(os.path.join(out, f"{pref}_{nom}.glb"))
        print("valise", nom, len(m.faces), "triangles")
    for nom, c in SACS.items():
        m = sac(c)
        m.export(os.path.join(out, f"Sac_{nom}.glb"))
        # version rangée : le même sac couché à plat sur le dos (bretelles dessous, poche avant
        # vers le haut), pivot au centre du dessous : il se pose à plat sur le fond du coffre
        r = m.copy()
        r.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        c0 = r.bounds.mean(axis=0)
        r.apply_translation([-c0[0], -r.bounds[0][1], -c0[2]])
        r.export(os.path.join(out, f"SacRange_{nom}.glb"))
        print("sac", nom, len(m.faces), "triangles")
