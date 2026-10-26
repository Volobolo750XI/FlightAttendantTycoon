"""PLATEFORME DU SPAWN (centre du lobby) : ronde, symetrique, pour 4 joueurs.

- un grand disque pave (40 m) un peu sureleve, 2 marches tout autour, liseret dore
- 4 ENTREES (nord / est / sud / ouest, vers les gates A B C D) entre 4 jardinieres en arc
  (haies + fleurs) : ce sont les "creux" du bord de la plateforme
- 4 SPAWNS (pastilles vertes) entre les entrees : on y pose les 4 Player Spawn Pad
- au milieu : une fontaine ronde avec un AVION DORE qui decolle sur une colonne
- 4 panneaux cartoon sur les jardinieres : MUSIC ON/OFF (avec 2 dalles ON / OFF devant),
  HOW TO PLAY, FAVORITE / RECOMMEND, EVERYTHING SAVES
Chaque element est un objet separe. Origine : le centre de la plateforme, au sol.
Sortie : Modeles/Lobby/Plateforme_Spawn.glb (+ apercu)      Usage : python3 generate_plateforme_spawn.py
"""
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, Polygon
from trimesh.transformations import rotation_matrix

from generate_interieurs import Interieur, M, mat, tex_uni, exporter, plante
from generate_siege_business_v2 import bruit

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby")
POLICE = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Outils", "TitanOne-Regular.ttf")
CONTOUR = (22, 27, 48)
R = 20.0                    # rayon du dessus de la plateforme
H = 0.45                    # hauteur du dessus
ENTREE = 34.0               # demi-ouverture des entrees (degres)


# ------------------------------------------------------------------ textures
def tex_sol(n=2048):
    """Le dessus vu d'en haut : paves en anneaux, rosace verte et doree, lettres des gates."""
    im = Image.new("RGB", (n, n), (226, 220, 206))
    d = ImageDraw.Draw(im)
    c = n / 2
    k = n / (2 * R)                                        # pixels par metre
    rng = np.random.default_rng(4)
    # anneaux de paves
    r = 1.0
    while r < R:
        nb = max(8, int(2 * math.pi * r / 1.1))
        for i in range(nb):
            a0, a1 = 2 * math.pi * i / nb, 2 * math.pi * (i + 1) / nb
            t = rng.uniform(-10, 10)
            coul = tuple(int(v + t) for v in (226, 220, 206))
            pts = [(c + (r + e) * k * math.cos(a), c + (r + e) * k * math.sin(a))
                   for e, a in ((0, a0), (0, a1), (1.0, a1), (1.0, a0))]
            d.polygon(pts, fill=coul, outline=(196, 188, 172))
        r += 1.0
    # rosace : etoile a 8 branches verte et or, et un anneau vert
    for rr, w, coul in ((14.2, 0.9, (30, 140, 80)), (13.3, 0.25, (214, 178, 110)), (6.2, 0.35, (214, 178, 110))):
        d.ellipse([c - rr * k, c - rr * k, c + rr * k, c + rr * k], outline=coul, width=int(w * k))
    for i in range(8):
        a = math.pi / 4 * i
        L = 12.5 if i % 2 == 0 else 8.5
        pts = [(c + 6.4 * k * math.cos(a - 0.22), c + 6.4 * k * math.sin(a - 0.22)),
               (c + L * k * math.cos(a), c + L * k * math.sin(a)),
               (c + 6.4 * k * math.cos(a + 0.22), c + 6.4 * k * math.sin(a + 0.22))]
        d.polygon(pts, fill=(30, 150, 85) if i % 2 == 0 else (214, 178, 110), outline=CONTOUR)
    # lettre de la gate devant chaque entree (lisible en arrivant du centre)
    f = ImageFont.truetype(POLICE, int(2.4 * k))
    for lettre, a in (("A", -math.pi / 2), ("B", 0.0), ("C", math.pi / 2), ("D", math.pi)):
        # texte le long du bord (tangent), lisible en marchant du centre vers la gate
        t = Image.new("RGBA", (int(12 * k), int(4 * k)), (0, 0, 0, 0))
        ImageDraw.Draw(t).text((t.width / 2, t.height / 2), "GATE " + lettre, font=f, fill="white", anchor="mm",
                               stroke_width=int(0.25 * k), stroke_fill=CONTOUR)
        t = t.rotate(-math.degrees(a) - 90, expand=True, resample=Image.BICUBIC)
        x, y = c + 16.8 * k * math.cos(a), c + 16.8 * k * math.sin(a)
        im.paste(t, (int(x - t.width / 2), int(y - t.height / 2)), t)
    a = np.asarray(im).astype(float) * (0.95 + 0.06 * np.asarray(
        Image.fromarray((bruit(512, 6, 3) * 255).astype(np.uint8)).resize((n, n)), float)[..., None] / 255)
    return np.clip(a, 0, 255).astype(np.uint8)


