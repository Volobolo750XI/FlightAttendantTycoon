"""Images de la feuille de mission et du billet d'embarquement (une feuille par trajet).

Sortie (Textures/FeuilleMission) :
  FondFeuille.png   la feuille en gros plan (presse-papier), 1640 x 2000 -> 820 x 1000 a l'ecran
  Billet.png        le billet d'embarquement VIDE (le Verse ecrit les valeurs), 1800 x 720
                    -> 900 x 360 a l'ecran. Positions des valeurs : BILLET plus bas.
  Passeport.png     la page du passeport VIDE (le Verse ecrit les valeurs et met la photo),
                    1260 x 1000 -> 630 x 500 a l'ecran. Positions des valeurs : PASSEPORT plus bas.
                    (les memes positions que dans feuille_mission.verse)
  Case.png, CaseCochee.png, CaseRatee.png   les cases de la feuille
  TamponOk.png, TamponRefus.png             les tampons poses sur le billet
  Photo1.png ... Photo5.png  les photos des passagers (decoupees dans Modeles/personnages_apercu.png,
                    de gauche a droite : 1 vieux monsieur, 2 femme veste orange, 3 grand-mere,
                    4 homme barbu, 5 femme blouson noir)
Les grandes images sont ensuite centrees dans un carre / rectangle en puissance de 2 (vide
transparent autour) pour UEFN : FondFeuille 2048 x 2048, Billet 2048 x 1024, Passeport 2048 x 1024,
tampons 1024 x 512. Le Verse les affiche plus grandes d'autant (le dessin tombe au meme endroit).
Et Modeles/Feuille/FeuilleMur.glb : le presse-papier a accrocher au mur (texture = FondFeuille).

Usage : python3 feuille_mission.py
"""
import os
import random

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from trimesh.visual.material import PBRMaterial

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SORTIE = os.path.join(RACINE, "Textures", "FeuilleMission")
MODELES = os.path.join(RACINE, "Modeles", "Feuille")
TITRE = os.path.join(RACINE, "Outils", "ArchivoBlack.ttf")
CARTOON = os.path.join(RACINE, "Outils", "TitanOne-Regular.ttf")   # police des interfaces cartoon
CONTOUR = (22, 27, 48, 255)                                          # contour sombre du style cartoon
VERT_H, VERT_B = (46, 190, 104, 255), (18, 128, 70, 255)
ETIQ = os.path.join(RACINE, "Outils", "BarlowSemiCondensed-Bold.ttf")

BLEU = (36, 74, 140, 255)
GRIS = (120, 128, 140, 255)
PHOTO = 256


def police(f, t):
    return ImageFont.truetype(f, t)


def centre(d, xy, texte, f, couleur):
    l, h, r, b = d.textbbox((0, 0), texte, font=f)
    d.text((xy[0] - (r - l) / 2 - l, xy[1] - (b - h) / 2 - h), texte, font=f, fill=couleur)


def avion(d, cx, cy, s, couleur):
    """Petit avion vu de dessus, nez vers la droite."""
    pts = [(1.0, 0), (0.75, 0.07), (0.15, 0.07), (-0.25, 0.62), (-0.42, 0.62), (-0.15, 0.07),
           (-0.62, 0.07), (-0.78, 0.3), (-0.9, 0.3), (-0.82, 0), (-0.9, -0.3), (-0.78, -0.3),
           (-0.62, -0.07), (-0.15, -0.07), (-0.42, -0.62), (-0.25, -0.62), (0.15, -0.07), (0.75, -0.07)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in pts], fill=couleur)


def code_barre(d, x0, y0, x1, y1, graine):
    r = random.Random(graine)
    x = x0
    while x < x1 - 6:
        w = r.choice([3, 3, 5, 7, 9])
        d.rectangle((x, y0, x + w, y1), fill=(25, 28, 34, 255))
        x += w + r.choice([3, 4, 6, 8])


def ombre(img, boite, rayon, decalage=12):
    o = Image.new("RGBA", img.size, (0, 0, 0, 0))
    b = (boite[0] + decalage, boite[1] + decalage, boite[2] + decalage, boite[3] + decalage)
    ImageDraw.Draw(o).rounded_rectangle(b, rayon, fill=(0, 0, 0, 110))
    img.alpha_composite(o.filter(ImageFilter.GaussianBlur(14)))


