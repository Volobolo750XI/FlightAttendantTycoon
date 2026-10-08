"""Genere un panneau d'achat PNG transparent : nom en haut, prix en dessous.

Usage : python3 generer_panneau.py "RANGEE 1" "GRATUIT" sortie.png
Le prix est en vert si "GRATUIT" ou "0 $", sinon en jaune.
"""
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
W, H = 1024, 512


def texte(draw, y, msg, taille, couleur):
    font = ImageFont.truetype(FONT, taille)
    while draw.textlength(msg, font=font) > W - 80:
        taille -= 4
        font = ImageFont.truetype(FONT, taille)
    x = (W - draw.textlength(msg, font=font)) / 2
    draw.text((x, y), msg, font=font, fill=couleur, stroke_width=max(6, taille // 10), stroke_fill=(20, 24, 40, 255))


def panneau(nom, prix, sortie):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    texte(d, 40, nom, 170, (255, 255, 255, 255))
    gratuit = prix.strip().upper() in ("GRATUIT", "0 $", "0$")
    texte(d, 270, prix, 150, (80, 230, 90, 255) if gratuit else (255, 210, 60, 255))
    # ombre douce derriere le texte pour la lisibilite
    ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ombre.putalpha(img.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda a: a * 0.5))
    fond = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fond = Image.alpha_composite(fond, ombre)
    out = Image.alpha_composite(fond, img)
    # alpha bleed : les pixels transparents prennent la couleur sombre du contour (pas de liseré blanc)
    px = out.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a == 0:
                px[x, y] = (20, 24, 40, 0)
    out.save(sortie)


if __name__ == "__main__":
    panneau(sys.argv[1], sys.argv[2], sys.argv[3])
