"""Personnages animés pour Flight Attendant Tycoon.

À partir d'un personnage très détaillé (Meshy, ~330 000 triangles, pose A) :
  1. allègement (~20 000 triangles) avec 2 textures recuites depuis l'original :
     couleur (base color) + normal map (les détails de l'original : plis, visage, doigts) ;
  2. squelette placé automatiquement selon la morphologie + poids de peau lissés ;
  3. animations : "Marche_Valise" (valise tenue à la main droite), "Marche_SacADos",
     "Assis" (assis sur un siège, respiration et petits mouvements de tête) ;
  4. export GLB (skeletal mesh + animations). La valise et le sac sont des meshes à part,
     accrochés à leurs os (main droite / haut du dos) et cachés (échelle 0) dans les
     animations où ils ne servent pas.

Y vers le haut, pieds à y = 0, le personnage regarde vers +Z. Unités : mètres.

Usage : python3 personnage.py source.glb sortie_dossier nom taille_m
"""
import json
import os
import struct
import sys

import numpy as np
import pyfqmr
import trimesh
import xatlas
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot

sys.path.insert(0, os.path.dirname(__file__))
import passager as accessoires  # noqa: E402  (valise / sac à dos low poly)

FPS = 30


# =============================================================== 1. allègement + cuisson
def charger(path, taille):
    s = trimesh.load(path)
    m = s.to_geometry() if isinstance(s, trimesh.Scene) else s
    m.apply_translation([-m.centroid[0], -m.bounds[0][1], -m.centroid[2]])
    m.apply_scale(taille / m.bounds[1][1])
    return m


def alleger(orig, cible):
    soude = trimesh.Trimesh(orig.vertices, orig.faces, process=True)
    s = pyfqmr.Simplify()
    s.setMesh(soude.vertices, soude.faces)
    s.simplify_mesh(target_count=cible, aggressiveness=5, preserve_border=True, verbose=0)
    v, f, _ = s.getMesh()
    return trimesh.Trimesh(v, f, process=True), soude


def rasteriser(uv, f, v, n, taille):
    pts, nn, pix, fid = [], [], [], []
    for fi, tri in enumerate(f):
        tt = uv[tri] * taille
        x0, y0 = np.floor(tt.min(0)).astype(int) - 1
        x1, y1 = np.ceil(tt.max(0)).astype(int) + 1
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        q = np.column_stack([xs.ravel() + 0.5, ys.ravel() + 0.5])
        a, b, c = tt
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (q[:, 0] - c[0]) + (c[0] - b[0]) * (q[:, 1] - c[1])) / den
        l2 = ((c[1] - a[1]) * (q[:, 0] - c[0]) + (a[0] - c[0]) * (q[:, 1] - c[1])) / den
        L = np.column_stack([l1, l2, 1 - l1 - l2])
        ok = (L > -0.03).all(1)
        if not ok.any():
            continue
        L = np.clip(L[ok], 0, 1)
        L /= L.sum(1, keepdims=True)
        pts.append(L @ v[tri])
        nn.append(L @ n[tri])
        pix.append(np.floor(q[ok]).astype(int))
        fid.append(np.full(ok.sum(), fi))
    return np.vstack(pts), np.vstack(nn), np.vstack(pix), np.concatenate(fid)


def tangentes(v, f, uv, n):
    t = np.zeros_like(v)
    b = np.zeros_like(v)
    p0, p1, p2 = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    w0, w1, w2 = uv[f[:, 0]], uv[f[:, 1]], uv[f[:, 2]]
    e1, e2 = p1 - p0, p2 - p0
    d1, d2 = w1 - w0, w2 - w0
    r = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    r = np.where(np.abs(r) < 1e-12, 1e-12, r)
    sd = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / r[:, None]
    td = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / r[:, None]
    for k in range(3):
        np.add.at(t, f[:, k], sd)
        np.add.at(b, f[:, k], td)
    t = t - n * (n * t).sum(1, keepdims=True)
    t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-12
    w = np.where((np.cross(n, t) * b).sum(1) < 0, -1.0, 1.0)
    return np.column_stack([t, w])


