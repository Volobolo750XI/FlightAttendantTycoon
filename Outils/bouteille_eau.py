"""Bouteille d'eau (comme l'icone Produit_01_Eau) : 1 static mesh, 1 materiau, 1 texture.
Fichier : Modeles/Produits/Bouteille_Eau.glb   Y vers le haut, pivot au sol au centre. Metres.
"""
import os
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter
from trimesh.visual.material import PBRMaterial

OUT = os.path.join(os.path.dirname(__file__), "..", "Modeles", "Produits")
os.makedirs(OUT, exist_ok=True)

# ---------- texture : a gauche les couleurs unies, a droite l'etiquette ----------
W, H = 1024, 512
tex = Image.new("RGB", (W, H))
COUL = {"bouchon": (25, 95, 220), "bouchon_fonce": (15, 65, 170), "plastique": (150, 200, 238),
        "plastique_fonce": (110, 165, 215), "eau": (120, 185, 235)}
noms = list(COUL)
case = 512 // len(noms)
for i, n in enumerate(noms):
    tex.paste(COUL[n], (i * case, 0, (i + 1) * case, H))
# etiquette (512 x 512 a droite) : degrade cyan -> bleu, vague blanche, goutte
et = Image.new("RGB", (512, 512))
d = ImageDraw.Draw(et)
for x in range(512):
    t = x / 511
    d.line((x, 0, x, 512), fill=(int(40 + 20 * t), int(200 - 60 * t), int(235 - 10 * t)))
# vague : bande blanche sinueuse
pts_h, pts_b = [], []
for x in range(0, 513, 4):
    y = 300 + 60 * np.sin(x / 512 * 2 * np.pi * 2)
    pts_h.append((x, y - 22)); pts_b.append((x, y + 22))
d.polygon(pts_h + pts_b[::-1], fill=(245, 250, 255))
for x0 in (128, 384):
    d.ellipse((x0 - 30, 150, x0 + 30, 230), fill=(170, 230, 250))
    d.polygon([(x0, 95), (x0 - 27, 175), (x0 + 27, 175)], fill=(170, 230, 250))
et = et.filter(ImageFilter.GaussianBlur(1.2))
# liseres foncés haut/bas de l'etiquette
ImageDraw.Draw(et).rectangle((0, 0, 512, 14), fill=(25, 110, 200))
ImageDraw.Draw(et).rectangle((0, 497, 512, 512), fill=(25, 110, 200))
tex.paste(et, (512, 0))

def uv_couleur(n):
    return [(noms.index(n) + 0.5) * case / W, 0.5]

def revolve(profil, sections=64):
    """profil = [(rayon, z)], tourne autour de Z."""
    p = np.array(profil, float)
    ang = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    V = [(r * np.cos(a), r * np.sin(a), z) for r, z in p for a in ang]
    F = []
    n = sections
    for i in range(len(p) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            F += [[a, b, b + n], [a, b + n, a + n]]
    m = trimesh.Trimesh(V, F, process=False)
    return m, ang, len(p)

pieces = []
def ajouter(m, uv):
    m.visual = trimesh.visual.TextureVisuals(uv=uv)
    pieces.append(m)

# corps (plastique), avec rainures
Z0, ZE0, ZE1, ZEP, ZN = 0.004, 0.065, 0.118, 0.150, 0.172
R = 0.038
prof = [(0.0, 0.0), (0.032, 0.0), (0.037, 0.003), (R, 0.012), (R, 0.022), (R - 0.0025, 0.026), (R, 0.030),
        (R, 0.040), (R - 0.0025, 0.044), (R, 0.048), (R, ZE0), (R, ZE1), (R, 0.128), (R - 0.0025, 0.132),
        (R, 0.136), (R, 0.140), (0.035, 0.150), (0.028, 0.159), (0.020, 0.165), (0.016, 0.169), (0.016, ZN)]
m, _, _ = revolve(prof)
ajouter(m, np.tile(uv_couleur("plastique"), (len(m.vertices), 1)))
# fond (ferme)
m = trimesh.creation.cylinder(radius=0.032, height=0.001, sections=64); m.apply_translation((0, 0, 0.0005))
ajouter(m, np.tile(uv_couleur("plastique_fonce"), (len(m.vertices), 1)))

# etiquette : cylindre un peu plus large, UV sur la partie droite de la texture
sec = 64
ang = np.linspace(0, 2 * np.pi, sec + 1)
Re = R + 0.0008
V, UV, F = [], [], []
NZ = 12
for k, z in enumerate(np.linspace(ZE0, ZE1, NZ)):
    for a in ang:
        V.append((Re * np.cos(a), Re * np.sin(a), z))
        UV.append((0.5 + 0.5 * a / (2 * np.pi), 1.0 - k / (NZ - 1)))
for i in range(NZ - 1):
    for j in range(sec):
        a, b = i * (sec + 1) + j, i * (sec + 1) + j + 1
        F += [[a, b, b + sec + 1], [a, b + sec + 1, a + sec + 1]]
m = trimesh.Trimesh(V, F, process=False)
ajouter(m, np.array(UV))

# bague du goulot
m = trimesh.creation.cylinder(radius=0.019, height=0.004, sections=48); m.apply_translation((0, 0, 0.170))
ajouter(m, np.tile(uv_couleur("plastique_fonce"), (len(m.vertices), 1)))
# bouchon cranté
Zb0, Zb1 = 0.172, 0.197
prof_b = [(0.0, Zb1), (0.019, Zb1), (0.021, Zb1 - 0.002), (0.021, Zb0)]
m, _, _ = revolve(prof_b, 64)
ajouter(m, np.tile(uv_couleur("bouchon"), (len(m.vertices), 1)))
for k in range(18):
    a = 2 * np.pi * k / 18
    c = trimesh.creation.box(extents=(0.003, 0.004, 0.019))
    c.apply_transform(trimesh.transformations.rotation_matrix(a, (0, 0, 1)))
    c.apply_translation((0.0212 * np.cos(a), 0.0212 * np.sin(a), (Zb0 + Zb1 - 0.004) / 2))
    ajouter(c, np.tile(uv_couleur("bouchon_fonce"), (len(c.vertices), 1)))

out = trimesh.util.concatenate(pieces)
out.visual = trimesh.visual.TextureVisuals(uv=out.visual.uv, material=PBRMaterial(
    baseColorTexture=tex, metallicFactor=0.0, roughnessFactor=0.25))
out.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
out.fix_normals()
out.export(os.path.join(OUT, "Bouteille_Eau.glb"))
print(len(out.faces), "triangles")
