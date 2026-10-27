"""TABLEAU "REBIRTH LEADERBOARD" du lobby (comme Infinity Tower Tycoon) : un grand panneau sur pied avec le
TOP 10 des joueurs. Comme dans leur map, la liste est une IMAGE qu'on met a jour a la main (Fortnite ne
laisse pas Verse lire le nom des joueurs pour un classement permanent).

Pour mettre a jour : modifie la liste TOP ci-dessous, relance le script, puis dans UEFN reimporte
Textures/Lobby/Classement_Top10.png (le panneau se met a jour tout seul).

Sorties : Modeles/Lobby/Tableau_Classement.glb, Textures/Lobby/Classement_Top10.png
Repere : face vers -Z, Y en haut, sol a y = 0.     Usage : python3 generate_tableau_classement.py
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(HERE))
POLICE = os.path.join(RACINE, "Outils", "TitanOne-Regular.ttf")
PNG = os.path.join(RACINE, "Textures", "Lobby", "Classement_Top10.png")
GLB = os.path.join(os.path.dirname(HERE), "Lobby", "Tableau_Classement.glb")

# ---------------------------------------------------------------- A MODIFIER : le top 10
TOP = [
    ("YOUR NAME HERE", 0), ("---", 0), ("---", 0), ("---", 0), ("---", 0),
    ("---", 0), ("---", 0), ("---", 0), ("---", 0), ("---", 0),
]
BAS_DE_PAGE = "SEND YOUR REBIRTHS ON DISCORD"

CONTOUR = (22, 27, 48)
VERT = (40, 185, 100)
VERT_FONCE = (16, 92, 54)


def f(t):
    return ImageFont.truetype(POLICE, t)


def image():
    W, H = 1024, 1280
    img = Image.new("RGB", (W, H), CONTOUR)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([18, 18, W - 18, H - 18], 40, fill=VERT_FONCE)
    d.rounded_rectangle([18, 18, W - 18, 190], 40, fill=VERT)
    d.rectangle([18, 120, W - 18, 190], fill=VERT)
    d.text((W / 2, 104), "REBIRTH LEADERBOARD", font=f(82), fill="white", anchor="mm", stroke_width=8, stroke_fill=CONTOUR)
    d.text((70, 250), "PLAYER NAME", font=f(50), fill="white", anchor="lm", stroke_width=5, stroke_fill=CONTOUR)
    d.text((W - 70, 250), "REBIRTHS", font=f(50), fill=(134, 239, 172), anchor="rm", stroke_width=5, stroke_fill=CONTOUR)
    medailles = [(255, 255, 255), (200, 210, 225), (230, 150, 90)]
    for i, (nom, score) in enumerate(TOP[:10]):
        y = 330 + i * 82
        if i % 2 == 0:
            d.rounded_rectangle([46, y - 36, W - 46, y + 36], 18, fill=(24, 104, 62))
        c = medailles[i] if i < 3 else (255, 255, 255)
        d.text((96, y), f"{i + 1}.", font=f(46), fill=c, anchor="mm", stroke_width=5, stroke_fill=CONTOUR)
        d.text((140, y), nom[:18], font=f(44), fill=c, anchor="lm", stroke_width=5, stroke_fill=CONTOUR)
        d.text((W - 70, y), str(score), font=f(44), fill=(134, 239, 172), anchor="rm", stroke_width=5, stroke_fill=CONTOUR)
    d.text((W / 2, H - 80), BAS_DE_PAGE, font=f(40), fill="white", anchor="mm", stroke_width=5, stroke_fill=CONTOUR)
    return img


def lin(rgb):
    c = np.asarray(rgb, float) / 255.0
    return list(np.round(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4) * 255).astype(int)) + [255]


def boite(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box((x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


if __name__ == "__main__":
    img = image()
    os.makedirs(os.path.dirname(PNG), exist_ok=True)
    img.save(PNG)
    PBR = trimesh.visual.material.PBRMaterial
    w, h, y0 = 6.4, 8.0, 3.2                         # panneau 6,4 x 8 m, bas a 3,2 m
    cadre = trimesh.util.concatenate([boite(-w / 2 - 0.35, y0 - 0.35, 0.0, w / 2 + 0.35, y0 + h + 0.35, 0.5)])
    cadre.visual = trimesh.visual.TextureVisuals(material=PBR(name="TableauCadre", baseColorFactor=lin(CONTOUR), roughnessFactor=0.6))
    pied = trimesh.util.concatenate([boite(-0.5, 0, 0.1, 0.5, y0, 0.6), boite(-1.6, 0, -0.6, 1.6, 0.5, 1.3)])
    pied.visual = trimesh.visual.TextureVisuals(material=PBR(name="TableauPied", baseColorFactor=lin(VERT), roughnessFactor=0.5))
    v = np.array([[-w / 2, y0, -0.02], [w / 2, y0, -0.02], [w / 2, y0 + h, -0.02], [-w / 2, y0 + h, -0.02]])
    ecran = trimesh.Trimesh(v, [[0, 2, 1], [0, 3, 2]], process=False)
    ecran.visual = trimesh.visual.TextureVisuals(uv=np.array([[1, 0], [0, 0], [0, 1], [1, 1]]),
                                                  material=PBR(name="Classement_Top10", baseColorTexture=img, roughnessFactor=0.6,
                                                               emissiveTexture=img, emissiveFactor=[0.35, 0.35, 0.35]))
    sc = trimesh.Scene()
    sc.add_geometry(cadre, node_name="Tableau_Cadre", geom_name="Tableau_Cadre")
    sc.add_geometry(pied, node_name="Tableau_Pied", geom_name="Tableau_Pied")
    sc.add_geometry(ecran, node_name="Tableau_Ecran", geom_name="Tableau_Ecran")
    sc.export(GLB)
    print(GLB, PNG)
