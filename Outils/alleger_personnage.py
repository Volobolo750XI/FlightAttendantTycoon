"""Allège un personnage très détaillé (FBX/GLB de plusieurs centaines de milliers de triangles)
en un static mesh low poly, en gardant exactement son style : la texture d'origine est
"recuite" (baked) sur le modèle allégé.

Étapes : fusion des sommets -> réduction (quadric) -> nouvelles UV (xatlas)
-> pour chaque pixel de la nouvelle texture, on retrouve le point le plus proche
sur le modèle d'origine et on y lit la couleur.

Usage : python3 alleger_personnage.py entree.glb sortie.glb [triangles=8000] [texture=1024]
"""
import sys

import numpy as np
import trimesh
import xatlas
import pyfqmr
from PIL import Image, ImageFilter
from scipy.spatial import cKDTree
from trimesh.visual.material import PBRMaterial


def charger(path):
    s = trimesh.load(path)
    m = s.dump(concatenate=True) if isinstance(s, trimesh.Scene) else s
    return m


def bake(orig, low_v, low_f, uv, taille):
    img_src = np.asarray(orig.visual.material.baseColorTexture.convert("RGB"), dtype=np.float32)
    H, W = img_src.shape[:2]
    ouv = orig.visual.uv
    tri = orig.triangles
    tree = cKDTree(tri.mean(axis=1))
    out = np.zeros((taille, taille, 3), np.float32)
    rempli = np.zeros((taille, taille), bool)
    # rasterise chaque triangle low poly dans l'espace UV
    pts3d, pix = [], []
    for f in low_f:
        t = uv[f] * taille
        x0, y0 = np.floor(t.min(0)).astype(int)
        x1, y1 = np.ceil(t.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        p = np.column_stack([xs.ravel() + 0.5, ys.ravel() + 0.5])
        a, b, c = t
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (p[:, 0] - c[0]) + (c[0] - b[0]) * (p[:, 1] - c[1])) / den
        l2 = ((c[1] - a[1]) * (p[:, 0] - c[0]) + (a[0] - c[0]) * (p[:, 1] - c[1])) / den
        l3 = 1 - l1 - l2
        ok = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
        if not ok.any():
            continue
        L = np.column_stack([l1, l2, l3])[ok]
        pts3d.append(L @ low_v[f])
        pix.append(np.floor(p[ok]).astype(int))
    P = np.vstack(pts3d)
    X = np.vstack(pix)
    keep = (X[:, 0] >= 0) & (X[:, 0] < taille) & (X[:, 1] >= 0) & (X[:, 1] < taille)
    P, X = P[keep], X[keep]
    # point le plus proche sur l'original : parmi les 8 triangles aux centres les plus proches
    _, cand = tree.query(P, k=8)
    best = np.full(len(P), np.inf)
    best_uv = np.zeros((len(P), 2))
    for j in range(cand.shape[1]):
        ti = cand[:, j]
        T = tri[ti]
        q = trimesh.triangles.closest_point(T, P)
        d = np.linalg.norm(q - P, axis=1)
        bc = trimesh.triangles.points_to_barycentric(T, q)
        u = np.einsum("ij,ijk->ik", bc, ouv[orig.faces[ti]])
        m = d < best
        best[m] = d[m]
        best_uv[m] = u[m]
    px = np.clip((best_uv[:, 0] % 1.0) * W, 0, W - 1).astype(int)
    py = np.clip((1 - best_uv[:, 1] % 1.0) * H, 0, H - 1).astype(int)
    out[taille - 1 - X[:, 1], X[:, 0]] = img_src[py, px]
    rempli[taille - 1 - X[:, 1], X[:, 0]] = True
    img = Image.fromarray(out.astype(np.uint8))
    # bords : on étale les couleurs dans les zones vides (évite les coutures)
    masque = Image.fromarray((rempli * 255).astype(np.uint8))
    for _ in range(8):
        flou = img.filter(ImageFilter.MaxFilter(3))
        img = Image.composite(img, flou, masque)
        masque = masque.filter(ImageFilter.MaxFilter(3))
    return img


def alleger(entree, sortie, cible=8000, taille=1024):
    orig = charger(entree)
    soude = trimesh.Trimesh(orig.vertices, orig.faces, process=True)  # fusionne les coutures UV
    s = pyfqmr.Simplify()
    s.setMesh(soude.vertices, soude.faces)
    s.simplify_mesh(target_count=cible, aggressiveness=5, preserve_border=True, verbose=0)
    v, f, _ = s.getMesh()
    vmap, idx, uv = xatlas.parametrize(v, f)
    v2 = v[vmap]
    tex = bake(orig, v2, idx, uv, taille)
    low = trimesh.Trimesh(v2, idx, process=False,
                          visual=trimesh.visual.TextureVisuals(uv=uv, material=PBRMaterial(
                              baseColorTexture=tex, metallicFactor=0.0, roughnessFactor=0.85)))
    low.export(sortie)
    print(sortie, len(idx), "triangles")
    return low


if __name__ == "__main__":
    a = sys.argv
    alleger(a[1], a[2], int(a[3]) if len(a) > 3 else 8000, int(a[4]) if len(a) > 4 else 1024)
