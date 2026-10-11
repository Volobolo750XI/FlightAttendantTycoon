"""Chariot de service (demi-chariot d'avion), 1 static mesh + 1 materiau.

Fichier : Modeles/Chariot/Chariot.glb
Y vers le haut, la porte (avant) vers +Z. PIVOT = au sol, au centre. Unites : metres.
Usage : python3 chariot.py
"""
import os
import sys

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

sys.path.insert(0, os.path.dirname(__file__))
from bagages import superellipsoide, tube, assembler  # noqa: E402

METAL = (196, 200, 208)
METAL_FONCE = (142, 148, 158)
BLEU = (32, 52, 118)
PNEU = (40, 42, 46)
ROUGE = (200, 40, 40)
VERT = (40, 160, 70)

W, D = 0.32, 0.55          # largeur (porte), profondeur
Y0, Y1 = 0.13, 1.00        # bas / haut de la caisse


def boite(t, c, e=0.12):
    return superellipsoide(t, c, e=e, res=(32, 16))


def cube(t, c):
    m = trimesh.creation.box(extents=t)
    m.apply_translation(c)
    return m


P = []
add = lambda col, m: P.append((col, m))
H = Y1 - Y0
yc = (Y0 + Y1) / 2

# caisse
add(METAL, boite((W, H, D), (0, yc, 0), e=0.08))
# plateau du dessus avec rebord
add(METAL, boite((W + 0.02, 0.025, D + 0.02), (0, Y1 + 0.005, 0), e=0.15))
for x in (-1, 1):
    add(METAL, boite((0.012, 0.02, D + 0.02), (x * (W / 2 + 0.004), Y1 + 0.025, 0), e=0.3))
add(METAL, boite((W + 0.02, 0.02, 0.012), (0, Y1 + 0.025, -(D / 2 + 0.004)), e=0.3))
# barre de poussee a l'avant du dessus
add(METAL, tube((-W / 2 - 0.01, Y1 + 0.03, D / 2 + 0.012), (W / 2 + 0.01, Y1 + 0.03, D / 2 + 0.012), 0.016, 16))
for x in (-1, 1):
    add(METAL, boite((0.03, 0.04, 0.03), (x * (W / 2 - 0.005), Y1 + 0.015, D / 2), e=0.3))

# porte avant : cadre metal + panneau bleu
zf = D / 2
add(METAL, boite((W - 0.01, H - 0.03, 0.02), (0, yc, zf + 0.004), e=0.1))
add(BLEU, boite((W - 0.065, H - 0.10, 0.012), (0, yc - 0.01, zf + 0.014), e=0.06))
# loquet
add(METAL, boite((0.075, 0.12, 0.016), (0.07, yc + 0.06, zf + 0.022), e=0.15))
add(METAL_FONCE, boite((0.05, 0.085, 0.01), (0.07, yc + 0.06, zf + 0.03), e=0.15))
add(METAL, tube((0.05, yc + 0.06, zf + 0.04), (0.095, yc + 0.06, zf + 0.04), 0.008, 10))
add(METAL, tube((0.055, yc + 0.06, zf + 0.032), (0.055, yc + 0.06, zf + 0.045), 0.012, 12))
# charnieres a gauche
for y in (Y0 + 0.14, Y1 - 0.14):
    add(METAL_FONCE, boite((0.018, 0.06, 0.02), (-W / 2 - 0.002, y, zf + 0.004), e=0.3))

# nervures sur les cotes
for x in (-1, 1):
    for y in (Y1 - 0.12, Y1 - 0.17, Y0 + 0.12, Y0 + 0.17):
        add(METAL, boite((0.012, 0.022, D - 0.10), (x * (W / 2 + 0.003), y, -0.02), e=0.3))
# coins renforces
for x in (-1, 1):
    for z in (-1, 1):
        for y in (Y0 + 0.02, Y1 - 0.03):
            add(METAL_FONCE, boite((0.04, 0.05, 0.04), (x * (W / 2 - 0.012), y, z * (D / 2 - 0.012)), e=0.25))

# socle + roues
add(METAL_FONCE, boite((W - 0.02, 0.03, D - 0.02), (0, Y0 - 0.005, 0), e=0.15))
R = 0.045
for x in (-1, 1):
    for z in (-1, 1):
        cx, cz = x * (W / 2 - 0.05), z * (D / 2 - 0.06)
        add(METAL_FONCE, boite((0.04, 0.05, 0.04), (cx, Y0 - 0.035, cz), e=0.3))
        add(PNEU, tube((cx - 0.016, R, cz), (cx + 0.016, R, cz), R, 20))
        add(METAL, tube((cx - 0.019, R, cz), (cx + 0.019, R, cz), 0.018, 12))
# pedales de frein (rouge / vert)
add(ROUGE, boite((0.05, 0.02, 0.05), (-0.04, 0.07, zf - 0.02), e=0.3))
add(VERT, boite((0.05, 0.02, 0.05), (0.03, 0.07, zf - 0.02), e=0.3))

m = assembler(P)
m.visual.material = PBRMaterial(baseColorTexture=m.visual.material.baseColorTexture,
                                metallicFactor=0.35, roughnessFactor=0.4)
out = os.path.join(os.path.dirname(__file__), "..", "Modeles", "Chariot")
os.makedirs(out, exist_ok=True)
m.export(os.path.join(out, "Chariot.glb"))
print(len(m.faces), "triangles")
