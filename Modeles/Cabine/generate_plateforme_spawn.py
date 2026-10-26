"""PLATEFORME DU SPAWN (centre du lobby), facon Infinity Tower Tycoon :
- sol rond en paves (beige / terre cuite)
- tout autour, une couronne de bacs a herbe (bordure en pierre grise + herbe dessus), pour y poser des buissons
- 6 ouvertures pour sortir
Origine : centre, au sol. Y en haut.   Sortie : Modeles/Lobby/Plateforme_Spawn.glb
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter
from shapely.affinity import rotate
from shapely.geometry import Point, Polygon
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Plateforme_Spawn.glb")
R_SOL = 16.0        # rayon du sol pave
R_IN, R_OUT = 16.0, 19.0   # couronne des bacs a herbe
H_SOL = 0.15
H_BAC = 0.55
BORD = 0.3          # largeur de la bordure en pierre
TROU = 4.5
ANGLES = (0, 60, 120, 180, 240, 300)
TUILE = 4.0         # metres couverts par une repetition de texture
rng = np.random.default_rng(3)


def texture_paves(n=1024):
    img = Image.new("RGB", (n, n), (120, 92, 78))
    d = ImageDraw.Draw(img)
    rows, cols = 8, 4            # paves 0,5 x 1 m, en quinconce
    ph, pw = n // rows, n // cols
    teintes = [(196, 150, 120), (184, 136, 108), (206, 166, 134), (176, 128, 104), (214, 178, 146)]
    for r in range(rows):
        dec = (pw // 2) * (r % 2)
        for c in range(-1, cols + 1):
            x0 = c * pw + dec
            t = np.array(teintes[rng.integers(len(teintes))]) + rng.integers(-8, 8, 3)
            d.rectangle([x0 + 4, r * ph + 4, x0 + pw - 4, r * ph + ph - 4], fill=tuple(int(v) for v in t))
    bruit = (rng.normal(0, 7, (n, n, 1))).astype(np.int16)
    a = np.clip(np.asarray(img).astype(np.int16) + bruit, 0, 255).astype(np.uint8)
    return Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.8))


def texture_herbe(n=512):
    a = np.zeros((n, n, 3), np.int16) + np.array([86, 170, 60])
    a += rng.normal(0, 14, (n, n, 1)).astype(np.int16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))


def extrusion(poly, y0, y1):
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_translation([0, y0, 0])
    return m


def avec_uv(m, img, nom):
    v = m.vertices
    uv = np.c_[v[:, 0] / TUILE, v[:, 2] / TUILE + v[:, 1] / TUILE]
    mat = trimesh.visual.material.PBRMaterial(name=nom, baseColorTexture=img, metallicFactor=0.0, roughnessFactor=0.9)
    m.visual = trimesh.visual.TextureVisuals(uv=uv, material=mat)
    return m


def uni(m, rgb, nom):
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name=nom, baseColorFactor=[*rgb, 255], metallicFactor=0.0, roughnessFactor=0.85))
    return m


def sans_trous(poly):
    coupe = Polygon([(-TROU / 2, R_IN - 1), (TROU / 2, R_IN - 1), (TROU / 2, R_OUT + 1), (-TROU / 2, R_OUT + 1)])
    for a in ANGLES:
        poly = poly.difference(rotate(coupe, a, origin=(0, 0)))
    return list(getattr(poly, "geoms", [poly]))


sol = Point(0, 0).buffer(R_SOL, 128)
for a in ANGLES:   # les chemins de sortie, paves aussi
    sol = sol.union(rotate(Polygon([(-TROU / 2, 0), (TROU / 2, 0), (TROU / 2, R_OUT), (-TROU / 2, R_OUT)]), a, origin=(0, 0)))
couronne = Point(0, 0).buffer(R_OUT, 128).difference(Point(0, 0).buffer(R_IN, 128))
bacs = sans_trous(couronne)
herbes = [p.buffer(-BORD, join_style=2) for p in bacs]

sc = trimesh.Scene()
sc.add_geometry(avec_uv(extrusion(sol, 0.0, H_SOL), texture_paves(), "Paves"), node_name="Sol_Paves", geom_name="Sol_Paves")
bord = trimesh.util.concatenate([extrusion(p.difference(h), H_SOL, H_BAC) for p, h in zip(bacs, herbes)] +
                                [extrusion(h, H_SOL, H_BAC - 0.08) for h in herbes])
sc.add_geometry(uni(bord, (150, 154, 160), "PierreGrise"), node_name="Bacs_Bordure", geom_name="Bacs_Bordure")
herbe = trimesh.util.concatenate([extrusion(h, H_BAC - 0.08, H_BAC - 0.04) for h in herbes])
sc.add_geometry(avec_uv(herbe, texture_herbe(), "Herbe"), node_name="Bacs_Herbe", geom_name="Bacs_Herbe")
sc.export(SORTIE)
print(SORTIE, round(os.path.getsize(SORTIE) / 1e6, 2), "Mo")
