"""CASQUETTE DE PILOTE (commandant de bord), modele "ressemblant" : calotte blanche bombee et relevee a l'avant,
bandeau bleu marine, visiere noire vernie, cordon dore avec 2 boutons, insigne a ailes dore sur l'avant,
doublure sombre a l'interieur. Tout est lisse (normales partagees).
Repere : avant (visiere) vers -Z, Y en haut, bas du bandeau a y = 0, taille reelle (tete ~ 58 cm).
Sorties : Modeles/Lobby/Casquette_Pilote.glb    Usage : python3 generate_casquette_pilote.py [--apercu]
(--apercu : couleurs non converties en lineaire, pour les rendus de controle)
"""
import math
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import Polygon
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Casquette_Pilote.glb")
APERCU = "--apercu" in sys.argv
PBR = trimesh.visual.material.PBRMaterial


def lin(rgb):
    c = np.asarray(rgb, float) / 255.0
    if APERCU:
        return list(np.round(c * 255).astype(int)) + [255]
    return list(np.round(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4) * 255).astype(int)) + [255]


M = {
    "blanc": PBR(name="CasquetteBlanc", baseColorFactor=lin((244, 245, 248)), roughnessFactor=0.55, metallicFactor=0.0),
    "marine": PBR(name="CasquetteMarine", baseColorFactor=lin((26, 32, 62)), roughnessFactor=0.6, metallicFactor=0.0),
    "visiere": PBR(name="CasquetteVisiere", baseColorFactor=lin((14, 15, 20)), roughnessFactor=0.12, metallicFactor=0.0),
    "or": PBR(name="CasquetteOr", baseColorFactor=lin((222, 178, 92)), roughnessFactor=0.28, metallicFactor=1.0),
    "doublure": PBR(name="CasquetteDoublure", baseColorFactor=lin((40, 36, 44)), roughnessFactor=0.8, metallicFactor=0.0),
    "passepoil": PBR(name="CasquettePassepoil", baseColorFactor=lin((18, 20, 34)), roughnessFactor=0.5, metallicFactor=0.0),
}

A, B = 0.098, 0.118          # demi-largeur / demi-profondeur du tour de tete (ellipse)
N = 96                       # points par anneau
TH = np.linspace(0, 2 * np.pi, N, endpoint=False)
AVANT = ((1 - np.sin(TH)) / 2) ** 1.5         # 1 a l'avant (-Z), 0 a l'arriere, transition douce (pas de pli)

# profil exterieur : (echelle du rayon, hauteur, relevement avant) -- de bas en haut
PROFIL = [(1.000, 0.000, 0.000), (1.000, 0.020, 0.000), (1.004, 0.040, 0.000), (1.012, 0.056, 0.003),
          (1.05, 0.066, 0.012), (1.12, 0.077, 0.026), (1.21, 0.088, 0.041), (1.29, 0.098, 0.053),
          (1.335, 0.105, 0.060), (1.34, 0.1105, 0.063), (1.31, 0.1145, 0.063), (1.21, 0.1175, 0.058),
          (1.02, 0.1195, 0.047), (0.78, 0.1205, 0.034), (0.50, 0.1210, 0.021), (0.24, 0.1212, 0.009), (0.0, 0.1213, 0.0)]
BANDEAU_HAUT = 0.058         # au-dessus : calotte blanche


def anneau(e, y, rel, decal=0.0):
    x = (A * e + decal) * np.cos(TH)
    z = (B * e + decal) * np.sin(TH)
    yy = y + rel * AVANT
    return np.c_[x, yy, z]


def loft(anneaux, fermer_haut=True):
    V = np.vstack(anneaux)
    F = []
    for i in range(len(anneaux) - 1):
        for j in range(N):
            a, b = i * N + j, i * N + (j + 1) % N
            F += [[a, a + N, b], [b, a + N, b + N]]
    return V, F


