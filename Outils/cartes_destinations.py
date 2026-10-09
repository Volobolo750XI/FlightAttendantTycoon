"""Cartes de destination pour le PC (format UEFN 2048 x 2048, fond transparent).

- Les cartes deja faites (dossier source) sont detourees : on garde le cadre,
  on supprime le fond, on recree le halo lumineux, et on centre dans un carre
  2048 x 2048 transparent (la carte n'est pas etiree).
- Les cartes manquantes sont generees a partir d'une carte vide reconstruite
  depuis une des cartes (texte efface), avec la meme mise en page :
  ville / pays en dessous, fleche au milieu, prix en vert.

Usage : python3 cartes_destinations.py DOSSIER_SOURCE DOSSIER_SORTIE
"""
import glob
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F_CITY = os.path.join(HERE, "BarlowSemiCondensed-Bold.ttf")
F_COUNTRY = os.path.join(HERE, "Exo2-SemiBold.ttf")

PW, PH, RADIUS = 3478, 928, 46        # panneau (cadre compris)
GLOW = 90                              # marge pour le halo autour du cadre
OUT = 2048

# (numero, ville A, pays A, ville B, pays B, prix)
DESTINATIONS = [
    (1, "TIRANA", "ALBANIA", "MINSK", "BELARUS", "FREE"),
    (2, "LAGOS", "NIGERIA", "DAKAR", "SENEGAL", "150 $"),
    (3, "LIMA", "PERU", "ASUNCIÓN", "PARAGUAY", "400 $"),
    (4, "DHAKA", "BANGLADESH", "KATHMANDU", "NEPAL", "900 $"),
    (5, "ALMATY", "KAZAKHSTAN", "BAKU", "AZERBAIJAN", "1.8K $"),
    (6, "MANILA", "PHILIPPINES", "HANOI", "VIETNAM", "4K $"),
    (7, "NAIROBI", "KENYA", "JOHANNESBURG", "SOUTH AFRICA", "8K $"),
    (8, "BUCHAREST", "ROMANIA", "DUBLIN", "IRELAND", "15K $"),
    (9, "PANAMA CITY", "PANAMA", "HAVANA", "CUBA", "25K $"),
    (10, "CASABLANCA", "MOROCCO", "ISTANBUL", "TURKEY", "50K $"),
    (11, "DELHI", "INDIA", "BANGKOK", "THAILAND", "90K $"),
    (12, "CAIRO", "EGYPT", "ROME", "ITALY", "160K $"),
    (13, "MONTREAL", "CANADA", "CANCÚN", "MEXICO", "280K $"),
    (14, "BUENOS AIRES", "ARGENTINA", "LIMA", "PERU", "480K $"),
    (15, "SEOUL", "SOUTH KOREA", "BALI", "INDONESIA", "800K $"),
    (16, "LONDON", "UK", "NEW YORK", "USA", "1.4M $"),
    (17, "LISBON", "PORTUGAL", "RIO DE JANEIRO", "BRAZIL", "2.4M $"),
    (18, "JOHANNESBURG", "SOUTH AFRICA", "SYDNEY", "AUSTRALIA", "4M $"),
    (19, "MADRID", "SPAIN", "MEXICO CITY", "MEXICO", "7M $"),
    (20, "ISTANBUL", "TURKEY", "BANGKOK", "THAILAND", "12M $"),
    (21, "ROME", "ITALY", "LOS ANGELES", "USA", "20M $"),
    (22, "ZURICH", "SWITZERLAND", "SINGAPORE", "SINGAPORE", "35M $"),
    (23, "VANCOUVER", "CANADA", "HONG KONG", "CHINA", "60M $"),
    (24, "MILAN", "ITALY", "TOKYO", "JAPAN", "100M $"),
    (25, "NEW YORK", "USA", "SYDNEY", "AUSTRALIA", "170M $"),
    (26, "PARIS", "FRANCE", "DUBAI", "UAE", "300M $"),
    (27, "DOHA", "QATAR", "MALÉ", "MALDIVES", "500M $"),
    (28, "GENEVA", "SWITZERLAND", "MAHÉ", "SEYCHELLES", "850M $"),
    (29, "LOS ANGELES", "USA", "BORA BORA", "FRENCH POLYNESIA", "1.4B $"),
    (30, "MONACO", "MONACO", "TAHITI", "FRENCH POLYNESIA", "2.5B $"),
]


def panel_bbox(a):
    cy = (a[:, :, 2] > 200) & (a[:, :, 1] > 190) & (a[:, :, 0] < 200)
    ys, xs = np.where(cy)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def rounded_mask(w, h, r, ss=4):
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def load_panel(path):
    a = np.asarray(Image.open(path).convert("RGB"))
    x0, y0, x1, y1 = panel_bbox(a)
    return Image.fromarray(a[y0:y1, x0:x1]).resize((PW, PH), Image.LANCZOS)


