"""Avion niveau 4 : gros-porteur a DEUX ETAGES (type A380), le plus realiste possible.

- Pont principal (en bas) : identique a l'avion 3 : 3 | 3 | 3, 2 allees, coffres lateraux et
  centraux, zones First / Business / eco avec leurs cloisons.
- Pont superieur (en haut) : plus etroit car le fuselage s'arrondit : 2 | 3 | 2 (sieges de 60 cm),
  2 allees, coffres lateraux et centraux, sa propre rangee de hublots.
- Un ESCALIER droit au centre, a l'arriere de la cabine (comme l'escalier arriere de l'A380) :
  21 marches, une tremie dans le plafond du bas / le plancher du haut, garde-corps autour en haut.
- Fuselage ovale, plus haut que large (comme l'A380) ; l'avion est rallonge de la longueur de la
  zone de l'escalier (troncon ajoute derriere les ailes). Rien n'est deforme : portes, cloisons,
  sieges gardent leur taille ; ailes, moteurs, queue = l'A320 a la meme echelle.

Usage : python3 generate_avion_niveau4.py [sortie.glb]
"""
import os
import sys

import numpy as np
import trimesh
from shapely.geometry import box
from shapely.ops import unary_union

import generate_avion_niveau3 as N3
import generate_cabin as G
from generate_cabin import Profile

B, E, N = N3.B, N3.E, N3.N

# ---------------------------------------------------------------- dimensions
UP = 3.70                     # hauteur du plancher du pont superieur (le bas est a 0)
SU = 1.05                     # pont superieur : section gros-porteur x1,05 (6,1 m de large)
STAIR_LEN = 6.0               # zone de l'escalier, inseree entre la porte arriere et la cabine
N_MARCHES = 21
GIRON = 0.25                  # profondeur d'une marche
LARG_ESC = 1.20               # largeur de l'escalier
TREMIE_X = 0.65               # demi-largeur de la tremie (ouverture dans le plancher du haut)
HZ, HY = 4.25, 5.40           # demi-largeur / demi-hauteur du fuselage ovale
CY = 2.60                     # hauteur du centre du fuselage

# ---------------------------------------------------------------- zones
z_cab0 = G.CABIN[0]
ESC = (z_cab0 - STAIR_LEN, z_cab0)
G.REAR_DOOR = (G.REAR_DOOR[0] - STAIR_LEN, G.REAR_DOOR[1] - STAIR_LEN)
G.LAV = (G.LAV[0] - STAIR_LEN, G.LAV[1] - STAIR_LEN)
TREMIE = (ESC[0] + 0.10, ESC[0] + 0.30 + N_MARCHES * GIRON + 0.20)   # z de l'ouverture


def section_haute():
    def P(pts):
        return Profile([(x * SU, y * SU) for x, y in pts])
    W = P([(2.73, 0.00), (2.83, 0.35), (2.90, 0.80), (2.91, 1.20), (2.87, 1.50), (2.77, 1.68)])
    BB = P([(2.77, 1.68), (2.48, 1.695), (2.19, 1.72)])
    BF = P([(2.19, 1.72), (2.105, 1.80), (2.08, 1.94), (2.12, 2.07), (2.22, 2.16)])
    C = P([(2.22, 2.16), (2.12, 2.27), (1.85, 2.39), (1.40, 2.46), (0.90, 2.49), (0.0, 2.51)])
    WF = P([(2.73, 0.00), (2.83, 0.35), (2.90, 0.80), (2.91, 1.20), (2.88, 1.52), (2.78, 1.84), (2.57, 2.06), (2.22, 2.16)])
    CB = P([(0.94, 2.49), (0.985, 2.33), (0.975, 2.08), (0.93, 1.90), (0.83, 1.80), (0.40, 1.785), (0.0, 1.785)])
    return {"WALL": W, "BIN_BOTTOM": BB, "BIN_FACE": BF, "CEILING": C, "WALL_FULL": WF,
            "BIN_PROFILES": [W, BB, BF, C], "OPEN_PROFILES": [WF, C], "FLOOR_X": W.x[0],
            "OUTLINE_BINS": G.outline([W, BB, BF, C]), "OUTLINE_OPEN": G.outline([WF, C]),
            # 2 | 3 | 2 : 3 sieges de 60 cm au centre (|x| < 0,9), allees de 0,9 a 1,65 m, 2 sieges
            # contre chaque paroi
            "AISLE_LINES": (-1.65, -0.9, 0.9, 1.65), "CEIL_LIGHT_X": (2.1, 1.27, 0.3),
            "CENTER_BIN": CB, "CENTER_BIN_SECTION": G.outline([CB])}


