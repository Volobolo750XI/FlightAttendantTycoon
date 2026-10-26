"""VEHICULES ET OBJETS D'AEROPORT (decor du lobby), style cartoon, couleurs de la compagnie (blanc + vert argent).
Chaque fonction renvoie un dict {cle_materiau: [meshes]} dans un repere local : avant vers -Z, Y en haut, sol a y = 0.
- tracteur a bagages + chariots avec valises, camion escalier, camion citerne, camion catering, pushback,
  voiture FOLLOW ME, plots, conteneurs cargo, mat d'eclairage, camion de pompiers
- service_avion() : tout le ballet autour d'un avion gare (dans le repere de l'avion de generate_avion_decor.py)
"""
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box as rect
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(HERE))
PBR = trimesh.visual.material.PBRMaterial
POLICE = os.path.join(RACINE, "Outils", "TitanOne-Regular.ttf")


def _col(nom, rgb, rugo=0.5, metal=0.0, em=None):
    return PBR(name=nom, baseColorFactor=[*rgb, 255], roughnessFactor=rugo, metallicFactor=metal, emissiveFactor=em)


def tex_damier():
    n = 256
    img = Image.new("RGB", (n, n), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for i in range(8):
        for j in range(8):
            if (i + j) % 2:
                d.rectangle([i * 32, j * 32, i * 32 + 31, j * 32 + 31], fill=(30, 170, 90))
    return img


def tex_texte(txt, fond, encre, w=1024, h=256, taille=170):
    img = Image.new("RGB", (w, h), fond)
    d = ImageDraw.Draw(img)
    d.text((w / 2, h / 2 + 8), txt, font=ImageFont.truetype(POLICE, taille), fill=encre, anchor="mm")
    return img


MATERIAUX = {
    "ve_blanc": _col("VehiculeBlanc", (244, 246, 248), 0.4),
    "ve_vert": _col("VehiculeVert", (30, 170, 90), 0.4),
    "ve_vert_fonce": _col("VehiculeVertFonce", (16, 112, 62), 0.45),
    "ve_gris": _col("VehiculeGris", (120, 126, 136), 0.6),
    "ve_sombre": _col("VehiculeSombre", (40, 44, 54), 0.6),
    "ve_pneu": _col("VehiculePneu", (26, 26, 30), 0.9),
    "ve_vitre": _col("VehiculeVitre", (40, 62, 90), 0.1),
    "ve_chrome": _col("VehiculeChrome", (200, 206, 214), 0.25, 0.7),
    "ve_orange": _col("PlotOrange", (255, 110, 40), 0.6),
    "ve_rouge": _col("PompiersRouge", (225, 45, 45), 0.4),
    "ve_feu_orange": _col("GyrophareOrange", (255, 140, 40), 0.3, 0.0, [1.0, 0.55, 0.15]),
    "ve_feu_bleu": _col("GyrophareBleu", (60, 140, 255), 0.3, 0.0, [0.25, 0.55, 1.0]),
    "ve_lumiere": _col("ProjecteurBlanc", (255, 255, 250), 0.3, 0.0, [1.0, 1.0, 0.95]),
    "ve_valise_1": _col("ValiseBleue", (60, 130, 230), 0.5),
    "ve_valise_2": _col("ValiseRose", (240, 90, 150), 0.5),
    "ve_valise_3": _col("ValiseViolette", (140, 90, 220), 0.5),
    "ve_valise_4": _col("ValiseVerte", (40, 190, 110), 0.5),
    "ve_valise_5": _col("ValiseOrange", (250, 120, 50), 0.5),
    "ve_conteneur": _col("ConteneurAlu", (190, 196, 204), 0.35, 0.6),
    "ve_damier": PBR(name="DamierFollowMe", baseColorTexture=tex_damier(), roughnessFactor=0.5, metallicFactor=0.0),
    "ve_followme": PBR(name="PanneauFollowMe", baseColorTexture=tex_texte("FOLLOW ME", (30, 170, 90), (255, 255, 255)),
                       roughnessFactor=0.5, metallicFactor=0.0, emissiveFactor=[0.25, 0.25, 0.25]),
    "ve_fuel": PBR(name="TexteFuel", baseColorTexture=tex_texte("FUEL", (244, 246, 248), (30, 170, 90)),
                   roughnessFactor=0.4, metallicFactor=0.0),
}


# ------------------------------------------------------------------ briques
def P_add(P, k, m):
    if m.is_watertight and m.volume < 0:                       # faces toujours tournees vers l'exterieur
        m.invert()
    P.setdefault(k, []).append(m)
    return m


def rbox(w, h, l, r, x=0, y=0, z=0):
    """boite a coins arrondis (vue de dessus), posee sur y"""
    r = min(r, w / 2 - 0.01, l / 2 - 0.01)
    p = rect(-w / 2 + r, -l / 2 + r, w / 2 - r, l / 2 - r).buffer(r, 3)
    m = trimesh.creation.extrude_polygon(p, h)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_transform(np.diag([1, 1, -1, 1]))
    m.invert()
    m.apply_translation([x, y, z])
    return m


def boite(w, h, l, x=0, y=0, z=0):
    m = trimesh.creation.box((w, h, l))
    m.apply_translation([x, y + h / 2, z])
    return m


def roue(P, r, ep, x, y, z):
    w = trimesh.creation.cylinder(radius=r, height=ep, sections=20)
    w.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
    w.apply_translation([x, y, z])
    P_add(P, "ve_pneu", w)
    j = trimesh.creation.cylinder(radius=r * 0.5, height=ep + 0.04, sections=14)
    j.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
    j.apply_translation([x, y, z])
    P_add(P, "ve_chrome", j)


def quatre_roues(P, larg, z_av, z_ar, r=0.35, ep=0.28):
    for x in (-larg / 2, larg / 2):
        for z in (z_av, z_ar):
            roue(P, r, ep, x, r, z)


def gyrophare(P, x, y, z, k="ve_feu_orange"):
    P_add(P, "ve_sombre", boite(0.22, 0.06, 0.22, x, y, z))
    g = trimesh.creation.cylinder(radius=0.09, height=0.16, sections=12)
    g.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    g.apply_translation([x, y + 0.14, z])
    P_add(P, k, g)


def cabine(P, w, x, y, z, l=1.6, h=1.5, k="ve_blanc"):
    """petite cabine de camion avec pare-brise vers -Z"""
    P_add(P, k, rbox(w, h, l, 0.18, x, y, z))
    P_add(P, "ve_vitre", rbox(w - 0.2, h * 0.42, 0.06, 0.03, x, y + h * 0.45, z - l / 2 - 0.01))
    for sx in (-1, 1):
        P_add(P, "ve_vitre", boite(0.05, h * 0.38, l * 0.5, x + sx * (w / 2 + 0.005), y + h * 0.48, z - l * 0.1))


def transformer(P, T):
    out = {}
    for k, ms in P.items():
        for m in ms:
            m = m.copy()
            m.apply_transform(T)
            out.setdefault(k, []).append(m)
    return out


def fusion(*dicts):
    out = {}
    for d in dicts:
        for k, ms in d.items():
            out.setdefault(k, []).extend(ms)
    return out


def place(P, x, z, cap=0.0, y=0.0):
    return transformer(P, translation_matrix([x, y, z]) @ rotation_matrix(math.radians(cap), [0, 1, 0]))


# ------------------------------------------------------------------ vehicules
def tracteur():
    P = {}
    P_add(P, "ve_vert", rbox(1.5, 0.75, 2.6, 0.25, 0, 0.3, 0))
    P_add(P, "ve_blanc", rbox(1.5, 0.12, 2.6, 0.25, 0, 1.05, 0))
    P_add(P, "ve_sombre", boite(0.6, 0.5, 0.5, 0, 1.17, 0.5))             # siege
    for sx in (-0.65, 0.65):                                                # arceau
        for sz in (-0.35, 0.95):
            P_add(P, "ve_chrome", boite(0.07, 1.1, 0.07, sx, 1.17, sz))
    P_add(P, "ve_blanc", rbox(1.6, 0.1, 1.6, 0.2, 0, 2.27, 0.3))
    gyrophare(P, 0, 2.37, 0.3)
    P_add(P, "ve_sombre", boite(0.3, 0.12, 0.4, 0, 0.35, 1.45))            # attelage
    quatre_roues(P, 1.45, -0.8, 0.8, 0.36, 0.3)
    return P


def chariot(seed=0):
    r = np.random.default_rng(seed)
    P = {}
    P_add(P, "ve_gris", boite(1.5, 0.12, 2.6, 0, 0.55, 0))
    for sx in (-0.72, 0.72):
        P_add(P, "ve_vert", boite(0.06, 0.35, 2.6, sx, 0.67, 0))
    for sx in (-0.7, 0.7):
        for sz in (-1.25, 1.25):
            P_add(P, "ve_chrome", boite(0.06, 1.5, 0.06, sx, 0.67, sz))
    P_add(P, "ve_vert", boite(1.6, 0.08, 2.75, 0, 2.17, 0))                # toit
    P_add(P, "ve_sombre", boite(0.1, 0.1, 0.8, 0, 0.45, -1.6))             # timon
    for x, z in ((-0.6, -1.0), (0.6, -1.0), (-0.6, 1.0), (0.6, 1.0)):
        roue(P, 0.24, 0.16, x, 0.24, z)
    y = 0.67
    for rang in range(2):                                                   # valises
        z = -1.15
        while z < 1.0:
            l = r.uniform(0.32, 0.5)
            for x0 in (-0.38, 0.32):
                w, h = r.uniform(0.55, 0.7), r.uniform(0.4, 0.55)
                k = f"ve_valise_{r.integers(1, 6)}"
                P_add(P, k, rbox(w, h, l, 0.06, x0, y + rang * 0.6, z + l / 2))
                P_add(P, "ve_sombre", boite(0.22, 0.05, 0.05, x0, y + rang * 0.6 + h, z + l / 2))
            z += l + 0.05
    return P


def train_bagages(n=3):
    P = place(tracteur(), 0, 0)
    for i in range(n):
        P = fusion(P, place(chariot(i), 0, 3.4 + i * 3.6))
    return P


def camion_escalier(hauteur=3.6):
    P = {}
    P_add(P, "ve_sombre", boite(2.1, 0.4, 6.6, 0, 0.55, 0.6))
    cabine(P, 2.1, 0, 0.75, -2.0)
    P_add(P, "ve_vert", boite(2.12, 0.35, 6.2, 0, 0.6, 0.9))
    # escalier : monte de l'arriere (z+) vers l'avant (z-) au-dessus de la cabine
    z0, z1 = 3.6, -2.6
    n = 14
    for i in range(n):
        t = i / (n - 1)
        y = 1.0 + (hauteur - 1.0) * t
        z = z0 + (z1 - z0) * t
        P_add(P, "ve_gris", boite(1.3, 0.08, 0.42, 0, y, z))
    L = math.hypot(z0 - z1, hauteur - 1.0)
    ang = math.atan2(hauteur - 1.0, z0 - z1)
    for sx in (-0.68, 0.68):
        for dy, k in ((0.0, "ve_blanc"), (1.0, "ve_chrome")):
            b = trimesh.creation.box((0.08, 0.14 if dy == 0 else 0.06, L))
            b.apply_transform(rotation_matrix(ang, [1, 0, 0]))
            b.apply_translation([sx, (1.0 + hauteur) / 2 + dy, (z0 + z1) / 2])
            P_add(P, k, b)
    P_add(P, "ve_gris", boite(1.4, 0.1, 1.2, 0, hauteur, z1 - 0.7))          # palier
    for sx in (-0.7, 0.7):
        P_add(P, "ve_chrome", boite(0.06, 1.0, 1.2, sx, hauteur, z1 - 0.7))
    quatre_roues(P, 2.1, -2.2, 2.8, 0.45, 0.35)
    gyrophare(P, 0, 2.25, -2.0)
    return P


def camion_citerne():
    P = {}
    P_add(P, "ve_sombre", boite(2.3, 0.4, 8.0, 0, 0.6, 0.6))
    cabine(P, 2.3, 0, 0.8, -2.5, 1.9, 1.7, "ve_vert")
    t = trimesh.creation.capsule(height=5.0, radius=1.05, count=[24, 16])
    t.apply_scale([1.0, 0.9, 1.0])
    t.apply_translation([0, 2.1, 1.7])
    P_add(P, "ve_blanc", t)
    b = trimesh.creation.cylinder(radius=1.07, height=0.6, sections=32)
    b.apply_scale([1.0, 0.9, 1.0])
    b.apply_translation([0, 2.1, 1.7])
    P_add(P, "ve_vert", b)
    for sx in (-1, 1):                                                       # texte FUEL
        q = trimesh.Trimesh([[0, -0.35, -1.4], [0, -0.35, 1.4], [0, 0.35, 1.4], [0, 0.35, -1.4]], [[0, 1, 2], [0, 2, 3]],
                            process=False)
        uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]]) if sx < 0 else np.array([[1, 0], [0, 0], [0, 1], [1, 1]])
        q.apply_translation([sx * 1.07, 2.05, 3.0])
        if sx > 0:
            q.invert()
        q.visual = trimesh.visual.TextureVisuals(uv=uv, material=MATERIAUX["ve_fuel"])
        P_add(P, "ve_fuel", q)
    quatre_roues(P, 2.3, -2.6, 3.6, 0.5, 0.4)
    roue(P, 0.5, 0.4, -1.15, 0.5, 2.4)
    roue(P, 0.5, 0.4, 1.15, 0.5, 2.4)
    gyrophare(P, 0, 2.55, -2.5)
    return P


