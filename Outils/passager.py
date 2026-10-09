"""Passager low poly (classe moyenne, tenue simple un peu négligée).

Un seul mesh, un seul matériau : les couleurs viennent d'une petite texture palette.
Le corps est fait de "lofts" (anneaux arrondis empilés le long d'un chemin), ce qui donne
des facettes douces comme les modèles de référence. Pivot entre les pieds, au sol.
Le personnage regarde vers +Z, Y vers le haut. Unités : mètres (1,78 m).

La valise et le sac à dos sont des meshes séparés.

Usage : python3 passager.py [dossier_sortie]
"""
import os
import sys

import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial

PALETTE = {
    "peau": (214, 164, 128), "peau_ombre": (176, 124, 92), "cheveux": (58, 42, 30),
    "barbe": (120, 92, 72), "yeux": (30, 26, 24), "sweat": (104, 112, 98), "sweat_fonce": (80, 86, 76),
    "tshirt": (196, 188, 168), "jean": (70, 88, 118), "jean_fonce": (52, 64, 88),
    "basket": (212, 208, 198), "semelle": (70, 66, 62), "lacet": (150, 146, 138),
    "valise": (46, 60, 78), "valise_bord": (30, 36, 44), "poignee": (24, 24, 26), "roue": (20, 20, 20),
    "sac": (128, 52, 44), "sac_fonce": (84, 34, 30), "sangle": (40, 40, 40), "zip": (170, 170, 170),
}
NAMES = list(PALETTE)
CELL = 8


def palette_texture():
    img = Image.new("RGB", (CELL * len(NAMES), CELL))
    for i, n in enumerate(NAMES):
        img.paste(PALETTE[n], (i * CELL, 0, (i + 1) * CELL, CELL))
    return img


def uv_of(color):
    return ((NAMES.index(color) + 0.5) / len(NAMES), 0.5)


def superellipse(n, rx, ry, e=2.2):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    return np.column_stack([np.sign(c) * np.abs(c) ** (2 / e) * rx, np.sign(s) * np.abs(s) ** (2 / e) * ry])


def loft(path, rx, ry, color, n=12, e=2.2, side=(1, 0, 0), dz=None, caps=True):
    """Anneaux (rx, ry) placés le long de `path`. `side` = direction de rx.
    dz : décalage avant/arrière de chaque anneau (pour cambrer le dos, le ventre...)."""
    path = np.asarray(path, float)
    k = len(path)
    side = np.asarray(side, float)
    ring_pts = []
    for i in range(k):
        t = path[min(i + 1, k - 1)] - path[max(i - 1, 0)]
        t /= np.linalg.norm(t)
        a = side - t * np.dot(side, t)
        a /= np.linalg.norm(a)
        b = np.cross(a, t)  # pour un chemin vers le haut et side = X : b = +Z (avant)
        p2 = superellipse(n, rx[i], ry[i], e)
        c = path[i] + (b * dz[i] if dz is not None else 0)
        ring_pts.append(c + p2[:, :1] * a + p2[:, 1:] * b)
    v = np.vstack(ring_pts)
    f = []
    for i in range(k - 1):
        for j in range(n):
            p, q = i * n + j, i * n + (j + 1) % n
            f += [[p, q, q + n], [p, q + n, p + n]]
    if caps:
        v = np.vstack([v, path[0], path[-1]])
        b0, b1 = len(v) - 2, len(v) - 1
        for j in range(n):
            f.append([b0, (j + 1) % n, j])
            f.append([b1, (k - 1) * n + j, (k - 1) * n + (j + 1) % n])
    m = trimesh.Trimesh(v, f, process=True)
    m.fix_normals()
    return color, m


