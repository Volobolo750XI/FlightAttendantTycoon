"""PLATEFORME DU SPAWN (centre du lobby), forme facon Infinity Tower Tycoon, un seul gris :
- sol plat rond, presque au ras du sol
- autour, des bacs a haies BAS et larges (polygone a 12 cotes), flanc exterieur en pente, creux dessus
  pour y mettre les haies/buissons
- 6 ouvertures entre les bacs
Origine : centre, au sol. Y en haut.   Sortie : Modeles/Lobby/Plateforme_Spawn.glb
"""
import math
import os

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Plateforme_Spawn.glb")
H_SOL = 0.08
A_IN = 14.0                     # apotheme du bord interieur des bacs
LARGE = 2.6                     # largeur du bac en haut
H = 0.55                        # hauteur du bac
PENTE = 0.45                    # debord du flanc exterieur en bas
LEVRE = 0.25                    # epaisseur du rebord
CREUX = 0.2
TROU = 4.5
COTES = 12
PAS = 360 / COTES
OUVERTURES = [15 + 60 * k for k in range(6)]   # au milieu d'un cote sur deux

# profil (apotheme, hauteur) du bac, ferme, sens anti-horaire
P = [(A_IN, H_SOL), (A_IN + LARGE + PENTE, H_SOL), (A_IN + LARGE, H), (A_IN + LARGE - LEVRE, H),
     (A_IN + LARGE - LEVRE, H - CREUX), (A_IN + LEVRE, H - CREUX), (A_IN + LEVRE, H), (A_IN, H)]


def point(a, y, t):
    c = math.radians(math.floor(t / PAS) * PAS + PAS / 2)
    r = a / math.cos(math.radians(t) - c)
    return [r * math.cos(math.radians(t)), y, r * math.sin(math.radians(t))]


def bac(t0, t1):
    ts = [t0] + [k * PAS for k in range(int(t0 // PAS) + 1, int(math.ceil(t1 / PAS)))] + [t1]
    n = len(P)
    v = [point(a, y, t) for t in ts for a, y in P]
    f = []
    for i in range(len(ts) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            f += [[a, b, b + n], [a, b + n, a + n]]
    tri_v, tri_f = trimesh.creation.triangulate_polygon(Polygon(P))
    idx = {tuple(np.round(p, 6)): k for k, p in enumerate(P)}
    loc = [idx[tuple(np.round(p, 6))] for p in tri_v]
    last = (len(ts) - 1) * n
    for t in tri_f:
        f.append([loc[t[0]], loc[t[2]], loc[t[1]]])
        f.append([last + loc[t[0]], last + loc[t[1]], last + loc[t[2]]])
    m = trimesh.Trimesh(np.array(v), np.array(f), process=True)
    trimesh.repair.fix_normals(m)
    return m


def extrusion(poly, y0, y1):
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_translation([0, y0, 0])
    return m


demi = math.degrees(math.atan(TROU / 2 / A_IN))
pieces = [extrusion(Point(0, 0).buffer(A_IN + 0.3, 128), 0.0, H_SOL)]
for k, o in enumerate(OUVERTURES):
    pieces.append(bac(o + demi, OUVERTURES[(k + 1) % 6] + (360 if k == 5 else 0) - demi))
m = trimesh.util.concatenate(pieces)
m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
    name="Gris", baseColorFactor=[140, 143, 148, 255], metallicFactor=0.0, roughnessFactor=0.85))
sc = trimesh.Scene()
sc.add_geometry(m, node_name="Plateforme_Spawn", geom_name="Plateforme_Spawn")
sc.export(SORTIE)
print(SORTIE, round(os.path.getsize(SORTIE) / 1e3), "Ko")