def camion_catering(levee=2.8):
    P = {}
    P_add(P, "ve_sombre", boite(2.3, 0.4, 7.4, 0, 0.6, 0.4))
    cabine(P, 2.3, 0, 0.8, -2.6, 1.8, 1.6)
    for i in range(4):                                                       # ciseaux
        y = 1.0 + i * (levee / 4)
        for s in (-1, 1):
            b = trimesh.creation.box((0.1, 0.1, 3.8))
            b.apply_transform(rotation_matrix(s * math.atan2(levee / 4, 3.6), [1, 0, 0]))
            b.apply_translation([0.9 * s, y + levee / 8, 1.3])
            P_add(P, "ve_chrome", b)
    P_add(P, "ve_blanc", rbox(2.4, 2.4, 4.6, 0.2, 0, 1.0 + levee, 1.3))
    P_add(P, "ve_vert", boite(2.42, 0.45, 4.62, 0, 1.0 + levee + 0.9, 1.3))
    P_add(P, "ve_gris", boite(2.0, 0.08, 1.0, 0, 1.0 + levee, -1.4))         # plateforme avant
    quatre_roues(P, 2.3, -2.6, 3.0, 0.45, 0.35)
    gyrophare(P, 0, 2.45, -2.6)
    return P


def pushback():
    P = {}
    P_add(P, "ve_vert", rbox(2.8, 1.0, 5.6, 0.5, 0, 0.35, 0))
    P_add(P, "ve_sombre", boite(2.82, 0.2, 5.62, 0, 0.35, 0))
    P_add(P, "ve_blanc", rbox(1.4, 1.0, 1.4, 0.2, 0.5, 1.35, 1.2))          # cabine basse
    P_add(P, "ve_vitre", boite(1.2, 0.45, 0.05, 0.5, 1.75, 0.48))
    P_add(P, "ve_sombre", boite(0.25, 0.25, 2.6, 0, 0.5, -4.0))              # barre de remorquage
    quatre_roues(P, 2.7, -1.8, 1.8, 0.55, 0.45)
    gyrophare(P, 0.5, 2.37, 1.2)
    return P