def blob(size, center, color, res=(10, 7), e=0.6, rot=None):
    a, b, c = np.asarray(size) / 2
    u = np.linspace(-np.pi, np.pi, res[0], endpoint=False)
    w = np.linspace(-np.pi / 2, np.pi / 2, res[1])
    U, W = np.meshgrid(u, w)
    p = lambda x, k: np.sign(x) * np.abs(x) ** k
    x = a * p(np.cos(W), e) * p(np.cos(U), e)
    z = c * p(np.cos(W), e) * p(np.sin(U), e)
    y = b * p(np.sin(W), e)
    v = np.column_stack([x.ravel(), y.ravel(), z.ravel()])
    f = []
    for j in range(res[1] - 1):
        for i in range(res[0]):
            p0, q = j * res[0] + i, j * res[0] + (i + 1) % res[0]
            f += [[p0, q + res[0], q], [p0, p0 + res[0], q + res[0]]]
    m = trimesh.Trimesh(v, f)
    m.fix_normals()
    if rot is not None:
        m.apply_transform(rot)
    m.apply_translation(center)
    return color, m


def rot(axis, deg):
    return trimesh.transformations.rotation_matrix(np.radians(deg), axis)


def assemble(parts):
    meshes = []
    for color, m in parts:
        m = m.copy()
        m.visual = trimesh.visual.TextureVisuals(uv=np.tile(uv_of(color), (len(m.vertices), 1)))
        meshes.append(m)
    out = trimesh.util.concatenate(meshes)
    out.visual = trimesh.visual.TextureVisuals(
        uv=out.visual.uv,
        material=PBRMaterial(baseColorTexture=palette_texture(), metallicFactor=0.0, roughnessFactor=0.9))
    return out


def lin(a, b, n):
    return np.linspace(a, b, n)