# ---------- la feuille (gros plan) ----------
def feuille():
    W, H = 1640, 2000
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ombre(img, (20, 40, W - 30, H - 30), 60)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 40, W - 30, H - 30), 60, fill=(122, 82, 50, 255), outline=(78, 50, 30, 255), width=10)
    d.rounded_rectangle((80, 140, W - 90, H - 90), 16, fill=(250, 247, 238, 255), outline=(206, 198, 180, 255), width=4)
    for y in range(470, H - 140, 110):
        d.line((140, y + 90, W - 150, y + 90), fill=(220, 226, 236, 255), width=3)
    d.line((250, 420, 250, H - 120), fill=(240, 180, 180, 255), width=3)
    d.rectangle((80, 200, W - 90, 380), fill=BLEU)
    avion(d, 210, 290, 70, (255, 255, 255, 255))
    centre(d, (W / 2 + 40, 290), "FLIGHT BRIEFING", police(TITRE, 100), (255, 255, 255, 255))
    # pince
    d.rounded_rectangle((W / 2 - 260, 0, W / 2 + 250, 170), 34, fill=(178, 184, 192, 255), outline=(96, 102, 110, 255), width=10)
    d.rounded_rectangle((W / 2 - 120, 36, W / 2 + 110, 92), 22, fill=(122, 82, 50, 255))
    img.save(os.path.join(SORTIE, "FondFeuille.png"))
    return img


# ---------- le billet ----------
# Positions (pixels de Billet.png) du coin haut-gauche de chaque VALEUR ecrite par le Verse.
BILLET = {
    "NOM": (60, 205), "DE": (60, 345), "VERS": (720, 345),
    "VOL": (60, 535), "PORTE": (320, 535), "SIEGE": (560, 535), "EMBARQ": (800, 535),
    "DATE": (1050, 205), "SEQ": (1050, 345),
    "TALON_VOL": (1390, 205), "TALON_SIEGE": (1390, 345), "TALON_VERS": (1390, 455),
}


def billet():
    W, H = 1800, 720
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # style cartoon : gros contour sombre, epaisseur en bas, bandeau vert brillant
    d.rounded_rectangle((0, 0, W - 1, H - 1), 48, fill=CONTOUR)
    d.rounded_rectangle((14, 14, W - 15, H - 15), 36, fill=(206, 214, 226, 255))
    d.rounded_rectangle((14, 14, W - 15, H - 27), 36, fill=(255, 255, 255, 255))
    bandeau(img, (14, 14, W - 15, 146), 36)
    avion(d, 96, 80, 46, (255, 255, 255, 255))
    cartoon(d, (162, 80), "TYCOON AIR", 66, "lm")
    cartoon(d, (860, 80), "BOARDING PASS", 50, "lm", (220, 255, 232, 255))
    cartoon(d, (1390, 80), "ECONOMY", 50, "lm", (220, 255, 232, 255))
    # perforation entre le billet et le talon
    for y in range(160, H - 20, 34):
        d.ellipse((1323, y, 1337, y + 14), fill=(210, 214, 222, 255))
    e = police(CARTOON, 32)
    for cle, nom in [("NOM", "PASSENGER NAME"), ("DE", "FROM"), ("VERS", "TO"), ("VOL", "FLIGHT"),
                     ("PORTE", "GATE"), ("SIEGE", "SEAT"), ("EMBARQ", "BOARDING"), ("DATE", "DATE"),
                     ("TALON_VOL", "FLIGHT"), ("TALON_SIEGE", "SEAT"), ("TALON_VERS", "TO")]:
        x, y = BILLET[cle][:2]
        d.text((x, y - 46), nom, font=e, fill=(120, 132, 150, 255))
    # petit logo de classe
    d.rounded_rectangle((1050, 470, 1150, 570), 16, outline=BLEU, width=6)
    centre(d, (1100, 520), "Y", police(TITRE, 60), BLEU)
    # codes-barres et symboles
    code_barre(d, 60, 620, 980, 690, 7)
    code_barre(d, 1390, 560, 1750, 690, 11)
    d.text((1010, 628), "SECURITY", font=police(CARTOON, 28), fill=(120, 132, 150, 255))
    d.rounded_rectangle((1010, 664, 1160, 696), 8, outline=(120, 132, 150, 255), width=3)
    d.text((1085, 680), "CHECKED", font=police(CARTOON, 22), fill=(120, 132, 150, 255), anchor="mm")
    img.save(os.path.join(SORTIE, "Billet.png"))