def cuire(orig, soude, low, taille, J=None, H=None):
    """Retourne (sommets, faces, uv, normales, tangentes, tex_couleur, tex_normale)."""
    vmap, f, uv = xatlas.parametrize(low.vertices, low.faces)
    v = low.vertices[vmap]
    n = low.vertex_normals[vmap]
    tg = tangentes(v, f, uv, n)
    T = taille * 2  # cuisson en 2x puis réduction (anti-crénelage)
    P, N, X, F = rasteriser(uv, f, v, n, T)
    TG = np.zeros((len(P), 4))
    # tangente interpolée : on reprend celle du triangle (moyenne de ses sommets)
    TG[:, :3] = tg[f[F]][:, :, :3].mean(1)
    TG[:, 3] = np.sign(tg[f[F]][:, :, 3].sum(1) + 1e-9)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    Tt = TG[:, :3] - N * (N * TG[:, :3]).sum(1, keepdims=True)
    Tt /= np.linalg.norm(Tt, axis=1, keepdims=True) + 1e-12
    B = np.cross(N, Tt) * TG[:, 3:4]
    # point le plus proche sur l'original
    tri = orig.triangles
    arbre = cKDTree(tri.mean(1))
    _, cand = arbre.query(P, k=16)
    if J is not None:
        # une main ne prend ses couleurs que sur une main, la hanche que sur la hanche
        g_orig = zone_main(tri.mean(1), J, H)
        g_low = zone_main(v[f].mean(1), J, H)[F]
    best = np.full(len(P), np.inf)
    buv = np.zeros((len(P), 2))
    bn = np.zeros((len(P), 3))
    hn = soude.vertex_normals
    assert len(soude.faces) == len(orig.faces)
    for j in range(cand.shape[1]):
        ti = cand[:, j]
        Tr = tri[ti]
        q = trimesh.triangles.closest_point(Tr, P)
        d = np.linalg.norm(q - P, axis=1)
        if J is not None:
            d = np.where(g_orig[ti] != g_low, d + 0.05, d)
        bc = trimesh.triangles.points_to_barycentric(Tr, q)
        u = np.einsum("ij,ijk->ik", bc, orig.visual.uv[orig.faces[ti]])
        nh = np.einsum("ij,ijk->ik", bc, hn[soude.faces[ti]])
        m = d < best
        best[m], buv[m], bn[m] = d[m], u[m], nh[m]
    src = np.asarray(orig.visual.material.baseColorTexture.convert("RGB"), np.float32)
    H, W = src.shape[:2]
    px = np.clip((buv[:, 0] % 1) * W, 0, W - 1).astype(int)
    py = np.clip((1 - buv[:, 1] % 1) * H, 0, H - 1).astype(int)
    coul = src[py, px]
    bn /= np.linalg.norm(bn, axis=1, keepdims=True) + 1e-12
    # si la normale haute déf. pointe vers l'intérieur (zones fines), on garde la normale basse
    bn = np.where(((bn * N).sum(1) < 0.2)[:, None], N, bn)
    ts = np.column_stack([(bn * Tt).sum(1), (bn * B).sum(1), (bn * N).sum(1)])
    nrm = (ts * 0.5 + 0.5) * 255

    def image(valeurs, fond):
        img = np.tile(np.array(fond, np.float32), (T, T, 1))
        rempli = np.zeros((T, T), bool)
        img[T - 1 - X[:, 1], X[:, 0]] = valeurs
        rempli[T - 1 - X[:, 1], X[:, 0]] = True
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        masque = Image.fromarray((rempli * 255).astype(np.uint8))
        for _ in range(8):
            im = Image.composite(im, im.filter(ImageFilter.MaxFilter(3)), masque)
            masque = masque.filter(ImageFilter.MaxFilter(3))
        return im.resize((taille, taille), Image.LANCZOS)

    return v, f, uv, n, tg, image(coul, (0, 0, 0)), image(nrm, (128, 128, 255))


# =============================================================== 2. squelette
OS = [  # nom, parent
    ("root", None), ("pelvis", "root"), ("spine_01", "pelvis"), ("spine_02", "spine_01"),
    ("spine_03", "spine_02"), ("neck_01", "spine_03"), ("head", "neck_01"),
    ("clavicle_l", "spine_03"), ("upperarm_l", "clavicle_l"), ("lowerarm_l", "upperarm_l"),
    ("hand_l", "lowerarm_l"), ("fingers_l", "hand_l"),
    ("clavicle_r", "spine_03"), ("upperarm_r", "clavicle_r"), ("lowerarm_r", "upperarm_r"),
    ("hand_r", "lowerarm_r"), ("fingers_r", "hand_r"),
    ("thigh_l", "pelvis"), ("calf_l", "thigh_l"), ("foot_l", "calf_l"), ("ball_l", "foot_l"),
    ("thigh_r", "pelvis"), ("calf_r", "thigh_r"), ("foot_r", "calf_r"), ("ball_r", "foot_r"),
    ("prop_valise", "hand_r"), ("prop_sac", "spine_03"),
]
NOMS = [o[0] for o in OS]
PARENT = {o[0]: o[1] for o in OS}


def ligne_bras(v, H, cote):
    """Centre (x, z) du bras à différentes hauteurs : en pose A, c'est la partie la plus
    à l'extérieur du corps sous l'aisselle."""
    s = H / 1.9
    pts = []
    sel = v[np.sign(v[:, 0]) == cote]
    for fr in np.arange(0.40, 0.735, 0.015):
        y = fr * H
        tr = sel[np.abs(sel[:, 1] - y) < 0.008 * s]
        if len(tr) < 8:
            continue
        xm = np.abs(tr[:, 0]).max()
        bras = tr[np.abs(tr[:, 0]) > xm - 0.09 * s]
        pts.append((y, xm, np.abs(bras[:, 0]).mean(), bras[:, 2].mean(), np.abs(bras[:, 0]).min()))
    return np.array(pts)


