"""Moquettes de luxe pour les zones Business et First (une plaque fine + texture a motif).

Chaque moquette est placee DANS LE REPERE DE L'AVION : dans UEFN, pose-la exactement a la meme
position / rotation / echelle que l'avion, elle tombe pile sur le sol de sa zone.
  Moquette_Business_Avion2.glb : avion 2 | 2 (Business)
  Moquette_Business_Avion3.glb : avion 3 | 3 | 3 (Business)
  Moquette_First_Avion3.glb    : avion 3 | 3 | 3 (First)
Business = bleu nuit avec un fin motif dore ; First = bordeaux avec un motif dore plus riche.
Unites : metres. Usage : python3 moquettes.py
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter
from trimesh.visual.material import PBRMaterial

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Modeles", "Moquettes")
TUILE = 1.0          # 1 m de moquette = une fois la texture


def motif(fond, trait, riche):
    T = 512
    im = Image.new("RGB", (T, T), fond)
    rng = np.random.default_rng(3)
    # grain de la moquette
    a = np.asarray(im).astype(np.float32) + rng.normal(0, 5, (T, T, 1))
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # losanges dores
    pas = 128
    for y in range(-pas, T + pas, pas):
        for x in range(-pas, T + pas, pas):
            cx, cy = x + pas / 2, y + pas / 2
            r = 38 if riche else 30
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=trait, width=4)
            if riche:
                d.polygon([(cx, cy - 12), (cx + 12, cy), (cx, cy + 12), (cx - 12, cy)], fill=trait)
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=trait)
    return im.filter(ImageFilter.GaussianBlur(0.6))


def moquette(nom, x_demi, z0, z1, tex):
    """Plaque de x=-x_demi..x_demi, z=z0..z1 (repere glTF de l'avion), 8 mm au-dessus du sol."""
    y0, y1 = 0.004, 0.012
    b = trimesh.creation.box(extents=(2 * x_demi, y1 - y0, z1 - z0))
    b.apply_translation((0, (y0 + y1) / 2, (z0 + z1) / 2))
    v = b.vertices
    uv = np.column_stack([(v[:, 0] + x_demi) / TUILE, (v[:, 2] - z0) / TUILE])
    b.visual = trimesh.visual.TextureVisuals(uv=uv, material=PBRMaterial(baseColorTexture=tex, roughnessFactor=0.95, metallicFactor=0.0))
    b.export(os.path.join(SORTIE, nom + ".glb"))
    tex.save(os.path.join(SORTIE, nom + "_texture.png"))
    print(nom, round(2 * x_demi, 2), "x", round(z1 - z0, 2), "m")


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    business = motif((18, 30, 64), (196, 160, 82), False)
    first = motif((92, 18, 34), (214, 178, 96), True)
    # avion 2 | 2 : Business de z=-9,45 a -0,97 (glTF), sol de 3,25 m de large
    moquette("Moquette_Business_Avion2", 1.58, -9.45, -0.97, business)
    # avion 3 | 3 | 3 (sol de 7,1 m de large) : First -9,45 a -3,09 ; Business -3,09 a 5,39
    moquette("Moquette_First_Avion3", 3.50, -9.45, -3.09, first)
    moquette("Moquette_Business_Avion3", 3.50, -3.09, 5.39, business)
