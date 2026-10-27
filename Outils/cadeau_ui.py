"""Interface CARTOON du cadeau du lobby (Playtime Reward) -> Textures/InterfaceCadeau/*.png
Style : tres colore, gros contour bleu nuit, reflets, lettres arc-en-ciel (comme la Daily Spin).
  Fenetre_Cadeaux.png (1500 x 900) : la fenetre avec le titre FREE GIFTS
  Icone_Cadeau.png    (512 x 512)  : le cadeau dessine sur chaque carte
  Carte_1..6.png      (400 x 330)  : les cartes de couleur des cadeaux qui attendent
  Carte_Prete.png     (400 x 330)  : la carte verte (halo dore) du cadeau a ouvrir
Usage : python3 Outils/cadeau_ui.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(ICI), "Textures", "InterfaceCadeau")
POLICE = os.path.join(ICI, "TitanOne-Regular.ttf")
NUIT = (22, 27, 48)
ARC = [(238, 48, 56), (255, 136, 24), (250, 205, 30), (64, 196, 64), (24, 186, 220), (44, 104, 240), (136, 60, 230),
       (230, 50, 170)]
random.seed(3)


def f(t):
    return ImageFont.truetype(POLICE, t)


def degrade(w, h, haut, bas):
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(haut, bas)) + (255,))
    return im


def arrondi(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], r, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


def mot_arc_en_ciel(img, mot, cx, cy, taille, contour=18):
    d = ImageDraw.Draw(img)
    ft = f(taille)
    larg = [d.textlength(c, font=ft) + (6 if c != " " else 0) for c in mot]
    x = cx - sum(larg) / 2
    k = 0
    for c, lg in zip(mot, larg):
        if c != " ":
            col = ARC[k % len(ARC)]
            k += 1
            d.text((x, cy), c, font=ft, fill=col, anchor="lm", stroke_width=contour, stroke_fill=NUIT)
            # reflet sur le haut de la lettre
            couche = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(couche).text((x, cy), c, font=ft, fill=tuple(min(255, int(v * 0.55 + 120)) for v in col), anchor="lm")
            masque = Image.new("L", img.size, 0)
            bb = ImageDraw.Draw(couche).textbbox((x, cy), c, font=ft, anchor="lm")
            ImageDraw.Draw(masque).rectangle([0, 0, img.width, (bb[1] + bb[3]) / 2 - 4], fill=255)
            img.alpha_composite(Image.composite(couche, Image.new("RGBA", img.size, (0, 0, 0, 0)), masque))
        x += lg


def etincelle(d, x, y, r, col=(255, 255, 255)):
    pts = []
    for i in range(8):
        a = math.pi / 2 + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.3
        pts.append((x + rr * math.cos(a), y - rr * math.sin(a)))
    d.polygon(pts, fill=col)


def fenetre():
    W, H = 1500, 900
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ombre).rounded_rectangle([20, 34, W - 6, H - 6], 70, fill=(0, 0, 0, 110))
    img.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 20, W - 20, H - 20], 70, fill=NUIT)
    img.alpha_composite(arrondi(degrade(W - 60, H - 210, (125, 215, 255), (70, 120, 235)), 54), (24, 170))
    d = ImageDraw.Draw(img)
    for _ in range(34):
        etincelle(d, random.randint(70, W - 90), random.randint(230, H - 70), random.randint(6, 16), (255, 255, 255, 140))
    img.alpha_composite(arrondi(degrade(W - 60, 190, (255, 120, 200), (150, 70, 230)), 54), (24, 34))
    mot_arc_en_ciel(img, "FREE GIFTS", (W - 20) / 2 + 6, 130, 150)
    return img


def carte(haut, bas, pret=False):
    W, H = 400, 330
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if pret:                                                    # halo dore autour de la carte prete
        halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(halo).rounded_rectangle([0, 0, W - 1, H - 1], 50, fill=(255, 240, 120, 230))
        img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, W - 9, H - 9], 44, fill=NUIT)
    img.alpha_composite(arrondi(degrade(W - 40, H - 40, haut, bas), 34), (20, 20))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([44, 250, W - 45, 300], 25, fill=(22, 27, 48, 150))   # pastille du temps
    for x, y, r in ((60, 70, 12), (340, 110, 9), (330, 50, 7), (80, 200, 8)):
        etincelle(d, x, y, r, (255, 255, 255, 170))
    return img


def icone_cadeau():
    n = 512
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # halo
    halo = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([30, 30, n - 30, n - 30], fill=(255, 255, 255, 120))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(img)
    # boite
    d.rounded_rectangle([100, 230, 412, 470], 26, fill=(236, 58, 150), outline=NUIT, width=16)
    d.rounded_rectangle([118, 248, 394, 300], 18, fill=(255, 120, 190))
    # couvercle
    d.rounded_rectangle([76, 170, 436, 250], 24, fill=(250, 80, 170), outline=NUIT, width=16)
    d.rounded_rectangle([92, 182, 420, 206], 12, fill=(255, 150, 210))
    # ruban vertical + horizontal (cyan)
    d.rectangle([228, 178, 284, 462], fill=(40, 200, 235))
    d.line([(228, 178), (228, 462)], fill=NUIT, width=10)
    d.line([(284, 178), (284, 462)], fill=NUIT, width=10)
    d.rectangle([236, 186, 250, 456], fill=(150, 235, 255))
    # noeud
    for sx in (-1, 1):
        pts = [(256, 172), (256 + sx * 130, 70), (256 + sx * 160, 150), (256 + sx * 40, 176)]
        d.polygon(pts, fill=(40, 200, 235), outline=NUIT)
        d.line(pts + [pts[0]], fill=NUIT, width=14, joint="curve")
        d.polygon([(256 + sx * 30, 160), (256 + sx * 118, 92), (256 + sx * 136, 140)], fill=(150, 235, 255))
    d.ellipse([218, 132, 294, 196], fill=(40, 200, 235), outline=NUIT, width=14)
    # etincelles
    for x, y, r in ((70, 110, 34), (452, 90, 26), (462, 330, 22), (52, 360, 18)):
        etincelle(d, x, y, r + 8, NUIT)
        etincelle(d, x, y, r, (255, 255, 255))
    return img


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    for vieux in ("Fenetre_Cadeau", "Barre_Fond", "Barre_Plein", "Bouton_Open", "Bouton_Attente"):
        if os.path.exists(os.path.join(SORTIE, vieux + ".png")):
            os.remove(os.path.join(SORTIE, vieux + ".png"))
    fenetre().save(os.path.join(SORTIE, "Fenetre_Cadeaux.png"))
    icone_cadeau().save(os.path.join(SORTIE, "Icone_Cadeau.png"))
    COUL = [((255, 110, 110), (220, 50, 70)), ((255, 180, 80), (240, 120, 30)), ((170, 120, 255), (120, 60, 220)),
            ((90, 220, 255), (30, 150, 220)), ((255, 130, 210), (220, 60, 160)), ((255, 225, 90), (235, 170, 20))]
    for i, (h, b) in enumerate(COUL):
        carte(h, b).save(os.path.join(SORTIE, f"Carte_{i + 1}.png"))
    carte((140, 240, 110), (40, 180, 70), True).save(os.path.join(SORTIE, "Carte_Prete.png"))
    # apercu monte comme dans le jeu
    ap = Image.new("RGBA", (1920, 1080), (60, 70, 90, 255))
    ap.alpha_composite(Image.open(os.path.join(SORTIE, "Fenetre_Cadeaux.png")), (210, 60))
    ic = Image.open(os.path.join(SORTIE, "Icone_Cadeau.png")).resize((170, 170))
    d = ImageDraw.Draw(ap)
    textes = ["OPEN!", "05:00", "15:00", "30:00", "50:00", "1:20:00"]
    for k in range(6):
        x, y = 350 + (k % 3) * 420, 300 + (k // 3) * 325      # cartes affichees en 360 x 297 (comme dans Verse)
        nom = "Carte_Prete.png" if k == 0 else f"Carte_{k + 1}.png"
        ap.alpha_composite(Image.open(os.path.join(SORTIE, nom)).resize((360, 297)), (x, y))
        ap.alpha_composite(ic, (x + 95, y + 50))
        d.text((x + 180, y + 40), f"GIFT {k + 1}", font=f(38), fill="white", anchor="mm", stroke_width=8, stroke_fill=NUIT)
        d.text((x + 180, y + 247), textes[k], font=f(40), fill=(134, 239, 172) if k == 0 else "white", anchor="mm",
               stroke_width=8, stroke_fill=NUIT)
    ap.convert("RGB").save(os.path.join(os.path.dirname(ICI), "Modeles", "Lobby", "apercu_interface_cadeau.png"))
    print("ok", SORTIE)
