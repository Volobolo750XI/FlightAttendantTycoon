"""PLATEFORME DU SPAWN (centre du lobby), toute simple, un seul gris :
un sol rond, un muret fin tout autour, 6 ouvertures, et devant chaque ouverture un petit bout de chemin
(c'est la que se pose le CLAIM).
Origine : centre, au sol. Y en haut.   Sortie : Modeles/Lobby/Plateforme_Spawn.glb
"""
import os

import numpy as np
import trimesh
from shapely.affinity import rotate
from shapely.geometry import Point, Polygon
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Plateforme_Spawn.glb")
R = 15.0            # rayon du sol
H_SOL = 0.1
MURET_EP = 0.2      # muret fin
MURET_H = 0.5
TROU = 4.0          # largeur des ouvertures et des chemins
CHEMIN = 3.0        # longueur du debut de chemin, depuis le muret
ANGLES = (0, 60, 120, 180, 240, 300)


def extrusion(poly, y0, y1):
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_translation([0, y0, 0])
    return m


bande = lambda r0, r1: Polygon([(r0, -TROU / 2), (r1, -TROU / 2), (r1, TROU / 2), (r0, TROU / 2)])
sol = Point(0, 0).buffer(R, 128)
muret = sol.difference(Point(0, 0).buffer(R - MURET_EP, 128))
for a in ANGLES:
    sol = sol.union(rotate(bande(R - 1, R + CHEMIN), a, origin=(0, 0)))
    muret = muret.difference(rotate(bande(R - 1, R + 1), a, origin=(0, 0)))

m = trimesh.util.concatenate([extrusion(sol, 0.0, H_SOL)] + [extrusion(p, H_SOL, H_SOL + MURET_H) for p in muret.geoms])
m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
    name="Gris", baseColorFactor=[140, 143, 148, 255], metallicFactor=0.0, roughnessFactor=0.85))
sc = trimesh.Scene()
sc.add_geometry(m, node_name="Plateforme_Spawn", geom_name="Plateforme_Spawn")
sc.export(SORTIE)
print(SORTIE, round(os.path.getsize(SORTIE) / 1e3), "Ko")