def surface():
    """calotte + bandeau (exterieur), doublure (interieur), bord bas : un seul maillage ferme, par materiau"""
    ext = [anneau(e, y, r) for e, y, r in PROFIL[:-1]]
    V, F = loft(ext)
    top = len(V)
    V = np.vstack([V, [[0, PROFIL[-1][1], 0]]])
    last = (len(ext) - 1) * N
    for j in range(N):
        F.append([last + j, top, last + (j + 1) % N])
    # doublure : un peu plus petite, du bas jusqu'a un fond plat
    ep = 0.004
    doub = [anneau(1.0, 0.0, 0, -ep), anneau(1.0, 0.05, 0, -ep), anneau(1.03, 0.075, 0.004, -ep), anneau(0.9, 0.092, 0.006, -ep)]
    d0 = len(V)
    V = np.vstack([V] + doub + [[[0, 0.094, 0]]])
    for i in range(len(doub) - 1):
        for j in range(N):
            a, b = d0 + i * N + j, d0 + i * N + (j + 1) % N
            F += [[a, b, a + N], [b, b + N, a + N]]
    dl = d0 + (len(doub) - 1) * N
    for j in range(N):
        F.append([dl + j, dl + (j + 1) % N, len(V) - 1])
    # bord bas : relie l'exterieur (anneau 0) a la doublure (anneau d0)
    for j in range(N):
        a, b = j, (j + 1) % N
        F += [[a, b, d0 + j], [b, d0 + (j + 1) % N, d0 + j]]
    F = np.array(F)
    m = trimesh.Trimesh(V, F, process=False)
    # orientation : volume positif
    if m.volume < 0:
        m.invert()
    # materiaux par face
    c = m.triangles_center
    r = np.hypot(c[:, 0] / A, c[:, 2] / B)
    groupes = {"blanc": [], "marine": [], "doublure": []}
    for fi in range(len(m.faces)):
        dedans = np.dot(m.face_normals[fi], [c[fi][0], 0, c[fi][2]]) < 0 and c[fi][1] < 0.095 and r[fi] < 1.07
        if fi >= 0 and any(v >= d0 for v in m.faces[fi]) and not all(v < d0 for v in m.faces[fi]) and c[fi][1] < 0.002:
            groupes["marine"].append(fi)          # bord bas
        elif all(v >= d0 for v in m.faces[fi]):
            groupes["doublure"].append(fi)
        elif all(v < 4 * N for v in m.faces[fi]):            # anneaux 0..3 du profil = le bandeau
            groupes["marine"].append(fi)
        else:
            groupes["blanc"].append(fi)
    out = {}
    for k, idx in groupes.items():
        if idx:
            s = trimesh.Trimesh(m.vertices, m.faces[idx], process=False)
            s.remove_unreferenced_vertices()
            out[k] = [s]
    return out


