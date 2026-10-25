"""Avion niveau 3 : gros-porteur 3 | 3 | 3, SANS AUCUNE DEFORMATION.

- La section de la cabine est celle d'un vrai gros-porteur (profil d'origine de generate_cabin),
  agrandie de la meme facon en largeur ET en hauteur (x1,3) : 7,5 m de large au sol, assez pour
  3 sieges de 60 cm + allee de 90 cm + 3 sieges + allee + 3 sieges ; 2 allees laterales ;
  coffres a bagages sur les cotes ET au-dessus du bloc central.
- Les portes, cloisons, toilettes, cuisine, chambre gardent leur taille normale (rien n'est etire).
- L'exterieur est l'A320 agrandi de la meme facon dans toutes les directions (echelle unique),
  donc ailes, moteurs, nez et queue gardent leurs vraies proportions.
- Plus long : zones FIRST (avant), BUSINESS, puis l'eco ; 2 cloisons avec rideaux.
Les sieges sont des objets a part (dalles).

Usage : python3 generate_avion_niveau3.py [sortie.glb]
"""
import os
import sys

os.environ["N_EN_PLUS"] = "28"          # 12 hublots de First + 16 de Business
N_FIRST = 12
S = 1.3                                 # agrandissement uniforme de la section gros-porteur

import numpy as np  # noqa: E402

import generate_avion_niveau2_business as B  # noqa: E402
import generate_cabin as G  # noqa: E402
from generate_cabin import Profile  # noqa: E402

E, N = B.E, B.N


def P(pts):
    return Profile([(x * S, y * S) for x, y in pts])


# ---------------------------------------------------------------- section gros-porteur
W = P([(2.73, 0.00), (2.83, 0.35), (2.90, 0.80), (2.91, 1.20), (2.87, 1.50), (2.77, 1.68)])
BB = P([(2.77, 1.68), (2.48, 1.695), (2.19, 1.72)])
BF = P([(2.19, 1.72), (2.105, 1.80), (2.08, 1.94), (2.12, 2.07), (2.22, 2.16)])
C = P([(2.22, 2.16), (2.12, 2.27), (1.85, 2.39), (1.40, 2.46), (0.90, 2.49), (0.0, 2.51)])
WF = P([(2.73, 0.00), (2.83, 0.35), (2.90, 0.80), (2.91, 1.20), (2.88, 1.52), (2.78, 1.84), (2.57, 2.06), (2.22, 2.16)])
CB = P([(0.94, 2.49), (0.985, 2.33), (0.975, 2.08), (0.93, 1.90), (0.83, 1.80), (0.40, 1.785), (0.0, 1.785)])
LARGE = {"WALL": W, "BIN_BOTTOM": BB, "BIN_FACE": BF, "CEILING": C, "WALL_FULL": WF,
         "BIN_PROFILES": [W, BB, BF, C], "OPEN_PROFILES": [WF, C], "FLOOR_X": W.x[0],
         "OUTLINE_BINS": G.outline([W, BB, BF, C]), "OUTLINE_OPEN": G.outline([WF, C]),
         # 3 sieges de 60 cm au centre (|x| < 0,9), allees de 0,9 a 1,8 m, puis 3 sieges sur chaque cote
         "AISLE_LINES": (-1.8, -0.9, 0.9, 1.8), "CEIL_LIGHT_X": (2.3, 1.35, 0.3)}
for k, v in LARGE.items():
    setattr(G, k, v)
G.CENTER_BINS = True
G.CENTER_BIN = CB
G.CENTER_BIN_SECTION = G.outline([CB])

# ---------------------------------------------------------------- exterieur : A320 a l'echelle
# rayon exterieur : la cabine (7,6 m de large, 3,3 m de haut) tient dedans avec de la marge
E.CY_EXT = 1.35
E.R_EXT = 4.25
E.K = E.R_EXT / E.A_R
# l'avant du troncon droit de l'A320 tombe sur l'avant de la porte avant (la cuisine / chambre
# et le cockpit sont dans le nez, qui est beaucoup plus grand maintenant)
E.OFF = G.FRONT_DOOR[1] + E.MID_X[0] * E.K
# a cette echelle le troncon droit de l'A320 (~29 m) contient deja toute la cabine allongee :
# pas de troncon en plus (contrairement a l'avion 2 Business)
E.zi_of = lambda x: E.OFF - x * E.K
E.x_of = lambda zi: (E.OFF - zi) / E.K
E.STRAIGHT = (G.REAR_DOOR[0] + 0.5, E.zi_of(E.MID_X[0]))
E.NOSE_TIP = E.zi_of(E.NOSE[0][0])
E.TAIL_TIP = E.zi_of(E.TAIL[-1][0])


def profondeur(s_sur_profil, prof):
    """Distance du mur a la peau exterieure (embrasures des hublots / portes)."""
    def dist(d):
        p, _ = prof.map(np.array([s_sur_profil]), np.array([0.0]), d)
        return np.hypot(p[0, 0], p[0, 1] - E.CY_EXT) - E.R_EXT
    a, b = 0.0, 2.0
    for _ in range(60):
        m = (a + b) / 2
        if dist(m) > 0:
            b = m
        else:
            a = m
    return a + 0.004


G.WIN_DEPTH = profondeur(G.WIN_CENTER_S * S, W)
G.PAX_REVEAL = profondeur(W.s_at_x(float(W.x.max())), WF)

DEBUT_FIRST = B.FIN_ECO - N_FIRST * G.PITCH


def ajouter_separations():
    cabine = G.build_cabin

    def build_cabin(parts):
        cabine(parts)
        z = B.DEBUT_BUSINESS
        B.separation(parts)                  # eco / Business
        B.DEBUT_BUSINESS = DEBUT_FIRST
        B.separation(parts)                  # Business / First
        B.DEBUT_BUSINESS = z
    G.build_cabin = build_cabin


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(G.HERE, "avion_niveau3.glb")
    G.build_lavatories = N.toilettes_vides
    ajouter_separations()
    sc = E.build()
    N.enlever_cuvettes(sc)
    sc.export(out)
    lo, hi = sc.bounds
    print(f"{out}: {hi[2] - lo[2]:.1f} m de long, {hi[0] - lo[0]:.1f} m d'envergure, "
          f"cabine {2 * float(W.x.max()):.2f} m de large, {float(C.y.max()):.2f} m de haut ; "
          f"embrasures {G.WIN_DEPTH:.2f} / {G.PAX_REVEAL:.2f} m ; "
          f"First z={-B.FIN_ECO:.2f}..{-DEBUT_FIRST:.2f}, Business ..{-B.DEBUT_BUSINESS:.2f} (glTF)")
