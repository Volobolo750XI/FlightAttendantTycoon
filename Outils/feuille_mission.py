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
# Prevu pour le texte de Fortnite (environ 32 px de large par lettre a l'echelle de l'image).
BILLET = {
    "NOM": (60, 200), "DE": (60, 340), "VERS": (780, 340),
    "VOL": (60, 520), "DATE": (290, 520), "PORTE": (700, 520), "SIEGE": (880, 520), "EMBARQ": (1060, 520),
    "TALON_VOL": (1380, 200), "TALON_SIEGE": (1380, 340), "TALON_PORTE": (1380, 480),
}


def billet():
    W, H = 1800, 720
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 40, fill=(255, 255, 255, 255), outline=(200, 205, 214, 255), width=4)
    # bandeau
    d.rounded_rectangle((0, 0, W - 1, 140), 40, fill=BLEU)
    d.rectangle((0, 90, W - 1, 140), fill=BLEU)
    avion(d, 90, 70, 46, (255, 255, 255, 255))
    d.text((160, 30), "TYCOON AIR", font=police(TITRE, 64), fill=(255, 255, 255, 255))
    d.text((860, 44), "BOARDING PASS", font=police(ETIQ, 56), fill=(200, 215, 240, 255))
    d.text((1390, 44), "ECONOMY", font=police(ETIQ, 56), fill=(200, 215, 240, 255))
    # perforation entre le billet et le talon
    for y in range(160, H - 20, 34):
        d.ellipse((1323, y, 1337, y + 14), fill=(210, 214, 222, 255))
    e = police(ETIQ, 34)
    for cle, nom in [("NOM", "PASSENGER NAME"), ("DE", "FROM"), ("VERS", "TO"), ("VOL", "FLIGHT"),
                     ("PORTE", "GATE"), ("SIEGE", "SEAT"), ("EMBARQ", "BOARDING"), ("DATE", "DATE"),
                     ("TALON_VOL", "FLIGHT"), ("TALON_SIEGE", "SEAT"), ("TALON_PORTE", "GATE")]:
        x, y = BILLET[cle][:2]
        d.text((x, y - 44), nom, font=e, fill=GRIS)
    # avion entre FROM et TO
    avion(d, 680, 370, 50, BLEU)
    d.line((580, 370, 615, 370), fill=BLEU, width=6)
    # codes-barres et symboles
    code_barre(d, 60, 620, 980, 690, 7)
    code_barre(d, 1390, 560, 1750, 690, 11)
    d.text((1010, 630), "SECURITY", font=police(ETIQ, 30), fill=GRIS)
    d.rounded_rectangle((1010, 666, 1150, 696), 8, outline=GRIS, width=3)
    d.text((1028, 664), "CHECKED", font=police(ETIQ, 26), fill=GRIS)
    img.save(os.path.join(SORTIE, "Billet.png"))


# ---------- le passeport ----------
# Positions (pixels de Passeport.png) du coin haut-gauche de chaque VALEUR ecrite par le Verse.
# Prevu pour le texte de Fortnite (environ 33 px de large par lettre a l'echelle de l'image).
PASSEPORT = {
    "PHOTO": (50, 190, 340),
    "NOM": (440, 220), "NUMERO": (850, 220), "PRENOM": (440, 340),
    "NATION": (440, 460), "SEXE": (850, 460), "NAISSANCE": (440, 580), "EXPIRE": (850, 580),
    "MRZ1": (60, 790), "MRZ2": (60, 870),
}


def passeport():
    W, H = 1260, 1000
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 34, fill=(236, 240, 226, 255), outline=(120, 40, 50, 255), width=10)
    # fond guilloche discret (dessine a part puis decoupe a l'interieur du cadre)
    motif = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dm = ImageDraw.Draw(motif)
    for i in range(0, 60):
        r = 40 + i * 18
        dm.ellipse((W * 0.62 - r, H * 0.45 - r * 0.6, W * 0.62 + r, H * 0.45 + r * 0.6), outline=(214, 224, 204, 255), width=2)
    masque = Image.new("L", (W, H), 0)
    ImageDraw.Draw(masque).rounded_rectangle((12, 12, W - 13, H - 13), 26, fill=255)
    img.paste(motif, (0, 0), Image.composite(motif.getchannel("A"), Image.new("L", (W, H), 0), masque))
    # bandeau
    d.rounded_rectangle((0, 0, W - 1, 120), 34, fill=(120, 40, 50, 255))
    d.rectangle((0, 70, W - 1, 120), fill=(120, 40, 50, 255))
    d.ellipse((40, 22, 116, 98), outline=(230, 196, 120, 255), width=6)
    avion(d, 78, 60, 26, (230, 196, 120, 255))
    d.text((140, 26), "PASSPORT", font=police(TITRE, 60), fill=(240, 220, 170, 255))
    d.text((560, 40), "PASSEPORT  /  PASAPORTE", font=police(ETIQ, 40), fill=(230, 196, 160, 255))
    e = police(ETIQ, 32)
    for cle, nom in [("NOM", "SURNAME"), ("NUMERO", "PASSPORT No."), ("PRENOM", "GIVEN NAMES"),
                     ("NATION", "NATIONALITY"), ("SEXE", "SEX"), ("NAISSANCE", "DATE OF BIRTH"),
                     ("EXPIRE", "DATE OF EXPIRY")]:
        x, y = PASSEPORT[cle]
        d.text((x, y - 42), nom, font=e, fill=(110, 116, 100, 255))
    # cadre photo + signature
    x, y, c = PASSEPORT["PHOTO"]
    d.rectangle((x - 6, y - 6, x + c + 6, y + c + 6), fill=(200, 206, 192, 255), outline=(70, 74, 64, 255), width=4)
    d.text((x, y + c + 26), "SIGNATURE", font=police(ETIQ, 28), fill=(110, 116, 100, 255))
    d.line((x, y + c + 100, x + c, y + c + 100), fill=(110, 116, 100, 255), width=3)
    # zone de lecture automatique (MRZ)
    d.rectangle((30, 760, W - 30, 960), fill=(248, 250, 244, 255))
    img.save(os.path.join(SORTIE, "Passeport.png"))


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
