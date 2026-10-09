"""Habille le corps de base (Meshy, en caleçon, sans visage) pour créer des passagers.

Principe :
  1. le corps est allégé (~5000 triangles) ;
  2. chaque vêtement est une "coque" : la zone du corps qu'il couvre, découpée proprement
     par des plans, puis gonflée le long des normales (t-shirt, sweat, jean, chaussures, cheveux) ;
  3. tout est fusionné en UN mesh, déplié (xatlas) et une seule texture est peinte :
     peau d'origine + visage peint + tissus (grain, coutures, bords côtelés...).

Résultat : 1 static mesh, 1 matériau, ~8000 triangles. Y vers le haut, pieds à y = 0,
le personnage regarde vers +Z. Unités : mètres.

Usage : python3 habiller.py corps_base.glb dossier_sortie [nom_tenue ...]
"""
import os
import sys

import numpy as np
import pyfqmr
import trimesh
import xatlas
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree
from trimesh.visual.material import PBRMaterial

# ---------------------------------------------------------------- repères du corps de base (m)
CHEVILLE, ENTREJAMBE, TAILLE, POIGNET = 0.11, 0.75, 1.04, 1.00
AISSELLE, COU, MENTON, CRANE = 1.25, 1.545, 1.65, 1.90


def hexa(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


# ---------------------------------------------------------------- tenues
TENUES = {
    "passager_01": dict(
        peau=1.0, cheveux="3a2a1e", coupe="court", barbe=True,
        haut=dict(type="sweat", couleur="6f7466", manches="longues"),
        bas=dict(type="jean", couleur="3d4f6e"),
        chaussures=dict(couleur="d9d5cc", semelle="5a5650"),
    ),
}


# ---------------------------------------------------------------- géométrie
def charger_corps(path, cible=3600):
    s = trimesh.load(path)
    m = s.to_geometry() if isinstance(s, trimesh.Scene) else s
    m.apply_translation([0, -m.bounds[0][1], 0])
    soude = trimesh.Trimesh(m.vertices, m.faces, process=True)
    # la tête garde plus de détails que le reste du corps
    morceaux = []
    for part, n in ((couper(soude, [0, 1.60, 0], [0, -1, 0]), cible),
                    (couper(soude, [0, 1.60, 0], [0, 1, 0]), 1500)):
        simp = pyfqmr.Simplify()
        simp.setMesh(part.vertices, part.faces)
        simp.simplify_mesh(target_count=n, aggressiveness=5, preserve_border=True, verbose=0)
        v, f, _ = simp.getMesh()
        morceaux.append(trimesh.Trimesh(v, f))
    corps = trimesh.util.concatenate(morceaux)
    corps.merge_vertices()
    corps = trimesh.Trimesh(corps.vertices, corps.faces, process=True)
    trimesh.smoothing.filter_taubin(corps, iterations=4)
    return m, corps


def couper(m, origine, normale):
    """Garde la partie du mesh du côté de `normale`."""
    r = trimesh.intersections.slice_mesh_plane(m, plane_normal=normale, plane_origin=origine)
    return r if r is not None else trimesh.Trimesh()


def sans_mains(m):
    c = m.triangles_center
    garder = ~((np.abs(c[:, 0]) > 0.235) & (c[:, 1] < TAILLE + 0.02))
    m = m.copy()
    m.update_faces(garder)
    m.remove_unreferenced_vertices()
    return m


def bord_sommets(m):
    """Arêtes du bord, dans le sens où elles apparaissent dans leur triangle (a -> b)."""
    tri = m.edges_sorted
    u, inv, c = np.unique(tri, axis=0, return_inverse=True, return_counts=True)
    return m.edges[c[inv.ravel()] == 1]


NORMALES = {}


def gonfler(m, epaisseur, bruit=0.0, graine=0, fondu=0.0, ourlet=True):
    """Gonfle la zone. fondu > 0 : l'épaisseur diminue jusqu'à 0 près du bord (cheveux).
    ourlet : referme le bord par une bande vers la peau (pas de trou ni de bord effiloché)."""
    m = m.copy()
    # normales prises sur le corps entier (les bords découpés ont des normales faussées)
    _, i = NORMALES["arbre"].query(m.vertices, k=4)
    n = NORMALES["n"][i].mean(1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    e = np.full(len(m.vertices), epaisseur)
    bord = bord_sommets(m)
    if bruit:
        rng = np.random.default_rng(graine)
        # bosses douces (cheveux) : somme de quelques sinus 3D
        p = m.vertices
        for _ in range(4):
            d = rng.normal(size=3)
            d /= np.linalg.norm(d)
            e += bruit * np.sin(p @ d * rng.uniform(25, 60) + rng.uniform(0, 6))
    if fondu and len(bord):
        d, _ = cKDTree(m.vertices[np.unique(bord)]).query(m.vertices)
        e *= np.clip(d / fondu, 0, 1) ** 0.7
    v0 = m.vertices.copy()
    m.vertices = v0 + n * e[:, None]
    if ourlet and len(bord) and not fondu:
        k = len(m.vertices)
        v = np.vstack([m.vertices, v0 - n * 0.002])
        f = [m.faces]
        a, b = bord[:, 0], bord[:, 1]
        f.append(np.column_stack([b, a, a + k]))
        f.append(np.column_stack([b, a + k, b + k]))
        m = trimesh.Trimesh(v, np.vstack(f), process=False)
        m.remove_unreferenced_vertices()
    return m


def coques(corps, t):
    """Renvoie [(nom_partie, mesh)] pour la tenue t."""
    NORMALES["arbre"] = cKDTree(corps.vertices)
    NORMALES["n"] = corps.vertex_normals
    P = []
    # haut (t-shirt / sweat) : du bas du haut jusqu'au col, manches jusqu'au poignet
    h = t["haut"]
    bas_haut = 0.93 if h["type"] == "sweat" else 0.99
    haut = couper(couper(corps, [0, bas_haut, 0], [0, 1, 0]), [0, COU, 0], [0, -1, 0])
    if h["manches"] == "courtes":
        c = haut.triangles_center
        haut.update_faces(~((np.abs(c[:, 0]) > 0.2) & (c[:, 1] < 1.24)))
        haut.remove_unreferenced_vertices()
    P.append(("haut", gonfler(haut, 0.022 if h["type"] == "sweat" else 0.012)))
    # bas (jean / pantalon) : de la cheville à la taille, sans les mains
    bas = couper(couper(corps, [0, 0.085, 0], [0, 1, 0]), [0, TAILLE, 0], [0, -1, 0])
    P.append(("bas", gonfler(sans_mains(bas), 0.014)))
    # chaussures
    pieds = couper(corps, [0, 0.115, 0], [0, -1, 0])
    ch = gonfler(pieds, 0.016)
    v = ch.vertices.copy()
    v[:, 1] = np.maximum(v[:, 1] - 0.012, 0.0)  # semelle à plat sur le sol
    ch.vertices = v
    P.append(("chaussures", ch))
    # cheveux : plan incliné (plus bas derrière la tête, au-dessus du front devant)
    if t["coupe"] != "chauve":
        n = np.array([0.0, 1.0, -0.8])
        tete = couper(corps, [0, 1.755, 0], n / np.linalg.norm(n))
        tete = couper(tete, [0, MENTON + 0.02, 0], [0, 1, 0])
        P.append(("cheveux", gonfler(tete, 0.016, bruit=0.003, graine=2, fondu=0.03)))
    return P


# ---------------------------------------------------------------- peinture
def bruit2(p, f, graine):
    rng = np.random.default_rng(graine)
    s = np.zeros(len(p))
    for k in range(5):
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        s += np.sin(p @ d * f * (1.7 ** k) + rng.uniform(0, 6)) / (1.6 ** k)
    return s / 2.2


def peindre(partie, p, n, base_rgb, t):
    """Couleur de chaque point 3D p (normales n) de la partie."""
    if partie == "corps":
        c = base_rgb * t["peau"]
        visage = (p[:, 1] > MENTON - 0.01) & (n[:, 2] > 0.25) & (p[:, 2] > 0.04)
        x, y = p[:, 0], p[:, 1]
        fonce = np.array([28, 22, 20.0])
        sourcil = hexa(t["cheveux"]) * 0.8
        for s in (-1, 1):  # yeux
            oeil = visage & (((x - s * 0.035) / 0.010) ** 2 + ((y - 1.772) / 0.0065) ** 2 < 1)
            c[oeil] = fonce
            sc = visage & (((x - s * 0.037) / 0.021) ** 2 + ((y - 1.793 + 0.1 * (x - s * 0.037) * s) / 0.0045) ** 2 < 1)
            c[sc] = sourcil
        bouche = visage & ((x / 0.022) ** 2 + ((y - 1.705) / 0.0035) ** 2 < 1)
        c[bouche] = c[bouche] * 0.68 + np.array([60, 20, 20]) * 0.1
        if t.get("barbe"):
            mach = (p[:, 1] < 1.712 - 0.15 * np.abs(p[:, 0])) & (p[:, 1] > MENTON - 0.03) & (p[:, 2] > -0.03) & ~bouche
            mix = 0.16 + 0.08 * (bruit2(p, 600, 9) > 0)
            c[mach] = c[mach] * (1 - mix[mach, None]) + hexa(t["cheveux"]) * mix[mach, None]
        return c
    if partie == "haut":
        h = t["haut"]
        c = np.tile(hexa(h["couleur"]), (len(p), 1))
        c *= (0.94 + 0.06 * bruit2(p, 140, 1))[:, None]
        # bords côtelés : bas du haut, poignets
        bord = (p[:, 1] < (0.97 if h["type"] == "sweat" else 1.02))
        poignet = (np.abs(p[:, 0]) > 0.22) & (p[:, 1] < POIGNET + 0.05)
        c[bord | poignet] *= 0.86
        if h["type"] == "sweat":  # poche kangourou devant
            poche = (np.abs(p[:, 0]) < 0.11) & (p[:, 1] > 1.06) & (p[:, 1] < 1.17) & (n[:, 2] > 0.5)
            c[poche] *= 0.9
            bordp = poche & ((np.abs(np.abs(p[:, 0]) - 0.105) < 0.006) | (np.abs(p[:, 1] - 1.167) < 0.004))
            c[bordp] *= 0.85
        col = p[:, 1] > COU - 0.025
        c[col] *= 0.88
        return c
    if partie == "bas":
        b = t["bas"]
        c = np.tile(hexa(b["couleur"]), (len(p), 1))
        if b["type"] == "jean":
            # usure : plus clair sur le devant des cuisses et des genoux
            usure = np.clip((n[:, 2] - 0.2), 0, 1) * np.exp(-((p[:, 1] - 0.55) / 0.2) ** 2)
            c = c * (1 + 0.35 * usure[:, None])
            c *= (0.93 + 0.07 * bruit2(p * np.array([1, 0.15, 1]), 300, 3))[:, None]
            # ceinture + ourlet
            c[p[:, 1] > TAILLE - 0.04] *= 0.85
            c[p[:, 1] < 0.13] *= 0.85  # ourlet
        return c
    if partie == "chaussures":
        ch = t["chaussures"]
        c = np.tile(hexa(ch["couleur"]), (len(p), 1))
        c[p[:, 1] < 0.025] = hexa(ch["semelle"])
        c *= (0.95 + 0.05 * bruit2(p, 200, 4))[:, None]
        lacets = (p[:, 2] > 0.04) & (p[:, 1] > 0.06) & (np.abs(np.abs(p[:, 0]) - 0.11) < 0.025) & (np.sin(p[:, 2] * 260) > 0.3)
        c[lacets] *= 0.8
        return c
    if partie == "cheveux":
        c = np.tile(hexa(t["cheveux"]), (len(p), 1))
        meches = bruit2(p * np.array([3, 0.6, 3]), 180, 5)
        c *= (0.85 + 0.25 * meches)[:, None]
        return c
    raise ValueError(partie)


# ---------------------------------------------------------------- assemblage + cuisson
def construire(orig, corps, t, taille_finale=1024):
    taille = taille_finale * 2
    parties = [("corps", corps)] + coques(corps, t)
    noms = [n for n, _ in parties]
    meshes = [m for _, m in parties]
    ids = np.concatenate([np.full(len(m.faces), i) for i, m in enumerate(meshes)])
    tout = trimesh.util.concatenate(meshes)
    vmap, idx, uv = xatlas.parametrize(tout.vertices, tout.faces)
    v = tout.vertices[vmap]
    nrm = tout.vertex_normals[vmap]
    # rasterisation dans l'espace UV
    pts, nn, pix, part = [], [], [], []
    for fi, f in enumerate(idx):
        tt = uv[f] * taille
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
        pts.append(L @ v[f])
        nn.append(L @ nrm[f])
        pix.append(np.floor(q[ok]).astype(int))
        part.append(np.full(ok.sum(), ids[fi]))
    P, N, X, K = np.vstack(pts), np.vstack(nn), np.vstack(pix), np.concatenate(part)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-9
    garde = (X >= 0).all(1) & (X < taille).all(1)
    P, N, X, K = P[garde], N[garde], X[garde], K[garde]

    # couleur d'origine (peau) pour le corps : point le plus proche sur le modèle Meshy
    src = np.asarray(orig.visual.material.baseColorTexture.convert("RGB"), np.float32)
    H, W = src.shape[:2]
    tri = orig.triangles
    arbre = cKDTree(tri.mean(1))
    couleurs = np.zeros((len(P), 3))
    for i, nom in enumerate(noms):
        sel = K == i
        if not sel.any():
            continue
        base = None
        if nom == "corps":
            _, cand = arbre.query(P[sel], k=6)
            best = np.full(sel.sum(), np.inf)
            buv = np.zeros((sel.sum(), 2))
            for j in range(cand.shape[1]):
                T = tri[cand[:, j]]
                q = trimesh.triangles.closest_point(T, P[sel])
                d = np.linalg.norm(q - P[sel], axis=1)
                bc = trimesh.triangles.points_to_barycentric(T, q)
                u = np.einsum("ij,ijk->ik", bc, orig.visual.uv[orig.faces[cand[:, j]]])
                m = d < best
                best[m], buv[m] = d[m], u[m]
            px = np.clip((buv[:, 0] % 1) * W, 0, W - 1).astype(int)
            py = np.clip((1 - buv[:, 1] % 1) * H, 0, H - 1).astype(int)
            base = src[py, px]
        couleurs[sel] = peindre(nom, P[sel], N[sel], base, t)
    img = np.zeros((taille, taille, 3), np.float32)
    rempli = np.zeros((taille, taille), bool)
    img[taille - 1 - X[:, 1], X[:, 0]] = np.clip(couleurs, 0, 255)
    rempli[taille - 1 - X[:, 1], X[:, 0]] = True
    tex = Image.fromarray(img.astype(np.uint8))
    masque = Image.fromarray((rempli * 255).astype(np.uint8))
    for _ in range(6):
        tex = Image.composite(tex, tex.filter(ImageFilter.MaxFilter(3)), masque)
        masque = masque.filter(ImageFilter.MaxFilter(3))
    tex = tex.resize((taille_finale, taille_finale), Image.LANCZOS)
    mesh = trimesh.Trimesh(v, idx, process=False, visual=trimesh.visual.TextureVisuals(
        uv=uv, material=PBRMaterial(baseColorTexture=tex, metallicFactor=0.0, roughnessFactor=0.9)))
    return mesh


if __name__ == "__main__":
    base, sortie = sys.argv[1], sys.argv[2]
    noms = sys.argv[3:] or list(TENUES)
    orig, corps = charger_corps(base)
    orig.apply_translation([0, 0, 0])
    for nom in noms:
        m = construire(orig, corps, TENUES[nom])
        m.export(os.path.join(sortie, nom + ".glb"))
        print(nom, len(m.faces), "triangles", np.round(m.bounds, 3).tolist())
