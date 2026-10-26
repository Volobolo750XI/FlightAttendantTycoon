"""Plan du LOBBY (vu de dessus) : un aeroport ferme pour 4 joueurs.

- au centre, l'aerogare : place d'arrivee (spawn) autour de la tour de controle, avec tout ce qu'on
  trouve dans les lobbys des tycoons (classement, favori, sauvegarde, musique, roue, cadeau, boutique...)
- 4 GATES (une par joueur), au nord / est / sud / ouest : un tarmac de 110 x 110 m ou se gare l'avion
  du joueur (meme le plus gros, l'avion 4, rentre), sa dalle CLAIM, son PC, sa borne MONEY, ses dalles
  d'amelioration et la passerelle jusqu'a la porte avant de l'avion
- dans les 4 coins : hangar, depot de carburant, parking + bus, piste de decollage (decor)
- tout autour : la cloture de l'aeroport (on ne peut pas sortir)

Sortie : Modeles/Plans/plan_lobby.png      Usage : python3 generate_plan_lobby.py
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw

import generate_plans as GP
from generate_plans import police

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Plans", "plan_lobby.png")

S = 4.0                       # pixels par metre sur le plan
DEMI = 175.0                  # l'aeroport fait 350 x 350 m (cloture comprise)
PLACE = 50.0                  # la place centrale fait 100 x 100 m
GATE = 110.0                  # un tarmac de joueur fait 110 x 110 m
MARGE = 60                    # marge autour du plan (pixels)
LEG = 640                     # largeur de la legende a droite

VERT, OR, NUIT = (22, 120, 80), (214, 178, 110), (22, 27, 48)


def P(x, y):
    """metres (x vers la droite, y vers le bas, 0 au centre) -> pixels."""
    return MARGE + (x + DEMI) * S, MARGE + 120 + (y + DEMI) * S


def rect(d, x0, y0, x1, y1, **kw):
    a, b = P(x0, y0), P(x1, y1)
    d.rounded_rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])], kw.pop("r", 6), **kw)


def rond(d, x, y, r, **kw):
    a, b = P(x - r, y - r), P(x + r, y + r)
    d.ellipse([a[0], a[1], b[0], b[1]], **kw)


def pastille(d, x, y, n, coul=VERT):
    cx, cy = P(x, y)
    d.ellipse([cx - 19, cy - 19, cx + 19, cy + 19], fill=coul, outline="white", width=3)
    d.text((cx, cy + 1), str(n), font=police(19), fill="white", anchor="mm")


def texte(d, x, y, t, taille=18, coul=NUIT, ancre="mm"):
    d.text(P(x, y), t, font=police(taille), fill=coul, anchor=ancre)


def silhouette(fichier):
    """Vue de dessus de l'avion (exterieur), nez vers la gauche (-Z glTF a gauche)."""
    GP.PX = S
    sc = trimesh.load(os.path.join(HERE, fichier), force="scene")
    b = sc.bounds
    return GP.vue_dessus([sc], b[0][2] - 1, b[1][2] + 1, -36.0, 36.0, 40.0), b[0][2] - 1


def poser_avion(fond, img, z0, x_origine, y_origine, sens):
    """Pose la silhouette : l'origine de l'avion en (x, y) metres ; sens = direction du nez."""
    rot = {"bas": 90, "haut": -90, "droite": 180, "gauche": 0}[sens]
    im = img.rotate(rot, expand=True)
    # position de l'origine (z=0, x=0) dans l'image avant rotation
    ox, oy = (0 - z0) * S, img.height / 2
    w, h = img.width, img.height
    if sens == "gauche":
        px, py = ox, oy
    elif sens == "droite":
        px, py = w - ox, h - oy
    elif sens == "bas":          # rotation de 90 deg (sens inverse des aiguilles)
        px, py = oy, w - ox
    else:
        px, py = h - oy, ox
    cx, cy = P(x_origine, y_origine)
    fond.alpha_composite(im, (int(cx - px), int(cy - py)))


