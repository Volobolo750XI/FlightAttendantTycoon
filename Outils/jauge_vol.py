# Images de la jauge de vol cartoon (Textures/JaugeVol) :
#   Fond.png  : la jauge vide, arrondie, gros contour foncé (1024 x 128)
#   Rond.png  : un rond jaune (les 2 bouts arrondis du remplissage, 128 x 128)
#   Avion.png : l'avion cartoon vu de côté, nez vers la droite (256 x 256)
#   python Outils/jauge_vol.py
import os
from PIL import Image, ImageDraw, ImageFilter

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Textures", "JaugeVol")
K = 4  # dessin 4 fois plus grand puis réduit : bords bien lisses

CONTOUR = (27, 37, 65, 255)
JAUNE = (34, 197, 94, 255)        # (le remplissage est vert maintenant)
JAUNE_CLAIR = (134, 239, 172, 255)


def reduire(im, l, h):
    return im.resize((l, h), Image.LANCZOS)


def fond():
    L, H = 1024 * K, 128 * K
    im = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = H // 2
    d.rounded_rectangle([0, 0, L - 1, H - 1], r, fill=CONTOUR)
    e = 9 * K
    d.rounded_rectangle([e, e, L - 1 - e, H - 1 - e], r - e, fill=(214, 228, 247, 255))
    # ombre intérieure en haut (creux de la jauge)
    o = Image.new("L", (L, H), 0)
    do = ImageDraw.Draw(o)
    do.rounded_rectangle([e, e, L - 1 - e, int(H * 0.42)], (H * 0.42 - e) / 2, fill=70)
    o = o.filter(ImageFilter.GaussianBlur(6 * K))
    sombre = Image.new("RGBA", (L, H), (120, 140, 180, 255))
    masque = Image.new("L", (L, H), 0)
    ImageDraw.Draw(masque).rounded_rectangle([e, e, L - 1 - e, H - 1 - e], r - e, fill=255)
    from PIL import ImageChops
    im.paste(sombre, (0, 0), ImageChops.multiply(o, masque))
    reduire(im, 1024, 128).save(os.path.join(SORTIE, "Fond.png"))


def rond():
    T = 128 * K
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, T - 1, T - 1], fill=JAUNE)
    # bande claire en haut (la même que sur le milieu du remplissage : 0 % -> 38 % de la hauteur)
    m = Image.new("L", (T, T), 0)
    ImageDraw.Draw(m).ellipse([0, 0, T - 1, T - 1], fill=255)
    bande = Image.new("L", (T, T), 0)
    ImageDraw.Draw(bande).rectangle([0, int(T * 0.08), T, int(T * 0.38)], fill=255)
    from PIL import ImageChops
    im.paste(Image.new("RGBA", (T, T), JAUNE_CLAIR), (0, 0), ImageChops.multiply(m, bande))
    reduire(im, 128, 128).save(os.path.join(SORTIE, "Rond.png"))


def avion():
    """Avion cartoon : gros fuselage tout rond, ailes et queue arrondies, contour foncé épais."""
    T = 256 * K
    s = T / 256.0
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))

    def masque(dessin):
        m = Image.new("L", (T, T), 0)
        dessin(ImageDraw.Draw(m))
        return m

    def doux(m, r):
        # arrondit les coins d'une forme
        return m.filter(ImageFilter.GaussianBlur(r * s)).point(lambda v: 255 if v > 127 else 0)

    def poser(m, couleur, contour=7):
        if contour:
            gros = m.filter(ImageFilter.MaxFilter(int(contour * 2 * s) | 1))
            im.paste(Image.new("RGBA", (T, T), CONTOUR), (0, 0), gros)
        im.paste(Image.new("RGBA", (T, T), couleur), (0, 0), m)

    P = lambda pts: [(x * s, y * s) for x, y in pts]
    BLEU = (66, 153, 255, 255)
    BLEU_FONCE = (36, 104, 214, 255)
    BLANC = (255, 255, 255, 255)
    ROUGE = (255, 90, 95, 255)
    VITRE = (40, 70, 130, 255)

    # aile arrière (de l'autre côté, plus foncée)
    poser(doux(masque(lambda d: d.polygon(P([(126, 110), (156, 110), (118, 74), (102, 74)]), fill=255)), 4), BLEU_FONCE)
    # dérive
    poser(doux(masque(lambda d: d.polygon(P([(40, 118), (86, 118), (60, 52), (30, 52)]), fill=255)), 5), BLEU)
    # fuselage dodu : une gélule + la queue qui remonte
    def fuselage(d):
        d.rounded_rectangle(P([(44, 98), (232, 162)]), 32 * s, fill=255)
        d.polygon(P([(26, 104), (90, 100), (90, 150), (40, 140)]), fill=255)
    corps = doux(masque(fuselage), 6)
    poser(corps, BLANC)
    # nez rouge (la partie avant du fuselage), séparé par un trait
    nez = Image.new("L", (T, T), 0)
    ImageDraw.Draw(nez).rectangle(P([(200, 0), (256, 256)]), fill=255)
    from PIL import ImageChops
    nez = ImageChops.multiply(nez, corps)
    im.paste(Image.new("RGBA", (T, T), ROUGE), (0, 0), nez)
    trait = masque(lambda d: d.line(P([(200, 90), (200, 170)]), fill=255, width=int(5 * s)))
    im.paste(Image.new("RGBA", (T, T), CONTOUR), (0, 0), ImageChops.multiply(trait, corps))
    # cockpit
    poser(doux(masque(lambda d: d.polygon(P([(176, 106), (200, 106), (208, 124), (176, 124)]), fill=255)), 3), VITRE, 3)
    # hublots
    for x in (78, 104, 130, 156):
        poser(masque(lambda d, x=x: d.ellipse(P([(x, 112), (x + 14, 126)]), fill=255)), (140, 210, 255, 255), 3)
    # reflet blanc sur le haut
    poser(doux(masque(lambda d: d.rounded_rectangle(P([(60, 102), (170, 107)]), 3 * s, fill=255)), 1), (230, 242, 255, 255), 0)
    # aile avant (de notre côté)
    poser(doux(masque(lambda d: d.polygon(P([(122, 140), (160, 140), (100, 200), (80, 200)]), fill=255)), 5), BLEU)
    # bande bleue le long du corps
    bande = masque(lambda d: d.rectangle(P([(40, 140), (200, 148)]), fill=255))
    bande = ImageChops.multiply(bande, corps.filter(ImageFilter.MinFilter(int(4 * s) | 1)))
    aile = doux(masque(lambda d: d.polygon(P([(122, 140), (160, 140), (100, 200), (80, 200)]), fill=255)), 5)
    bande = ImageChops.subtract(bande, aile.filter(ImageFilter.MaxFilter(int(14 * s) | 1)))
    im.paste(Image.new("RGBA", (T, T), BLEU), (0, 0), bande)
    reduire(im, 256, 256).save(os.path.join(SORTIE, "Avion.png"))


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    fond()
    rond()
    # avion() : l'avion vient de Gemini (Textures/JaugeVol/Avion.png), on ne le redessine pas
    print("ok")