def finish(panel):
    """Panneau RGB -> image 2048x2048 transparente, avec halo, centree."""
    W, H = PW + 2 * GLOW, PH + 2 * GLOW
    mask = rounded_mask(PW, PH, RADIUS)
    halo = Image.new("L", (W, H), 0)
    halo.paste(mask, (GLOW, GLOW))
    border = halo.filter(ImageFilter.GaussianBlur(28))
    glow = Image.new("RGBA", (W, H), (90, 220, 255, 0))
    glow.putalpha(border.point(lambda v: int(v * 0.85)))
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    card.alpha_composite(glow)
    p = panel.convert("RGBA")
    p.putalpha(mask)
    card.alpha_composite(p, (GLOW, GLOW))
    card = card.resize((OUT, round(H * OUT / W)), Image.LANCZOS)
    out = Image.new("RGBA", (OUT, OUT), (0, 0, 0, 0))
    out.alpha_composite(card, (0, (OUT - card.size[1]) // 2))
    # pixels invisibles : couleur du halo (evite le lisere blanc dans UEFN)
    arr = np.array(out)
    arr[arr[:, :, 3] == 0, :3] = (90, 220, 255)
    return Image.fromarray(arr)


def blank_panel(panel):
    """Efface tout le texte (on garde l'icone d'avion et le cadre)."""
    a = np.asarray(panel.convert("RGB")).copy()
    bright = a.max(axis=2) > 62          # texte + son halo (le fond est ~45)
    zone = np.zeros(bright.shape, bool)
    zone[50:PH - 50, 290:PW - 50] = True
    mask = (bright & zone).astype(np.uint8) * 255
    mask = cv2.dilate(mask, np.ones((41, 41), np.uint8))
    mask[~zone] = 0
    out = cv2.inpaint(a, mask, 12, cv2.INPAINT_TELEA)
    # lissage leger de la zone reconstruite pour un fond uniforme
    soft = cv2.GaussianBlur(out, (0, 0), 6)
    m = cv2.GaussianBlur(mask, (0, 0), 8)[:, :, None] / 255.0
    return Image.fromarray((out * (1 - m) + soft * m).astype(np.uint8))


def fit_font(path, text, size, max_w):
    while size > 20:
        f = ImageFont.truetype(path, size)
        if f.getbbox(text)[2] <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(path, size)


def glow_text(base, xy, text, font, fill, glow, anchor):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font, fill=glow + (200,), anchor=anchor)
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(base).text(xy, text, font=font, fill=fill, anchor=anchor)


def draw_arrows(img, xm, yc, w=150, gap=34, t=16, head=26):
    """Double fleche ⇄ (fleche vers la droite en haut, vers la gauche en bas)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = (90, 220, 255, 255)
    for y, sens in ((yc - gap, 1), (yc + gap, -1)):
        x0, x1 = xm - w // 2, xm + w // 2
        d.line((x0, y, x1, y), fill=c, width=t)
        tip = x1 if sens > 0 else x0
        for dy in (-head, head):
            d.line((tip, y, tip - sens * head, y + dy), fill=c, width=t)
    glow = layer.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(glow)
    img.alpha_composite(layer)


def draw_card(blank, a, ca, b, cb, price):
    img = blank.convert("RGBA")
    colw = int(PW * 0.36)
    xl, xr, xm = int(PW * 0.285), int(PW * 0.765), int(PW * 0.525)
    yc, yp, yr = int(PH * 0.30), int(PH * 0.54), int(PH * 0.785)
    fa = fit_font(F_CITY, a, 330, colw)
    fb = fit_font(F_CITY, b, 330, colw)
    fc = min(fa.size, fb.size)
    fa = fb = ImageFont.truetype(F_CITY, fc)
    fca = fit_font(F_COUNTRY, ca, 120, colw)
    fcb = fit_font(F_COUNTRY, cb, 120, colw)
    fco = ImageFont.truetype(F_COUNTRY, min(fca.size, fcb.size))
    white, cyan, green = (245, 250, 255), (120, 215, 245), (70, 235, 60)
    glow_text(img, (xl, yc), a, fa, white, (120, 220, 255), "mm")
    glow_text(img, (xr, yc), b, fb, white, (120, 220, 255), "mm")
    glow_text(img, (xl, yp), ca, fco, cyan, (60, 160, 220), "mm")
    glow_text(img, (xr, yp), cb, fco, cyan, (60, 160, 220), "mm")
    draw_arrows(img, xm, yc)
    glow_text(img, (int(PW * 0.135), yr), price, ImageFont.truetype(F_CITY, 230), green, (40, 200, 40), "lm")
    return img.convert("RGB")


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    existing = dict((int(os.path.basename(p)[4:6]), p) for p in glob.glob(os.path.join(src, "Dest*.*")))
    template = blank_panel(load_panel(existing.get(6, sorted(existing.values())[0])))
    template.save(os.path.join(dst, "_carte_vide.png"))
    for n, a, ca, b, cb, price in DESTINATIONS:
        if n in existing:
            panel = load_panel(existing[n])
        else:
            panel = draw_card(template, a, ca, b, cb, price)
        finish(panel).save(os.path.join(dst, f"Dest{n:02d}.png"))
        print(f"Dest{n:02d}", "existante" if n in existing else "generee", a, "-", b)