def gate(d, fond, avions, nom, joueur, cx, cy, sens):
    """Un tarmac de joueur. (cx, cy) = centre du tarmac ; sens = vers ou regarde le nez (vers la place)."""
    h = GATE / 2
    rect(d, cx - h, cy - h, cx + h, cy + h, fill=(150, 158, 166), outline=NUIT, width=4, r=10)
    # marquages au sol
    vx, vy = {"bas": (0, 1), "haut": (0, -1), "droite": (1, 0), "gauche": (-1, 0)}[sens]
    # le nez a 7 m du bord cote place ; origine de l'avion 27,7 m derriere le nez
    bord = (cx + vx * h, cy + vy * h)
    nez = (bord[0] - vx * 7, bord[1] - vy * 7)
    ox, oy = nez[0] - vx * 27.7, nez[1] - vy * 27.7
    a, b = P(ox - vx * 60, oy - vy * 60), P(nez[0] + vx * 2, nez[1] + vy * 2)
    d.line([a, b], fill=(240, 200, 60), width=5)
    for avion, opa, z0 in avions:
        img = avion.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * opa)))
        poser_avion(fond, img, z0, ox, oy, sens)
    # cote gauche de l'avion (porte avant) : perpendiculaire a gauche du sens
    gx, gy = vy, -vx
    porte = (ox + vx * 10.5 + gx * 4.5, oy + vy * 10.5 + gy * 4.5)
    # le batiment de la gate (au bord de la place, cote porte avant de l'avion)
    bx, by = bord[0] + gx * 24, bord[1] + gy * 24
    rect(d, bx - 8, by - 6, bx + 8, by + 6, fill=(70, 160, 220), outline=NUIT, width=3)
    texte(d, bx, by, nom.replace("GATE ", ""), 22, "white")
    # passerelle : de la gate a la porte avant
    d.line([P(bx - vx * 4, by - vy * 4), P(*porte)], fill=(60, 70, 90), width=int(3.2 * S))
    d.line([P(bx - vx * 4, by - vy * 4), P(*porte)], fill=(205, 210, 220), width=int(2.4 * S))
    # dalle CLAIM : sur la place, devant la gate
    cl = (bx + vx * 13, by + vy * 13)
    rond(d, cl[0], cl[1], 4.5, fill=(60, 200, 120), outline=NUIT, width=3)
    texte(d, cl[0], cl[1], "CLAIM", 11, "white")
    # PC, borne MONEY, dalles d'amelioration : sur le tarmac, du meme cote que la gate, hors des ailes
    pc = (bord[0] - vx * 10 + gx * 38, bord[1] - vy * 10 + gy * 38)
    pastille(d, pc[0], pc[1], "P", (40, 50, 70))
    atm = (bord[0] - vx * 10 + gx * 48, bord[1] - vy * 10 + gy * 48)
    pastille(d, atm[0], atm[1], "$", (30, 150, 70))
    for k in range(4):
        dx, dy = bord[0] - vx * (22 + 7 * k) + gx * 44, bord[1] - vy * (22 + 7 * k) + gy * 44
        rect(d, dx - 2.5, dy - 2.5, dx + 2.5, dy + 2.5, fill=(250, 250, 250), outline=VERT, width=3, r=3)
    # nom du joueur sur le tarmac (cote queue)
    t = (cx - vx * 40 + gx * 34, cy - vy * 40 + gy * 34)
    texte(d, t[0], t[1], joueur, 22, "white")


