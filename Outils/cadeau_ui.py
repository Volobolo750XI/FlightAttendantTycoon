"""Interface CARTOON des cadeaux du lobby (FREE GIFTS) -> Textures/InterfaceCadeau/*.png
Tout est dessine en vectoriel a 4x puis reduit : bords nets, transparence propre, tailles en puissance de 2.
  Fenetre_Cadeaux.png (2048 x 1024) : la fenetre (affichee en 1440 x 720)
  Carte_1..6.png      (256 x 256)   : les cartes de couleur (affichees en 140 x 140)
  Carte_Prete.png     (256 x 256)   : la carte verte avec halo dore (cadeau pret)
  Icone_Cadeau.png    (256 x 256)   : le cadeau dessine sur chaque carte
  Bouton_Open.png     (256 x 128)   : le bouton OPEN (le seul endroit cliquable)
Usage : python3 Outils/cadeau_ui.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(ICI), "Textures", "InterfaceCadeau")
POLICE = os.path.join(ICI, "TitanOne-Regular.ttf")
NUIT = (22, 27, 48)
ARC = [(238, 48, 56), (255, 136, 24), (250, 205, 30), (64, 196, 64), (24, 186, 220), (44, 104, 240), (136, 60, 230),
       (230, 50, 170)]
S = 4                                   # sur-echantillonnage


def f(t):
    return ImageFont.truetype(POLICE, int(t))


def degrade(w, h, haut, bas):
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(haut, bas)) + (255,))
    return im


def forme(im, boite, r, remplissage):
    """colle une image (ou couleur) dans un rectangle arrondi"""
    x0, y0, x1, y1 = [int(v) for v in boite]
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([x0, y0, x1, y1], int(r), fill=255)
    if isinstance(remplissage, tuple):
        couche = Image.new("RGBA", im.size, remplissage + (255,) if len(remplissage) == 3 else remplissage)
    else:
        couche = Image.new("RGBA", im.size, (0, 0, 0, 0))
        couche.paste(remplissage.resize((x1 - x0, y1 - y0)), (x0, y0))
    im.paste(couche, (0, 0), m)


def reflet(im, boite, r, opacite=70):
    x0, y0, x1, y1 = boite
    c = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle([x0, y0, x1, y1], int(r), fill=(255, 255, 255, opacite))
    im.alpha_composite(c)


def etincelle(d, x, y, r, col=(255, 255, 255, 255)):
    pts = []
    for i in range(8):
        a = math.pi / 2 + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.28
        pts.append((x + rr * math.cos(a), y - rr * math.sin(a)))
    d.polygon(pts, fill=col)


def finir(im, taille):
    return im.resize(taille, Image.LANCZOS)


def mot_arc_en_ciel(img, mot, cx, cy, taille, contour):
    d = ImageDraw.Draw(img)
    ft = f(taille)
    esp = taille * 0.04
    larg = [d.textlength(c, font=ft) + (esp if c != " " else 0) for c in mot]
    x = cx - sum(larg) / 2
    k = 0
    for c, lg in zip(mot, larg):
        if c != " ":
            col = ARC[k % len(ARC)]
            k += 1
            # ombre portee + contour epais
            d.text((x + contour * 0.35, cy + contour * 0.6), c, font=ft, fill=NUIT, anchor="lm", stroke_width=contour, stroke_fill=NUIT)
            d.text((x, cy), c, font=ft, fill=col, anchor="lm", stroke_width=contour, stroke_fill=NUIT)
            # reflet sur le haut de la lettre
            couche = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(couche).text((x, cy), c, font=ft, fill=tuple(min(255, int(v * 0.5 + 128)) for v in col) + (255,), anchor="lm")
            bb = d.textbbox((x, cy), c, font=ft, anchor="lm")
            masque = Image.new("L", img.size, 0)
            ImageDraw.Draw(masque).rectangle([0, 0, img.width, bb[1] + (bb[3] - bb[1]) * 0.42], fill=255)
            img.paste(couche, (0, 0), Image.composite(couche, Image.new("RGBA", img.size, (0, 0, 0, 0)), masque).getchannel("A"))
        x += lg


def fenetre():
    W, H = 2048 * S // 2, 1024 * S // 2          # dessine a 2x de 2048 (assez net et rapide)
    k = W / 2048
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ep = 22 * k
    # corps de la fenetre
    corps = [10 * k, 130 * k, W - 10 * k, H - 10 * k]
    forme(img, corps, 90 * k, NUIT)
    forme(img, [corps[0] + ep, corps[1] + ep, corps[2] - ep, corps[3] - ep], 70 * k,
          degrade(400, 400, (130, 216, 255), (54, 112, 232)))
    d = ImageDraw.Draw(img)
    for x, y, r in ((120, 330, 16), (1930, 360, 20), (90, 820, 12), (1960, 760, 14), (300, 940, 10), (1760, 950, 12),
                    (1000, 960, 9), (640, 300, 8), (1420, 300, 9)):
        etincelle(d, x * k, y * k, r * k, (255, 255, 255, 170))
    # bandeau du titre
    b = [360 * k, 14 * k, W - 360 * k, 244 * k]
    forme(img, [b[0], b[1] + 14 * k, b[2], b[3] + 14 * k], 80 * k, (14, 18, 34))           # ombre
    forme(img, b, 80 * k, NUIT)
    forme(img, [b[0] + ep, b[1] + ep, b[2] - ep, b[3] - ep], 60 * k, degrade(400, 400, (255, 128, 206), (150, 72, 232)))
    reflet(img, [b[0] + 50 * k, b[1] + 36 * k, b[2] - 50 * k, b[1] + 100 * k], 30 * k, 60)
    mot_arc_en_ciel(img, "FREE GIFTS", W / 2, (b[1] + b[3]) / 2 + 2 * k, 164 * k, int(18 * k))
    return finir(img, (2048, 1024))


def carte(haut, bas, pret=False):
    n = 256 * S
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    m = 14 * S
    if pret:
        halo = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        ImageDraw.Draw(halo).rounded_rectangle([m - 8 * S, m - 8 * S, n - m + 8 * S, n - m + 8 * S], 46 * S, fill=(255, 222, 70, 255))
        img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(5 * S)))
    forme(img, [m, m + 6 * S, n - m, n - m + 6 * S], 40 * S, (14, 18, 34))                  # epaisseur sous la carte
    forme(img, [m, m, n - m, n - m], 40 * S, NUIT)
    forme(img, [m + 10 * S, m + 10 * S, n - m - 10 * S, n - m - 10 * S], 31 * S, degrade(64, 64, haut, bas))
    reflet(img, [m + 22 * S, m + 18 * S, n - m - 22 * S, m + 70 * S], 22 * S, 55)
    d = ImageDraw.Draw(img)
    etincelle(d, n - m - 34 * S, m + 40 * S, 12 * S, (255, 255, 255, 220))
    etincelle(d, n - m - 56 * S, m + 66 * S, 6 * S, (255, 255, 255, 180))
    etincelle(d, m + 34 * S, n - m - 90 * S, 6 * S, (255, 255, 255, 140))
    return finir(img, (256, 256))


def icone_cadeau():
    n = 256 * S
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = n / 512
    e = 15 * u
    # boite
    d.rounded_rectangle([104 * u, 236 * u, 408 * u, 470 * u], 26 * u, fill=(236, 58, 150), outline=NUIT, width=int(e))
    d.rectangle([120 * u, 252 * u, 392 * u, 296 * u], fill=(206, 40, 128))                   # ombre du couvercle
    d.rounded_rectangle([130 * u, 312 * u, 150 * u, 440 * u], 10 * u, fill=(255, 140, 200))     # reflet
    # couvercle
    d.rounded_rectangle([80 * u, 172 * u, 432 * u, 256 * u], 24 * u, fill=(255, 98, 180), outline=NUIT, width=int(e))
    d.rounded_rectangle([102 * u, 188 * u, 410 * u, 208 * u], 10 * u, fill=(255, 170, 215))
    # ruban
    d.rectangle([226 * u, 180 * u, 286 * u, 462 * u], fill=(40, 200, 235))
    d.line([(226 * u, 180 * u), (226 * u, 462 * u)], fill=NUIT, width=int(e * 0.7))
    d.line([(286 * u, 180 * u), (286 * u, 462 * u)], fill=NUIT, width=int(e * 0.7))
    d.rectangle([238 * u, 190 * u, 252 * u, 454 * u], fill=(160, 238, 255))
    d.line([(80 * u, 256 * u), (432 * u, 256 * u)], fill=NUIT, width=int(e))
    # noeud : 2 grandes boucles en goutte + 2 bouts qui pendent + le centre
    for sx in (-1, 1):
        boucle = [(256 + sx * 20, 168), (256 + sx * 70, 92), (256 + sx * 120, 62), (256 + sx * 156, 78),
                  (256 + sx * 160, 126), (256 + sx * 120, 160), (256 + sx * 40, 176)]
        pts = [(x * u, y * u) for x, y in boucle]
        d.polygon(pts, fill=(40, 200, 235))
        d.line(pts + [pts[0], pts[1]], fill=NUIT, width=int(e), joint="curve")
        creux = [(256 + sx * 44, 160), (256 + sx * 112, 110), (256 + sx * 128, 136)]
        d.polygon([(x * u, y * u) for x, y in creux], fill=(18, 140, 182))
        d.line([((256 + sx * 76) * u, 90 * u), ((256 + sx * 120) * u, 76 * u)], fill=(170, 240, 255), width=int(10 * u))
    d.ellipse([218 * u, 128 * u, 294 * u, 196 * u], fill=(40, 200, 235), outline=NUIT, width=int(e))
    d.ellipse([236 * u, 142 * u, 258 * u, 156 * u], fill=(170, 240, 255))
    return finir(img, (256, 256))


def bouton_open():
    W, H = 256 * S, 128 * S
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = 6 * S
    forme(img, [m, m + 10 * S, W - m, H - m], 34 * S, NUIT)
    forme(img, [m + 8 * S, m + 18 * S, W - m - 8 * S, H - m - 8 * S], 28 * S, (24, 120, 50))       # epaisseur
    forme(img, [m + 8 * S, m + 8 * S, W - m - 8 * S, H - m - 22 * S], 28 * S, degrade(64, 64, (130, 238, 96), (44, 178, 70)))
    reflet(img, [m + 24 * S, m + 14 * S, W - m - 24 * S, m + 38 * S], 12 * S, 85)
    d = ImageDraw.Draw(img)
    d.text((W / 2, H / 2 - 6 * S), "OPEN", font=f(60 * S), fill=(255, 255, 255), anchor="mm", stroke_width=9 * S, stroke_fill=NUIT)
    return finir(img, (256, 128))


COULEURS = [((255, 112, 112), (214, 42, 64)), ((255, 184, 80), (238, 116, 26)), ((178, 128, 255), (114, 58, 218)),
            ((96, 224, 255), (26, 146, 218)), ((255, 136, 212), (216, 56, 156)), ((255, 226, 96), (232, 166, 18))]

if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    for vieux in os.listdir(SORTIE):
        if vieux.endswith(".png"):
            os.remove(os.path.join(SORTIE, vieux))
    fenetre().save(os.path.join(SORTIE, "Fenetre_Cadeaux.png"))
    for i, (h, b) in enumerate(COULEURS):
        carte(h, b).save(os.path.join(SORTIE, f"Carte_{i + 1}.png"))
    carte((140, 240, 110), (36, 176, 66), True).save(os.path.join(SORTIE, "Carte_Prete.png"))
    icone_cadeau().save(os.path.join(SORTIE, "Icone_Cadeau.png"))
    bouton_open().save(os.path.join(SORTIE, "Bouton_Open.png"))

    # apercu monte exactement comme dans Verse (ecran 1920 x 1080)
    ap = Image.new("RGBA", (1920, 1080), (70, 86, 70, 255))
    ap.alpha_composite(Image.open(os.path.join(SORTIE, "Fenetre_Cadeaux.png")).resize((1440, 720), Image.LANCZOS), (240, 180))
    fx = os.path.join(os.path.dirname(ICI), "Textures", "InterfacePC", "Fermer.png")
    if os.path.exists(fx):
        ap.alpha_composite(Image.open(fx).resize((80, 80), Image.LANCZOS), (1612, 236))
    ic = Image.open(os.path.join(SORTIE, "Icone_Cadeau.png")).resize((80, 80), Image.LANCZOS)
    bo = Image.open(os.path.join(SORTIE, "Bouton_Open.png")).resize((100, 50), Image.LANCZOS)
    d = ImageDraw.Draw(ap)
    delais = [2, 5, 10, 15, 20, 30, 45, 60]
    cumul = 0
    for k in range(21):
        x, y = 398 + (k % 7) * 164, 372 + (k // 7) * 166
        nom = "Carte_Prete.png" if k == 0 else f"Carte_{k % 6 + 1}.png"
        ap.alpha_composite(Image.open(os.path.join(SORTIE, nom)).resize((140, 140), Image.LANCZOS), (x, y))
        ap.alpha_composite(ic, (x + 30, y + 30))
        d.text((x + 70, y + 24), f"GIFT {k + 1}", font=f(17), fill="white", anchor="mm", stroke_width=4, stroke_fill=NUIT)
        if k == 0:
            ap.alpha_composite(bo, (x + 20, y + 86))
        else:
            cumul += delais[min(k, 7)]
            t = f"{cumul // 60}:{cumul % 60:02d}:00" if cumul >= 60 else f"{cumul:02d}:00"
            d.text((x + 70, y + 112), t, font=f(20), fill="white", anchor="mm", stroke_width=4, stroke_fill=NUIT)
    ap.convert("RGB").save(os.path.join(os.path.dirname(ICI), "Modeles", "Lobby", "apercu_interface_cadeau.png"))
    print("ok", SORTIE)
