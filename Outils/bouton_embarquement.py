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


def texture_capuchon(txt="START BOARDING", coul=(235, 25, 28)):
    W, Hh = 1024, int(1024 * H / L)
    img = Image.new("RGB", (W, Hh))
    d = ImageDraw.Draw(img)
    for y in range(Hh):          # dégradé : plus clair au centre (bombé lumineux)
        t = abs(y / Hh - 0.42) * 2
        d.line([(0, y), (W, y)], fill=tuple(max(0, int(c * (1 - 0.3 * t))) for c in coul))
    taille = 112
    f = ImageFont.truetype(POLICE, taille)
    while d.textlength(txt, font=f) > W * 0.86:
        taille -= 4
        f = ImageFont.truetype(POLICE, taille)
    w = d.textlength(txt, font=f)
    halo = Image.new("L", img.size)
    ImageDraw.Draw(halo).text(((W - w) / 2, Hh / 2 - 66), txt, font=f, fill=255)
    halo = halo.filter(ImageFilter.GaussianBlur(14))
    img.paste(tuple(min(255, c + 120) for c in coul), mask=halo.point(lambda a: a * 0.7))
    d.text(((W - w) / 2, Hh / 2 - 66), txt, font=f, fill=(255, 250, 245))
    return img


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
    # deux morceaux séparés (même pivot) : le socle fixe et le capuchon qui s'enfonce
    for nom_f, noms in (("Bouton_Socle.glb", ("Socle", "Danger", "Collerette")), ("Bouton_Capuchon.glb", ("Liseret", "Capuchon", "Dome"))):
        part = trimesh.Scene()
        for nom, m in pieces:
            if nom in noms:
                part.add_geometry(m, node_name=nom, geom_name=nom)
        part.export(os.path.join(SORTIE, nom_f))
    tex.save(os.path.join(SORTIE, "texture_start_boarding.png"))
    # les 3 capuchons des 3 états du bouton (même pivot que le socle) :
    # START BOARDING vert -> STOP BOARDING rouge -> TAKE OFF vert
    for nom_f, txt, coul in (("Capuchon_StartBoarding", "START BOARDING", (40, 205, 70)),
                             ("Capuchon_StopBoarding", "STOP BOARDING", (235, 25, 28)),
                             ("Capuchon_TakeOff", "TAKE OFF", (40, 205, 70))):
        t = texture_capuchon(txt, coul)
        m_cap = trimesh.visual.material.PBRMaterial(nom_f, baseColorTexture=t, emissiveTexture=t,
                                                    emissiveFactor=[1.0, 1.0, 1.0], roughnessFactor=0.25, metallicFactor=0.0)
        m_lis = trimesh.visual.material.PBRMaterial("Liseret" + nom_f, baseColorFactor=list(coul) + [255],
                                                    emissiveFactor=[c / 255 for c in coul], roughnessFactor=0.3)
        part = trimesh.Scene()
        for nom, z0, z1, poly, mat, uv in (("Liseret", 0.05, 0.058, stade(L, H, 0.008), m_lis, None),
                                           ("Capuchon", 0.05, 0.10, stade(L, H), m_cap, (L, H)),
                                           ("Dome", 0.10, 0.108, stade(L - 0.02, H - 0.02), m_cap, (L, H))):
            m = couche(poly, z0, z1, mat, uv)
            m.apply_transform(rot)
            part.add_geometry(m, node_name=nom, geom_name=nom)
        part.export(os.path.join(SORTIE, nom_f + ".glb"))
    print(out)


if __name__ == "__main__":
    build()