# ---------- le passeport ----------
# Positions (pixels de Passeport.png) du coin haut-gauche de chaque VALEUR ecrite par le Verse.
PASSEPORT = {
    "PHOTO": (60, 190, 360),
    "NOM": (470, 228), "NUMERO": (900, 228), "PRENOM": (470, 348),
    "NATION": (470, 468), "SEXE": (900, 468), "NAISSANCE": (470, 588), "EXPIRE": (900, 588),
    "MRZ1": (60, 800), "MRZ2": (60, 880),
}


def passeport():
    W, H = 1260, 1000
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 44, fill=CONTOUR)
    d.rounded_rectangle((14, 14, W - 15, H - 15), 32, fill=(200, 206, 186, 255))
    d.rounded_rectangle((14, 14, W - 15, H - 27), 32, fill=(236, 240, 226, 255))
    # fond guilloche discret (dessine a part puis decoupe a l'interieur du cadre)
    motif = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(motif)
    for i in range(0, 60):
        r = 40 + i * 18
        dm.ellipse((W * 0.62 - r, H * 0.45 - r * 0.6, W * 0.62 + r, H * 0.45 + r * 0.6), outline=(214, 224, 204, 255), width=2)
    masque = Image.new("L", (W, H), 0)
    ImageDraw.Draw(masque).rounded_rectangle((20, 130, W - 21, H - 33), 26, fill=255)
    img.paste(motif, (0, 0), Image.composite(motif.getchannel("A"), Image.new("L", (W, H), 0), masque))
    # bandeau
    bandeau(img, (14, 14, W - 15, 124), 32, ((176, 58, 76, 255), (120, 32, 48, 255)))
    d.ellipse((40, 30, 112, 102), outline=(255, 255, 255, 255), width=6)
    avion(d, 76, 66, 24, (255, 255, 255, 255))
    cartoon(d, (132, 68), "PASSPORT", 58, "lm")
    cartoon(d, (560, 68), "PASSEPORT  /  PASAPORTE", 36, "lm", (255, 220, 226, 255))
    e = police(CARTOON, 30)
    for cle, nom in [("NOM", "SURNAME"), ("NUMERO", "PASSPORT No."), ("PRENOM", "GIVEN NAMES"),
                     ("NATION", "NATIONALITY"), ("SEXE", "SEX"), ("NAISSANCE", "DATE OF BIRTH"),
                     ("EXPIRE", "DATE OF EXPIRY")]:
        x, y = PASSEPORT[cle]
        d.text((x, y - 42), nom, font=e, fill=(110, 116, 100, 255))
    # zone de lecture automatique (MRZ)
    d.rounded_rectangle((30, 760, W - 30, 955), 14, fill=(248, 250, 244, 255), outline=(200, 206, 186, 255), width=3)
    img.save(os.path.join(SORTIE, "Passeport.png"))


def bandeau(img, boite, r, couleurs=(VERT_H, VERT_B)):
    """Bandeau du haut d'un document : degrade vertical + reflet, coins du haut arrondis."""
    x0, y0, x1, y1 = boite
    g = np.linspace(0, 1, y1 - y0)[:, None, None]
    c = np.array(couleurs[0][:3]) * (1 - g) + np.array(couleurs[1][:3]) * g
    bande = Image.fromarray(np.repeat(c, x1 - x0, 1).astype(np.uint8)).convert("RGBA")
    m = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 + r), r, fill=255)
    img.paste(bande, (x0, y0), m)
    reflet = Image.new("L", img.size, 0)
    ImageDraw.Draw(reflet).rounded_rectangle((x0 + r, y0 + 10, x1 - r, y0 + (y1 - y0) * 0.36), 16, fill=60)
    img.paste(Image.new("RGBA", img.size, (255, 255, 255, 255)), (0, 0), reflet)
    ImageDraw.Draw(img).line((x0, y1, x1, y1), fill=CONTOUR, width=6)


