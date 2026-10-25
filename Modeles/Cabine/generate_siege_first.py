"""Suite First Class luxe (style Emirates / Singapore) : une cabine privee fermee.

- 4 parois en noyer vernis, interieur en cuir capitonne vert emeraude, liseres et main-courante dores ;
- porte coulissante cote allee (noeuds "PorteCoulissante_*") : livree ouverte ; pour la fermer,
  la deplacer de 0,74 m vers l'avant (-Z) ;
- grand fauteuil en cuir creme capitonne, accoudoirs larges, appui-tete a oreilles ;
- pouf / repose-pieds a la meme hauteur que l'assise (le siege + le pouf = un lit) ;
- console laterale en noyer : lampe doree, petit frigo vitre, carafe d'eau et verres, commande du siege ;
- grand ecran 32 pouces dans la paroi avant, patere, coussin, plaid plie, chaussons.
Repere : metres, Y en haut, le passager regarde vers -Z. Origine au sol, au centre de la suite.
La paroi cote hublot est a gauche (-X), la porte cote allee a droite (+X) ; le fichier "gauche" est le miroir.

Usage : python3 generate_siege_first.py
"""
import os

import numpy as np
import trimesh
from PIL import Image

from generate_siege_business_v2 import bruit, tex_tissu, tex_cuir, tex_uni, mat, uv_boite, rbox, pose, cylindre

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ textures
def tex_noyer(n=512):
    y = np.linspace(0, 1, n)[:, None]
    b = bruit(n, 128, 4)
    fibres = bruit(n, 4, 2)[:, :1].repeat(n, 1)              # fines fibres paralleles
    veines = np.sin((y * 18 + b * 1.6) * np.pi) * 0.5 + 0.5
    fonce = np.array([74, 44, 27]); clair = np.array([112, 70, 42])
    c = fonce + (clair - fonce) * (0.55 * veines[..., None] ** 2 + 0.45 * fibres[..., None])
    c = c * (0.94 + 0.08 * bruit(n, 24, 2)[..., None])
    return np.clip(c, 0, 255).astype(np.uint8)


def tex_capitonne(rgb, n=512, pas=64):
    """Cuir capitonne en losanges : coussins bombes, coutures en creux, bouton a chaque croisement."""
    x, y = np.meshgrid(np.arange(n), np.arange(n))
    u, v = (x + y) % pas / pas, (x - y) % pas / pas
    du, dv = np.minimum(u, 1 - u), np.minimum(v, 1 - v)
    bombe = 0.80 + 0.20 * np.sin(np.pi * u) * np.sin(np.pi * v)
    couture = np.exp(-(du / 0.035) ** 2) + np.exp(-(dv / 0.035) ** 2)
    bouton = np.exp(-((du ** 2 + dv ** 2) / 0.004))
    grain = 0.95 + 0.08 * (bruit(n, 8, 3) - 0.5)
    val = bombe * grain * (1 - 0.20 * np.clip(couture, 0, 1)) * (1 - 0.35 * bouton)
    return np.clip(np.array(rgb)[None, None, :] * val[..., None], 0, 255).astype(np.uint8)


def tex_plaid(n=256):
    """Plaid vert emeraude avec deux fines bandes dorees."""
    y = np.arange(n)[:, None].repeat(n, 1) / n
    bande = np.abs((y * 2) % 1 - 0.5) < 0.04
    c = np.where(bande[..., None], np.array([214, 190, 140]), np.array([22, 92, 64]))
    c = c * (0.90 + 0.12 * tex_tissu((255, 255, 255), n)[..., :1] / 255)
    return np.clip(c, 0, 255).astype(np.uint8)


