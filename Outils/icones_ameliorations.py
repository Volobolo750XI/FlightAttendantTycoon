"""Pictogrammes blancs de l'onglet UPGRADES (traits epais, fond transparent, 512 x 512).

Simples et lisibles en un coup d'oeil : un escalier + "2F", un verre a cocktail pour le bar, etc.
Usage : python3 Outils/icones_ameliorations.py  -> Textures/Ameliorations/*.png
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Textures", "Ameliorations")
POLICE = os.path.join(ICI, "ArchivoBlack.ttf")
S = 4                      # supersampling
T = 512 * S
EP = 26 * S                # epaisseur des traits
BLANC = (255, 255, 255, 255)


class Dessin:
    def __init__(self):
        self.im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    @staticmethod
    def p(x, y):
        return (x * S, y * S)

    def trait(self, pts, ep=EP, ferme=False):
        pts = [self.p(*q) for q in pts]
        if ferme:
            pts = pts + [pts[0]]
        self.d.line(pts, fill=BLANC, width=ep, joint="curve")
        for q in (pts[0], pts[-1]):
            r = ep / 2
            self.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=BLANC)

    def rect(self, x0, y0, x1, y1, r=18, ep=EP, plein=False):
        box = [x0 * S, y0 * S, x1 * S, y1 * S]
        if plein:
            self.d.rounded_rectangle(box, radius=r * S, fill=BLANC)
        else:
            self.d.rounded_rectangle(box, radius=r * S, outline=BLANC, width=ep)

    def rond(self, cx, cy, r, ep=EP, plein=False):
        box = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
        if plein:
            self.d.ellipse(box, fill=BLANC)
        else:
            self.d.ellipse(box, outline=BLANC, width=ep)

    def arc(self, cx, cy, r, a0, a1, ep=EP):
        box = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
        self.d.arc(box, a0, a1, fill=BLANC, width=ep)

    def poly(self, pts):
        self.d.polygon([self.p(*q) for q in pts], fill=BLANC)

    def texte(self, s, cx, cy, taille=110):
        f = ImageFont.truetype(POLICE, taille * S)
        self.d.text((cx * S, cy * S), s, font=f, fill=BLANC, anchor="mm")

    def trou(self, x0, y0, x1, y1, r=0):
        """Efface une zone (pour detacher un texte d'un trait)."""
        self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=(0, 0, 0, 0))

    def sauver(self, nom):
        os.makedirs(SORTIE, exist_ok=True)
        self.im.resize((512, 512), Image.LANCZOS).save(os.path.join(SORTIE, nom + ".png"))


# ------------------------------------------------------------------ elements
def avion_cote(d, x0=60, y=250, L=390, k=1.0):
    """Avion vu de profil (contour)."""
    h = 70 * k
    d.trait([(x0 + 40, y - h / 2), (x0 + L - 70, y - h / 2)])
    d.arc(x0 + L - 70, y, h / 2, 270, 90)
    d.trait([(x0 + L - 70, y + h / 2), (x0 + 30, y + h / 2), (x0 + 5, y - h / 2 - 70 * k), (x0 + 40, y - h / 2)])
    # aile
    d.trait([(x0 + L * 0.45, y + 10), (x0 + L * 0.30, y + 120 * k), (x0 + L * 0.40, y + 120 * k), (x0 + L * 0.62, y + 10)])
    # hublots
    for i in range(5):
        d.rond(x0 + L * 0.35 + i * 38 * k, y - 8, 7 * k, plein=True)


def avion_face(d, moteurs=2, cy=270):
    """Avion vu de face : fuselage rond, ailes, moteurs."""
    d.rond(256, cy, 70)
    d.rond(256, cy - 10, 18, plein=True)                     # cockpit
    d.trait([(186, cy + 10), (40, cy + 40)])
    d.trait([(326, cy + 10), (472, cy + 40)])
    d.trait([(256, cy - 70), (256, cy - 150)])               # derive
    pos = {2: [130], 4: [110, 170], 6: [80, 130, 180]}[moteurs]
    for dx in pos:
        for sgn in (-1, 1):
            x = 256 - (256 - dx) * sgn
            d.rond(x, cy + 60, 24)


