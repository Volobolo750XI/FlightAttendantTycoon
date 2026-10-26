"""PLATEFORME DU SPAWN (centre du lobby), version SIMPLE, style cartoon.

- un disque plat de 32 m, dessus clair, large bord vert, gros contour sombre (comme les interfaces)
- 4 SPAWNS (pastilles vertes) : on y pose les 4 Player Spawn Pad
- au milieu : un socle rond avec un AVION cartoon (blanc et vert) et des LIASSES DE BILLETS autour
  (modele "Money Cartoon" de stealth86, Sketchfab, licence CC-BY 4.0 : a citer dans la description)
- au bord : une RADIO cartoon (boombox verte) et le panneau MUSIC ON/OFF (Textures/Lobby/Panneau_Music.png)
Chaque element est un objet separe. Origine : le centre de la plateforme, au sol.
Sortie : Modeles/Lobby/Plateforme_Spawn.glb      Usage : python3 generate_plateforme_spawn.py
"""
import math
import os

import numpy as np
import trimesh
from PIL import Image
from shapely.geometry import Point, Polygon
from trimesh.transformations import rotation_matrix, scale_matrix, translation_matrix

from generate_interieurs import Interieur, M, mat, tex_uni, exporter

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
SORTIE = os.path.join(MOD, "Lobby")
RACINE = os.path.dirname(MOD)
R = 16.0                 # rayon du dessus
H = 0.40                 # hauteur


def panneau_musique():
    m = mat("PanneauMusic", np.asarray(Image.open(os.path.join(RACINE, "Textures", "Lobby", "Panneau_Music.png")).convert("RGBA")), 0.5)
    m.alphaMode = "MASK"
    m.alphaCutoff = 0.5
    return m


M.update({
    "dessus": mat("DessusClair", tex_uni((236, 240, 232), var=0.03), 0.7),
    "bord_vert": mat("BordVert", tex_uni((46, 190, 104)), 0.5),
    "contour": mat("ContourSombre", tex_uni((22, 27, 48)), 0.6),
    "spawn": mat("PastilleSpawn", tex_uni((60, 220, 130)), 0.3, 0.0, [0.1, 0.5, 0.25]),
    "blanc_avion": mat("AvionBlanc", tex_uni((248, 250, 252)), 0.3),
    "vert_avion": mat("AvionVert", tex_uni((30, 170, 90)), 0.35),
    "hublot": mat("Hublot", tex_uni((40, 60, 90)), 0.1),
    "radio": mat("RadioVerte", tex_uni((90, 220, 60)), 0.35),
    "haut_parleur": mat("HautParleur", tex_uni((30, 34, 44)), 0.6),
    "bouton_orange": mat("BoutonRadioOrange", tex_uni((250, 120, 60)), 0.4),
    "bouton_bleu": mat("BoutonRadioBleu", tex_uni((60, 180, 240)), 0.4),
    "music": panneau_musique(),
})


def extrusion(I, k, poly, y0, y1):
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_transform(np.diag([1, 1, -1, 1]))
    m.invert()
    m.apply_translation([0, y0, 0])
    I.add(k, m)


def disque(r, n=128):
    return Point(0, 0).buffer(r, n)


def anneau(r0, r1, x=0.0, z=0.0, n=128):
    return Point(x, z).buffer(r1, n).difference(Point(x, z).buffer(r0, n))