def follow_me():
    P = {}
    P_add(P, "ve_damier", rbox(1.8, 0.75, 4.2, 0.4, 0, 0.4, 0))
    P_add(P, "ve_blanc", rbox(1.6, 0.65, 2.2, 0.35, 0, 1.15, 0.3))
    P_add(P, "ve_vitre", boite(1.62, 0.4, 1.6, 0, 1.25, 0.3))
    P_add(P, "ve_sombre", boite(0.1, 0.5, 0.1, 0, 1.8, 0.3))
    for sx in (-1, 1):                                                       # panneau FOLLOW ME sur le toit
        q = trimesh.Trimesh([[-0.75, 0, 0], [0.75, 0, 0], [0.75, 0.38, 0], [-0.75, 0.38, 0]], [[0, 1, 2], [0, 2, 3]],
                            process=False)
        uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]]) if sx < 0 else np.array([[1, 0], [0, 0], [0, 1], [1, 1]])
        if sx > 0:
            q.invert()
        q.apply_translation([0, 2.2, 0.3 + sx * 0.06])
        q.visual = trimesh.visual.TextureVisuals(uv=uv, material=MATERIAUX["ve_followme"])
        P_add(P, "ve_followme", q)
    P_add(P, "ve_vert", boite(1.55, 0.4, 0.1, 0, 2.18, 0.3))
    gyrophare(P, -0.6, 2.6, 0.3)
    gyrophare(P, 0.6, 2.6, 0.3)
    quatre_roues(P, 1.75, -1.35, 1.35, 0.36, 0.26)
    return P


