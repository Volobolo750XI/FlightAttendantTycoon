"""Texture de la moquette de luxe du pont superieur (Modeles/Cabine/moquette_luxe.png, 1024 x 1024,
se repete toutes les 1,6 m) : vert emeraude profond, medaillons et losanges dores, fin treillis.
Usage : python3 moquette_luxe.py
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SORTIE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Modeles", "Cabine", "moquette_luxe.png")
T, PAS = 1024, 256
FOND, TREILLIS = (10, 58, 44), (24, 80, 60)
OR, OR_CLAIR, FONCE = (212, 175, 92), (240, 214, 140), (6, 40, 30)

if __name__ == "__main__":
    rng = np.random.default_rng(5)
    a = np.zeros((T, T, 3), np.float32) + FOND + rng.normal(0, 4, (T, T, 1))
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for k in range(PAS // 4, T, PAS // 2):          # treillis entre les motifs
        d.line([(k, 0), (k, T)], fill=TREILLIS, width=2)
        d.line([(0, k), (T, k)], fill=TREILLIS, width=2)
    for y in range(0, T + PAS, PAS):
        for x in range(0, T + PAS, PAS):
            d.ellipse([x - 70, y - 70, x + 70, y + 70], outline=OR, width=6)
            d.ellipse([x - 52, y - 52, x + 52, y + 52], fill=FONCE, outline=OR, width=3)
            for k in range(8):
                t = k * np.pi / 4
                px, py = x + 36 * np.cos(t), y + 36 * np.sin(t)
                d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=OR)
            d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=OR_CLAIR)
            mx, my = x + PAS / 2, y + PAS / 2
            d.polygon([(mx, my - 40), (mx + 40, my), (mx, my + 40), (mx - 40, my)], fill=FONCE, outline=OR, width=4)
            d.ellipse([mx - 8, my - 8, mx + 8, my + 8], fill=OR_CLAIR)
    im.filter(ImageFilter.GaussianBlur(0.7)).save(SORTIE)
    print("ok", SORTIE)
