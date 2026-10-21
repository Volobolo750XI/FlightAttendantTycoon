"""Images de la feuille de mission (une par trajet) : le fond (presse-papier + feuille)
et les photos des passagers (pour la ligne "fraudeur").

Sortie : Textures/FeuilleMission/FondFeuille.png et Textures/FeuilleMission/Photo1.png ... Photo5.png
Les photos sont decoupees dans Modeles/personnages_apercu.png, de gauche a droite :
1 vieux monsieur, 2 femme veste orange, 3 grand-mere, 4 homme barbu, 5 femme blouson noir.

Usage : python3 feuille_mission.py
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SORTIE = os.path.join(RACINE, "Textures", "FeuilleMission")
POLICE = os.path.join(RACINE, "Outils", "ArchivoBlack.ttf")

W, H = 760, 1120          # fond (ratio de la feuille a l'ecran : 380 x 560)
PHOTO = 256


def fond():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # presse-papier (bois sombre) avec une ombre douce
    ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ombre).rounded_rectangle((18, 30, W - 6, H - 4), 34, fill=(0, 0, 0, 120))
    img.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(10)))
    d.rounded_rectangle((8, 20, W - 16, H - 14), 34, fill=(122, 82, 50, 255), outline=(78, 50, 30, 255), width=6)
    # la feuille
    d.rounded_rectangle((40, 70, W - 48, H - 44), 10, fill=(250, 247, 238, 255), outline=(206, 198, 180, 255), width=3)
    # lignes discretes
    for y in range(250, H - 70, 52):
        d.line((70, y, W - 78, y), fill=(220, 226, 236, 255), width=2)
    # bandeau du titre
    d.rectangle((40, 100, W - 48, 200), fill=(36, 74, 140, 255))
    f = ImageFont.truetype(POLICE, 50)
    t = "FLIGHT BRIEFING"
    l, h, r, b = d.textbbox((0, 0), t, font=f)
    d.text(((W - 8 - (r - l)) / 2, 150 - (b + h) / 2), t, font=f, fill=(255, 255, 255, 255))
    # pince metallique en haut
    d.rounded_rectangle((W / 2 - 130, 0, W / 2 + 122, 86), 18, fill=(178, 184, 192, 255), outline=(96, 102, 110, 255), width=5)
    d.rounded_rectangle((W / 2 - 60, 18, W / 2 + 52, 46), 12, fill=(122, 82, 50, 255))
    img.save(os.path.join(SORTIE, "FondFeuille.png"))


def portrait(src, cx, haut, cote):
    """Decoupe un carre (tete + epaules) puis ajoute un cadre de photo d'identite."""
    p = src.crop((int(cx - cote / 2), haut, int(cx + cote / 2), haut + cote)).resize((PHOTO, PHOTO), Image.LANCZOS)
    p = p.convert("RGBA")
    d = ImageDraw.Draw(p)
    d.rectangle((0, 0, PHOTO - 1, PHOTO - 1), outline=(30, 30, 30, 255), width=6)
    return p


def photos():
    groupe = Image.open(os.path.join(RACINE, "Modeles", "personnages_apercu.png")).convert("RGB")
    # 5 personnages, un tous les 300 px ; tete en haut de l'image
    for i, cx in enumerate([150, 450, 750, 1050, 1350]):
        portrait(groupe, cx, 4, 200).save(os.path.join(SORTIE, f"Photo{i + 1}.png"))


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    fond()
    photos()
    print("ok :", SORTIE)