def articulations(v, H):
    s = H / 1.9
    J = {}
    J["root"] = np.zeros(3)
    tronc = v[np.abs(v[:, 0]) < 0.05 * s]

    def z_tronc(y):
        t = tronc[np.abs(tronc[:, 1] - y) < 0.015 * s]
        return (t[:, 2].min() + t[:, 2].max()) / 2 if len(t) else 0.0

    hanche_y = 0.515 * H
    J["pelvis"] = np.array([0, 0.54 * H, z_tronc(0.54 * H)])
    J["spine_01"] = np.array([0, 0.60 * H, z_tronc(0.60 * H)])
    J["spine_02"] = np.array([0, 0.67 * H, z_tronc(0.67 * H)])
    J["spine_03"] = np.array([0, 0.74 * H, z_tronc(0.74 * H)])
    J["neck_01"] = np.array([0, 0.835 * H, z_tronc(0.835 * H) - 0.01 * s])
    J["head"] = np.array([0, 0.875 * H, z_tronc(0.875 * H)])
    J["_tete_haut"] = np.array([0, H, z_tronc(0.95 * H)])
    for cote, c in ((1, "l"), (-1, "r")):
        L = ligne_bras(v, H, cote)
        # bas de la main : plus basse tranche où le bras dépasse nettement du corps
        bas_main = v[(np.sign(v[:, 0]) == cote) & (np.abs(v[:, 0]) > 0.24 * s) & (v[:, 1] < 0.6 * H) & (v[:, 1] > 0.3 * H)][:, 1].min()
        poignet_y = bas_main + 0.098 * H
        epaule_y = 0.805 * H

        def centre(y):
            i = np.argmin(np.abs(L[:, 0] - y))
            return L[i, 2], L[i, 3]

        xe, ze = centre(0.72 * H)
        J[f"clavicle_{c}"] = np.array([cote * 0.03 * s, 0.79 * H, z_tronc(0.79 * H) + 0.01 * s])
        J[f"upperarm_{c}"] = np.array([cote * (xe - 0.012 * s), epaule_y, ze])
        coude_y = epaule_y - 0.52 * (epaule_y - poignet_y)
        xc, zc = centre(coude_y)
        J[f"lowerarm_{c}"] = np.array([cote * xc, coude_y, zc])
        xp, zp = centre(poignet_y)
        J[f"hand_{c}"] = np.array([cote * xp, poignet_y, zp])
        d = J[f"hand_{c}"] - J[f"lowerarm_{c}"]
        d /= np.linalg.norm(d)
        J[f"fingers_{c}"] = J[f"hand_{c}"] + d * 0.055 * H
        J[f"_bout_doigts_{c}"] = J[f"hand_{c}"] + d * 0.105 * H
        # jambes
        jambe = v[(np.sign(v[:, 0]) == cote) & (np.abs(v[:, 0]) < 0.2 * s)]

        def centre_j(y, ep=0.012):
            t = jambe[np.abs(jambe[:, 1] - y) < ep * s]
            t = t[np.abs(t[:, 0]) > 0.015 * s]
            return np.abs(t[:, 0]).mean(), (t[:, 2].min() + t[:, 2].max()) / 2

        xg, zg = centre_j(0.28 * H)
        xh, _ = centre_j(0.45 * H)
        J[f"thigh_{c}"] = np.array([cote * min(xh, 0.10 * s), hanche_y, J["pelvis"][2]])
        J[f"calf_{c}"] = np.array([cote * xg, 0.285 * H, zg])
        xa, za = centre_j(0.06 * H)
        pied = jambe[jambe[:, 1] < 0.03 * H]
        J[f"foot_{c}"] = np.array([cote * xa, 0.045 * H, za - 0.01 * s])
        bout = pied[:, 2].max()
        J[f"ball_{c}"] = np.array([cote * xa, 0.012 * H, bout - 0.065 * s])
        J[f"_bout_pied_{c}"] = np.array([cote * xa, 0.01 * H, bout])
        J[f"_L_{c}"] = L
    # accessoires (positions définies dans habiller_accessoires)
    J["prop_valise"] = J["hand_r"] + np.array([0.0, -0.055 * s, 0.01 * s])
    dos = v[(np.abs(v[:, 0]) < 0.08 * s) & (np.abs(v[:, 1] - 0.70 * H) < 0.03 * s)]
    J["prop_sac"] = np.array([0, 0.68 * H, dos[:, 2].min() - 0.085])
    return J


SEGMENTS = {  # os -> (début, fin) pour le calcul des poids
    "pelvis": ("pelvis", "spine_01"), "spine_01": ("spine_01", "spine_02"),
    "spine_02": ("spine_02", "spine_03"), "spine_03": ("spine_03", "neck_01"),
    "neck_01": ("neck_01", "head"), "head": ("head", "_tete_haut"),
}
for c in "lr":
    SEGMENTS.update({
        f"clavicle_{c}": (f"clavicle_{c}", f"upperarm_{c}"), f"upperarm_{c}": (f"upperarm_{c}", f"lowerarm_{c}"),
        f"lowerarm_{c}": (f"lowerarm_{c}", f"hand_{c}"), f"hand_{c}": (f"hand_{c}", f"fingers_{c}"),
        f"fingers_{c}": (f"fingers_{c}", f"_bout_doigts_{c}"),
        f"thigh_{c}": (f"thigh_{c}", f"calf_{c}"), f"calf_{c}": (f"calf_{c}", f"foot_{c}"),
        f"foot_{c}": (f"foot_{c}", f"ball_{c}"), f"ball_{c}": (f"ball_{c}", f"_bout_pied_{c}"),
    })


def dist_segment(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab + 1e-12), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def zone_main(p, J, H):
    """Points appartenant aux mains (sous le poignet, près de l'os de la main)."""
    s = H / 1.9
    m = np.zeros(len(p), bool)
    for cote, c in ((1, "l"), (-1, "r")):
        dm = np.minimum(dist_segment(p, J[f"hand_{c}"], J[f"fingers_{c}"]),
                        dist_segment(p, J[f"fingers_{c}"], J[f"_bout_doigts_{c}"]))
        dh = np.minimum(dist_segment(p, J[f"thigh_{c}"], J[f"calf_{c}"]), dist_segment(p, J["pelvis"], J["spine_01"]))
        m |= (np.sign(p[:, 0]) == cote) & (p[:, 1] < J[f"hand_{c}"][1] + 0.03 * s) & (dm < 0.055 * s) & (dm < 0.6 * dh)
    return m