BAS = dict(N3.LARGE, CENTER_BIN=N3.CB, CENTER_BIN_SECTION=G.outline([N3.CB]))
HAUT = section_haute()
REGLES = list(HAUT) + ["WIN_DEPTH", "N_WINDOWS", "CABIN"]


def regler(d):
    for k, v in d.items():
        setattr(G, k, v)


def etat():
    return {k: getattr(G, k) for k in REGLES}


# ---------------------------------------------------------------- fuselage ovale
X_COUPE = 1.0                 # troncon droit ajoute derriere les ailes (repere A320)
K = HZ / E.A_R
E.K, E.R_EXT, E.CY_EXT = K, HZ, CY
E.OFF = G.FRONT_DOOR[1] + E.MID_X[0] * K


def zi_of(x):
    return E.OFF - x * K - (STAIR_LEN if x > X_COUPE else 0.0)


def x_of(zi):
    z_c = E.OFF - X_COUPE * K
    if zi >= z_c:
        return (E.OFF - zi) / K
    if zi <= z_c - STAIR_LEN:
        return (E.OFF - zi - STAIR_LEN) / K
    return X_COUPE


E.zi_of, E.x_of = zi_of, x_of
E.STRAIGHT = (G.REAR_DOOR[0] + 0.5, zi_of(E.MID_X[0]))
E.NOSE_TIP = zi_of(E.NOSE[0][0])
E.TAIL_TIP = zi_of(E.TAIL[-1][0])
RAT = HY / HZ
_section = E.section


def section(table, x):
    """Nez et queue de l'A320, rehausses pour rejoindre le fuselage ovale (comme l'A380)."""
    cy, hy, hz = _section(table, x)
    return CY + (cy - CY) * RAT, hy * RAT, hz


E.section = section


def ext_section(zi):
    x = x_of(zi)
    if x < E.MID_X[0]:
        return section(E.NOSE, x)
    if zi >= E.STRAIGHT[0]:
        return CY, HY, HZ
    w = min((E.STRAIGHT[0] - zi) / E.BLEND, 1.0)
    cy, hy, hz = section(E.TAIL, x) if x > E.MID_X[1] else (CY, HY, HZ)
    return CY + w * (cy - CY), HY + w * (hy - HY), HZ + w * (hz - HZ)


E.ext_section = ext_section


def profondeur(s, prof, dy=0.0):
    """Distance du mur a la peau ovale (embrasures des hublots / portes)."""
    def dedans(d):
        p, _ = prof.map(np.array([s]), np.array([0.0]), d)
        return (p[0, 0] / HZ) ** 2 + ((p[0, 1] + dy - CY) / HY) ** 2 - 1
    a, b = 0.0, 2.0
    for _ in range(60):
        m = (a + b) / 2
        if dedans(m) > 0:
            b = m
        else:
            a = m
    return a + 0.004


regler(BAS)
PROF_BAS = profondeur(G.WIN_CENTER_S * N3.S, BAS["WALL"])
PROF_HAUT = profondeur(G.WIN_CENTER_S * SU, HAUT["WALL"], UP)
G.WIN_DEPTH = PROF_BAS
G.PAX_REVEAL = profondeur(BAS["WALL"].s_at_x(float(BAS["WALL"].x.max())), BAS["WALL_FULL"])
HAUT_CABIN = (ESC[0], G.CABIN[1])
HAUT_N_WIN = int((HAUT_CABIN[1] - HAUT_CABIN[0] - 2 * G.MARGIN) / G.PITCH) + 1


def hublots_haut():
    """Positions (z, s sur la peau) des hublots du pont superieur, pour percer le fuselage."""
    skin = E.ellipse_profile(CY, HY, HZ)
    out = []
    for i in range(HAUT_N_WIN):
        zw = HAUT_CABIN[0] + G.MARGIN + i * G.PITCH
        p, _ = HAUT["WALL"].map(np.array([G.WIN_CENTER_S]), np.array([zw]), PROF_HAUT)
        out.append(G.rrect(zw, skin.s_at_y(p[0, 1] + UP), G.WIN_W + 0.02, G.WIN_H + 0.02, G.WIN_R + 0.01))
    return out