# ------------------------------------------------------------------ l'avion cartoon
def avion(I, y0, s=1.0, cap=30.0):
    """Avion cartoon tout rond, nez vers -Z puis tourne de cap degres, leger cabre."""
    def T(m):
        m.apply_transform(rotation_matrix(math.radians(8), [1, 0, 0]))
        m.apply_transform(rotation_matrix(math.radians(cap), [0, 1, 0]))
        m.apply_translation([0, y0, 0])
        return m
    fus = trimesh.creation.capsule(height=4.4 * s, radius=0.85 * s, count=[32, 24])     # le long de Z
    I.add("blanc_avion", T(fus))
    bande = trimesh.creation.cylinder(radius=0.87 * s, height=0.35 * s, sections=48)     # bande verte
    bande.apply_translation([0, 0, 0.4 * s])
    I.add("vert_avion", T(bande))
    def plaque(points, ep, y, k):
        p = Polygon(points)
        m = trimesh.creation.extrude_polygon(p, ep)
        m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
        m.apply_transform(np.diag([1, 1, -1, 1]))
        m.invert()
        m.apply_translation([0, y, 0])
        I.add(k, T(m))
    # ailes (en fleche), stabilisateur, derive
    plaque([(0, -0.9 * s), (3.6 * s, 0.4 * s), (3.6 * s, 0.95 * s), (0, 0.7 * s), (-3.6 * s, 0.95 * s), (-3.6 * s, 0.4 * s)],
           0.22 * s, -0.35 * s, "blanc_avion")
    plaque([(0, 2.0 * s), (1.6 * s, 2.7 * s), (1.6 * s, 3.05 * s), (0, 2.85 * s), (-1.6 * s, 3.05 * s), (-1.6 * s, 2.7 * s)],
           0.16 * s, 0.25 * s, "vert_avion")
    der = trimesh.creation.extrude_polygon(Polygon([(1.9 * s, 0), (3.05 * s, 0), (3.2 * s, 1.6 * s), (2.7 * s, 1.6 * s)]), 0.18 * s)
    der.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))          # plan (z, y)
    der.apply_translation([-0.09 * s, 0.4 * s, 0])
    I.add("vert_avion", T(der))
    for x in (-1.9, 1.9):                                                # reacteurs
        r = trimesh.creation.capsule(height=0.9 * s, radius=0.33 * s, count=[16, 12])
        r.apply_translation([x * s, -0.6 * s, 0.0])
        I.add("vert_avion", T(r))
        e = trimesh.creation.cylinder(radius=0.24 * s, height=0.05 * s, sections=24)
        e.apply_translation([x * s, -0.6 * s, -0.78 * s])
        I.add("hublot", T(e))
    for z in np.arange(-1.6, 1.4, 0.45):                                  # hublots ronds
        for x in (-1, 1):
            h = trimesh.creation.icosphere(2, 0.16 * s)
            h.apply_scale([0.4, 1.0, 1.0])
            h.apply_translation([x * 0.84 * s, 0.18 * s, z * s])
            I.add("hublot", T(h))
    pare = trimesh.creation.icosphere(2, 0.5 * s)                          # pare-brise
    pare.apply_scale([1.1, 0.45, 0.7])
    pare.apply_translation([0, 0.42 * s, -2.35 * s])
    I.add("hublot", T(pare))


# ------------------------------------------------------------------ la radio
def radio(I, x, z, angle):
    """Boombox cartoon verte, face vers le centre (angle = direction du centre vers la radio)."""
    def T(m):
        m.apply_transform(rotation_matrix(-angle - np.pi / 2, [0, 1, 0]))
        m.apply_translation([x, H, z])
        return m
    from generate_siege_business_v2 import rbox
    I.add("radio", T(rbox(2.4, 1.3, 0.8, 0.18, 0.0, 3).apply_translation([0, 0.65, 0])))
    for dx in (-0.65, 0.65):                                               # haut-parleurs (face -Z = vers le centre)
        for r, k, dz in ((0.42, "contour", -0.40), (0.30, "haut_parleur", -0.43), (0.10, "contour", -0.46)):
            c = trimesh.creation.cylinder(radius=r, height=0.04, sections=40)
            c.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
            c.apply_translation([dx, 0.62, dz])
            I.add(k, T(c))
    for i, k in enumerate(("bouton_orange", "bouton_bleu", "bouton_bleu", "bouton_bleu", "bouton_orange")):
        b = rbox(0.18, 0.08, 0.14, 0.03, 0.0, 2).apply_translation([-0.5 + i * 0.25, 1.33, -0.1])
        I.add(k, T(b))
    poignee = trimesh.creation.box((1.8, 0.12, 0.14)).apply_translation([0, 1.62, 0.1])
    I.add("contour", T(poignee))
    for dx in (-0.85, 0.85):
        I.add("contour", T(trimesh.creation.box((0.12, 0.34, 0.14)).apply_translation([dx, 1.46, 0.1])))
    I.add("haut_parleur", T(trimesh.creation.cylinder(radius=0.025, height=1.0, sections=8)
                            .apply_transform(rotation_matrix(math.radians(-25), [0, 0, 1])).apply_translation([0.9, 1.75, 0.25])))


