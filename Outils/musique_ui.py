"""Icones MUSIQUE ON / OFF du HUD (style cartoon, dessinees a 4x puis reduites) -> Textures/InterfaceMusique/
  Musique_On.png  (256 x 256) : rond vert, note de musique blanche
  Musique_Off.png (256 x 256) : rond rouge, note barree
Usage : python3 Outils/musique_ui.py
"""
import os

from PIL import Image, ImageDraw

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(ICI), "Textures", "InterfaceMusique")
NUIT = (22, 27, 48)
S = 4


def degrade_rond(n, boite, haut, bas):
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(n):
        t = y / (n - 1)
        d.line([(0, y), (n, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(haut, bas)) + (255,))
    m = Image.new("L", (n, n), 0)
    ImageDraw.Draw(m).ellipse(boite, fill=255)
    out = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


def icone(haut, bas, barre):
    n = 256 * S
    u = S
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([12 * u, 20 * u, 244 * u, 252 * u], fill=(14, 18, 34))                  # epaisseur
    d.ellipse([12 * u, 10 * u, 244 * u, 242 * u], fill=NUIT)                           # contour
    img.alpha_composite(degrade_rond(n, [30 * u, 28 * u, 226 * u, 224 * u], haut, bas))
    reflet = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(reflet).ellipse([62 * u, 40 * u, 194 * u, 104 * u], fill=(255, 255, 255, 70))
    img.alpha_composite(reflet)
    d = ImageDraw.Draw(img)
    # double croche : 2 tetes, 2 hampes, une barre
    e = 12 * u
    for x0, y0 in ((70, 150), (142, 132)):
        d.ellipse([(x0 - 4) * u, (y0 - 4) * u, (x0 + 48) * u, (y0 + 38) * u], fill=NUIT)
        d.ellipse([x0 * u, y0 * u, (x0 + 44) * u, (y0 + 34) * u], fill=(255, 255, 255))
    d.polygon([(100 * u, 72 * u), (186 * u, 52 * u), (186 * u, 80 * u), (100 * u, 100 * u)], fill=NUIT)
    for x, y1 in ((100, 166), (172, 148)):
        d.rectangle([(x - 2) * u, 60 * u, (x + 16) * u, y1 * u], fill=NUIT)
        d.rectangle([(x + 2) * u, 70 * u, (x + 12) * u, (y1 - 4) * u], fill=(255, 255, 255))
    d.polygon([(104 * u, 78 * u), (182 * u, 60 * u), (182 * u, 74 * u), (104 * u, 92 * u)], fill=(255, 255, 255))
    if barre:
        d.line([(62 * u, 62 * u), (194 * u, 194 * u)], fill=NUIT, width=34 * u)
        d.line([(66 * u, 66 * u), (190 * u, 190 * u)], fill=(255, 255, 255), width=18 * u)
    return img.resize((256, 256), Image.LANCZOS)


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    icone((130, 238, 96), (36, 170, 66), False).save(os.path.join(SORTIE, "Musique_On.png"))
    icone((255, 112, 112), (206, 36, 60), True).save(os.path.join(SORTIE, "Musique_Off.png"))
    ap = Image.new("RGBA", (560, 300), (70, 86, 70, 255))
    ap.alpha_composite(Image.open(os.path.join(SORTIE, "Musique_On.png")), (20, 22))
    ap.alpha_composite(Image.open(os.path.join(SORTIE, "Musique_Off.png")), (290, 22))
    ap.convert("RGB").save(os.path.join(os.path.dirname(ICI), "Modeles", "Lobby", "apercu_musique.png"))
    print("ok")