CREME = (232, 220, 196)
EMERAUDE = (24, 96, 66)
M = {
    "noyer": mat("NoyerVerni", tex_noyer(), 0.30),
    "capitonne": mat("CuirCapitonneEmeraude", tex_capitonne(EMERAUDE), 0.5),
    "siege": mat("CuirCapitonneCreme", tex_capitonne(CREME, pas=80), 0.5),
    "cuir": mat("CuirCreme", tex_cuir(CREME), 0.5),
    "cuir_vert": mat("CuirEmeraude", tex_cuir(EMERAUDE), 0.5),
    "laque": mat("LaqueCreme", tex_uni((238, 230, 214)), 0.25),
    "or": mat("OrDore", tex_uni((200, 164, 104)), 0.22, 1.0),
    "noir": mat("LaqueNoire", tex_uni((22, 22, 26)), 0.3),
    "ecran": mat("EcranVeille", tex_uni((10, 16, 28), var=0.4), 0.06, 0.0, [0.02, 0.04, 0.08]),
    "verre": mat("VerreFume", tex_uni((40, 52, 50)), 0.05),
    "cristal": mat("Cristal", tex_uni((215, 228, 226)), 0.05),
    "lumiere": mat("LumiereLampe", tex_uni((255, 240, 214)), 0.3, 0.0, [1.0, 0.92, 0.78]),
    "plaid": mat("PlaidEmeraude", tex_plaid(), 0.9),
    "coussin": mat("CoussinCreme", tex_tissu((226, 214, 190)), 0.85),
}
PIECES = {k: [] for k in M}
PORTE = {k: [] for k in M}


def ajouter(k, m, echelle=1.0, porte=False):
    (PORTE if porte else PIECES)[k].append(uv_boite(m, echelle))


def boite(k, l, h, e, x, y, z, r=0.01, echelle=1.0, porte=False, rx=0.0, ry=0.0, bombe=0.0):
    n = 3 if (r >= 0.02 or bombe) else 2                     # assez de facettes pour les arrondis visibles
    ajouter(k, pose(rbox(l, h, e, r, bombe, n), rx, ry, (x, y, z)), echelle, porte)


# ------------------------------------------------------------------ dimensions
L = 1.20          # largeur exterieure de la suite
P = 2.25          # profondeur exterieure
EP = 0.06         # epaisseur des parois
H_HAUT = 1.45     # parois arriere et allee (intimite)
H_BAS = 1.20      # parois hublot et avant
X_SIEGE = 0.09    # le fauteuil est decale vers l'allee (la console est cote hublot)
Z_OUVERTURE = (-0.55, 0.15)   # passage cote allee, entre le pouf et le fauteuil
LG_PORTE = 0.74


def paroi(longueur, hauteur, centre, axe, interieur, porte=False, ecran=False):
    """Paroi en noyer : face interieure capitonnee emeraude, main-courante doree, liseres dores dehors.
    axe='x' : paroi le long de X (avant / arriere) ; axe='z' : paroi le long de Z (cotes).
    interieur = signe (+1 / -1) de la direction vers l'interieur de la suite, sur l'axe perpendiculaire."""
    cx, cz = centre
    def b(k, lg, h, ep, y, decal, r=0.01, echelle=1.0):
        if axe == "x":
            boite(k, lg, h, ep, cx, y, cz + interieur * decal, r, echelle, porte)
        else:
            boite(k, ep, h, lg, cx + interieur * decal, y, cz, r, echelle, porte)
    b("noyer", longueur, hauteur - 0.03, EP, (hauteur - 0.03) / 2, 0, 0.012, 0.8)
    # coussin capitonne a l'interieur (entre la plinthe et la main-courante)
    if not ecran:
        b("capitonne", longueur - 0.10, hauteur - 0.30, 0.03, 0.12 + (hauteur - 0.30) / 2, EP / 2 + 0.012, 0.012, 0.35)
    # main-courante doree arrondie sur le dessus
    b("or", longueur + 0.004, 0.035, EP + 0.016, hauteur - 0.017, 0, 0.016)
    # plinthe noire en bas, des deux cotes
    for s in (-1, 1):
        b("noir", longueur - 0.004, 0.08, 0.008, 0.04, s * (EP / 2 + 0.002), 0.003)
    # deux liserets dores a l'exterieur
    for y in (0.30, hauteur - 0.16):
        b("or", longueur - 0.06, 0.012, 0.006, y, -(EP / 2 + 0.002), 0.003)


