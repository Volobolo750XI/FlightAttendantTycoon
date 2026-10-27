"""Interface CARTOON du cadeau du lobby (Playtime Reward) -> Textures/InterfaceCadeau/*.png
Style : tres colore, gros contour bleu nuit, reflets, lettres arc-en-ciel (comme la Daily Spin).
  Fenetre_Cadeau.png  (1100 x 900) : la fenetre avec le titre FREE GIFT
  Icone_Cadeau.png    (512 x 512)  : le gros cadeau au milieu
  Barre_Fond.png      (900 x 110)  : le fond de la barre de progression
  Barre_Plein.png     (900 x 110)  : le remplissage (vert -> arc-en-ciel), etire par Verse
  Bouton_Open.png     (560 x 190)  : le gros bouton OPEN! (vert)
  Bouton_Attente.png  (560 x 190)  : le bouton gris WAIT...
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
    W, H = 1100, 900
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # ombre portee
    ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ombre).rounded_rectangle([20, 34, W - 6, H - 6], 70, fill=(0, 0, 0, 110))
    img.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 20, W - 20, H - 20], 70, fill=NUIT)
    corps = arrondi(degrade(W - 60, H - 210, (125, 215, 255), (70, 120, 235)), 54)
    img.alpha_composite(corps, (24, 170))
    # paillettes dans le fond
    d = ImageDraw.Draw(img)
    for _ in range(26):
        x, y = random.randint(70, W - 90), random.randint(220, H - 80)
        etincelle(d, x, y, random.randint(6, 16), (255, 255, 255, 140))
    # bandeau titre rose -> violet
    bandeau = arrondi(degrade(W - 60, 190, (255, 120, 200), (150, 70, 230)), 54)
    img.alpha_composite(bandeau, (24, 34))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 44, W - 76, 120], 40, fill=(255, 255, 255, 55))
    mot_arc_en_ciel(img, "FREE GIFT", (W - 20) / 2 + 6, 130, 150)
    # carte claire au milieu (pour le temps / la barre)
    d.rounded_rectangle([90, 600, W - 110, 700], 36, fill=(255, 255, 255, 70))
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


def barre(fond):
    W, H = 900, 110
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if fond:
        d.rounded_rectangle([0, 0, W - 1, H - 1], 55, fill=NUIT)
        d.rounded_rectangle([12, 12, W - 13, H - 13], 44, fill=(40, 52, 96))
        return img
    # remplissage arc-en-ciel avec reflet
    bande = Image.new("RGBA", (W, H))
    db = ImageDraw.Draw(bande)
    for x in range(W):
        t = x / (W - 1) * (len(ARC) - 1)
        i = min(int(t), len(ARC) - 2)
        u = t - i
        c = tuple(int(a + (b - a) * u) for a, b in zip(ARC[i], ARC[i + 1]))
        db.line([(x, 0), (x, H)], fill=c + (255,))
    bande = arrondi(bande, 44)
    img.alpha_composite(bande)
    reflet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(reflet).rounded_rectangle([18, 10, W - 18, H / 2 - 6], 24, fill=(255, 255, 255, 90))
    img.alpha_composite(reflet)
    return img


def bouton(texte, haut, bas, bord):
    W, H = 560, 190
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 10, W - 1, H - 1], 60, fill=NUIT)
    d.rounded_rectangle([12, 22, W - 13, H - 13], 50, fill=bord)                 # epaisseur 3D (bas)
    face = arrondi(degrade(W - 24, H - 58, haut, bas), 48)
    img.alpha_composite(face, (12, 14))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([34, 24, W - 34, 70], 22, fill=(255, 255, 255, 80))
    d.text((W / 2, 86), texte, font=f(96), fill=(255, 255, 255), anchor="mm", stroke_width=12, stroke_fill=NUIT)
    return img


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    fenetre().save(os.path.join(SORTIE, "Fenetre_Cadeau.png"))
    icone_cadeau().save(os.path.join(SORTIE, "Icone_Cadeau.png"))
    barre(True).save(os.path.join(SORTIE, "Barre_Fond.png"))
    barre(False).save(os.path.join(SORTIE, "Barre_Plein.png"))
    bouton("OPEN!", (120, 235, 90), (40, 175, 70), (25, 120, 50)).save(os.path.join(SORTIE, "Bouton_Open.png"))
    bouton("WAIT...", (190, 196, 210), (130, 138, 156), (90, 96, 112)).save(os.path.join(SORTIE, "Bouton_Attente.png"))
    # apercu de l'interface montee (comme dans le jeu)
    ap = Image.new("RGBA", (1920, 1080), (60, 70, 90, 255))
    F = Image.open(os.path.join(SORTIE, "Fenetre_Cadeau.png"))
    ap.alpha_composite(F, (410, 90))
    ap.alpha_composite(Image.open(os.path.join(SORTIE, "Icone_Cadeau.png")).resize((380, 380)), (770, 270))
    ap.alpha_composite(Image.open(os.path.join(SORTIE, "Barre_Fond.png")), (500, 700))
    ap.alpha_composite(Image.open(os.path.join(SORTIE, "Barre_Plein.png")).crop((0, 0, 620, 110)), (500, 700))
    ap.alpha_composite(Image.open(os.path.join(SORTIE, "Bouton_Open.png")), (680, 830))
    d = ImageDraw.Draw(ap)
    d.text((950, 650), "READY IN 04:32", font=f(64), fill="white", anchor="mm", stroke_width=10, stroke_fill=NUIT)
    ap.convert("RGB").save(os.path.join(os.path.dirname(ICI), "Modeles", "Lobby", "apercu_interface_cadeau.png"))
    print("ok", SORTIE)
