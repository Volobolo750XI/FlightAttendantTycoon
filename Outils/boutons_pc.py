# Boutons arrondis cartoon du PC (Textures/BoutonsPC) : contour foncé, reflet clair en haut.
#   Vert / Bleu / Jaune / Gris : gros boutons des cartes de vol (512 x 256, affichés 2:1)
#   OngletBleu / OngletSombre  : onglets et CLOSE (512 x 128, affichés 4:1)
#   python Outils/boutons_pc.py
import os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Textures", "BoutonsPC")
K = 4
CONTOUR = (27, 37, 65, 255)


def hexa(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def bouton(nom, l, h, couleur, rayon, ep):
    L, H = l * K, h * K
    r, e = rayon * K, ep * K
    im = Image.new("RGBA", (L, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, L - 1, H - 1], r, fill=CONTOUR)
    c = hexa(couleur)
    d.rounded_rectangle([e, e, L - 1 - e, H - 1 - e], r - e, fill=c)
    interieur = Image.new("L", (L, H), 0)
    ImageDraw.Draw(interieur).rounded_rectangle([e, e, L - 1 - e, H - 1 - e], r - e, fill=255)
    # bas un peu plus foncé (relief), reflet clair en haut
    bas = Image.new("L", (L, H), 0)
    ImageDraw.Draw(bas).rectangle([0, int(H * 0.6), L, H + 40 * K], fill=255)
    bas = ImageChops.multiply(bas.filter(ImageFilter.GaussianBlur(14 * K)), interieur)
    sombre = tuple(int(v * 0.84) for v in c[:3]) + (255,)
    im.paste(Image.new("RGBA", (L, H), sombre), (0, 0), bas)
    reflet = Image.new("L", (L, H), 0)
    m = e + int(H * 0.08)
    ImageDraw.Draw(reflet).rounded_rectangle([m + r // 3, m, L - 1 - m - r // 3, int(H * 0.36)], (H * 0.36 - m) / 2, fill=110)
    reflet = ImageChops.multiply(reflet, interieur)
    im.paste(Image.new("RGBA", (L, H), (255, 255, 255, 255)), (0, 0), reflet)
    im.resize((l, h), Image.LANCZOS).save(os.path.join(SORTIE, nom + ".png"))


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    for nom, c in (("Vert", "16A34A"), ("Bleu", "0284C7"), ("Jaune", "EAB308"), ("Gris", "64748B")):
        bouton(nom, 512, 256, c, 56, 12)
    for nom, c in (("OngletBleu", "0284C7"), ("OngletSombre", "334155")):
        bouton(nom, 512, 128, c, 48, 10)
    print("ok")