def plan():
    W = int(2 * DEMI * S) + 2 * MARGE + LEG
    H = int(2 * DEMI * S) + 2 * MARGE + 130
    fond = Image.new("RGBA", (W, H), (236, 244, 240, 255))
    d = ImageDraw.Draw(fond)
    d.text((MARGE, 24), "LOBBY : L'AEROPORT DE FLIGHT ATTENDANT TYCOON (4 JOUEURS)", font=police(40), fill=VERT)
    d.text((MARGE, 80), "Vu de dessus - 1 carreau = 10 m - le nord en haut - aeroport ferme par une cloture (350 x 350 m)",
           font=police(20, False), fill=(60, 80, 70))
    # herbe + cloture
    rect(d, -DEMI, -DEMI, DEMI, DEMI, fill=(120, 190, 110), outline=NUIT, width=6, r=14)
    for x in np.arange(-DEMI + 10, DEMI, 10):
        d.line([P(x, -DEMI), P(x, DEMI)], fill=(110, 178, 100), width=1)
        d.line([P(-DEMI, x), P(DEMI, x)], fill=(110, 178, 100), width=1)
    for t in np.arange(-DEMI + 4, DEMI - 2, 8):                      # arbres le long de la cloture
        for (x, y) in ((t, -DEMI + 4), (t, DEMI - 4), (-DEMI + 4, t), (DEMI - 4, t)):
            rond(d, x, y, 2.6, fill=(40, 130, 60), outline=NUIT, width=1)
    # 4 coins
    coins = [((-DEMI + 8, -DEMI + 8, -GATE / 2 - 12, -GATE / 2 - 12), "HANGAR", (190, 196, 205), 7),
             ((GATE / 2 + 12, -DEMI + 8, DEMI - 8, -GATE / 2 - 12), "DEPOT CARBURANT", (200, 205, 190), 8),
             ((-DEMI + 8, GATE / 2 + 12, -GATE / 2 - 12, DEMI - 8), "PARKING + BUS", (170, 175, 185), 9),
             ((GATE / 2 + 12, GATE / 2 + 12, DEMI - 8, DEMI - 8), "PISTE (DECOR)", (110, 115, 125), 10)]
    for (x0, y0, x1, y1), nom, c, n in coins:
        rect(d, x0, y0, x1, y1, fill=c, outline=NUIT, width=3, r=10)
        texte(d, (x0 + x1) / 2, (y0 + y1) / 2 - 8, nom, 20, NUIT)
        pastille(d, (x0 + x1) / 2, (y0 + y1) / 2 + 12, n)
    d.line([P(GATE / 2 + 20, DEMI - 20), P(DEMI - 20, GATE / 2 + 20)], fill="white", width=int(1.2 * S))
    # place centrale (aerogare)
    rect(d, -PLACE, -PLACE, PLACE, PLACE, fill=(226, 222, 214), outline=NUIT, width=5, r=14)
    for k in range(-4, 5):
        d.line([P(k * 10, -PLACE), P(k * 10, PLACE)], fill=(212, 206, 196), width=1)
        d.line([P(-PLACE, k * 10), P(PLACE, k * 10)], fill=(212, 206, 196), width=1)
    rond(d, 0, 0, 9, fill=(250, 250, 250), outline=NUIT, width=4)        # tour de controle
    rond(d, 0, 0, 5, fill=(70, 160, 220), outline=NUIT, width=3)
    texte(d, 0, 12, "TOUR", 13)
    for a in np.linspace(0, 2 * np.pi, 4, endpoint=False):              # 4 points d'apparition
        x, y = 20 * np.cos(a + np.pi / 4), 20 * np.sin(a + np.pi / 4)
        rond(d, x, y, 3, fill=(255, 255, 255), outline=VERT, width=3)
    texte(d, 0, 27, "SPAWN (4 JOUEURS)", 13, VERT)
    # equipements du lobby (numeros de la legende), le long des bords de la place
    equip = [(1, -38, -38), (2, 38, -38), (3, -38, 38), (4, 38, 38), (5, -40, -12), (6, 40, -12),
             (11, -40, 12), (12, 40, 12), (13, 0, 38), (14, 0, -38)]
    for n, x, y in equip:
        pastille(d, x, y, n, OR if n >= 11 else VERT)
    # 4 gates
    # l'avion 4 en transparent (la place qu'il prendra) et l'avion 1 par-dessus (celui du debut)
    avions = [silhouette("avion_niveau4.glb") + (0.35,), silhouette("avion_niveau1_wc_vides.glb") + (1.0,)]
    avions = [(a, o, z0) for a, z0, o in avions]
    m = PLACE + GATE / 2
    gate(d, fond, avions, "GATE A", "JOUEUR 1", 0, -m, "bas")
    gate(d, fond, avions, "GATE B", "JOUEUR 2", m, 0, "gauche")
    gate(d, fond, avions, "GATE C", "JOUEUR 3", 0, m, "haut")
    gate(d, fond, avions, "GATE D", "JOUEUR 4", -m, 0, "droite")
    # valises secretes (7)
    for x, y in ((-150, -60), (150, 70), (-70, 150), (95, -150), (-150, 150), (160, -20), (-25, -120)):
        cx, cy = P(x, y)
        d.rounded_rectangle([cx - 9, cy - 7, cx + 9, cy + 7], 3, fill=OR, outline=NUIT, width=2)
        d.line([cx - 4, cy - 7, cx - 4, cy - 11, cx + 4, cy - 11, cx + 4, cy - 7], fill=NUIT, width=2)
    # legende
    x0 = int(2 * DEMI * S) + 2 * MARGE + 20
    y = 150
    lignes = [("PLACE CENTRALE (AEROGARE)", None),
              ("1", "CLASSEMENT (LEADERBOARD) : les plus riches"), ("2", "FAVORITE / RECOMMEND"),
              ("3", "EVERYTHING SAVES (sauvegarde)"), ("4", "MUSIQUE ON / OFF"),
              ("5", "ROUE DU JOUR (DAILY SPIN)"), ("6", "CADEAU : JOUE 30 MIN (PLAYTIME)"),
              ("11", "DUTY FREE : la boutique (boosts x2)"), ("12", "NEW LOBBY (si ca lag)"),
              ("13", "HALL OF FAME : statues des rebirths"), ("14", "PARKOUR DE LA TOUR (cadeau en haut)"),
              ("", ""), ("CHAQUE GATE (1 PAR JOUEUR)", None),
              ("CLAIM", "la dalle pour prendre la gate"), ("P", "le PC : vols, supplies, upgrades"),
              ("$", "la borne MONEY (l'argent du vol)"), ("[]", "les dalles d'amelioration"),
              ("=", "la passerelle jusqu'a la porte avant"), ("", "l'avion : petit (1) -> geant (4), meme place"),
              ("", ""), ("COINS (DECOR)", None),
              ("7", "HANGAR"), ("8", "DEPOT CARBURANT"), ("9", "PARKING + BUS"), ("10", "PISTE (DECOR)"),
              ("", ""), ("VALISES", "7 valises secretes cachees (bonus)")]
    for k, v in lignes:
        if v is None:
            d.text((x0, y), k, font=police(22), fill=VERT)
            y += 36
            continue
        if k:
            coul = OR if k in ("11", "12", "13", "14") else (NUIT if k in ("P",) else VERT)
            d.ellipse([x0, y - 2, x0 + 34, y + 32], fill=coul, outline="white", width=2)
            d.text((x0 + 17, y + 15), k, font=police(14 if len(k) < 3 else 7), fill="white", anchor="mm")
        d.text((x0 + 46, y + 15), v, font=police(17, False), fill=(30, 40, 35), anchor="lm")
        y += 36
    fond.convert("RGB").save(SORTIE)
    print("plan :", SORTIE, fond.size)


if __name__ == "__main__":
    plan()