def parois():
    zi_av, zi_ar = -P / 2 + EP / 2, P / 2 - EP / 2
    paroi(L, H_HAUT, (0, zi_ar), "x", -1)                          # arriere
    paroi(L, H_BAS, (0, zi_av), "x", +1, ecran=True)               # avant (ecran)
    paroi(P - 2 * EP, H_BAS, (-L / 2 + EP / 2, 0), "z", +1)        # hublot
    # cote allee : partie fixe devant (patere) et partie fixe a cote du fauteuil ;
    # l'ouverture est entre le fauteuil et le pouf, comme dans une vraie suite
    z_o0, z_o1 = Z_OUVERTURE
    zf, zr = -P / 2 + EP, P / 2 - EP
    paroi(z_o0 - zf, H_HAUT, (L / 2 - EP / 2, (zf + z_o0) / 2), "z", -1)
    paroi(zr - z_o1, H_HAUT, (L / 2 - EP / 2, (z_o1 + zr) / 2), "z", -1)
    for z in Z_OUVERTURE:                                           # montants dores de l'ouverture
        boite("or", EP + 0.01, H_HAUT - 0.03, 0.014, L / 2 - EP / 2, (H_HAUT - 0.03) / 2, z, 0.005)
    # porte coulissante : ouverte, rangee devant la partie fixe arriere, cote allee
    zp = z_o1 + LG_PORTE / 2 + 0.02
    xp = L / 2 + EP / 2 + 0.008
    boite("noyer", EP * 0.6, H_HAUT - 0.06, LG_PORTE, xp, (H_HAUT - 0.06) / 2 + 0.01, zp, 0.012, 0.8, True)
    boite("or", EP * 0.6 + 0.012, 0.03, LG_PORTE, xp, H_HAUT - 0.05 + 0.015, zp, 0.012, 1.0, True)
    for y in (0.30, H_HAUT - 0.20):
        boite("or", 0.006, 0.012, LG_PORTE - 0.06, xp + EP * 0.3 + 0.002, y, zp, 0.003, 1.0, True)
    # poignee doree verticale sur le chant avant de la porte (cote ouverture)
    zpo = zp - LG_PORTE / 2 + 0.06
    boite("or", 0.022, 0.30, 0.022, xp + EP * 0.3 + 0.02, 0.98, zpo, 0.01, 1.0, True)
    for y in (0.86, 1.10):
        boite("or", 0.024, 0.014, 0.014, xp + EP * 0.3 + 0.009, y, zpo, 0.005, 1.0, True)
    return zp


# ------------------------------------------------------------------ fauteuil
def fauteuil():
    x0 = X_SIEGE
    z_dos = P / 2 - EP - 0.28          # arriere du dossier (le dossier incline ne touche pas la paroi)
    lc = 0.62                          # largeur du coussin
    # socle laque + base noyer
    boite("noyer", lc + 0.18, 0.14, 0.70, x0, 0.07, z_dos - 0.40, 0.02, 0.8)
    boite("noyer", lc - 0.04, 0.22, 0.50, x0, 0.24, z_dos - 0.36, 0.03, 0.8)
    # assise capitonnee : coussin epais bombe
    boite("siege", lc, 0.12, 0.62, x0, 0.40, z_dos - 0.42, 0.05, 0.45, bombe=0.015)
    # dossier incline (2 volumes : lombaire + haut), coussin d'appui-tete a oreilles
    for hh, yc, dz in ((0.46, 0.68, 0.0), (0.34, 1.05, 0.09)):
        boite("siege", lc, hh, 0.16, x0, yc, z_dos - 0.10 + dz, 0.06, 0.45, rx=12, bombe=0.03)
    boite("noyer", lc + 0.05, 1.02, 0.09, x0, 0.86, z_dos + 0.06, 0.04, 0.8, rx=12)   # coque du dossier
    boite("or", lc + 0.056, 0.012, 0.095, x0, 0.46, z_dos - 0.04, 0.005, rx=12)
    boite("cuir", lc * 0.80, 0.20, 0.10, x0, 1.29, z_dos + 0.02, 0.05, rx=12, bombe=0.02)
    for s in (-1, 1):                                                         # oreilles
        boite("cuir", 0.07, 0.22, 0.12, x0 + s * (lc * 0.40 + 0.02), 1.28, z_dos + 0.0, 0.035, rx=12, ry=s * 18)
    # accoudoirs larges : base noyer, dessus cuir creme surpique, bout dore
    for s in (-1, 1):
        xa = x0 + s * (lc / 2 + 0.065)
        boite("noyer", 0.12, 0.58, 0.64, xa, 0.29, z_dos - 0.38, 0.02, 0.8)
        boite("cuir", 0.14, 0.06, 0.62, xa, 0.61, z_dos - 0.38, 0.028)
        boite("or", 0.124, 0.012, 0.006, xa, 0.555, z_dos - 0.38 - 0.322, 0.003)
    # ceinture discrete
    for s in (-1, 1):
        boite("cuir_vert", 0.05, 0.006, 0.22, x0 + s * 0.11, 0.465, z_dos - 0.48, 0.002)
    boite("or", 0.07, 0.014, 0.05, x0, 0.47, z_dos - 0.60, 0.006)
    # deux coussins : creme et emeraude, poses contre le dossier
    boite("coussin", 0.40, 0.30, 0.11, x0 + 0.04, 0.63, z_dos - 0.24, 0.05, 0.3, rx=14, ry=-6, bombe=0.04)
    boite("cuir_vert", 0.30, 0.22, 0.10, x0 + 0.06, 0.60, z_dos - 0.30, 0.05, 0.3, rx=20, ry=10, bombe=0.03)
    return z_dos


