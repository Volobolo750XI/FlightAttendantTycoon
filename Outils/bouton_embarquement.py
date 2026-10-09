"""Bouton d'urgence rouge lumineux « START BOARDING » (forme ovale-rectangle).

Socle gris foncé, anneau jaune/noir type danger, gros capuchon rouge émissif avec le texte.
Pivot au centre du dessous, le bouton regarde vers le haut (+Y glTF = haut dans UEFN).
Usage : python3 bouton_embarquement.py
"""
import os
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import box

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Modeles", "Boutons")
L, H = 0.60, 0.26          # taille du capuchon (m)
POLICE = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"


def stade(l, h, marge=0.0):
    r = h / 2 + marge
    return box(-l / 2 + h / 2, -h / 2 + h / 2, l / 2 - h / 2, h / 2 - h / 2).buffer(r, 32)


def couche(poly, z0, z1, mat, uv=None):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0)
    m.apply_translation([0, 0, z0])
    if uv is not None:
        bx, by = uv
        u = (m.vertices[:, 0] + bx / 2) / bx
        v = (m.vertices[:, 1] + by / 2) / by
        m.visual = trimesh.visual.TextureVisuals(uv=np.c_[u, v], material=mat)
    else:
        m.visual = trimesh.visual.TextureVisuals(material=mat)
    return m


def texture_capuchon():
    W, Hh = 1024, int(1024 * H / L)
    img = Image.new("RGB", (W, Hh))
    d = ImageDraw.Draw(img)
    for y in range(Hh):          # dégradé : plus clair au centre (bombé lumineux)
        t = abs(y / Hh - 0.42) * 2
        d.line([(0, y), (W, y)], fill=(int(235 - 70 * t), int(25 - 10 * t), int(28 - 10 * t)))
    f = ImageFont.truetype(POLICE, 112)
    txt = "START BOARDING"
    w = d.textlength(txt, font=f)
    halo = Image.new("L", img.size)
    ImageDraw.Draw(halo).text(((W - w) / 2, Hh / 2 - 66), txt, font=f, fill=255)
    halo = halo.filter(ImageFilter.GaussianBlur(14))
    img.paste((255, 170, 160), mask=halo.point(lambda a: a * 0.7))
    d.text(((W - w) / 2, Hh / 2 - 66), txt, font=f, fill=(255, 250, 245))
    return img.transpose(Image.FLIP_TOP_BOTTOM)


def anneau_danger():
    img = Image.new("RGB", (512, 512), (255, 200, 0))
    d = ImageDraw.Draw(img)
    for k in range(-512, 1024, 64):
        d.polygon([(k, 0), (k + 32, 0), (k + 32 + 512, 512), (k + 512, 512)], fill=(20, 20, 20))
    return img


def build():
    os.makedirs(SORTIE, exist_ok=True)
    socle = trimesh.visual.material.PBRMaterial("Socle", baseColorFactor=[38, 40, 44, 255], metallicFactor=0.6, roughnessFactor=0.45)
    jaune = trimesh.visual.material.PBRMaterial("Danger", baseColorTexture=anneau_danger(), roughnessFactor=0.5, metallicFactor=0.0)
    tex = texture_capuchon()
    rouge = trimesh.visual.material.PBRMaterial("BoutonRouge", baseColorTexture=tex, emissiveTexture=tex,
                                                emissiveFactor=[1.0, 1.0, 1.0], roughnessFactor=0.25, metallicFactor=0.0)
    lis = trimesh.visual.material.PBRMaterial("Liseret", baseColorFactor=[255, 60, 50, 255], emissiveFactor=[1.0, 0.12, 0.08], roughnessFactor=0.3)
    pieces = [
        ("Socle", couche(stade(L, H, 0.075), 0.0, 0.03, socle)),
        ("Danger", couche(stade(L, H, 0.055).difference(stade(L, H, 0.022)), 0.03, 0.038, jaune, (L + 0.15, H + 0.15))),
        ("Collerette", couche(stade(L, H, 0.022), 0.03, 0.05, socle)),
        ("Liseret", couche(stade(L, H, 0.008), 0.05, 0.058, lis)),
        ("Capuchon", couche(stade(L, H), 0.05, 0.10, rouge, (L, H))),
    ]
    # bord arrondi du capuchon : léger chanfrein lumineux au-dessus
    pieces.append(("Dome", couche(stade(L - 0.02, H - 0.02), 0.10, 0.108, rouge, (L, H))))
    sc = trimesh.Scene()
    rot = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])   # Z-up -> Y-up glTF
    for nom, m in pieces:
        m.apply_transform(rot)
        sc.add_geometry(m, node_name=nom, geom_name=nom)
    out = os.path.join(SORTIE, "Bouton_StartBoarding.glb")
    sc.export(out)
    tex.transpose(Image.FLIP_TOP_BOTTOM).save(os.path.join(SORTIE, "texture_start_boarding.png"))
    print(out)


if __name__ == "__main__":
    build()