def poids(v, f, J, H):
    s = H / 1.9
    os_ = list(SEGMENTS)
    D = np.stack([dist_segment(v, J[SEGMENTS[o][0]], J[SEGMENTS[o][1]]) for o in os_], 1)
    autorise = np.ones_like(D, bool)
    col = {o: i for i, o in enumerate(os_)}
    for cote, c in ((1, "l"), (-1, "r")):
        L = J[f"_L_{c}"]
        # bras : sommets proches de la ligne du bras ET à l'extérieur de son bord intérieur
        bord_int = np.interp(v[:, 1], L[:, 0], L[:, 4]) - 0.01 * s
        d_bras = np.minimum.reduce([D[:, col[f"upperarm_{c}"]], D[:, col[f"lowerarm_{c}"]],
                                    D[:, col[f"hand_{c}"]], D[:, col[f"fingers_{c}"]]])
        main = zone_main(v, J, H) & (np.sign(v[:, 0]) == cote)
        d_corps = np.minimum.reduce([D[:, col[o]] for o in ("pelvis", "spine_01", "spine_02", "spine_03",
                                                            f"thigh_{c}", f"calf_{c}")])
        est_bras = ((np.sign(v[:, 0]) == cote) & (v[:, 1] < 0.745 * H) & (d_bras < 0.08 * s)
                    & ((np.abs(v[:, 0]) > bord_int) | main))
        bras_os = [col[f"{b}_{c}"] for b in ("upperarm", "lowerarm", "hand", "fingers")]
        for b in bras_os:
            autorise[(v[:, 1] < 0.745 * H) & ~est_bras, b] = False
        autorise[np.ix_(est_bras, [i for i in range(len(os_)) if i not in bras_os])] = False
        # jambes : chaque côté ne prend que ses propres os de jambe
        for b in ("thigh", "calf", "foot", "ball"):
            autorise[np.sign(v[:, 0]) == -cote, col[f"{b}_{c}"]] = False
    # la tête et le cou ne tirent pas le bas du corps, et inversement
    autorise[v[:, 1] < 0.70 * H, col["neck_01"]] = False
    autorise[v[:, 1] < 0.80 * H, col["head"]] = False
    for b in ("thigh", "calf", "foot", "ball"):
        for c in "lr":
            autorise[v[:, 1] > 0.62 * H, col[f"{b}_{c}"]] = False
    D = np.where(autorise, D, np.inf)
    Wt = 1.0 / (D + 0.004 * s) ** 4
    Wt[~autorise] = 0
    Wt /= Wt.sum(1, keepdims=True) + 1e-12
    # lissage sur le maillage (articulations douces)
    from scipy.sparse import csr_matrix
    ar = np.vstack([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    lignes = np.concatenate([ar[:, 0], ar[:, 1]])
    cols = np.concatenate([ar[:, 1], ar[:, 0]])
    M = csr_matrix((np.ones(len(lignes)), (lignes, cols)), shape=(len(v), len(v)))
    deg = np.asarray(M.sum(1)).ravel() + 1e-9
    for _ in range(6):
        Wt = 0.5 * Wt + 0.5 * (M @ Wt) / deg[:, None]
        Wt[~autorise] = 0
        Wt /= Wt.sum(1, keepdims=True) + 1e-12
    # 4 influences max
    idx = np.argsort(-Wt, 1)[:, :4]
    w4 = np.take_along_axis(Wt, idx, 1)
    w4 /= w4.sum(1, keepdims=True)
    joints = np.array([[NOMS.index(os_[k]) for k in row] for row in idx])
    return joints, w4


# =============================================================== 3. animations
def q(axe, deg):
    return Rot.from_rotvec(np.asarray(axe, float) / np.linalg.norm(axe) * np.radians(deg))


X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)


def gauss(phi, centre, larg):
    d = (phi - centre + 0.5) % 1.0 - 0.5
    return np.exp(-(d / larg) ** 2)


def cycle_jambe(phi):
    """Angles (degrés) d'une jambe au cours d'un pas, phi = 0 : talon qui touche le sol.
    hanche > 0 = cuisse vers l'avant ; genou > 0 = plié ; cheville > 0 = pointe relevée."""
    hanche = 8 + 19 * np.cos(2 * np.pi * phi) + 3 * np.cos(4 * np.pi * phi - 0.6)
    genou = 4 + 14 * gauss(phi, 0.13, 0.07) + 58 * gauss(phi, 0.73, 0.12)
    cheville = (-7 * gauss(phi, 0.06, 0.04) + 10 * gauss(phi, 0.42, 0.12)
                - 18 * gauss(phi, 0.62, 0.05) + 4 * gauss(phi, 0.85, 0.08))
    orteils = 22 * gauss(phi, 0.58, 0.05)
    return hanche, genou, cheville, orteils


def adduction(J, c, cible_deg):
    """Rotation qui ramène le bras (pose A) à `cible_deg` degrés de la verticale."""
    d = J[f"lowerarm_{c}"] - J[f"upperarm_{c}"]
    ang = np.degrees(np.arctan2(abs(d[0]), -d[1]))
    sgn = 1 if c == "l" else -1
    return q(Z, -sgn * (ang - cible_deg))


def anim_marche(J, H, avec_valise):
    duree = 1.1  # pas complet (2 pas)
    n = int(round(duree * FPS)) + 1
    t = np.linspace(0, duree, n)
    R = {o: [] for o in NOMS}
    T_pelvis = []
    s = H / 1.75
    for ti in t:
        phi = ti / duree
        rot = {o: Rot.identity() for o in NOMS}
        # bassin : monte au milieu de l'appui, descend à la pose du talon ; balancement
        dy = 0.016 * s * (-np.cos(4 * np.pi * phi))
        dx = 0.018 * s * np.sin(2 * np.pi * phi)
        T_pelvis.append(J["pelvis"] + np.array([dx, dy - 0.012 * s, 0]))
        lacet = 4 * np.cos(2 * np.pi * phi)
        roulis = 3 * np.sin(4 * np.pi * phi - 0.3) * 0.5
        rot["pelvis"] = q(Y, lacet) * q(Z, roulis) * q(X, 3)
        # le buste compense le bassin (contre-rotation) ; tête stable
        rot["spine_01"] = q(Y, -lacet * 0.5) * q(X, 1.5)
        rot["spine_02"] = q(Y, -lacet * 0.5) * q(Z, -roulis * 0.6)
        rot["spine_03"] = q(Y, -lacet * 0.4) * q(X, -1)
        rot["neck_01"] = q(Y, lacet * 0.2)
        rot["head"] = q(X, -dy / s * 60)
        if avec_valise:  # on penche un peu vers la gauche pour équilibrer la valise
            rot["spine_02"] = rot["spine_02"] * q(Z, 3.5)
            rot["spine_03"] = rot["spine_03"] * q(Z, 2)
            rot["neck_01"] = rot["neck_01"] * q(Z, -3)
        for c, dec in (("r", 0.0), ("l", 0.5)):
            h, g, ch, o = cycle_jambe((phi + dec) % 1.0)
            rot[f"thigh_{c}"] = q(X, -h) * q(Y, 2 if c == "l" else -2)
            rot[f"calf_{c}"] = q(X, g)
            rot[f"foot_{c}"] = q(X, -ch)
            rot[f"ball_{c}"] = q(X, -o)
        # bras : opposés aux jambes
        for c, dec in (("r", 0.5), ("l", 0.0)):
            balance = 17 * np.cos(2 * np.pi * (phi + dec))
            coude = 14 + 9 * max(0.0, np.cos(2 * np.pi * (phi + dec)))
            sgn = 1 if c == "l" else -1
            rot[f"clavicle_{c}"] = q(X, -balance * 0.08)
            rot[f"upperarm_{c}"] = adduction(J, c, 6) * q(X, -balance)
            rot[f"lowerarm_{c}"] = q(X, -coude) * q(Y, sgn * 8)
            rot[f"hand_{c}"] = q(Y, sgn * 10)
            rot[f"fingers_{c}"] = q(X, -12)
            if avec_valise and c == "r":
                # bras droit tendu le long du corps, légèrement écarté, petit balancement
                rot["clavicle_r"] = q(Z, 3)
                rot["upperarm_r"] = adduction(J, "r", 14) * q(X, -4 * np.cos(2 * np.pi * phi))
                rot["lowerarm_r"] = q(X, -4)
                rot["hand_r"] = Rot.identity()
                rot["fingers_r"] = q(X, -75)  # main fermée sur la poignée
        if avec_valise:
            # la valise pend verticalement : on annule la rotation de toute la chaîne du bras
            monde = Rot.identity()
            for o in ("pelvis", "spine_01", "spine_02", "spine_03", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"):
                monde = monde * rot[o]
            rot["prop_valise"] = q(Y, lacet * 0.3) * monde.inv()
        for o in NOMS:
            R[o].append(rot[o].as_quat())
    echelles = {"prop_valise": 1.0 if avec_valise else 0.0, "prop_sac": 0.0 if avec_valise else 1.0}
    return dict(t=t, rot=R, pelvis=np.array(T_pelvis), echelles=echelles)


def fk_monde(J, rot, pelvis_pos):
    """Rotations et positions monde de chaque os (pour la cinématique inverse)."""
    W = {}
    for o in NOMS:
        p = PARENT[o]
        r = rot[o]
        if p is None:
            W[o] = (r, J[o].copy())
            continue
        pr, pp = W[p]
        tr = (pelvis_pos - J["root"]) if o == "pelvis" else (J[o] - J[p])
        W[o] = (pr * r, pp + pr.apply(tr))
    return W


def aligner(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    ax = np.cross(a, b)
    s_ = np.linalg.norm(ax)
    if s_ < 1e-9:
        return Rot.identity()
    return Rot.from_rotvec(ax / s_ * np.arctan2(s_, a @ b))


def ik_bras(J, rot, pelvis_pos, c, cible, pole):
    """Place la main `c` sur `cible` (monde) ; le coude part vers `pole`. Modifie rot."""
    W = fk_monde(J, rot, pelvis_pos)
    S = W[f"upperarm_{c}"][1]
    la = np.linalg.norm(J[f"lowerarm_{c}"] - J[f"upperarm_{c}"])
    lb = np.linalg.norm(J[f"hand_{c}"] - J[f"lowerarm_{c}"])
    d = cible - S
    dist = np.clip(np.linalg.norm(d), abs(la - lb) + 1e-3, la + lb - 1e-3)
    dn = d / np.linalg.norm(d)
    x = (la ** 2 - lb ** 2 + dist ** 2) / (2 * dist)
    h = np.sqrt(max(la ** 2 - x ** 2, 0))
    pp = np.asarray(pole, float) - dn * (np.asarray(pole, float) @ dn)
    pp /= np.linalg.norm(pp)
    coude = S + dn * x + pp * h
    main = S + dn * dist
    u0 = J[f"lowerarm_{c}"] - J[f"upperarm_{c}"]
    l0 = J[f"hand_{c}"] - J[f"lowerarm_{c}"]
    parent_w = W[f"clavicle_{c}"][0]
    Ru = aligner(u0, coude - S)
    # torsion : l'avant de l'os (+Z au repos) regarde vers la main
    av = Ru.apply([0, 0, 1.0])
    ax = (coude - S) / np.linalg.norm(coude - S)
    vise = (main - coude) - ax * ((main - coude) @ ax)
    av_p = av - ax * (av @ ax)
    if np.linalg.norm(vise) > 1e-6 and np.linalg.norm(av_p) > 1e-6:
        Ru = aligner(av_p, vise) * Ru
    Rl = aligner(Ru.apply(l0), main - coude) * Ru
    rot[f"upperarm_{c}"] = parent_w.inv() * Ru
    rot[f"lowerarm_{c}"] = Ru.inv() * Rl


def anim_assis(J, H):
    """Assis sur un siège (assise à ~0,45 m), adossé, mains sur les cuisses.
    Boucle de 6 s : respiration + petits mouvements de tête."""
    duree = 6.0
    n = int(round(duree * FPS)) + 1
    t = np.linspace(0, duree, n)
    R = {o: [] for o in NOMS}
    T_pelvis = []
    cuisse = np.linalg.norm(J["calf_r"] - J["thigh_r"])
    mollet = np.linalg.norm(J["foot_r"] - J["calf_r"])
    # hauteur de la hanche pour que les pieds reposent à plat, tibia légèrement incliné
    hanche_y = mollet * np.cos(np.radians(8)) + J["foot_r"][1]
    descente = J["thigh_r"][1] - hanche_y
    for ti in t:
        ph = ti / duree
        resp = np.sin(2 * np.pi * ph * 2)  # 2 respirations par boucle (3 s)
        regard = 6 * np.sin(2 * np.pi * ph) + 2 * np.sin(2 * np.pi * ph * 3 + 1)
        rot = {o: Rot.identity() for o in NOMS}
        # bassin basculé en arrière (adossé), cuisses à l'horizontale
        rot["pelvis"] = q(X, -12)
        rot["spine_01"] = q(X, 4 + 0.6 * resp)
        rot["spine_02"] = q(X, 3 + 0.8 * resp)
        rot["spine_03"] = q(X, 2 + 0.6 * resp)
        rot["neck_01"] = q(X, 4) * q(Y, regard * 0.4)
        rot["head"] = q(X, 3 - 0.5 * resp) * q(Y, regard * 0.6) * q(Z, 1.5 * np.sin(2 * np.pi * ph + 2))
        for c, sgn in (("l", 1), ("r", -1)):
            rot[f"thigh_{c}"] = q(X, 12) * q(X, -90) * q(Y, sgn * -4) * q(Z, sgn * 4)
            rot[f"calf_{c}"] = q(X, 90 - 8)
            rot[f"foot_{c}"] = q(X, 8 - 12 * 0)
            # bras : coudes pliés, avant-bras posés sur les cuisses
            rot[f"clavicle_{c}"] = q(X, -3)
            rot[f"hand_{c}"] = q(X, 25)
            rot[f"fingers_{c}"] = q(X, 15)
        pel = J["pelvis"] + np.array([0, -descente, -0.02 * H / 1.75])
        # mains posées sur le dessus des cuisses (cinématique inverse), coudes vers l'arrière
        W = fk_monde(J, rot, pel)
        for c, sgn in (("l", 1), ("r", -1)):
            hanche, genou = W[f"thigh_{c}"][1], W[f"calf_{c}"][1]
            cible = hanche + (genou - hanche) * 0.48 + np.array([sgn * 0.01, 0.10 * H / 1.75 + 0.003 * resp, 0])
            # la cible est la paume : on recule du demi-main le long de l'avant-bras
            ik_bras(J, rot, pel, c, cible - np.array([0, 0.0, 0.07 * H / 1.75]), (sgn * 0.6, -0.2, -1.0))
            # main à plat le long de la cuisse (paume vers le bas)
            W2 = fk_monde(J, rot, pel)
            Rl = W2[f"lowerarm_{c}"][0]
            le_long = (genou - hanche) / np.linalg.norm(genou - hanche) + np.array([0, -0.12, 0])
            h0 = J[f"fingers_{c}"] - J[f"hand_{c}"]
            Rh = aligner(Rl.apply(h0), le_long) * Rl
            rot[f"hand_{c}"] = Rl.inv() * Rh
            rot[f"fingers_{c}"] = q(X, 8)
        for o in NOMS:
            R[o].append(rot[o].as_quat())
        T_pelvis.append(pel)
    return dict(t=t, rot=R, pelvis=np.array(T_pelvis), echelles={"prop_valise": 0.0, "prop_sac": 0.0})


# =============================================================== 4. accessoires
def mesh_valise():
    """Valise cabine portée par la poignée du dessus (long côté vers l'avant)."""
    P = []
    b = accessoires.blob
    P.append(b((0.21, 0.52, 0.37), (0, 0.29, 0), "valise", res=(16, 10), e=0.22))
    for y in (0.15, 0.29, 0.43):
        P.append(b((0.215, 0.012, 0.375), (0, y, 0), "valise_bord", res=(16, 4), e=0.22))
    for z in (-0.15, 0.15):
        for x in (-0.07, 0.07):
            P.append(b((0.03, 0.045, 0.045), (x, 0.025, z), "roue", res=(8, 6), e=0.8))
    for z in (-0.06, 0.06):
        P.append(b((0.025, 0.04, 0.025), (0, 0.565, z), "poignee", res=(6, 4), e=0.5))
    P.append(b((0.03, 0.025, 0.16), (0, 0.59, 0), "poignee", res=(8, 4), e=0.5))
    m = accessoires.assemble(P)
    m.apply_translation([0, -0.59, 0])  # origine = poignée (dans la main)
    return m


def mesh_sac():
    m = accessoires.sac_a_dos()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0]))  # bretelles vers le dos
    m.apply_translation([0, -0.24, 0])
    return m