# ------------------------------------------------------------------ pouf / lit, ecran
def pouf():
    z = -P / 2 + EP + 0.36
    boite("noyer", 0.66, 0.28, 0.58, X_SIEGE, 0.14, z, 0.03, 0.8)
    boite("or", 0.664, 0.012, 0.584, X_SIEGE, 0.283, z, 0.006)
    boite("siege", 0.64, 0.12, 0.56, X_SIEGE, 0.35, z, 0.05, 0.45, bombe=0.015)
    # plaid plie + chaussons poses sur le pouf
    boite("plaid", 0.40, 0.06, 0.28, X_SIEGE - 0.04, 0.44, z - 0.04, 0.025, 0.5)
    for s in (-1, 1):
        boite("coussin", 0.09, 0.035, 0.24, X_SIEGE + 0.22 + s * 0.055, 0.428, z + 0.06, 0.03, 0.3)
        boite("or", 0.07, 0.006, 0.02, X_SIEGE + 0.22 + s * 0.055, 0.447, z - 0.02, 0.002)
    return z


def ecran():
    z = -P / 2 + EP + 0.004
    x = X_SIEGE
    # cadre dore fin + dalle noire 32 pouces (0,71 x 0,40), encastre dans la paroi avant
    boite("or", 0.76, 0.45, 0.012, x, 0.80, z, 0.006)
    boite("noir", 0.74, 0.43, 0.014, x, 0.80, z + 0.004, 0.004)
    boite("ecran", 0.71, 0.40, 0.004, x, 0.80, z + 0.012, 0.002)
    # panneau capitonne de chaque cote de l'ecran et en dessous
    zi = -P / 2 + EP + 0.012
    gauche = (x - 0.38) - (-L / 2 + EP)
    droite = (L / 2 - EP) - (x + 0.38)
    boite("capitonne", gauche - 0.02, 0.90, 0.03, -L / 2 + EP + gauche / 2, 0.57, zi, 0.012, 0.35)
    boite("capitonne", droite - 0.02, 0.90, 0.03, x + 0.38 + droite / 2, 0.57, zi, 0.012, 0.35)
    boite("capitonne", 0.74, 0.40, 0.03, x, 0.33, zi, 0.012, 0.35)
    # patere doree pour le manteau (paroi cote allee, partie fixe)
    boite("or", 0.03, 0.03, 0.03, L / 2 - EP - 0.03, 1.22, -P / 2 + 0.50, 0.012)
    ajouter("or", cylindre(0.008, 0.08, (L / 2 - EP - 0.06, 1.24, -P / 2 + 0.50), axe=(-1, 0.4, 0)))