# ---------------------------------------------------------------- personnage
def passager():
    P = []
    # --- jambes (jean) : de la cheville à la hanche, légèrement écartées
    for s in (-1, 1):
        z = [0.075, 0.12, 0.30, 0.47, 0.52, 0.70, 0.86, 0.95]
        x = [0.095, 0.095, 0.092, 0.090, 0.090, 0.088, 0.085, 0.075]
        rx = [0.056, 0.060, 0.064, 0.066, 0.070, 0.082, 0.092, 0.096]
        ry = [0.058, 0.064, 0.070, 0.068, 0.070, 0.080, 0.088, 0.090]
        path = [(s * xi, zi, 0.0) for xi, zi in zip(x, z)]
        P.append(loft(path, rx, ry, "jean", n=12))
        # bas du jean un peu large, retroussé
        P.append(loft([(s * 0.095, 0.075, 0.0), (s * 0.095, 0.115, 0.0)], [0.064, 0.064], [0.068, 0.068], "jean_fonce", n=12))
        # basket : semelle + dessus + lacets
        P.append(blob((0.115, 0.036, 0.285), (s * 0.097, 0.018, 0.045), "semelle", res=(12, 6), e=0.35))
        P.append(blob((0.110, 0.090, 0.255), (s * 0.097, 0.066, 0.040), "basket", res=(12, 7), e=0.55))
        P.append(blob((0.050, 0.020, 0.090), (s * 0.097, 0.100, 0.080), "lacet", res=(8, 5), e=0.5))

    # --- bassin + torse (sweat à capuche), un peu de ventre
    z = [0.86, 0.92, 1.00, 1.08, 1.17, 1.26, 1.34, 1.40, 1.44]
    rx = [0.170, 0.175, 0.168, 0.165, 0.172, 0.182, 0.190, 0.180, 0.120]
    ry = [0.110, 0.112, 0.118, 0.122, 0.120, 0.115, 0.108, 0.100, 0.085]
    dz = [0.000, 0.002, 0.010, 0.014, 0.010, 0.006, 0.000, -0.008, -0.012]
    P.append(loft([(0, zi, 0) for zi in z], rx, ry, "sweat", n=16, e=2.4, dz=dz))
    # ceinture du jean qui dépasse sous le sweat
    P.append(loft([(0, 0.855, 0), (0, 0.895, 0)], [0.168, 0.170], [0.110, 0.111], "jean", n=16, e=2.4))
    # bas du sweat (bande côtelée)
    P.append(loft([(0, 0.895, 0), (0, 0.935, 0)], [0.180, 0.180], [0.118, 0.118], "sweat_fonce", n=16, e=2.4))
    # poche kangourou
    P.append(blob((0.22, 0.10, 0.03), (0, 0.99, 0.120), "sweat_fonce", res=(10, 5), e=0.3))
    # capuche rabattue dans le dos + col
    P.append(loft([(0, 1.36, -0.07), (0, 1.43, -0.085), (0, 1.48, -0.075)], [0.13, 0.14, 0.12], [0.05, 0.06, 0.05], "sweat_fonce", n=12, side=(1, 0, 0)))
    P.append(loft([(0, 1.42, 0.0), (0, 1.46, 0.0)], [0.085, 0.080], [0.075, 0.072], "tshirt", n=12))
    # cordons de capuche
    for s in (-1, 1):
        P.append(loft([(s * 0.04, 1.40, 0.075), (s * 0.045, 1.30, 0.105)], [0.007, 0.007], [0.007, 0.007], "tshirt", n=5, side=(0, 0, 1)))

    # --- bras : manche (épaule -> poignet) puis main
    for s in (-1, 1):
        pts = np.array([(0.165, 1.39, -0.005), (0.215, 1.34, -0.01), (0.235, 1.20, -0.01), (0.245, 1.08, 0.0),
                        (0.255, 0.98, 0.015), (0.262, 0.88, 0.025)])
        pts[:, 0] *= s
        rx = [0.062, 0.060, 0.055, 0.050, 0.046, 0.044]
        P.append(loft(pts, rx, [r * 0.95 for r in rx], "sweat", n=10, side=(0, 0, 1)))
        P.append(loft([(s * 0.262, 0.885, 0.025), (s * 0.264, 0.86, 0.027)], [0.045, 0.045], [0.044, 0.044], "sweat_fonce", n=10, side=(0, 0, 1)))
        # main : paume + pouce
        P.append(blob((0.050, 0.120, 0.088), (s * 0.268, 0.795, 0.030), "peau", res=(8, 7), e=0.65))
        P.append(blob((0.028, 0.060, 0.030), (s * 0.250, 0.815, 0.074), "peau", res=(6, 5), e=0.8, rot=rot((1, 0, 0), -20)))

    # --- cou + tête
    P.append(loft([(0, 1.43, 0.0), (0, 1.53, 0.005)], [0.052, 0.050], [0.055, 0.052], "peau", n=10))
    z = [1.50, 1.535, 1.57, 1.61, 1.65, 1.69, 1.725, 1.75, 1.768]
    rx = [0.042, 0.066, 0.077, 0.082, 0.085, 0.084, 0.075, 0.056, 0.024]
    ry = [0.045, 0.075, 0.088, 0.097, 0.100, 0.098, 0.088, 0.066, 0.028]
    dz = [0.035, 0.022, 0.016, 0.014, 0.010, 0.006, 0.000, -0.004, -0.006]
    P.append(loft([(0, zi, 0) for zi in z], rx, ry, "peau", n=14, e=2.1, dz=dz))
    # barbe de quelques jours (mâchoire)
    P.append(loft([(0, 1.505, 0.032), (0, 1.535, 0.027), (0, 1.575, 0.024)], [0.044, 0.066, 0.075], [0.050, 0.076, 0.086], "barbe", n=14, e=2.1, caps=False))
    # nez
    P.append(blob((0.026, 0.050, 0.030), (0, 1.618, 0.112), "peau_ombre", res=(6, 5), e=0.7, rot=rot((1, 0, 0), 12)))
    # oreilles
    for s in (-1, 1):
        P.append(blob((0.018, 0.050, 0.032), (s * 0.085, 1.635, 0.004), "peau_ombre", res=(6, 5), e=0.8))
        # yeux et sourcils
        P.append(blob((0.020, 0.012, 0.008), (s * 0.033, 1.655, 0.104), "yeux", res=(6, 4), e=0.8))
        P.append(blob((0.034, 0.010, 0.010), (s * 0.034, 1.676, 0.103), "cheveux", res=(6, 4), e=0.5, rot=rot((0, 0, 1), s * -8)))
    # bouche
    P.append(blob((0.036, 0.007, 0.008), (0, 1.581, 0.106), "peau_ombre", res=(6, 4), e=0.6))
    # cheveux courts en bataille : calotte + mèches
    z = [1.665, 1.70, 1.735, 1.76, 1.778, 1.788]
    rx = [0.089, 0.091, 0.085, 0.070, 0.048, 0.013]
    ry = [0.102, 0.105, 0.099, 0.084, 0.058, 0.016]
    dz = [-0.012, -0.004, 0.000, 0.000, -0.002, -0.004]
    P.append(loft([(0, zi, 0) for zi in z], rx, ry, "cheveux", n=14, e=2.1, dz=dz))
    P.append(blob((0.168, 0.15, 0.12), (0, 1.672, -0.045), "cheveux", res=(12, 8), e=0.7))  # arrière / nuque
    rng = np.random.default_rng(3)
    for k in range(9):
        ang = rng.uniform(-np.pi, np.pi)
        P.append(blob((0.05, 0.03, 0.05), (0.06 * np.sin(ang), 1.765 + rng.uniform(-0.01, 0.01), 0.07 * np.cos(ang) - 0.01),
                      "cheveux", res=(6, 4), e=0.7, rot=rot((0, 1, 0), np.degrees(ang))))
    P.append(blob((0.13, 0.03, 0.05), (0.008, 1.725, 0.082), "cheveux", res=(8, 4), e=0.7, rot=rot((0, 0, 1), -6)))  # frange
    return assemble(P)