# =============================================================== 5. export GLB
class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.g = {"asset": {"version": "2.0", "generator": "flight-attendant-tycoon"}, "buffers": [],
                  "bufferViews": [], "accessors": [], "images": [], "textures": [], "samplers": [{}],
                  "materials": [], "meshes": [], "nodes": [], "skins": [], "animations": [],
                  "scenes": [{"nodes": []}], "scene": 0}

    def vue(self, data, cible=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        off = len(self.bin)
        self.bin += data
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if cible:
            v["target"] = cible
        self.g["bufferViews"].append(v)
        return len(self.g["bufferViews"]) - 1

    def acc(self, arr, type_, comp, cible=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        bv = self.vue(arr.tobytes(), cible)
        a = {"bufferView": bv, "componentType": comp, "count": len(arr), "type": type_}
        if minmax:
            a["min"] = arr.min(0).tolist() if arr.ndim > 1 else [float(arr.min())]
            a["max"] = arr.max(0).tolist() if arr.ndim > 1 else [float(arr.max())]
        self.g["accessors"].append(a)
        return len(self.g["accessors"]) - 1

    def image(self, img):
        import io
        b = io.BytesIO()
        img.save(b, "PNG")
        bv = self.vue(b.getvalue())
        self.g["images"].append({"bufferView": bv, "mimeType": "image/png"})
        self.g["textures"].append({"source": len(self.g["images"]) - 1, "sampler": 0})
        return len(self.g["textures"]) - 1

    def materiau(self, nom, couleur, normale=None):
        m = {"name": nom, "pbrMetallicRoughness": {"baseColorTexture": {"index": couleur},
                                                   "metallicFactor": 0.0, "roughnessFactor": 0.9}}
        if normale is not None:
            m["normalTexture"] = {"index": normale}
        self.g["materials"].append(m)
        return len(self.g["materials"]) - 1

    def sauver(self, path):
        while len(self.bin) % 4:
            self.bin.append(0)
        self.g["buffers"] = [{"byteLength": len(self.bin)}]
        js = json.dumps(self.g, separators=(",", ":")).encode()
        while len(js) % 4:
            js += b" "
        with open(path, "wb") as fh:
            fh.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin)))
            fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            fh.write(struct.pack("<II", len(self.bin), 0x004E4942) + bytes(self.bin))


