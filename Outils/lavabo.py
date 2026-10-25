"""Lavabo de toilettes d'avion : simple mais realiste (un seul mesh, une petite texture palette).

Fichier : Modeles/Lavabo/Lavabo.glb
- meuble bas gris clair (portes avec poignee), plan de travail gris clair ;
- vasque ovale en ceramique blanche creusee dans le plan, bonde chromee ;
- robinet chrome (pied, bec courbe, levier) ;
- petit distributeur de savon chrome.
Pivot au sol, au centre du DOS (contre le mur) ; l'avant regarde vers +Z. Unites : metres.
Usage : python3 lavabo.py
"""
import os

import numpy as np
import trimesh
from PIL import Image
from trimesh.transformations import rotation_matrix
from trimesh.visual.material import PBRMaterial

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "..", "Modeles", "Lavabo")

PALETTE = {"meuble": (214, 218, 224), "plan": (232, 234, 238), "ceramique": (250, 250, 252),
           "chrome": (205, 210, 218), "joint": (120, 126, 136), "fond": (225, 228, 233)}
NOMS = list(PALETTE)
CASE = 16

L, P, H = 0.56, 0.42, 0.80          # meuble
EP = 0.035                           # epaisseur du plan
RX, RZ, PROF = 0.17, 0.12, 0.11      # vasque (demi-axes, profondeur)
CZ = P / 2 + 0.02                    # centre de la vasque (un peu vers l'avant)


def texture():
    im = Image.new("RGB", (CASE * len(NOMS), CASE))
    for i, n in enumerate(NOMS):
        im.paste(PALETTE[n], (i * CASE, 0, (i + 1) * CASE, CASE))
    return im


def colorer(m, nom):
    i = NOMS.index(nom)
    m.visual = trimesh.visual.TextureVisuals(uv=np.tile(((i + 0.5) / len(NOMS), 0.5), (len(m.vertices), 1)))
    return m


def boite(lx, ly, lz, x, y, z, nom):
    b = trimesh.creation.box(extents=(lx, ly, lz))
    b.apply_translation((x, y, z))
    return colorer(b, nom)


def tube(rayon, pts, nom, sections=20):
    """Un tube (robinet) qui suit une suite de points."""
    morceaux = []
    for a, b in zip(pts, pts[1:]):
        a, b = np.array(a), np.array(b)
        seg = trimesh.creation.cylinder(radius=rayon, segment=(a, b), sections=sections)
        morceaux.append(seg)
        s = trimesh.creation.icosphere(subdivisions=2, radius=rayon)
        s.apply_translation(b)
        morceaux.append(s)
    return colorer(trimesh.util.concatenate(morceaux), nom)


def plan_troue():
    """Le plan de travail avec un trou ovale (grille : on garde les cases hors de l'ovale)."""
    n = 64
    xs = np.linspace(-L / 2, L / 2, n + 1)
    zs = np.linspace(0, P, n + 1)
    y0, y1 = H, H + EP
    V, F = [], []

    def dedans(x, z):
        return ((x / RX) ** 2 + ((z - CZ) / RZ) ** 2) < 1.0

    idx = {}

    def v(x, z, y):
        k = (round(x, 6), round(z, 6), y)
        if k not in idx:
            idx[k] = len(V)
            V.append((x, y, z))
        return idx[k]

    for i in range(n):
        for j in range(n):
            x0, x1, z0, z1 = xs[i], xs[i + 1], zs[j], zs[j + 1]
            if dedans((x0 + x1) / 2, (z0 + z1) / 2):
                continue
            a, b, c, d = v(x0, z0, y1), v(x1, z0, y1), v(x1, z1, y1), v(x0, z1, y1)
            F += [[a, c, b], [a, d, c]]
    dessus = trimesh.Trimesh(vertices=V, faces=F)
    # le plan est epais : une boite pleine en dessous du dessus, sauf la vasque qui passe a travers
    # (on donne l'epaisseur avec 4 bandes autour de l'ovale)
    bandes = [
        boite(L, EP, CZ - RZ, 0, H + EP / 2, (CZ - RZ) / 2, "plan"),
        boite(L, EP, P - (CZ + RZ), 0, H + EP / 2, (CZ + RZ + P) / 2, "plan"),
        boite(L / 2 - RX, EP, 2 * RZ, -(L / 2 + RX) / 2, H + EP / 2, CZ, "plan"),
        boite(L / 2 - RX, EP, 2 * RZ, (L / 2 + RX) / 2, H + EP / 2, CZ, "plan"),
    ]
    return trimesh.util.concatenate([colorer(dessus, "plan")] + bandes)


