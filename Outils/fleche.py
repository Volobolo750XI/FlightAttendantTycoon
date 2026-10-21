"""Fleche au-dessus des passagers qui commandent (1 static mesh, 1 materiau vert lumineux).

Fichier : Modeles/Fleche/Fleche.glb
Y vers le haut, la pointe en BAS. PIVOT = la pointe (le code la place au-dessus de la tete).
Taille : 45 cm de haut. Unites : metres.
Usage : python3 fleche.py
"""
import os

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SORTIE = os.path.join(RACINE, "Modeles", "Fleche")

VERT = (0, 255, 0, 255)


def fleche():
    # pointe : cone a 24 cotes, pointe en bas (y = 0), base a 0.18 m
    tete = trimesh.creation.cone(radius=0.13, height=0.18, sections=24)
    tete.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))  # axe Z -> -Y
    tete.apply_translation((0, 0.18, 0))
    # tige : cylindre arrondi au-dessus
    tige = trimesh.creation.cylinder(radius=0.055, height=0.27, sections=24)
    tige.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
    tige.apply_translation((0, 0.18 + 0.135 - 0.01, 0))
    bout = trimesh.creation.icosphere(subdivisions=2, radius=0.055)
    bout.apply_translation((0, 0.18 + 0.27 - 0.01, 0))
    m = trimesh.util.concatenate([tete, tige, bout])
    # la pointe vers le bas : on verifie et on retourne si besoin
    if m.vertices[:, 1].min() < -0.01:
        m.apply_translation((0, -m.vertices[:, 1].min(), 0))
    m.visual = trimesh.visual.TextureVisuals(
        uv=np.full((len(m.vertices), 2), 0.5),
        material=PBRMaterial(baseColorFactor=VERT, emissiveFactor=(0.0, 1.0, 0.0), roughnessFactor=0.4, metallicFactor=0.0))
    return m


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    m = fleche()
    m.export(os.path.join(SORTIE, "Fleche.glb"))
    b = m.bounds
    print("ok :", b[0].round(3), b[1].round(3))