def plot():
    P = {}
    P_add(P, "ve_orange", boite(0.4, 0.04, 0.4))
    c = trimesh.creation.cone(radius=0.17, height=0.7, sections=16)
    c.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    c.apply_translation([0, 0.04, 0])
    P_add(P, "ve_orange", c)
    b = trimesh.creation.cylinder(radius=0.105, height=0.12, sections=16)
    b.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    b.apply_translation([0, 0.42, 0])
    P_add(P, "ve_blanc", b)
    return P


def conteneur():
    P = {}
    prof = [(-0.78, 0), (0.78, 0), (0.78, 1.62), (-0.28, 1.62), (-0.78, 1.1)]
    from shapely.geometry import Polygon
    m = trimesh.creation.extrude_polygon(Polygon(prof), 1.5)
    m.apply_translation([0, 0, -0.75])
    P_add(P, "ve_conteneur", m)
    for y in (0.4, 0.8, 1.2):
        P_add(P, "ve_gris", boite(1.58, 0.04, 1.52, 0, y, 0))
    P_add(P, "ve_vert", boite(0.9, 0.3, 0.02, 0.3, 1.2, -0.76))
    return P


def camion_pompiers():
    P = {}
    P_add(P, "ve_rouge", rbox(2.5, 2.1, 9.0, 0.3, 0, 0.6, 0))
    P_add(P, "ve_vitre", boite(2.2, 0.8, 0.06, 0, 1.6, -4.52))
    for sx in (-1, 1):
        P_add(P, "ve_vitre", boite(0.05, 0.7, 1.4, sx * 1.26, 1.65, -3.6))
        P_add(P, "ve_blanc", boite(0.05, 0.25, 8.6, sx * 1.26, 1.1, 0))
    P_add(P, "ve_chrome", boite(0.5, 0.5, 0.5, 0, 2.7, -2.5))               # lance a eau
    l = trimesh.creation.cylinder(radius=0.09, height=1.6, sections=10)
    l.apply_translation([0, 3.1, -3.3])
    P_add(P, "ve_chrome", l)
    gyrophare(P, -0.8, 2.7, -3.9, "ve_feu_bleu")
    gyrophare(P, 0.8, 2.7, -3.9, "ve_feu_bleu")
    for z in (-3.0, 0.5, 3.0):
        for sx in (-1.15, 1.15):
            roue(P, 0.6, 0.45, sx, 0.6, z)
    return P


