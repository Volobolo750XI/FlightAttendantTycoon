"""Barre de patience : fond + remplissages deja colores (aucun materiau a creer).
Chaque fichier = 1 mesh, 1 materiau, couleurs dans une petite texture.
PIVOT DES REMPLISSAGES = BORD GAUCHE : en reduisant l'echelle X, la barre se vide vers la gauche.
Taille a l'echelle 1 : 60 cm de long (X), 8 cm de haut (Z), face vers -Y. Unites UE (cm) via metres GLB.
"""
import os
import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial

OUT = os.path.join(os.path.dirname(__file__), "..", "Modeles", "Bulle")
L, H, E = 0.60, 0.08, 0.015

def barre(longueur, hauteur, epaisseur, x0, couleur, nom, emissif=False):
    m = trimesh.creation.box(extents=(longueur, epaisseur, hauteur))
    m.apply_translation((x0 + longueur / 2, 0, 0))
    img = Image.new("RGB", (4, 4), couleur)
    m.visual = trimesh.visual.TextureVisuals(uv=np.full((len(m.vertices), 2), 0.5), material=PBRMaterial(
        baseColorTexture=img, emissiveTexture=img if emissif else None, emissiveFactor=[1, 1, 1] if emissif else None,
        metallicFactor=0.0, roughnessFactor=0.6))
    # glTF : Y en haut -> on tourne pour que Z (hauteur) devienne le haut
    m.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
    m.export(os.path.join(OUT, nom))

# fond : centre sur le pivot, un peu plus grand, legerement derriere
barre(L + 0.012, H + 0.012, E, -(L + 0.012) / 2, (25, 28, 34), "Barre_Fond.glb")
# remplissages : pivot au bord gauche (x = 0), plus epais que le fond : visibles des deux cotes
for nom, c in (("Barre_Verte.glb", (60, 210, 90)), ("Barre_Orange.glb", (245, 160, 40)), ("Barre_Rouge.glb", (230, 50, 50))):
    barre(L, H, E * 1.6, 0.0, c, nom, emissif=True)
print("ok")
