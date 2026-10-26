"""PLATEFORME DU SPAWN (centre du lobby), forme facon Infinity Tower Tycoon, un seul gris :
- un sol plat rond (fin, presque au ras du sol)
- autour, des bacs a plantes droits (segments d'un polygone a 12 cotes), creux dessus pour y mettre des buissons
- 6 ouvertures entre les bacs
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
R_SOL = 14.6
R_IN, R_OUT = 14.5, 17.5      # bacs (rayons des sommets du 12-gone)
H_SOL = 0.08
H_BAC = 0.9
PAROI = 0.3
CREUX = 0.25                  # profondeur du creux pour la terre / buissons
TROU = 4.5
ANGLES = (15, 75, 135, 195, 255, 315)   # ouvertures au milieu d'un cote du 12-gone


def polygone(r, n=12):
    a = np.radians(np.arange(n) * 360 / n)
    return Polygon(np.c_[r * np.cos(a), r * np.sin(a)])


def extrusion(poly, y0, y1):
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_translation([0, y0, 0])
    return m


coupe = Polygon([(-TROU / 2, 0), (TROU / 2, 0), (TROU / 2, R_OUT + 2), (-TROU / 2, R_OUT + 2)])
couronne = polygone(R_OUT).difference(polygone(R_IN))
for a in ANGLES:
    couronne = couronne.difference(rotate(coupe, a - 90, origin=(0, 0)))
bacs = list(couronne.geoms)

pieces = [extrusion(Point(0, 0).buffer(R_SOL, 128), 0.0, H_SOL)]
for b in bacs:
    fond = b.buffer(-PAROI, join_style=2)
    pieces.append(extrusion(b.difference(fond), H_SOL, H_BAC))        # parois
    pieces.append(extrusion(fond, H_SOL, H_BAC - CREUX))              # fond du creux
m = trimesh.util.concatenate(pieces)
m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
    name="Gris", baseColorFactor=[140, 143, 148, 255], metallicFactor=0.0, roughnessFactor=0.85))
sc = trimesh.Scene()
sc.add_geometry(m, node_name="Plateforme_Spawn", geom_name="Plateforme_Spawn")
sc.export(SORTIE)
print(SORTIE, len(bacs), "bacs", round(os.path.getsize(SORTIE) / 1e3), "Ko")