def mat_eclairage(h=24.0):
    P = {}
    P_add(P, "ve_gris", boite(1.4, 0.5, 1.4))
    c = trimesh.creation.cylinder(radius=0.32, height=h, sections=16)
    c.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation([0, h / 2, 0])
    P_add(P, "ve_gris", c)
    P_add(P, "ve_sombre", boite(4.2, 1.4, 0.5, 0, h, 0))
    for i in range(4):
        for j in range(2):
            P_add(P, "ve_lumiere", boite(0.8, 0.5, 0.05, -1.5 + i * 1.0, h + 0.2 + j * 0.6, -0.27))
    return P


# ------------------------------------------------------------------ autour d'un avion gare
def service_avion(variante=0):
    """dans le repere de l'avion (nez vers -Z, gauche = -X). Portes : avant z=-10.7, arriere z=+11.7, seuil ~3.6 m"""
    P = {}
    P = fusion(P, place(camion_escalier(3.5), 3.5 + 3.7, 12.6, 90))           # porte arriere droite
    P = fusion(P, place(train_bagages(3), 6.5, -6.0, 200))                    # soute avant
    P = fusion(P, place(camion_citerne(), 10.5, 4.5, 160))                     # sous l'aile droite
    if variante % 2 == 0:
        P = fusion(P, place(camion_catering(2.6), 2.4 + 4.6, -13.4 if False else 9.0, -90 + 180))
    P = fusion(P, place(pushback(), 0, -21.5, 180))                            # devant le nez
    for x, z in ((-16.7, 6.5), (16.7, 6.5), (0, -24.5), (-2.5, 19.0), (2.5, 19.0), (-4.5, -2.0), (4.5, -2.0)):
        P = fusion(P, place(plot(), x, z))
    return P


def parts_demo():
    P = fusion(place(tracteur(), -16, 0), place(chariot(1), -16, 3.6), place(camion_escalier(), -10, 0),
               place(camion_citerne(), -4, 0), place(camion_catering(), 3, 0), place(pushback(), 10, 0),
               place(follow_me(), 15, 0), place(plot(), 18, 0), place(conteneur(), 20.5, 0),
               place(camion_pompiers(), 25, 0), place(mat_eclairage(10), 31, 0))
    return P


if __name__ == "__main__":
    sc = trimesh.Scene()
    for k, ms in parts_demo().items():
        m = trimesh.util.concatenate(ms)
        if k not in ("ve_fuel", "ve_followme"):
            m.visual = trimesh.visual.TextureVisuals(material=MATERIAUX[k])
        sc.add_geometry(m, node_name=k, geom_name=k)
    out = os.path.join(os.path.dirname(HERE), "Lobby", "Vehicules_Aeroport_Demo.glb")
    sc.export(out)
    print(out, round(os.path.getsize(out) / 1e6, 2), "Mo")