def build_fuselage(parts):
    """Comme generate_avion_exterieur.build_fuselage, mais peau ovale + hublots des 2 ponts."""
    z0, z1 = E.STRAIGHT
    skin = E.ellipse_profile(CY, HY, HZ)
    holes = []
    for zw in [G.CABIN[0] + G.MARGIN + i * G.PITCH for i in range(G.N_WINDOWS)]:
        p, _ = G.WALL.map(np.array([G.WIN_CENTER_S]), np.array([zw]), G.WIN_DEPTH)
        holes.append(G.rrect(zw, skin.s_at_y(p[0, 1]), G.WIN_W + 0.02, G.WIN_H + 0.02, G.WIN_R + 0.01))
    holes += hublots_haut()
    n_win = len(holes)
    for zz in (G.REAR_DOOR, G.FRONT_DOOR):
        zd = (zz[0] + zz[1]) / 2
        s0, s1 = skin.s_at_y(0.06), skin.s_at_y(G.PAX_DOOR_TOP)
        holes.append(G.rrect(zd, (s0 + s1) / 2, G.PAX_DOOR_W + 0.02, s1 - s0, 0.18))
    poly = box(z0, 0, z1, skin.length).difference(unary_union(holes))
    parts.add("exterior", G.surface(skin, poly, 0.0, 0.05), sym=True)
    rims = unary_union([h.buffer(0.03).difference(h) for h in holes[:n_win]])
    parts.add("dark", G.surface(skin, rims, 0.004, 0.02), sym=True)
    zs = np.concatenate([np.linspace(z0, z0 - E.BLEND, 8), np.linspace(z0 - E.BLEND, E.TAIL_TIP, 50)[1:]])
    verts, faces = E.loft(parts, zs)
    n = 192
    verts = np.vstack([verts, [[0.0, ext_section(E.TAIL_TIP)[0], E.TAIL_TIP]]])
    last = (len(zs) - 1) * n
    faces += [[last + i, last + (i + 1) % n, len(verts) - 1] for i in range(n)]
    parts.add("exterior", trimesh.Trimesh(verts, np.array(faces), process=False))
    verts, faces = E.loft(parts, np.linspace(z1, G.COCKPIT[0], 30))
    parts.add("exterior", trimesh.Trimesh(verts, np.array(faces), process=False))


E.build_fuselage = build_fuselage


# ---------------------------------------------------------------- l'escalier et la zone
def escalier(parts):
    z0 = ESC[0] + 0.30
    h = UP / N_MARCHES
    a = LARG_ESC / 2
    for i in range(N_MARCHES):
        # marche pleine (du sol a son dessus) + nez de marche fonce
        parts.add("panel", G.B(-a, a, 0.0, (i + 1) * h, z0 + i * GIRON, z0 + (i + 1) * GIRON))
        parts.add("carpet", G.B(-a + 0.02, a - 0.02, (i + 1) * h, (i + 1) * h + 0.004, z0 + i * GIRON, z0 + (i + 1) * GIRON - 0.02))
        parts.add("dark", G.B(-a, a, (i + 1) * h - 0.03, (i + 1) * h + 0.005, z0 + (i + 1) * GIRON - 0.025, z0 + (i + 1) * GIRON))
    # limons (cotes) et mains courantes inox
    for s in (-1, 1):
        x = s * (a + 0.03)
        limon = trimesh.Trimesh(
            vertices=[[x - 0.03, 0, z0], [x + 0.03, 0, z0], [x + 0.03, UP, z0 + N_MARCHES * GIRON], [x - 0.03, UP, z0 + N_MARCHES * GIRON],
                      [x - 0.03, 0.25, z0], [x + 0.03, 0.25, z0], [x + 0.03, UP + 0.25, z0 + N_MARCHES * GIRON], [x - 0.03, UP + 0.25, z0 + N_MARCHES * GIRON]],
            faces=[[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6], [0, 4, 5], [0, 5, 1], [3, 2, 6], [3, 6, 7], [0, 3, 7], [0, 7, 4], [1, 5, 6], [1, 6, 2]])
        parts.add("panel", limon)
        p0 = np.array([x, 0.95, z0])
        p1 = np.array([x, UP + 0.95, z0 + N_MARCHES * GIRON])
        parts.add("steel", G.cyl(0.022, p0, p1))
        for t in np.linspace(0, 1, 6):
            q = p0 + t * (p1 - p0)
            parts.add("steel", G.cyl(0.015, q - [0, 0.70, 0], q))


