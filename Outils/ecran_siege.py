"""Ecran au dos d'un siege d'avion (petit, style cartoon, un seul mesh, une texture).

Fichier : Modeles/Ecran/EcranSiege.glb
- cadre noir aux bords arrondis, 26 x 17 cm, 2,5 cm d'epaisseur ;
- l'ecran (face avant, vers +Z) affiche la carte du vol : la carte du monde, la ligne du vol
  en pointilles, l'avion cartoon et une barre de progression ;
- une petite LED verte en bas a droite et un logo d'avion en bas a gauche (dans le cadre).
Pivot : centre de la face ARRIERE (celle qu'on colle contre le dossier). Unites : metres.
Usage : python3 ecran_siege.py
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from trimesh.visual.material import PBRMaterial

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.join(ICI, "..")
SORTIE = os.path.join(RACINE, "Modeles", "Ecran")
POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

L, H, P = 0.26, 0.17, 0.025          # cadre
BORD = 0.012                          # epaisseur du cadre autour de l'ecran
TEX = 1024                            # texture carree : haut = ecran, bande du bas = couleurs


def texture():
    tex = Image.new("RGB", (TEX, TEX), (20, 22, 28))
    # --- l'ecran (zone 1024 x 640 en haut, ratio de l'ecran)
    E = Image.new("RGB", (1024, 640))
    carte_png = os.path.join(RACINE, "Textures", "Destinations", "CarteVols.png")
    carte = Image.open(carte_png).convert("RGB")
    # on zoome sur l'Europe / l'Atlantique (le vol Paris -> New York par exemple)
    w, h = carte.size
    carte = carte.crop((int(w * 0.22), int(h * 0.15), int(w * 0.62), int(h * 0.55))).resize((1024, 640), Image.LANCZOS)
    E.paste(carte)
    d = ImageDraw.Draw(E, "RGBA")
    # bandeau du haut
    d.rectangle([0, 0, 1024, 70], fill=(5, 46, 22, 220))
    f = ImageFont.truetype(POLICE, 38)
    d.text((24, 35), "PARIS  >  NEW YORK", font=f, fill="white", anchor="lm")
    d.text((1000, 35), "2:41", font=f, fill=(187, 247, 208), anchor="rm")
    # la route en pointilles (courbe) et l'avion
    # vraies positions de Paris et New York sur la carte zoomee
    a, b = (733, 206), (190, 310)
    c = ((a[0] + b[0]) / 2, 90)
    pts = []
    for i in range(41):
        t = i / 40
        x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0]
        y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]
        pts.append((x, y))
    for i, (x, y) in enumerate(pts):
        if i % 2 == 0:
            col = (34, 197, 94, 255) if i <= 20 else (255, 255, 255, 230)
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=col, outline=(5, 46, 22, 255), width=2)
    for (x, y), col in ((a, (34, 197, 94)), (b, (255, 255, 255))):
        d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=col, outline=(5, 46, 22), width=4)
    avion_png = os.path.join(RACINE, "Textures", "JaugeVol", "Avion.png")
    if os.path.exists(avion_png):
        av = Image.open(avion_png).convert("RGBA").resize((130, 130), Image.LANCZOS).transpose(Image.FLIP_LEFT_RIGHT)
        x, y = pts[20]
        E.paste(av, (int(x - 65), int(y - 75)), av)
    # barre de progression en bas
    d.rounded_rectangle([60, 570, 964, 606], 18, fill=(5, 46, 22, 230), outline=(255, 255, 255, 255), width=4)
    d.rounded_rectangle([66, 576, 66 + int(892 * 0.5), 600], 12, fill=(34, 197, 94, 255))
    # leger reflet de vitre
    reflet = Image.new("L", (1024, 640), 0)
    ImageDraw.Draw(reflet).polygon([(0, 0), (420, 0), (180, 640), (0, 640)], fill=28)
    E.paste(Image.new("RGB", (1024, 640), (255, 255, 255)), (0, 0), reflet.filter(ImageFilter.GaussianBlur(30)))
    tex.paste(E, (0, 0))
    # --- bande du bas : couleurs unies (cadre, LED, logo)
    cases = {"cadre": (26, 28, 34), "led": (34, 220, 94), "logo": (150, 155, 165)}
    for i, col in enumerate(cases.values()):
        tex.paste(col, (i * 64, 960, i * 64 + 64, 1024))
    return tex


def uv_case(i):
    return ((i * 64 + 32) / TEX, 1 - (992 / TEX))


def boite_arrondie(lx, ly, lz, r, sections=8):
    """Boite aux coins arrondis (vue de face) : contour arrondi extrude en Z (dos z=0, face z=lz)."""
    pts = []
    for cx, cy, a0 in ((lx / 2 - r, ly / 2 - r, 0), (-lx / 2 + r, ly / 2 - r, 90), (-lx / 2 + r, -ly / 2 + r, 180), (lx / 2 - r, -ly / 2 + r, 270)):
        for k in range(sections + 1):
            t = np.radians(a0 + 90 * k / sections)
            pts.append((cx + r * np.cos(t), cy + r * np.sin(t)))
    n = len(pts)
    v = [(x, y, 0.0) for x, y in pts] + [(x, y, lz) for x, y in pts] + [(0, 0, 0.0), (0, 0, lz)]
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + j], [i, n + j, n + i]]          # cotes
        f += [[2 * n, j, i]]                              # dos
        f += [[2 * n + 1, n + i, n + j]]                  # face avant
    m = trimesh.Trimesh(vertices=v, faces=f, process=True)
    trimesh.repair.fix_normals(m)
    return m


def ecran():
    tex = texture()
    # cadre (dos au z = 0, face avant au z = P)
    cadre = boite_arrondie(L, H, P, 0.018)
    cadre.visual = trimesh.visual.TextureVisuals(uv=np.tile(uv_case(0), (len(cadre.vertices), 1)))
    # l'ecran : un quad un peu devant la face avant
    lx, ly = L - 2 * BORD, H - 2 * BORD - 0.012
    z = P + 0.0006
    y0 = 0.006  # decale vers le haut (place pour la LED en bas)
    v = np.array([[-lx / 2, y0 - ly / 2, z], [lx / 2, y0 - ly / 2, z], [lx / 2, y0 + ly / 2, z], [-lx / 2, y0 + ly / 2, z]])
    uv = np.array([[0, 1 - 640 / TEX], [1, 1 - 640 / TEX], [1, 1], [0, 1]])
    quad = trimesh.Trimesh(vertices=v, faces=[[0, 1, 2], [0, 2, 3]], process=False)
    quad.visual = trimesh.visual.TextureVisuals(uv=uv)
    # LED verte et petit logo (boutons) en bas
    led = trimesh.creation.icosphere(subdivisions=2, radius=0.003)
    led.apply_translation((L / 2 - 0.02, -H / 2 + 0.008, P))
    led.visual = trimesh.visual.TextureVisuals(uv=np.tile(uv_case(1), (len(led.vertices), 1)))
    logo = trimesh.creation.cylinder(radius=0.004, height=0.002, sections=16)
    logo.apply_translation((-L / 2 + 0.02, -H / 2 + 0.008, P + 0.001))
    logo.visual = trimesh.visual.TextureVisuals(uv=np.tile(uv_case(2), (len(logo.vertices), 1)))
    m = trimesh.util.concatenate([cadre, quad, led, logo])
    mat = PBRMaterial(baseColorTexture=tex, emissiveTexture=tex, emissiveFactor=(0.6, 0.6, 0.6), roughnessFactor=0.35, metallicFactor=0.0)
    m.visual = trimesh.visual.TextureVisuals(uv=m.visual.uv, material=mat)
    return m, tex


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    m, tex = ecran()
    m.export(os.path.join(SORTIE, "EcranSiege.glb"))
    tex.crop((0, 0, 1024, 640)).save(os.path.join(SORTIE, "apercu_ecran.png"))
    b = m.bounds
    print("ok :", b[0].round(3), b[1].round(3), len(m.faces), "faces")
