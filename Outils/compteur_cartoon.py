"""Les 3 barres du compteur a gauche de l'ecran (Textures/Interface), style cartoon du jeu :
memes icones que les originales (liasse de billets ; billets + avion ; 2 fleches rouge et bleue),
redessinees avec un gros contour sombre, des reflets et du relief ; la barre derriere a le style
du kit (contour, epaisseur en bas, reflet). 1024 x 256 (affichees 288 x 72 dans le jeu).
Usage : python3 compteur_cartoon.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import interface_cartoon as IC

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Textures", "Interface")
CONTOUR = IC.CONTOUR
K = 4                       # sur-echantillonnage
T = 300                     # taille de l'icone (pixels finaux)
TRAIT = 9                   # epaisseur du contour (pixels finaux)
POLICE = os.path.join(ICI, "TitanOne-Regular.ttf")


def h(c, a=255):
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


class Dessin:
    """On empile des formes : chacune a son contour epais (dilate) puis son remplissage."""

    def __init__(self):
        self.im = Image.new("RGBA", (T * K, T * K), (0, 0, 0, 0))

    def masque(self, f):
        m = Image.new("L", self.im.size, 0)
        f(ImageDraw.Draw(m))
        return m

    def forme(self, f, couleur, trait=TRAIT, degrade=None):
        m = self.masque(f)
        if trait:
            r = int(trait * K) | 1
            self.im.paste(Image.new("RGBA", self.im.size, CONTOUR), (0, 0), m.filter(ImageFilter.MaxFilter(r)))
        if degrade:
            g = np.linspace(0, 1, self.im.size[1])[:, None, None]
            a, b = np.array(h(degrade[0])[:3]), np.array(h(degrade[1])[:3])
            box = m.getbbox()
            if box:
                y0, y1 = box[1], box[3]
                t = np.clip((np.arange(self.im.size[1]) - y0) / max(1, y1 - y0), 0, 1)[:, None, None]
                c = a * (1 - t) + b * t
                img = Image.fromarray(np.repeat(c, self.im.size[0], 1).astype(np.uint8)).convert("RGBA")
                self.im.paste(img, (0, 0), m)
        else:
            self.im.paste(Image.new("RGBA", self.im.size, h(couleur)), (0, 0), m)
        return m

    def dessus(self, f, couleur, alpha=255):
        """Detail sans contour (reflet, motif) : dessine par-dessus."""
        m = self.masque(f)
        self.im.paste(Image.new("RGBA", self.im.size, h(couleur, alpha)), (0, 0), m)

    def fin(self):
        return self.im.resize((T, T), Image.LANCZOS)


def P(pts):
    return [(x * K, y * K) for x, y in pts]


def billet_dollar(D, cx, cy, l, hh, ang, c1="5FCB5A", c2="2E8B3A"):
    """Un billet a plat (rectangle tourne), bord clair, cercle au $."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    def r(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)
    coin = [r(-l / 2, -hh / 2), r(l / 2, -hh / 2), r(l / 2, hh / 2), r(-l / 2, hh / 2)]
    D.forme(lambda d: d.polygon(P(coin), fill=255), None, degrade=(c1, c2))
    inner = [r(-l / 2 + 9, -hh / 2 + 8), r(l / 2 - 9, -hh / 2 + 8), r(l / 2 - 9, hh / 2 - 8), r(-l / 2 + 9, hh / 2 - 8)]
    D.dessus(lambda d: d.polygon(P(inner), outline=255, width=3 * K), "1E6B2C", 160)
    ccx, ccy = r(0, 0)
    rr = hh * 0.30
    D.dessus(lambda d: d.ellipse([(ccx - rr) * K, (ccy - rr) * K, (ccx + rr) * K, (ccy + rr) * K], fill=255), "BFF2B5")
    f = ImageFont.truetype(POLICE, int(rr * 1.5 * K))
    D.dessus(lambda d: d.text((ccx * K, ccy * K + K), "$", font=f, fill=255, anchor="mm"), "1E6B2C")