def zone_escalier(parts):
    """Pont principal sous l'escalier : parois, sol, plafond perce, puits de tremie."""
    z0, z1 = ESC
    G.build_open_zone(parts, z0, z1)
    G.floor(parts, z0, z1)
    C = G.CEILING
    s_h = C.s_at_x(TREMIE_X)
    plafond = box(z0, 0, z1, C.length).difference(box(TREMIE[0], s_h, TREMIE[1], C.length + 1))
    parts.add("ceiling", G.surface(C, plafond, strip=0.02), sym=True)
    # puits de la tremie : 4 parois verticales du plafond du bas au plancher du haut
    y0 = float(np.interp(TREMIE_X, C.x[::-1], C.y[::-1])) - 0.02
    for s in (-1, 1):
        parts.add("panel", G.B(s * TREMIE_X - 0.02, s * TREMIE_X + 0.02, y0, UP, TREMIE[0], TREMIE[1]))
    parts.add("panel", G.B(-TREMIE_X, TREMIE_X, y0, UP, TREMIE[0] - 0.02, TREMIE[0]))
    escalier(parts)


# ---------------------------------------------------------------- le pont superieur
def plancher_haut(parts):
    """Plancher du pont superieur (sur toute sa longueur), avec la tremie de l'escalier."""
    z0, z1 = HAUT_CABIN
    fx = HAUT["FLOOR_X"]
    G.floor(parts, z0, z1, -fx, -TREMIE_X, y=0.0)
    G.floor(parts, z0, z1, TREMIE_X, fx, y=0.0)
    G.floor(parts, z0, TREMIE[0], -TREMIE_X, TREMIE_X, y=0.0)
    G.floor(parts, TREMIE[1], z1, -TREMIE_X, TREMIE_X, y=0.0)
    # garde-corps (panneau plein + main courante inox) sur 3 cotes de la tremie ; l'avant reste ouvert
    for s in (-1, 1):
        parts.add("panel", G.B(s * TREMIE_X - 0.015, s * TREMIE_X + 0.015, 0.0, 1.0, TREMIE[0], TREMIE[1] - 0.02))
        parts.add("steel", G.cyl(0.025, [s * TREMIE_X, 1.05, TREMIE[0]], [s * TREMIE_X, 1.05, TREMIE[1] - 0.02]))
    parts.add("panel", G.B(-TREMIE_X, TREMIE_X, 0.0, 1.0, TREMIE[0], TREMIE[0] + 0.03))
    parts.add("steel", G.cyl(0.025, [-TREMIE_X, 1.05, TREMIE[0]], [TREMIE_X, 1.05, TREMIE[0]]))


def pont_superieur(parts):
    sauve = etat()
    regler(HAUT)
    G.WIN_DEPTH, G.N_WINDOWS, G.CABIN = PROF_HAUT, HAUT_N_WIN, HAUT_CABIN
    h = G.Parts()
    _build_cabin(h)
    G.build_ceiling(h, *HAUT_CABIN, lights=False)
    plancher_haut(h)
    G.bulkhead(h, HAUT_CABIN[0] + G.PART_T)
    G.bulkhead(h, HAUT_CABIN[1])
    regler(sauve)
    for k, meshes in h.items():
        for m in meshes:
            m.apply_translation([0, UP, 0])
            parts[k].append(m)


_build_cabin = G.build_cabin


def build_cabin(parts):
    regler(BAS)
    _build_cabin(parts)
    N3.cloison(parts, B.DEBUT_BUSINESS)
    N3.cloison(parts, N3.DEBUT_FIRST)
    zone_escalier(parts)
    pont_superieur(parts)


G.build_cabin = build_cabin


def baisser_a320(sc):
    """Ailes, moteurs, train : places sous le ventre du fuselage ovale (plus bas que l'A320)."""
    dy = -(HY - HZ)
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]
        if g.startswith("A320"):
            M = T.copy()
            M[1, 3] += dy
            sc.graph.update(node, matrix=M)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(G.HERE, "avion_niveau4.glb")
    G.build_lavatories = N.toilettes_vides
    sc = E.build()
    N.enlever_cuvettes(sc)
    baisser_a320(sc)
    sc.export(out)
    lo, hi = sc.bounds
    print(f"{out}: {hi[2] - lo[2]:.1f} m de long, {hi[1] - lo[1]:.1f} m de haut, {hi[0] - lo[0]:.1f} m d'envergure ; "
          f"pont haut {2 * float(HAUT['WALL'].x.max()):.2f} m de large, {HAUT_N_WIN} hublots ; "
          f"escalier z={-ESC[1]:.2f}..{-ESC[0]:.2f} (glTF) ; embrasures {PROF_BAS:.2f} / {PROF_HAUT:.2f}")