def panneau(titre, lignes, couleur=(46, 190, 104), sous=None):
    """Panneau cartoon 1024 x 640 : gros contour, bandeau titre, texte blanc a contour."""
    W, Hh = 1024, 640
    im = Image.new("RGB", (W, Hh), CONTOUR)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 14, W - 15, Hh - 15], 40, fill=couleur)
    d.rounded_rectangle([14, 14, W - 15, 150], 40, fill=tuple(int(v * 0.75) for v in couleur))
    d.rounded_rectangle([40, 24, W - 41, 70], 20, fill=tuple(min(255, int(v * 1.25) + 30) for v in couleur))
    def ecrire(xy, t, taille, coul="white"):
        d.text(xy, t, font=ImageFont.truetype(POLICE, taille), fill=coul, anchor="mm",
               stroke_width=max(4, taille // 9), stroke_fill=CONTOUR)
    ecrire((W / 2, 84), titre, 88)
    y = 220
    for t, taille, coul in lignes:
        ecrire((W / 2, y), t, taille, coul)
        y += taille + 28
    return np.asarray(im)


M.update({
    "sol_spawn": mat("SolPlateforme", tex_sol(), 0.8),
    "pierre": mat("PierreClaire", tex_uni((208, 202, 188), var=0.08), 0.85),
    "haie": mat("Haie", tex_uni((52, 140, 62), var=0.25), 0.9),
    "terre": mat("Terreau", tex_uni((92, 66, 44), var=0.2), 1.0),
    "pastille_spawn": mat("PastilleSpawn", tex_uni((60, 220, 130)), 0.3, 0.0, [0.1, 0.5, 0.25]),
    "fleur_rose": mat("FleurRose", tex_uni((240, 110, 160)), 0.6),
    "fleur_blanche": mat("FleurBlanche", tex_uni((250, 250, 250)), 0.6),
    "p_musique": mat("PanneauMusique", panneau("MUSIC", [("ON  /  OFF", 120, "white"),
                                                        ("STEP ON A PAD", 50, (220, 255, 232))], (70, 120, 230)), 0.4),
    "p_jouer": mat("PanneauHowToPlay", panneau("HOW TO PLAY", [("1. CLAIM A GATE", 54, "white"),
                                                             ("2. FLY & SERVE PASSENGERS", 54, "white"),
                                                             ("3. BUY BIGGER PLANES", 54, "white"),
                                                             ("4. REBIRTH TO EARN MORE", 54, "white")]), 0.4),
    "p_favori": mat("PanneauFavorite", panneau("LIKE THE MAP?", [("FAVORITE", 110, (255, 120, 160)),
                                                               ("& RECOMMEND", 90, (120, 200, 255))], (60, 60, 90)), 0.4),
    "p_sauve": mat("PanneauSave", panneau("EVERYTHING", [("SAVES!", 150, "white"),
                                                        ("COME BACK ANYTIME", 50, (220, 255, 232))], (226, 56, 110)), 0.4),
    "dalle_on": mat("DalleOn", panneau("ON", [], (46, 190, 104))[:220], 0.4, 0.0, [0.05, 0.25, 0.1]),
    "dalle_off": mat("DalleOff", panneau("OFF", [], (220, 50, 60))[:220], 0.4, 0.0, [0.25, 0.05, 0.05]),
})


# ------------------------------------------------------------------ formes
def extrusion(I, k, poly, y0, y1, uv_haut=None):
    """Extrusion verticale d'un polygone (x, z) ; uv_haut(x, z) -> UV pour une texture vue de dessus."""
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_transform(np.diag([1, 1, -1, 1]))
    m.invert()
    m.apply_translation([0, y0, 0])
    if uv_haut is None:
        I.add(k, m, 1.0)
        return
    v = m.vertices[m.faces].reshape(-1, 3)
    mm = trimesh.Trimesh(v, np.arange(len(v)).reshape(-1, 3), process=False)
    mm.metadata["uv"] = uv_haut(v[:, 0], v[:, 2])
    mm.metadata["normales"] = np.repeat(m.face_normals, 3, 0)
    I.meubles[I.courant].setdefault(k, []).append(mm)


def anneau_arc(r0, r1, a0, a1, n=48):
    a = np.linspace(a0, a1, n)
    ext = [(r1 * math.cos(t), r1 * math.sin(t)) for t in a]
    inn = [(r0 * math.cos(t), r0 * math.sin(t)) for t in a[::-1]]
    return Polygon(ext + inn)


def avion_dore(I, y0, echelle=1.0):
    """Petit avion cartoon tout en or, nez vers le haut (il decolle), sur une colonne en spirale."""
    s = echelle
    def T(m, ry=0.0):
        m.apply_transform(rotation_matrix(math.radians(35), [1, 0, 0]))       # cabre
        m.apply_transform(rotation_matrix(math.radians(ry), [0, 1, 0]))
        m.apply_translation([0, y0 + 2.6 * s, 0])
        return m
    fus = trimesh.creation.capsule(height=3.2 * s, radius=0.45 * s, count=[24, 16])   # le long de Z
    I.add("or", T(fus))
    def fleche(envergure, corde, recul, ep, z0, y):
        """Aile en fleche (vue de dessus) extrudee, nez vers -Z."""
        p = Polygon([(-0.0, z0 - corde / 2), (envergure / 2, z0 + recul - corde * 0.2), (envergure / 2, z0 + recul + corde * 0.25),
                     (0.0, z0 + corde / 2), (-envergure / 2, z0 + recul + corde * 0.25), (-envergure / 2, z0 + recul - corde * 0.2)])
        m = trimesh.creation.extrude_polygon(p, ep)
        m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
        m.apply_transform(np.diag([1, 1, -1, 1]))
        m.invert()
        m.apply_translation([0, y, 0])
        return m
    I.add("or", T(fleche(5.4 * s, 1.5 * s, 0.9 * s, 0.14 * s, 0.0, -0.18 * s)))
    I.add("or", T(fleche(2.1 * s, 0.7 * s, 0.4 * s, 0.1 * s, 1.75 * s, 0.05 * s)))
    derive = trimesh.creation.box((0.12 * s, 1.0 * s, 0.8 * s))
    derive.apply_translation([0, 0.55 * s, 1.75 * s])
    I.add("or", T(derive))
    for x in (-1.3, 1.3):                                                      # reacteurs
        r = trimesh.creation.cylinder(radius=0.22 * s, height=0.8 * s, sections=24)
        r.apply_translation([x * s, -0.35 * s, -0.1 * s])
        I.add("or", T(r))
    for z in (-1.3, -0.8, -0.3, 0.2, 0.7):                                       # hublots
        for x in (-1, 1):
            h = trimesh.creation.icosphere(1, 0.09 * s)
            h.apply_translation([x * 0.44 * s, 0.12 * s, z * s])
            I.add("noir", T(h))
    # colonne + spirale de nuage (trainee)
    I.cyl("or", 0.16 * s, 2.4 * s, 0, y0 + 1.2 * s, 0)
    for i in range(26):
        t = i / 25
        a = t * 4 * math.pi
        b = trimesh.creation.icosphere(1, (0.18 + 0.12 * (1 - t)) * s)
        b.apply_translation([0.45 * s * math.cos(a), y0 + 0.1 + 2.2 * s * t, 0.45 * s * math.sin(a)])
        I.add("fleur_blanche", b)


def panneau_sur_pieds(I, k, x, z, angle, l=4.2, h=2.6, y=1.25):
    """Panneau texture sur 2 poteaux, face vers le centre (angle = direction du centre vers le panneau)."""
    ux, uz = math.cos(angle), math.sin(angle)               # vers l'exterieur
    tx, tz = -uz, ux                                         # le long du panneau
    for s in (-1, 1):
        p = (x + tx * s * (l / 2 - 0.25), z + tz * s * (l / 2 - 0.25))
        I.cyl("noir", 0.09, y + 0.2, p[0] + ux * 0.08, (y + 0.2) / 2, p[1] + uz * 0.08)
    cadre = trimesh.creation.box((l + 0.2, h + 0.2, 0.12))
    cadre.apply_transform(rotation_matrix(-angle - math.pi / 2, [0, 1, 0]))
    cadre.apply_translation([x + ux * 0.1, y + h / 2, z + uz * 0.1])
    I.add("noir", cadre)
    c = np.array([x, y, z]) - np.array([ux, 0, uz]) * 0.0
    t = np.array([tx, 0, tz])
    hh = np.array([0, h, 0])
    # le panneau se lit depuis le centre : gauche = -t vu du centre
    I.quad(k, [c - t * l / 2, c + t * l / 2, c + t * l / 2 + hh, c - t * l / 2 + hh])


# ------------------------------------------------------------------ la plateforme
def construire():
    I = Interieur("PlateformeSpawn")
    # --- le dessus pave + 2 marches + liseret dore
    I.meuble("Plateforme")
    uv = lambda x, z: np.column_stack([(x + R) / (2 * R), 1 - (z + R) / (2 * R)])
    extrusion(I, "sol_spawn", Point(0, 0).buffer(R, 128), 0.0, H, uv)
    extrusion(I, "or", Point(0, 0).buffer(R + 0.12, 128).difference(Point(0, 0).buffer(R - 0.02, 128)), H - 0.06, H + 0.02)
    extrusion(I, "pierre", Point(0, 0).buffer(R + 0.9, 128).difference(Point(0, 0).buffer(R + 0.1, 128)), 0.0, H * 0.66)
    extrusion(I, "pierre", Point(0, 0).buffer(R + 1.8, 128).difference(Point(0, 0).buffer(R + 0.9, 128)), 0.0, H * 0.33)
    # --- 4 jardinieres en arc entre les entrees (les "creux" sont les entrees)
    for q in range(4):
        a0 = math.radians(q * 90 + ENTREE)
        a1 = math.radians(q * 90 + 90 - ENTREE)
        I.meuble(f"Jardiniere_{q + 1}")
        bac = anneau_arc(16.0, 19.6, a0, a1)
        extrusion(I, "pierre", bac, H, H + 0.6)
        extrusion(I, "or", bac.exterior.buffer(0.08), H + 0.6, H + 0.64)
        extrusion(I, "terre", bac.buffer(-0.25), H + 0.6, H + 0.62)
        extrusion(I, "haie", anneau_arc(17.6, 19.3, a0 + 0.04, a1 - 0.04), H + 0.6, H + 1.6)
        rng = np.random.default_rng(q)
        for i in range(26):                                               # fleurs devant la haie
            t = rng.uniform(a0 + 0.05, a1 - 0.05)
            rr = rng.uniform(16.4, 17.4)
            f = trimesh.creation.icosphere(1, 0.16)
            f.apply_translation([rr * math.cos(t), H + 0.75, rr * math.sin(t)])
            I.add("fleur_rose" if i % 2 else "fleur_blanche", f)
    # --- 4 spawns (entre les entrees, a 9 m du centre)
    for i, deg in enumerate((45, 135, 225, 315)):
        a = math.radians(deg)
        x, z = 9 * math.cos(a), 9 * math.sin(a)
        I.meuble(f"Spawn_{i + 1}")
        extrusion(I, "pastille_spawn", Point(x, z).buffer(1.1, 48), H, H + 0.05)
        extrusion(I, "fleur_blanche", Point(x, z).buffer(1.3, 48).difference(Point(x, z).buffer(1.1, 48)), H, H + 0.07)
    # --- la fontaine et l'avion dore au milieu
    I.meuble("Fontaine")
    extrusion(I, "marbre", Point(0, 0).buffer(4.2, 96).difference(Point(0, 0).buffer(3.6, 96)), H, H + 0.75)
    extrusion(I, "or", Point(0, 0).buffer(4.26, 96).difference(Point(0, 0).buffer(3.54, 96)), H + 0.75, H + 0.81)
    extrusion(I, "mosaique", Point(0, 0).buffer(3.6, 96), H, H + 0.05)
    extrusion(I, "eau", Point(0, 0).buffer(3.6, 96), H + 0.55, H + 0.58)
    extrusion(I, "marbre", Point(0, 0).buffer(1.0, 64), H, H + 1.2)
    extrusion(I, "or", Point(0, 0).buffer(1.08, 64).difference(Point(0, 0).buffer(0.9, 64)), H + 1.2, H + 1.28)
    I.meuble("AvionDore")
    avion_dore(I, H + 1.25, 1.0)
    # --- les 4 panneaux sur les jardinieres (face au centre) + dalles ON / OFF devant MUSIC
    for k, deg, nom in (("p_musique", 45, "Panneau_Musique"), ("p_jouer", 135, "Panneau_HowToPlay"),
                        ("p_favori", 225, "Panneau_Favorite"), ("p_sauve", 315, "Panneau_EverythingSaves")):
        a = math.radians(deg)
        I.meuble(nom)
        panneau_sur_pieds(I, k, 18.4 * math.cos(a), 18.4 * math.sin(a), a, y=H + 1.0)
    a = math.radians(45)
    for nom, k, d in (("Dalle_MusicOn", "dalle_on", -1.4), ("Dalle_MusicOff", "dalle_off", 1.4)):
        I.meuble(nom)
        tx, tz = -math.sin(a), math.cos(a)
        cx, cz = 14.6 * math.cos(a) + tx * d, 14.6 * math.sin(a) + tz * d
        extrusion(I, "noir", Point(cx, cz).buffer(1.05, 48), H, H + 0.06)
        y = H + 0.065
        u = np.array([math.cos(a), 0, math.sin(a)])
        t = np.array([tx, 0, tz])
        c = np.array([cx, y, cz])
        I.quad(k, [c - t * 0.75 + u * 0.47, c + t * 0.75 + u * 0.47, c + t * 0.75 - u * 0.47, c - t * 0.75 - u * 0.47])
    return I


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    I = construire()
    out = os.path.join(SORTIE, "Plateforme_Spawn.glb")
    noms = exporter(I.scene(), out)
    print(out, len(noms), "objets", round(os.path.getsize(out) / 1e6, 1), "Mo :", ", ".join(noms))