# ------------------------------------------------------------------ la plateforme
def construire():
    I = Interieur("PlateformeSpawn")
    I.meuble("Plateforme")
    extrusion(I, "contour", disque(R + 0.35), 0.0, H - 0.02)              # flanc sombre (gros contour)
    extrusion(I, "bord_vert", anneau(R - 1.6, R + 0.2), H - 0.06, H)
    extrusion(I, "dessus", disque(R - 1.6), H - 0.06, H - 0.01)
    extrusion(I, "contour", anneau(R - 1.75, R - 1.6), H - 0.05, H + 0.005)
    # 4 spawns
    for i, deg in enumerate((45, 135, 225, 315)):
        a = math.radians(deg)
        x, z = 9.5 * math.cos(a), 9.5 * math.sin(a)
        I.meuble(f"Spawn_{i + 1}")
        extrusion(I, "contour", Point(x, z).buffer(1.35, 48), H - 0.01, H + 0.03)
        extrusion(I, "spawn", Point(x, z).buffer(1.2, 48), H - 0.01, H + 0.05)
    # socle + avion
    I.meuble("Socle")
    extrusion(I, "contour", disque(3.5, 96), H, H + 0.9)
    extrusion(I, "bord_vert", disque(3.3, 96), H + 0.9, H + 1.0)
    extrusion(I, "contour", disque(0.32, 32), H + 1.0, H + 2.4)
    I.meuble("Avion")
    avion(I, H + 3.1, 1.0, cap=30)
    # liasses de billets : en piles autour du socle (et sur le socle)
    I.meuble("Liasses")
    billets = os.path.join(SORTIE, "Liasse_Billets.glb")
    rng = np.random.default_rng(7)
    k = 3.0                                                                 # une liasse : 0,74 x 0,35 x 0,95 m
    for i in range(12):
        a = 2 * math.pi * i / 12 + rng.uniform(-0.08, 0.08)
        r = rng.uniform(4.3, 5.2)
        for j in range(int(rng.integers(1, 4))):
            T = translation_matrix([r * math.cos(a), H + j * 0.34, r * math.sin(a)]) @ \
                rotation_matrix(a + rng.uniform(-0.4, 0.4), [0, 1, 0]) @ scale_matrix(k) @ translation_matrix([0, 0.005, 0])
            I.externe(billets, T)
    for i in range(6):                                                      # sur le socle, autour de la colonne
        a = 2 * math.pi * i / 6
        T = translation_matrix([2.2 * math.cos(a), H + 1.0, 2.2 * math.sin(a)]) @ rotation_matrix(a, [0, 1, 0]) @ \
            scale_matrix(k) @ translation_matrix([0, 0.005, 0])
        I.externe(billets, T)
    # radio + panneau MUSIC (vers la gate B, a droite)
    a = math.radians(0)
    I.meuble("Radio")
    radio(I, 13.3 * math.cos(a), 13.3 * math.sin(a), a)
    I.meuble("Panneau_Music")
    c = np.array([14.8, H + 2.0, 0.0])
    t = np.array([0, 0, 1.0])
    hh = np.array([0, 3.2, 0])
    I.quad("music", [c - t * 1.6, c + t * 1.6, c + t * 1.6 + hh, c - t * 1.6 + hh])
    for dz in (-1.3, 1.3):
        I.cyl("contour", 0.07, 2.2, 14.85, H + 1.1, dz)
    return I


if __name__ == "__main__":
    I = construire()
    out = os.path.join(SORTIE, "Plateforme_Spawn.glb")
    noms = exporter(I.scene(), out)
    print(out, len(noms), "objets", round(os.path.getsize(out) / 1e6, 1), "Mo :", ", ".join(noms))