# ------------------------------------------------------------------ 1. la liasse de billets
def icone_argent():
    D = Dessin()
    # liasse vue de 3/4 : dessus (parallelogramme), face avant (tranche des billets), cote
    dx, dy = 44, -30
    x0, x1, y0, y1 = 40, 230, 150, 236                 # face avant
    dessus = [(x0, y0), (x1, y0), (x1 + dx, y0 + dy), (x0 + dx, y0 + dy)]
    cote = [(x1, y0), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1)]
    face = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    D.forme(lambda d: d.polygon(P(cote), fill=255), "2A7D36")
    D.forme(lambda d: d.polygon(P(face), fill=255), None, degrade=("3FAF4A", "237A30"))
    for k in range(1, 6):                              # tranches des billets empiles
        y = y0 + k * (y1 - y0) / 6
        D.dessus(lambda d, y=y: d.line(P([(x0 + 6, y), (x1 - 6, y)]), fill=255, width=3 * K), "A6E8A0", 200)
    D.forme(lambda d: d.polygon(P(dessus), fill=255), None, degrade=("8BE57F", "4DBA52"))
    # billet du dessus : bord, cercle et $
    cx, cy = (x0 + x1 + dx) / 2, y0 + dy / 2
    D.dessus(lambda d: d.polygon(P([(x0 + 18, y0 - 4), (x1 - 10, y0 - 4), (x1 + dx - 18, y0 + dy + 4), (x0 + dx + 10, y0 + dy + 4)]), outline=255, width=3 * K), "2E8B3A", 190)
    D.dessus(lambda d: d.ellipse(P([(cx - 22, cy - 12), (cx + 22, cy + 12)]), fill=255), "D9F7D2")
    D.dessus(lambda d: d.text((cx * K, cy * K + 2 * K), "$", font=ImageFont.truetype(POLICE, 26 * K), fill=255, anchor="mm"), "1E6B2C")
    # bande orange autour de la liasse (dessus + face)
    bx = 118
    D.forme(lambda d: d.polygon(P([(bx, y0), (bx + 40, y0), (bx + 40 + dx, y0 + dy), (bx + dx, y0 + dy)]), fill=255), "FF9A3C", trait=6)
    D.forme(lambda d: d.polygon(P([(bx, y0), (bx + 40, y0), (bx + 40, y1), (bx, y1)]), fill=255), None, trait=6, degrade=("FFA94D", "E5711F"))
    D.dessus(lambda d: d.polygon(P([(bx + 6, y0 + 4), (bx + 14, y0 + 4), (bx + 14, y1 - 6), (bx + 6, y1 - 6)]), fill=255), "FFFFFF", 110)
    # reflet sur la face avant
    D.dessus(lambda d: d.rounded_rectangle(P([(x0 + 10, y0 + 6), (x0 + 70, y0 + 16)]), 4 * K, fill=255), "FFFFFF", 90)
    return D.fin()