def tube(points, rayon, sec=12):
    pts = np.asarray(points)
    V, F = [], []
    for i, p in enumerate(pts):
        t = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        t /= np.linalg.norm(t)
        a = np.cross(t, [0, 1, 0])
        if np.linalg.norm(a) < 1e-6:
            a = np.cross(t, [1, 0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(t, a)
        for j in range(sec):
            u = 2 * np.pi * j / sec
            V.append(p + (a * np.cos(u) + b * np.sin(u)) * rayon)
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


def visiere():
    """coque fine et bombee, posee sur l'avant du bas du bandeau, inclinee vers le bas"""
    th = np.linspace(np.radians(196), np.radians(344), 48)
    prof = np.linspace(0, 1, 10)
    larg = 0.060 * np.sin((th - th[0]) / (th[-1] - th[0]) * np.pi) ** 0.55
    haut, bas = [], []
    for k, s in enumerate(prof):
        ligne_h, ligne_b = [], []
        for i, t in enumerate(th):
            d = larg[i] * s
            x = (A + 0.002 + d) * np.cos(t)
            z = (B + 0.002 + d) * np.sin(t)
            y = 0.004 - 0.42 * d - 2.2 * d * d          # descend et se courbe
            ligne_h.append([x, y, z])
            ligne_b.append([x, y - 0.0045 * (1 - 0.4 * s), z])
        haut.append(ligne_h)
        bas.append(ligne_b)
    haut, bas = np.array(haut), np.array(bas)
    nk, ni = haut.shape[:2]
    V = np.vstack([haut.reshape(-1, 3), bas.reshape(-1, 3)])
    off = nk * ni
    F = []
    for k in range(nk - 1):
        for i in range(ni - 1):
            a, b, c, d = k * ni + i, k * ni + i + 1, (k + 1) * ni + i, (k + 1) * ni + i + 1
            F += [[a, c, b], [b, c, d], [off + a, off + b, off + c], [off + b, off + d, off + c]]
    # bords : avant (k = nk-1), arriere (k = 0), extremites (i = 0 et ni-1)
    for i in range(ni - 1):
        for k in (0, nk - 1):
            a, b = k * ni + i, k * ni + i + 1
            F += [[a, b, off + a], [b, off + b, off + a]]
    for k in range(nk - 1):
        for i in (0, ni - 1):
            a, c = k * ni + i, (k + 1) * ni + i
            F += [[a, off + a, c], [c, off + a, off + c]]
    m = trimesh.Trimesh(V, F, process=True)
    trimesh.repair.fix_normals(m)
    return m


def feuilles_visiere():
    """branche de laurier doree sur la visiere (une tige de chaque cote du centre, feuilles pointues en V) :
    la marque du commandant de bord"""
    out = []
    th0, th1 = np.radians(196), np.radians(344)
    SV = 0.70

    def point(sv, t):
        u = (t - th0) / (th1 - th0)
        d = 0.060 * np.sin(u * np.pi) ** 0.55 * sv
        return np.array([(A + 0.002 + d) * np.cos(t), 0.004 - 0.42 * d - 2.2 * d * d, (B + 0.002 + d) * np.sin(t)])

    def repere(t):
        p = point(SV, t)
        tu = point(SV, t + 0.01) - point(SV, t - 0.01)
        tv = point(SV + 0.05, t) - point(SV - 0.05, t)
        n = np.cross(tv, tu)
        n /= np.linalg.norm(n)
        if n[1] < 0:
            n = -n
        tu /= np.linalg.norm(tu)
        return p, tu, n

    feuille = Polygon([(0, 0), (0.0035, 0.0022), (0.0085, 0.0018), (0.0125, 0.0), (0.0085, -0.0018), (0.0035, -0.0022)]).buffer(0.0004, 3)
    gabarit = trimesh.creation.extrude_polygon(feuille, 0.0009)
    centre = np.radians(270)
    for cote in (-1, 1):
        ts = np.linspace(centre + cote * np.radians(6), centre + cote * np.radians(58), 40)
        tige = []
        for t in ts:
            p, tu, n = repere(t)
            tige.append(p + n * 0.0012)
        out.append(tube(tige, 0.0007, 6))
        for i, t in enumerate(ts[2::3]):
            p, tu, n = repere(t)
            dirn = tu * (cote if True else 1)               # la branche pousse vers l'exterieur
            for sgn in (1, -1):
                ang = np.radians(38) * sgn
                ax = dirn * np.cos(ang) + np.cross(n, dirn) * np.sin(ang)
                ay = np.cross(n, ax)
                R = np.eye(4)
                R[:3, 0], R[:3, 1], R[:3, 2] = ax, ay, n
                f = gabarit.copy()
                f.apply_scale(0.85 + 0.35 * (1 - i / 13))
                f.apply_transform(R)
                f.apply_translation(p + n * 0.0010)
                out.append(f)
    return out


def cordon():
    """cordon dore (2 brins tresses) au-dessus de la visiere + 2 boutons"""
    out = []
    th = np.linspace(np.radians(205), np.radians(335), 70)
    for phase in (0, np.pi):
        pts = []
        for i, t in enumerate(th):
            tw = phase + i * 0.9
            r = 0.0048 + 0.0014 * np.cos(tw)
            x = (A + r) * np.cos(t)
            z = (B + r) * np.sin(t)
            y = 0.015 + 0.0014 * np.sin(tw)
            pts.append([x, y, z])
        out.append(tube(pts, 0.0019, 8))
    for t in (np.radians(203), np.radians(337)):
        b = trimesh.creation.icosphere(2, 0.0075)
        b.apply_scale([1, 1, 0.55])
        n = np.array([np.cos(t) / A, 0, np.sin(t) / B])
        n /= np.linalg.norm(n)
        b.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], n))
        b.apply_translation([(A + 0.004) * np.cos(t), 0.015, (B + 0.004) * np.sin(t)])
        out.append(b)
    return out