def cartoon(d, xy, texte, taille, ancre="lm", couleur=(255, 255, 255, 255)):
    """Texte blanc tres epais avec un gros contour sombre (comme les interfaces du jeu)."""
    d.text(xy, texte, font=police(CARTOON, taille), fill=couleur, anchor=ancre,
           stroke_width=max(4, taille // 9), stroke_fill=CONTOUR)


# ---------- cases et tampons ----------
def cases():
    for nom, signe in [("Case", None), ("CaseCochee", "ok"), ("CaseRatee", "x")]:
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((14, 14, 114, 114), 14, outline=(40, 48, 60, 255), width=8)
        if signe == "ok":
            d.line((30, 66, 56, 96, 116, 18), fill=(22, 163, 74, 255), width=16, joint="curve")
        elif signe == "x":
            d.line((32, 32, 96, 96), fill=(220, 38, 38, 255), width=14)
            d.line((96, 32, 32, 96), fill=(220, 38, 38, 255), width=14)
        img.save(os.path.join(SORTIE, nom + ".png"))


def tampon(nom, texte, couleur):
    W, H = 640, 260
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((10, 10, W - 10, H - 10), 30, outline=couleur, width=16)
    d.rounded_rectangle((34, 34, W - 34, H - 34), 18, outline=couleur, width=5)
    centre(d, (W / 2, H / 2), texte, police(TITRE, 92), couleur)
    img = img.rotate(-12, expand=True, resample=Image.BICUBIC)
    # aspect tampon : quelques trous dans l'encre
    a = np.array(img)
    r = np.random.default_rng(3)
    a[..., 3] = (a[..., 3] * (r.random(a.shape[:2]) > 0.12)).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(SORTIE, nom + ".png"))


# ---------- photos ----------
def photos():
    groupe = Image.open(os.path.join(RACINE, "Modeles", "personnages_apercu.png")).convert("RGB")
    for i, cx in enumerate([150, 450, 750, 1050, 1350]):
        p = groupe.crop((cx - 100, 4, cx + 100, 204)).resize((PHOTO, PHOTO), Image.LANCZOS).convert("RGBA")
        ImageDraw.Draw(p).rectangle((0, 0, PHOTO - 1, PHOTO - 1), outline=(30, 30, 30, 255), width=6)
        p.save(os.path.join(SORTIE, f"Photo{i + 1}.png"))


# ---------- le presse-papier du mur (3D) ----------
def modele_mur(tex):
    """Plaque fine 41 x 50 cm, la feuille texturee sur la face avant.
    Pivot au centre de la face arriere (contre le mur), face avant vers +X, haut = +Y (glTF)."""
    L, Hh, E = 0.41, 0.50, 0.012
    petite = tex.resize((820, 1000), Image.LANCZOS)
    v = np.array([[E, -Hh / 2, L / 2], [E, -Hh / 2, -L / 2], [E, Hh / 2, -L / 2], [E, Hh / 2, L / 2]])
    f = np.array([[0, 1, 2], [0, 2, 3]])
    uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    avant = trimesh.Trimesh(v, f, process=False)
    avant.visual = trimesh.visual.TextureVisuals(uv=uv, material=PBRMaterial(baseColorTexture=petite, roughnessFactor=0.9, metallicFactor=0.0))
    bois = trimesh.creation.box(extents=(E * 0.95, Hh * 0.97, L * 0.97))
    bois.apply_translation((E * 0.95 / 2, 0, 0))
    bois.visual = trimesh.visual.TextureVisuals(uv=np.full((len(bois.vertices), 2), 0.5),
                                                material=PBRMaterial(baseColorFactor=(122, 82, 50, 255), roughnessFactor=0.8))
    os.makedirs(MODELES, exist_ok=True)
    trimesh.Scene([avant, bois]).export(os.path.join(MODELES, "FeuilleMur.glb"))


def puissance2(nom):
    """Centre l'image dans la puissance de 2 superieure (vide transparent autour)."""
    chemin = os.path.join(SORTIE, nom + ".png")
    img = Image.open(chemin).convert("RGBA")
    p2 = lambda n: 1 << (n - 1).bit_length()
    W, H = p2(img.width), p2(img.height)
    fond = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fond.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
    fond.save(chemin)


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    t = feuille()
    billet()
    passeport()
    cases()
    tampon("TamponOk", "VALID", (22, 150, 70, 235))
    tampon("TamponRefus", "REFUSED", (210, 34, 34, 235))
    photos()
    modele_mur(t)
    for n in ["FondFeuille", "Billet", "Passeport", "TamponOk", "TamponRefus"]:
        puissance2(n)
    print("ok :", SORTIE)