# ------------------------------------------------------------------ 2. billets + avion
def icone_revenu():
    D = Dessin()
    for cx, cy, a in ((98, 128, -28), (128, 112, -8), (150, 120, 14)):        # eventail de billets
        billet_dollar(D, cx, cy, 120, 66, a)
    # liasse au premier plan, bande creme
    billet_dollar(D, 118, 196, 150, 70, -4, "4FBF52", "277F33")
    D.forme(lambda d: d.polygon(P([(96, 162), (124, 160), (128, 232), (100, 234)]), fill=255), None, trait=6, degrade=("FFE9C2", "F3C98A"))
    # traits de vitesse
    for x0, y0, x1, y1 in ((150, 52, 178, 36), (180, 50, 214, 30), (226, 168, 260, 150), (40, 236, 70, 222)):
        D.forme(lambda d, a=(x0, y0, x1, y1): d.line(P([(a[0], a[1]), (a[2], a[3])]), fill=255, width=5 * K), "FFFFFF", trait=5)
    # l'avion : fuselage blanc, nez rouge, ailes bleues, hublots
    ang = math.radians(-22)
    cx, cy = 196, 110
    def r(x, y):
        return (cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang))
    queue = [r(-70, -6), r(-96, -44), r(-78, -46), r(-50, -10)]
    D.forme(lambda d: d.polygon(P(queue), fill=255), "3B82F6")
    aile_ar = [r(-4, 8), r(40, 8), r(10, 52), r(-14, 52)]
    D.forme(lambda d: d.polygon(P(aile_ar), fill=255), "2563EB")
    corps = [r(x, y) for x, y in [(-84, -4)] + [(80 * math.cos(t), 22 * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 24)] + [(-84, 14)]]
    D.forme(lambda d: d.polygon(P(corps), fill=255), None, degrade=("FFFFFF", "D6E2F0"))
    nez = [r(80 * math.cos(t), 22 * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 20)] + [r(58, 20), r(58, -20)]
    D.forme(lambda d: d.polygon(P(nez), fill=255), "EF4444", trait=6)
    for k in range(4):
        wx, wy = r(-34 + k * 20, -4)
        D.dessus(lambda d, wx=wx, wy=wy: d.ellipse(P([(wx - 6, wy - 6), (wx + 6, wy + 6)]), fill=255), "1D4ED8")
    aile = [r(-10, -2), r(30, -2), r(-6, -48), r(-26, -48)]
    D.forme(lambda d: d.polygon(P(aile), fill=255), "60A5FA")
    D.dessus(lambda d: d.polygon(P([r(-50, -14), r(40, -14), r(40, -10), r(-50, -10)]), fill=255), "FFFFFF", 200)
    return D.fin()


# ------------------------------------------------------------------ 3. les 2 fleches (rebirth)
def fleche_courbe(D, cx, cy, r, ep, a0, a1, c1, c2):
    """Fleche epaisse en arc de cercle, de l'angle a0 a a1 (degres, sens des aiguilles), pointe au bout."""
    n = 40
    ext = [(cx + (r + ep / 2) * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cy + (r + ep / 2) * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    inn = [(cx + (r - ep / 2) * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cy + (r - ep / 2) * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    a = math.radians(a1)
    s = 1 if a1 > a0 else -1
    tx, ty = -math.sin(a) * s, math.cos(a) * s                    # direction de la pointe
    nx, ny = math.cos(a), math.sin(a)
    bx, by = cx + r * nx, cy + r * ny
    W, L = ep * 1.15, ep * 1.25
    tete = [(bx + nx * W, by + ny * W), (bx + tx * L, by + ty * L), (bx - nx * W, by - ny * W)]
    corps = ext + inn[::-1]
    D.forme(lambda d: (d.polygon(P(corps), fill=255), d.polygon(P(tete), fill=255)), None, degrade=(c1, c2))
    # reflet le long de l'arc
    ref = [(cx + (r + ep * 0.22) * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cy + (r + ep * 0.22) * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(4, n - 4)]
    D.dessus(lambda d: d.line(P(ref), fill=255, width=int(ep * 0.16 * K), joint="curve"), "FFFFFF", 120)


def icone_rebirth():
    D = Dessin()
    fleche_courbe(D, 150, 150, 86, 40, 168, 318, "FF6B86", "D9264F")        # rouge : en haut, vers la droite
    fleche_courbe(D, 150, 150, 86, 40, -12, 138, "BDE9FF", "5BB8F0")         # bleue : en bas, vers la gauche
    return D.fin()


# ------------------------------------------------------------------ les barres
def barre(nom, haut, bas, icone):
    W, H = 1024, 256
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b = IC.piece("_tmp", W - 150, 184, 44, haut, bas, ep=9, levre=12, reflet=0.30, dossier=SORTIE)
    im.alpha_composite(b, (140, 36))
    ic = icone.resize((256, 256), Image.LANCZOS)
    im.alpha_composite(ic, (0, 0))
    im.save(os.path.join(SORTIE, nom + ".png"))


if __name__ == "__main__":
    barre("FondArgent", "7CF07A", "22B24C", icone_argent())
    barre("FondRevenu", "5BE3FF", "1497E0", icone_revenu())
    barre("FondRebirth", "FF8AB0", "E2386E", icone_rebirth())
    os.remove(os.path.join(SORTIE, "_tmp.png"))
    print("ok")