# ---------------------------------------------------------------- bagages (séparés)
def valise():
    P = []
    P.append(blob((0.40, 0.58, 0.22), (0, 0.33, 0), "valise", res=(16, 10), e=0.22))
    for y in (0.16, 0.33, 0.50):  # nervures
        P.append(blob((0.405, 0.015, 0.225), (0, y, 0), "valise_bord", res=(16, 4), e=0.22))
    for s in (-1, 1):  # tubes de la poignée télescopique
        P.append(loft([(s * 0.12, 0.60, -0.095), (s * 0.12, 0.86, -0.095)], [0.012, 0.012], [0.012, 0.012], "poignee", n=8, side=(0, 0, 1)))
        for z in (-0.08, 0.08):  # roulettes
            P.append(blob((0.03, 0.05, 0.05), (s * 0.16, 0.03, z), "roue", res=(8, 6), e=0.8))
    P.append(blob((0.29, 0.035, 0.04), (0, 0.875, -0.095), "poignee", res=(10, 5), e=0.5))
    P.append(blob((0.14, 0.03, 0.03), (0, 0.635, 0.0), "poignee", res=(8, 4), e=0.5))  # poignée du dessus
    return assemble(P)


def sac_a_dos():
    P = []
    P.append(blob((0.30, 0.44, 0.16), (0, 0.22, 0), "sac", res=(14, 10), e=0.45))
    P.append(blob((0.24, 0.18, 0.07), (0, 0.13, 0.085), "sac_fonce", res=(12, 7), e=0.45))  # poche avant
    P.append(blob((0.20, 0.012, 0.012), (0, 0.225, 0.118), "zip", res=(8, 4), e=0.5))
    P.append(blob((0.07, 0.03, 0.04), (0, 0.455, -0.02), "sangle", res=(8, 4), e=0.5))  # poignée
    for s in (-1, 1):  # bretelles dans le dos
        P.append(loft([(s * 0.08, 0.40, -0.085), (s * 0.09, 0.25, -0.10), (s * 0.10, 0.06, -0.085)],
                      [0.028, 0.030, 0.028], [0.010, 0.010, 0.010], "sangle", n=8, side=(1, 0, 0)))
    return assemble(P)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Modeles")
    for nom, fn in (("passager_01", passager), ("valise", valise), ("sac_a_dos", sac_a_dos)):
        m = fn()
        m.export(os.path.join(out, nom + ".glb"))
        print(nom, len(m.faces), "triangles", np.round(m.bounds, 3).tolist())