# ------------------------------------------------------------------ console cote hublot
def console(z_dos):
    x_in = -L / 2 + EP
    lg = X_SIEGE - 0.31 - 0.13 - x_in - 0.01      # jusqu'a l'accoudoir gauche
    xc = x_in + lg / 2
    z0, z1 = z_dos - 0.90, P / 2 - EP - 0.035          # jusqu'a la paroi arriere
    zc, pz = (z0 + z1) / 2, z1 - z0
    yt = 0.70
    boite("laque", lg, yt - 0.03, pz, xc, (yt - 0.03) / 2, zc, 0.02)
    boite("noyer", lg + 0.01, 0.03, pz + 0.01, xc, yt - 0.015, zc, 0.008, 0.6)
    boite("or", lg + 0.014, 0.008, pz + 0.014, xc, yt - 0.032, zc, 0.003)
    # petit frigo vitre sur la face cote passager (+X), cadre dore, 2 bouteilles visibles derriere
    xm = xc + lg / 2 + 0.002
    zm = z0 + 0.24
    boite("or", 0.006, 0.30, 0.32, xm, 0.36, zm, 0.003)
    boite("verre", 0.006, 0.27, 0.29, xm + 0.003, 0.36, zm, 0.003)
    boite("or", 0.012, 0.10, 0.012, xm + 0.008, 0.36, zm + 0.12, 0.005)
    # commande du siege + tablette tactile encastrees sur le plateau
    boite("noir", lg * 0.55, 0.008, 0.16, xc, yt + 0.004, z1 - 0.20, 0.004)
    boite("ecran", lg * 0.48, 0.002, 0.13, xc, yt + 0.009, z1 - 0.20, 0.002)
    # lampe : pied dore, abat-jour creme lumineux
    xl, zl = xc, z0 + 0.12
    ajouter("or", cylindre(0.045, 0.014, (xl, yt + 0.007, zl)))
    ajouter("or", cylindre(0.008, 0.26, (xl, yt + 0.14, zl)))
    abat = trimesh.creation.cylinder(radius=1, height=1, sections=32)
    v = abat.vertices.copy()
    r = np.where(v[:, 2] > 0, 0.055, 0.085)
    v[:, :2] = v[:, :2] / np.maximum(np.linalg.norm(v[:, :2], axis=1, keepdims=True), 1e-9) * r[:, None] * \
        (np.linalg.norm(v[:, :2], axis=1, keepdims=True) > 1e-6)
    v[:, 2] *= 0.12
    abat = trimesh.Trimesh(v[:, [0, 2, 1]], abat.faces[:, ::-1], process=True)
    abat.apply_translation((xl, yt + 0.30, zl))
    ajouter("lumiere", abat)
    # carafe et 2 verres en cristal sur un plateau dore
    xp, zp = xc, z0 + 0.42
    boite("or", lg * 0.70, 0.008, 0.20, xp, yt + 0.004, zp, 0.004)
    ajouter("cristal", cylindre(0.035, 0.16, (xp - 0.03, yt + 0.088, zp)))
    ajouter("cristal", cylindre(0.012, 0.05, (xp - 0.03, yt + 0.19, zp)))
    ajouter("or", cylindre(0.016, 0.014, (xp - 0.03, yt + 0.222, zp)))
    for dz in (-0.05, 0.06):
        ajouter("cristal", cylindre(0.024, 0.09, (xp + 0.05, yt + 0.053, zp + dz)))


# ------------------------------------------------------------------ assemblage
def scene_de(pieces, prefixe, sc):
    for k, lst in pieces.items():
        if not lst:
            continue
        m = trimesh.util.concatenate(lst)
        uv = np.vstack([p.metadata["uv"] for p in lst])
        vn = np.vstack([p.metadata["normales"] for p in lst])
        m = trimesh.Trimesh(m.vertices, m.faces, vertex_normals=vn, process=False)
        m.visual = trimesh.visual.TextureVisuals(uv=uv, material=M[k])
        sc.add_geometry(m, node_name=f"{prefixe}_{M[k].name}", geom_name=f"{prefixe}_{M[k].name}")


def construire():
    for d in (PIECES, PORTE):
        for k in d:
            d[k].clear()
    parois()
    z_dos = fauteuil()
    pouf()
    ecran()
    console(z_dos)
    sc = trimesh.Scene()
    scene_de(PIECES, "SuiteFirst", sc)
    scene_de(PORTE, "PorteCoulissante", sc)
    return sc


if __name__ == "__main__":
    # droite : hublot a gauche, porte a droite (rangee de gauche de l'avion) ; gauche : miroir
    for nom, miroir in (("suite_first_droite.glb", False), ("suite_first_gauche.glb", True)):
        sc = construire()
        if miroir:
            for g in sc.geometry.values():
                g.apply_transform(np.diag([-1, 1, 1, 1]))
                g.invert()
        out = os.path.join(HERE, nom)
        sc.export(out, include_normals=True)
        b = sc.bounds
        print(f"{out}: {b[1][0]-b[0][0]:.2f} x {b[1][2]-b[0][2]:.2f} m, {b[1][1]-b[0][1]:.2f} m de haut, "
              f"{sum(len(g.faces) for g in sc.geometry.values())} triangles, "
              f"{os.path.getsize(out)/1e6:.1f} Mo")
