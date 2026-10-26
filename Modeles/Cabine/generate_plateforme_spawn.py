"""PLATEFORME DU SPAWN (centre du lobby) : juste un disque gris avec un rebord et 6 ouvertures (tous les 60 degres).
Origine : centre de la plateforme, au sol. Y en haut.
Sortie : Modeles/Lobby/Plateforme_Spawn.glb      Usage : python3 generate_plateforme_spawn.py
"""
import math
import os

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon
from shapely.affinity import rotate
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Plateforme_Spawn.glb")
R = 16.0           # rayon exterieur
H = 0.30           # epaisseur du disque (petite marche, on monte sans sauter)
MUR_EP = 0.6       # epaisseur du rebord
MUR_H = 0.7        # hauteur du rebord au-dessus du sol de la plateforme
TROU = 4.0         # largeur de chaque ouverture


def extrusion(poly, y0, y1):
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_translation([0, y0, 0])
    return m


def materiau(nom, rgb, rugo):
    return trimesh.visual.material.PBRMaterial(name=nom, baseColorFactor=[*rgb, 255], metallicFactor=0.0, roughnessFactor=rugo)


def objet(m, mat):
    m.visual = trimesh.visual.TextureVisuals(material=mat)
    return m


sol = extrusion(Point(0, 0).buffer(R, 128), 0.0, H)
anneau = Point(0, 0).buffer(R, 128).difference(Point(0, 0).buffer(R - MUR_EP, 128))
coupe = Polygon([(-TROU / 2, R - 3), (TROU / 2, R - 3), (TROU / 2, R + 1), (-TROU / 2, R + 1)])
for a in (0, 60, 120, 180, 240, 300):
    anneau = anneau.difference(rotate(coupe, a, origin=(0, 0)))
murs = [extrusion(p, H, H + MUR_H) for p in anneau.geoms]

sc = trimesh.Scene()
sc.add_geometry(objet(sol, materiau("GrisSol", (150, 152, 156), 0.85)), node_name="Plateforme_Sol", geom_name="Plateforme_Sol")
sc.add_geometry(objet(trimesh.util.concatenate(murs), materiau("GrisRebord", (105, 108, 114), 0.85)),
                node_name="Plateforme_Rebord", geom_name="Plateforme_Rebord")
sc.export(SORTIE)
print(SORTIE, round(os.path.getsize(SORTIE) / 1e3), "Ko")