def primitive(glb, v, f, uv, n, tg, joints, w, mat):
    F, U, I, I4 = 5126, 5123, 5125, 34962
    attrs = {"POSITION": glb.acc(v.astype(np.float32), "VEC3", F, I4, True),
             "NORMAL": glb.acc(n.astype(np.float32), "VEC3", F, I4),
             "TEXCOORD_0": glb.acc(np.column_stack([uv[:, 0], 1 - uv[:, 1]]).astype(np.float32), "VEC2", F, I4),
             "JOINTS_0": glb.acc(joints.astype(np.uint16), "VEC4", U, I4),
             "WEIGHTS_0": glb.acc(w.astype(np.float32), "VEC4", F, I4)}
    if tg is not None:
        attrs["TANGENT"] = glb.acc(tg.astype(np.float32), "VEC4", F, I4)
    return {"attributes": attrs, "indices": glb.acc(f.astype(np.uint32).ravel(), "SCALAR", I, 34963), "material": mat}


def exporter(path, corps, J, joints, w, anims, props):
    glb = GLB()
    v, f, uv, n, tg, tex_c, tex_n = corps
    m_corps = glb.materiau("Corps", glb.image(tex_c), glb.image(tex_n))
    prims = [primitive(glb, v, f, uv, n, tg, joints, w, m_corps)]
    for nom_os, m in props:
        mt = glb.materiau("Accessoire_" + nom_os, glb.image(m.visual.material.baseColorTexture))
        jo = np.zeros((len(m.vertices), 4), int)
        jo[:, 0] = NOMS.index(nom_os)
        wo = np.zeros((len(m.vertices), 4))
        wo[:, 0] = 1
        vv = m.vertices + J[nom_os]  # en pose de repos, l'accessoire est à son os
        prims.append(primitive(glb, vv, m.faces, m.visual.uv * np.array([1, -1]) + np.array([0, 1]),
                               m.vertex_normals, None, jo, wo, mt))
    glb.g["meshes"].append({"name": "Personnage", "primitives": prims})
    # noeuds des os (rotation de repos = identité, translation relative au parent)
    base = 0
    for i, nom in enumerate(NOMS):
        p = PARENT[nom]
        tr = J[nom] - (J[p] if p else 0)
        enfants = [k for k, o in enumerate(NOMS) if PARENT[o] == nom]
        nd = {"name": nom, "translation": [float(x) for x in tr]}
        if enfants:
            nd["children"] = enfants
        glb.g["nodes"].append(nd)
    ibm = np.stack([np.linalg.inv(trimesh.transformations.translation_matrix(J[o])).T for o in NOMS]).astype(np.float32)
    glb.g["skins"].append({"joints": list(range(len(NOMS))), "skeleton": 0,
                           "inverseBindMatrices": glb.acc(ibm.reshape(-1, 16), "MAT4", 5126)})
    glb.g["nodes"].append({"name": "Personnage", "mesh": 0, "skin": 0})
    glb.g["scenes"][0]["nodes"] = [0, len(NOMS)]
    for nom, a in anims.items():
        chans, samps = [], []
        t_acc = glb.acc(a["t"].astype(np.float32), "SCALAR", 5126, None, True)

        def canal(noeud, chemin, valeurs, typ):
            samps.append({"input": t_acc, "output": glb.acc(np.asarray(valeurs, np.float32), typ, 5126), "interpolation": "LINEAR"})
            chans.append({"sampler": len(samps) - 1, "target": {"node": noeud, "path": chemin}})

        for i, o in enumerate(NOMS):
            if o.startswith("prop_"):
                e = a["echelles"][o]
                canal(i, "scale", np.full((len(a["t"]), 3), max(e, 1e-4)), "VEC3")
                canal(i, "rotation", np.array(a["rot"][o]), "VEC4")
                continue
            if o == "root":
                continue
            canal(i, "rotation", np.array(a["rot"][o]), "VEC4")
        canal(NOMS.index("pelvis"), "translation", a["pelvis"] - J["root"], "VEC3")
        glb.g["animations"].append({"name": nom, "channels": chans, "samplers": samps})
    glb.sauver(path)