def insigne():
    """ailes dorees + medaillon (bleu marine, etoile doree), sur l'avant du bandeau"""
    pieces_or, pieces_marine = [], []
    # une aile = une silhouette courbee vers le haut, bord inferieur festonne (plumes), + plumes en relief
    for sx in (1, -1):
        haut = [(0.011, 0.0060), (0.020, 0.0085), (0.030, 0.0110), (0.040, 0.0140), (0.049, 0.0175), (0.054, 0.0195)]
        bas = []
        for i in range(6):                                     # festons : une pointe de plume tous les 7 mm
            x = 0.052 - i * 0.0075
            yb = 0.0150 - i * 0.0042 - 0.0052
            bas += [(x, yb + 0.0016), (x - 0.0035, yb - 0.0010)]
        contour = haut + bas + [(0.011, -0.0050)]
        p = Polygon(contour).buffer(0.0006, 3).buffer(-0.0002, 3)
        m = trimesh.creation.extrude_polygon(p, 0.0020)
        for i in range(5):                                     # plumes en relief (un peu en avant)
            x0 = 0.014 + i * 0.0072
            plume = Polygon([(x0, 0.0062 + i * 0.0021), (x0 + 0.0085, 0.0082 + i * 0.0026), (x0 + 0.0075, 0.0050 + i * 0.0021 - 0.004),
                             (x0 - 0.0005, 0.0030 + i * 0.0010 - 0.0035)]).buffer(0.0005, 2)
            r = trimesh.creation.extrude_polygon(plume, 0.0012)
            r.apply_translation([0, 0, 0.0021])
            m = trimesh.util.concatenate([m, r])
        if sx < 0:
            m.apply_transform(np.diag([-1, 1, 1, 1]))
        pieces_or.append(m)
    disque = trimesh.creation.cylinder(radius=0.0125, height=0.0035, sections=40)
    pieces_or.append(disque.apply_translation([0, 0.0, 0.00175]))
    email = trimesh.creation.cylinder(radius=0.0095, height=0.0016, sections=40)
    pieces_marine.append(email.apply_translation([0, 0.0, 0.0040]))
    etoile = []
    for i in range(10):
        a = np.pi / 2 + i * np.pi / 5
        rr = 0.0072 if i % 2 == 0 else 0.0030
        etoile.append((rr * np.cos(a), rr * np.sin(a)))
    e = trimesh.creation.extrude_polygon(Polygon(etoile), 0.0012)
    pieces_or.append(e.apply_translation([0, 0, 0.0048]))
    # placement : sur l'avant du bandeau, face vers -Z, un peu incline vers l'arriere comme la casquette
    e, y, rel = 1.12, 0.077, 0.026          # point du profil ou on pose l'insigne (devant la calotte)
    zf = -(B * 1.075) - 0.009
    T = translation_matrix([0, 0.078 + 0.026 * 0.6, zf]) @ rotation_matrix(np.pi, [0, 1, 0]) @ \
        rotation_matrix(np.radians(-38), [1, 0, 0]) @ np.diag([1.35, 1.35, 1.35, 1])
    for m in pieces_or + pieces_marine:
        m.apply_transform(T)
    return pieces_or, pieces_marine


def passepoil():
    """fin cordon sombre au bord de la calotte (couture entre dessus et cote)"""
    e, y, r = PROFIL[9]
    pts = anneau(e + 0.008, y, r)
    pts = np.vstack([pts, pts[:1]])
    return tube(pts, 0.0016, 8)


def construire():
    P = surface()
    P.setdefault("visiere", []).append(visiere())
    P.setdefault("or", []).extend(cordon())
    P["or"].extend(feuilles_visiere())
    o, mar = insigne()
    P["or"].extend(o)
    P["marine"].extend(mar)
    P.setdefault("passepoil", []).append(passepoil())
    return P


def exporter(P, chemin, nom="Casquette_Pilote", echelle=1.0):
    sc = trimesh.Scene()
    for k, ms in P.items():
        m = trimesh.util.concatenate(ms)
        m.apply_scale(echelle)
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
    print(chemin, round(os.path.getsize(chemin) / 1e3), "Ko", sum(len(m.faces) for ms in P.values() for m in ms), "triangles")


if __name__ == "__main__":
    out = SORTIE if not APERCU else os.path.join(os.environ.get("APERCU_DIR", "/tmp"), "casquette_apercu.glb")
    exporter(construire(), out)