def vasque():
    """Vasque ovale : une demi-ellipsoide creuse, ouverte en haut, avec un bord arrondi."""
    nu, nv = 48, 16
    u = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    v = np.linspace(0, np.pi / 2, nv)  # 0 = bord, pi/2 = fond
    V = []
    for vv in v:
        for uu in u:
            V.append((RX * np.cos(vv) * np.cos(uu), H + EP - PROF * np.sin(vv), CZ + RZ * np.cos(vv) * np.sin(uu)))
    F = []
    for j in range(nv - 1):
        for i in range(nu):
            a = j * nu + i
            b = j * nu + (i + 1) % nu
            c = (j + 1) * nu + (i + 1) % nu
            d = (j + 1) * nu + i
            F += [[a, b, c], [a, c, d]]  # faces vers l'interieur (on les voit d'en haut)
    m = trimesh.Trimesh(vertices=V, faces=F, process=True)
    m.faces = np.fliplr(m.faces) if m.volume > 0 else m.faces
    colorer(m, "ceramique")
    # petit bord arrondi en ceramique autour du trou
    bord = trimesh.creation.torus(major_radius=1.0, minor_radius=0.012 / RX, major_sections=48, minor_sections=10)
    bord.apply_scale((RX, RX, RZ * RX / RX * (RZ / RZ)))
    bord.vertices[:, 1] *= RZ / RX
    bord.apply_transform(rotation_matrix(np.pi / 2, (1, 0, 0)))
    bord.apply_translation((0, H + EP + 0.002, CZ))
    colorer(bord, "ceramique")
    # bonde chromee au fond
    bonde = trimesh.creation.cylinder(radius=0.022, height=0.004, sections=24)
    bonde.apply_transform(rotation_matrix(np.pi / 2, (1, 0, 0)))
    bonde.apply_translation((0, H + EP - PROF + 0.002, CZ))
    colorer(bonde, "chrome")
    return trimesh.util.concatenate([m, bord, bonde])


def meuble():
    # le corps s'arrete sous le fond de la vasque ; au-dessus, juste des panneaux (devant, cotes, dos)
    Hc = H + EP - PROF - 0.01
    corps = trimesh.util.concatenate([
        boite(L, Hc, P, 0, Hc / 2, P / 2, "meuble"),
        boite(L, H - Hc, 0.015, 0, (H + Hc) / 2, P - 0.0075, "meuble"),
        boite(L, H - Hc, 0.015, 0, (H + Hc) / 2, 0.0075, "meuble"),
        boite(0.015, H - Hc, P, -L / 2 + 0.0075, (H + Hc) / 2, P / 2, "meuble"),
        boite(0.015, H - Hc, P, L / 2 - 0.0075, (H + Hc) / 2, P / 2, "meuble"),
    ])
    socle = boite(L - 0.04, 0.06, 0.02, 0, 0.03, P + 0.005, "joint")
    # 2 portes (un peu en relief) avec un joint entre elles et une poignee chromee chacune
    portes = []
    for s in (-1, 1):
        portes.append(boite(L / 2 - 0.025, H - 0.14, 0.01, s * (L / 4), H / 2 + 0.03, P + 0.005, "fond"))
        portes.append(tube(0.007, [(s * 0.045, H - 0.18, P + 0.025), (s * 0.045, H - 0.30, P + 0.025)], "chrome", 12))
        for yy in (H - 0.18, H - 0.30):
            portes.append(tube(0.004, [(s * 0.045, yy, P + 0.011), (s * 0.045, yy, P + 0.025)], "chrome", 10))
    return trimesh.util.concatenate([corps, socle] + portes)


def robinet():
    zb = CZ - RZ - 0.035                    # derriere la vasque
    y = H + EP
    pied = tube(0.016, [(0, y, zb), (0, y + 0.11, zb)], "chrome")
    bec = tube(0.011, [(0, y + 0.11, zb), (0, y + 0.15, zb + 0.03), (0, y + 0.15, zb + 0.08), (0, y + 0.11, zb + 0.11)], "chrome")
    embout = trimesh.creation.cylinder(radius=0.012, height=0.012, sections=20)
    embout.apply_transform(rotation_matrix(np.pi / 2, (1, 0, 0)))
    embout.apply_translation((0, y + 0.10, zb + 0.11))
    colorer(embout, "chrome")
    levier = tube(0.006, [(0, y + 0.12, zb - 0.005), (0, y + 0.16, zb - 0.06)], "chrome", 12)
    socle = trimesh.creation.cylinder(radius=0.026, height=0.008, sections=24)
    socle.apply_transform(rotation_matrix(np.pi / 2, (1, 0, 0)))
    socle.apply_translation((0, y + 0.004, zb))
    colorer(socle, "chrome")
    # distributeur de savon a droite
    savon = tube(0.014, [(0.18, y, zb), (0.18, y + 0.07, zb)], "chrome")
    bec_savon = tube(0.005, [(0.18, y + 0.07, zb), (0.18, y + 0.075, zb + 0.04)], "chrome", 10)
    return trimesh.util.concatenate([pied, bec, embout, levier, socle, savon, bec_savon])


def lavabo():
    m = trimesh.util.concatenate([meuble(), plan_troue(), vasque(), robinet()])
    tex = texture()
    mat = PBRMaterial(baseColorTexture=tex, roughnessFactor=0.35, metallicFactor=0.0)
    m.visual = trimesh.visual.TextureVisuals(uv=m.visual.uv, material=mat)
    return m


if __name__ == "__main__":
    os.makedirs(SORTIE, exist_ok=True)
    m = lavabo()
    m.export(os.path.join(SORTIE, "Lavabo.glb"))
    b = m.bounds
    print("ok :", b[0].round(3), b[1].round(3), len(m.faces), "faces")
