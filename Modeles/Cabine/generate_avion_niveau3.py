"""Avion niveau 3 (VERSION GROSSIERE, a affiner ensuite) : gros-porteur 3 | 3 | 3.

On part de l'avion 2 Business et :
- on l'ALLONGE encore : 28 hublots en plus au lieu de 16 -> zone FIRST (6,4 m, a l'avant)
  + zone BUSINESS (8,5 m) + l'eco ;
- on l'ELARGIT : tout l'avion x2,1 en largeur et x1,15 en hauteur (cabine ~7,6 m de large :
  3 | 3 | 3 sieges de ~62 cm + 2 allees de ~84 cm) ;
- 2 ALLEES (pas au milieu) : entre le bloc gauche et le bloc central, et entre le central et le droit ;
- 2 cloisons avec rideaux : eco / Business et Business / First.
Les sieges sont des objets a part (dalles), comme avant.

Usage : python3 generate_avion_niveau3.py [sortie.glb]
"""
import os
import sys

os.environ["N_EN_PLUS"] = "28"
N_FIRST = 12                     # hublots de la zone First (a l'avant)
LARGEUR, HAUTEUR = 2.1, 1.15

import numpy as np  # noqa: E402

import generate_avion_niveau2_business as B  # noqa: E402
import generate_cabin as G  # noqa: E402

DEBUT_FIRST = B.FIN_ECO - N_FIRST * G.PITCH

# 2 allees (bandes au sol) : centrees a +-1,35 m (apres elargissement), 84 cm de large.
# Les valeurs ci-dessous sont AVANT l'elargissement (divisees par LARGEUR).
ALLEES = tuple(x / LARGEUR for x in (-1.77, -0.93, 0.93, 1.77))
B.N.LARGE["AISLE_LINES"] = ALLEES
B.N.LARGE["CEIL_LIGHT_X"] = (1.35 / LARGEUR, 0.25 / LARGEUR)


def ajouter_separations():
    cabine = G.build_cabin

    def build_cabin(parts):
        cabine(parts)
        B.separation(parts)                  # eco / Business
        z = B.DEBUT_BUSINESS
        B.DEBUT_BUSINESS = DEBUT_FIRST       # Business / First (meme cloison, plus a l'avant)
        B.separation(parts)
        B.DEBUT_BUSINESS = z
    G.build_cabin = build_cabin


def elargir(sc):
    S = np.diag([LARGEUR, HAUTEUR, 1.0, 1.0])
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]
        sc.graph.update(node, matrix=S @ T)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(G.HERE, "avion_niveau3.glb")
    G.build_lavatories = B.N.toilettes_vides
    B.N.installer()
    ajouter_separations()
    sc = B.E.build()
    B.N.reculer_ailes(sc)
    B.N.enlever_cuvettes(sc)
    elargir(sc)
    sc.export(out)
    lo, hi = sc.bounds
    print(f"{out}: {hi[2] - lo[2]:.1f} m de long, {hi[0] - lo[0]:.1f} m d'envergure, "
          f"cabine ~{2 * float(B.N.LARGE['WALL'].x.max()) * LARGEUR:.2f} m de large ; "
          f"First de z={-B.FIN_ECO:.2f} a {-DEBUT_FIRST:.2f}, Business jusqu'a {-B.DEBUT_BUSINESS:.2f} (glTF)")
