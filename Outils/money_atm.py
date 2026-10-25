"""Borne MONEY (collecteur d'argent du tycoon), en 2 modeles :
  Modeles/MoneyATM/MoneyATM.glb      : le socle, les 2 poteaux, l'ecran (blanc) et l'enseigne MONEY
  Modeles/MoneyATM/MoneyATM_Pad.glb  : la grosse plaque verte sur laquelle on marche (elle s'enfonce)
Style cartoon : formes arrondies, gris fonce, vert vif, bord blanc.
Pivots au sol, au centre ; l'avant (l'ecran) regarde vers +Z. Unites : metres.
Placer le Pad a la meme position que la borne : il tombe pile dans le creux du socle.
Usage : python3 money_atm.py
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.visual.material import PBRMaterial

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Modeles", "MoneyATM")
POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

COUL = {"fonce": (58, 62, 70), "fonce2": (40, 43, 50), "blanc": (245, 247, 250), "vert": (40, 230, 60),
        "vert2": (25, 175, 45)}
NOMS = list(COUL)


def texture_palette_et_enseigne():
    """Texture 1024 x 1024 : en haut l'enseigne MONEY (1024 x 256), en bas une rangee de couleurs."""
    t = Image.new("RGB", (1024, 1024), COUL["fonce2"])
    d = ImageDraw.Draw(t)
    f = ImageFont.truetype(POLICE, 190)
    for dx in range(-9, 10, 3):
        for dy in range(-9, 10, 3):
            d.text((512 + dx, 128 + dy), "MONEY", font=f, fill=(10, 30, 12), anchor="mm")
    d.text((512, 128), "MONEY", font=f, fill=COUL["vert"], anchor="mm")
    for i, n in enumerate(NOMS):
        t.paste(COUL[n], (i * 64, 960, i * 64 + 64, 1024))
    return t


def uv(n):
    i = NOMS.index(n)
    return ((i * 64 + 32) / 1024, 1 - 992 / 1024)


def couleur(m, n):
    m.visual = trimesh.visual.TextureVisuals(uv=np.tile(uv(n), (len(m.vertices), 1)))
    return m


def plaque_arrondie(lx, lz, ly, r, y0, nom, sections=10, z0=0.0):
    """Une plaque horizontale aux coins arrondis (vue de dessus), epaisseur ly, posee a y0."""
    pts = []
    for cx, cz, a0 in ((lx / 2 - r, lz / 2 - r, 0), (-lx / 2 + r, lz / 2 - r, 90), (-lx / 2 + r, -lz / 2 + r, 180), (lx / 2 - r, -lz / 2 + r, 270)):
        for k in range(sections + 1):
            a = np.radians(a0 + 90 * k / sections)
            pts.append((cx + r * np.cos(a), z0 + cz + r * np.sin(a)))
    n = len(pts)
    V = [(x, y0, z) for x, z in pts] + [(x, y0 + ly, z) for x, z in pts] + [(0, y0, z0), (0, y0 + ly, z0)]
    F = []
    for i in range(n):
        j = (i + 1) % n
        F += [[i, n + j, j], [i, n + i, n + j], [2 * n, i, j], [2 * n + 1, n + j, n + i]]
    m = trimesh.Trimesh(vertices=V, faces=F, process=True)
    trimesh.repair.fix_normals(m)
    return couleur(m, nom)


def cadre_vertical(lx, ly, lz, r, centre, nom, sections=10):
    """Panneau vertical aux coins arrondis (vu de face), epaisseur lz, centre (x, y, z)."""
    m = plaque_arrondie(lx, ly, lz, r, -lz / 2, nom, sections)
    # plaque_arrondie construit dans le plan X/Z : on la redresse (Z -> Y)
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
    m.apply_translation(centre)
    return m


def borne():
    tex = texture_palette_et_enseigne()
    morceaux = []
    # socle (creux : un cadre epais autour de l'emplacement du pad)
    morceaux.append(plaque_arrondie(1.9, 1.25, 0.10, 0.12, 0.0, "fonce"))
    morceaux.append(plaque_arrondie(1.9, 0.18, 0.06, 0.06, 0.10, "fonce2", z0=-0.535))   # rebord arriere
    # 2 poteaux a l'arriere
    for x in (-0.55, 0.55):
        p = trimesh.creation.cylinder(radius=0.07, height=1.25, sections=20)
        p.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
        p.apply_translation((x, 0.16 + 0.625, -0.52))
        morceaux.append(couleur(p, "fonce2"))
    # ecran : cadre gris fonce arrondi + face blanche (le Billboard se pose devant)
    morceaux.append(cadre_vertical(1.55, 0.85, 0.16, 0.14, (0, 1.75, -0.52), "fonce"))
    morceaux.append(cadre_vertical(1.31, 0.62, 0.02, 0.09, (0, 1.75, -0.43), "blanc"))
    # enseigne MONEY au-dessus (un panneau dont la face avant porte la texture)
    e = cadre_vertical(1.25, 0.32, 0.08, 0.06, (0, 2.38, -0.52), "fonce2")
    morceaux.append(e)
    lx, ly, z = 1.21, 0.28, -0.52 + 0.041
    v = np.array([[-lx / 2, 2.38 - ly / 2, z], [lx / 2, 2.38 - ly / 2, z], [lx / 2, 2.38 + ly / 2, z], [-lx / 2, 2.38 + ly / 2, z]])
    q = trimesh.Trimesh(vertices=v, faces=[[0, 1, 2], [0, 2, 3]], process=False)
    q.visual = trimesh.visual.TextureVisuals(uv=np.array([[0, 0.75], [1, 0.75], [1, 1], [0, 1]]))
    morceaux.append(q)
    m = trimesh.util.concatenate(morceaux)
    m.visual = trimesh.visual.TextureVisuals(uv=m.visual.uv, material=PBRMaterial(baseColorTexture=tex, roughnessFactor=0.5, metallicFactor=0.0))
    return m, tex


def pad(tex):
    morceaux = [plaque_arrondie(1.62, 0.95, 0.05, 0.12, 0.10, "blanc", z0=0.08),
                plaque_arrondie(1.52, 0.85, 0.05, 0.10, 0.12, "vert", z0=0.08),
                plaque_arrondie(1.40, 0.73, 0.012, 0.08, 0.17, "vert2", z0=0.08)]
    # reflet clair sur le dessus du vert (cartoon)
    m = trimesh.util.concatenate(morceaux)
    m.visual = trimesh.visual.TextureVisuals(uv=m.visual.uv, material=PBRMaterial(baseColorTexture=tex, emissiveTexture=tex, emissiveFactor=(0.25, 0.25, 0.25), roughnessFactor=0.4, metallicFactor=0.0))
    return m


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    b, tex = borne()
    b.export(os.path.join(SORTIE, "MoneyATM.glb"))
    p = pad(tex)
    p.export(os.path.join(SORTIE, "MoneyATM_Pad.glb"))
    print("borne", b.bounds.round(3).tolist(), "pad", p.bounds.round(3).tolist())