def siege(d, x, y, k=1.0, couche=False):
    """Siege d'avion de profil (dossier + assise + pied)."""
    if couche:
        d.trait([(x - 120 * k, y), (x + 120 * k, y)])
        d.trait([(x - 120 * k, y - 50 * k), (x - 120 * k, y + 60 * k)])
        d.trait([(x, y), (x, y + 70 * k)])
        d.trait([(x - 60 * k, y + 70 * k), (x + 60 * k, y + 70 * k)])
        return
    d.trait([(x - 60 * k, y - 140 * k), (x - 40 * k, y), (x + 70 * k, y)])
    d.trait([(x + 10 * k, y), (x + 10 * k, y + 80 * k)])
    d.trait([(x - 40 * k, y + 80 * k), (x + 60 * k, y + 80 * k)])


def avion_dessus(d, cx=256, cy=256, k=1.0):
    """Pictogramme avion vu de dessus (plein), nez vers le haut."""
    P = [(0, -200), (22, -170), (24, -60), (190, 20), (190, 55), (24, 15), (20, 120), (75, 160), (75, 185),
         (0, 165)]
    pts = P + [(-x, y) for x, y in reversed(P[1:-1])]
    d.poly([(cx + x * k, cy + y * k) for x, y in pts])


# ------------------------------------------------------------------ icones
def icones():
    I = {}

    # ---- AVION ----
    d = Dessin(); avion_dessus(d, 256, 266, 1.1); I["Avion_01"] = d

    d = Dessin()                                   # rangee du milieu : sieges vus de dessus 2 | 2 | 2
    for cx, plein in ((110, False), (256, True), (402, False)):
        for dx in (-34, 34):
            for y in (120, 230, 340):
                d.rect(cx + dx - 26, y, cx + dx + 26, y + 70, r=12, ep=12 * S, plein=plein)
    d.texte("+", 256, 455, 90)
    I["Avion_02"] = d

    d = Dessin()                                   # allonge : avion + fleches haut / bas
    avion_dessus(d, 215, 256, 1.0)
    d.trait([(440, 70), (440, 440)])
    d.trait([(405, 110), (440, 70), (475, 110)]); d.trait([(405, 400), (440, 440), (475, 400)])
    I["Avion_03"] = d

    d = Dessin(); avion_face(d, 4); I["Avion_04"] = d

    d = Dessin()                                   # 2e etage : escalier + 2F
    marches = [(70, 440), (70, 380), (150, 380), (150, 320), (230, 320), (230, 260), (310, 260), (310, 200), (390, 200)]
    d.trait(marches)
    d.trait([(70, 440), (390, 440), (390, 200)])
    d.texte("2F", 370, 105, 120)
    I["Avion_05"] = d

    d = Dessin()                                   # 3e etage : ascenseur + 3F
    d.rect(80, 120, 330, 450, r=14)
    d.trait([(205, 140), (205, 430)])
    d.trait([(140, 285), (180, 285)]); d.trait([(230, 285), (270, 285)])
    d.rect(370, 200, 450, 370, r=20)
    d.poly([(410, 225), (430, 255), (390, 255)]); d.poly([(410, 345), (430, 315), (390, 315)])
    d.texte("3F", 410, 90, 90)
    I["Avion_06"] = d

    d = Dessin(); avion_face(d, 6); I["Avion_07"] = d

    d = Dessin(); avion_dessus(d, 256, 300, 0.95)  # geant dore : avion + couronne
    d.trait([(176, 110), (176, 40), (216, 75), (256, 25), (296, 75), (336, 40), (336, 110)], ferme=True)
    I["Avion_08"] = d

    # ---- ESPACES ----
    d = Dessin()                                   # bar : verre a cocktail
    d.trait([(110, 110), (400, 110), (256, 290)], ferme=True)
    d.trait([(256, 290), (256, 420)]); d.trait([(170, 430), (342, 430)])
    d.trait([(330, 60), (290, 200)], ep=16 * S); d.rond(390, 120, 40)
    I["Espace_Bar"] = d

    d = Dessin()                                   # salon : canape
    d.rect(90, 180, 422, 300, r=40)
    d.rect(50, 240, 140, 380, r=30); d.rect(372, 240, 462, 380, r=30)
    d.trait([(140, 330), (372, 330)])
    d.trait([(90, 380), (90, 430)]); d.trait([(422, 380), (422, 430)])
    I["Espace_Salon"] = d

    d = Dessin()                                   # restaurant : assiette + couverts
    d.rond(256, 270, 130); d.rond(256, 270, 80, ep=14 * S)
    d.trait([(70, 130), (70, 420)]); d.trait([(50, 130), (50, 210), (90, 210), (90, 130)])
    d.trait([(442, 130), (442, 420)]); d.d.pieslice([(400 * S, 120 * S), (484 * S, 300 * S)], 180, 360, fill=BLANC)
    I["Espace_Restaurant"] = d

    d = Dessin()                                   # cinema : clap
    d.rect(70, 200, 442, 440, r=20)
    d.trait([(70, 200), (90, 110), (440, 60), (442, 150)])
    for x in (150, 250, 350):
        d.trait([(x, 165), (x + 40, 80)], ep=18 * S)
    d.poly([(220, 270), (220, 380), (310, 325)])
    I["Espace_Cinema"] = d

    d = Dessin()                                   # spa : lotus
    d.trait([(256, 150), (310, 260), (256, 360), (202, 260)], ferme=True)
    d.trait([(256, 360), (140, 330), (100, 230), (190, 250)])
    d.trait([(256, 360), (372, 330), (412, 230), (322, 250)])
    d.trait([(90, 420), (422, 420)])
    I["Espace_Spa"] = d

    d = Dessin()                                   # piscine : echelle + vagues
    d.trait([(170, 80), (170, 300)]); d.trait([(300, 80), (300, 300)])
    d.arc(210, 80, 40, 180, 360); d.arc(340, 80, 40, 180, 360)
    d.trait([(170, 160), (300, 160)]); d.trait([(170, 240), (300, 240)])
    for y in (340, 420):
        pts = [(60 + i * 8, y + 22 * math.sin(i * 8 / 392 * 4 * math.pi)) for i in range(50)]
        d.trait(pts)
    I["Espace_Piscine"] = d

    # ---- CLASSES ----
    d = Dessin(); siege(d, 220, 280, 1.4); d.texte("+", 390, 150, 160); I["Classe_Premium"] = d
    d = Dessin(); siege(d, 256, 280, 1.4, couche=True); d.trait([(120, 200), (200, 160)]); I["Classe_Business"] = d
    d = Dessin(); d.rect(70, 110, 442, 440, r=24); siege(d, 230, 300, 1.0); d.trait([(370, 130), (370, 420)]); I["Classe_First"] = d
    d = Dessin()                                   # suite : lit + couronne
    d.rect(60, 270, 452, 380, r=20); d.trait([(60, 200), (60, 440)]); d.trait([(452, 300), (452, 440)])
    d.rect(90, 225, 210, 270, r=20)
    d.trait([(200, 170), (200, 90), (233, 125), (256, 70), (279, 125), (312, 90), (312, 170)], ferme=True)
    I["Classe_Suite"] = d

    # ---- CONFORT ----
    d = Dessin(); d.rect(70, 100, 442, 350, r=24); d.poly([(220, 170), (220, 280), (310, 225)]); d.trait([(200, 430), (312, 430)]); d.trait([(256, 350), (256, 430)]); I["Confort_Ecrans"] = d
    d = Dessin()
    for r in (90, 170, 250):
        d.arc(256, 400, r, 225, 315)
    d.rond(256, 400, 30, plein=True)
    I["Confort_Wifi"] = d
    d = Dessin(); d.rect(80, 120, 432, 250, r=60); d.rect(60, 290, 452, 440, r=30); d.trait([(60, 360), (452, 360)], ep=14 * S); I["Confort_Couvertures"] = d
    d = Dessin(); siege(d, 220, 290, 1.4)
    for r in (60, 110):
        d.arc(300, 220, r, 300, 60, ep=18 * S)
    I["Confort_Massage"] = d

    # ---- REBIRTH ----
    d = Dessin()
    d.arc(256, 256, 170, 200, 340); d.arc(256, 256, 170, 20, 160)
    d.poly([(420, 210), (470, 300), (370, 290)]); d.poly([(92, 302), (42, 212), (142, 222)])
    d.rond(256, 256, 40, plein=True)
    I["Rebirth"] = d

    return I


if __name__ == "__main__":
    for nom, d in icones().items():
        d.sauver(nom)
        print(nom)