# =============================================================== main
def fabriquer(source, dossier, nom, taille, triangles=20000, tex=2048):
    import pickle
    orig = charger(source, taille)
    nuage, _ = trimesh.sample.sample_surface(orig, 250000, seed=1)
    J = articulations(nuage, taille)
    cache = os.path.join(dossier, f".cache3_{nom}_{triangles}_{tex}.pkl")
    if os.path.exists(cache):
        low, corps = pickle.load(open(cache, "rb"))
    else:
        low, soude = alleger(orig, triangles)
        corps = cuire(orig, soude, low, tex, J, taille)
        pickle.dump((low, corps), open(cache, "wb"))
    v, f = corps[0], corps[1]
    # squelette + poids sur le maillage soudé (pas de coutures UV), puis report
    jl, wl = poids(low.vertices, low.faces, J, taille)
    _, i = cKDTree(low.vertices).query(v)
    joints, w = jl[i], wl[i]
    # sur l'original, les mains (et parfois les coudes) sont soudées aux hanches / à la taille :
    # on supprime les triangles qui relient le bras au corps, sinon ils s'étirent en marchant
    bras = [NOMS.index(f"{o}_{c}") for o in ("lowerarm", "hand", "fingers") for c in "lr"]
    corps_os = [NOMS.index(o) for o in ("pelvis", "spine_01", "spine_02", "thigh_l", "thigh_r", "calf_l", "calf_r")]
    dom = joints[:, 0]
    gb, gc = np.isin(dom, bras)[f], np.isin(dom, corps_os)[f]
    melange = gb.any(1) & gc.any(1)
    f = f[~melange]
    # petits morceaux isolés restés collés (bouts de paume contre la hanche) : supprimés
    soude = trimesh.Trimesh(v, f, process=False)
    soude.merge_vertices(merge_tex=True, merge_norm=True)
    lab = trimesh.graph.connected_component_labels(soude.face_adjacency, node_count=len(f))
    tailles = np.bincount(lab)
    f = f[tailles[lab] >= 60]
    corps = (v, f) + tuple(corps[2:])
    # version statique (sans squelette), même maillage et mêmes textures
    statique = trimesh.Trimesh(v, f, process=False, visual=trimesh.visual.TextureVisuals(
        uv=corps[2], material=trimesh.visual.material.PBRMaterial(
            baseColorTexture=corps[5], normalTexture=corps[6], metallicFactor=0.0, roughnessFactor=0.9)))
    statique.export(os.path.join(dossier, nom + "_statique.glb"))
    anims = {"Marche_Valise": anim_marche(J, taille, True), "Marche_SacADos": anim_marche(J, taille, False),
             "Assis": anim_assis(J, taille)}
    exporter(os.path.join(dossier, nom + ".glb"), corps, J, joints, w, anims,
             [("prop_valise", mesh_valise()), ("prop_sac", mesh_sac())])
    print(nom, len(f), "triangles")
    return J


if __name__ == "__main__":
    a = sys.argv
    fabriquer(a[1], a[2], a[3], float(a[4]))
