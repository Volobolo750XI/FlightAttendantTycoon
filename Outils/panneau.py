"""Fabrique un panneau d'achat PNG transparent : nom de l'objet en haut, prix en dessous.

Style "CLAIM" : grosses lettres blanches avec un epais contour noir.
Le prix est en vert. Les pixels transparents sont remplis de noir (couleur du
contour) pour eviter le liseré blanc dans UEFN.

Usage : python3 panneau.py "SEAT ROW" "FREE" sortie.png
        python3 panneau.py "SEAT ROW" "$250" sortie.png
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ArchivoBlack.ttf")
W, H = 2048, 1024
WHITE, GREEN, BLACK = (255, 255, 255), (70, 220, 60), (0, 0, 0)


def fit_font(draw, text, max_w, max_h, stroke):
    size = max_h
    while size > 10:
        f = ImageFont.truetype(FONT, size)
        l, t, r, b = draw.textbbox((0, 0), text, font=f, stroke_width=stroke)
        if r - l <= max_w and b - t <= max_h:
            return f
        size -= 4
    return ImageFont.truetype(FONT, size)


def draw_line(img, text, color, cy, max_h, stroke):
    d = ImageDraw.Draw(img)
    f = fit_font(d, text, W - 120, max_h, stroke)
    l, t, r, b = d.textbbox((0, 0), text, font=f, stroke_width=stroke)
    x, y = (W - (r - l)) / 2 - l, cy - (b - t) / 2 - t
    # ombre portee sombre sous le texte, puis le texte avec son contour
    d.text((x + 10, y + 14), text, font=f, fill=BLACK, stroke_width=stroke, stroke_fill=BLACK)
    d.text((x, y), text, font=f, fill=color, stroke_width=stroke, stroke_fill=BLACK)


def make(name, price, out):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_line(img, name.upper(), WHITE, H * 0.32, 470, 30)
    draw_line(img, price.upper(), GREEN if price.upper() == "FREE" else GREEN, H * 0.76, 330, 26)
    # adoucit legerement le bord exterieur, puis "alpha bleed" : RGB des pixels transparents = noir
    a = np.array(img)
    alpha = Image.fromarray(a[..., 3]).filter(ImageFilter.GaussianBlur(1.2))
    a[..., 3] = np.array(alpha)
    a[a[..., 3] < 255, :3] = np.where(a[a[..., 3] < 255, :3] > 0, a[a[..., 3] < 255, :3], 0)
    a[a[..., 3] == 0, :3] = 0
    Image.fromarray(a).save(out)
    print(out)


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
