"""PARCELLE D'AVION (lobby) : ce qui APPARAIT quand un joueur fait CLAIM au bout d'un chemin du spawn.
Un seul fichier, 3 objets separes (a cacher / montrer par Verse) :
- Parcelle_Sol      : un rond gris comme la plateforme du spawn (meme gris, muret fin), ouvert vers le chemin,
                      avec une ligne jaune de guidage jusqu'a la roue avant
- Parcelle_Avion    : un avion de ligne CARTOON en version jouet (gros, rond, ~13 m), blanc et vert argent,
                      gros contour sombre, hublots ronds, cockpit, logo $ sur la derive
- Parcelle_Escalier : l'escalier roulant devant la porte avant (la plaque ENTER se pose a son pied)
Repere : centre du rond au sol, Y en haut. Le CHEMIN arrive du cote -X (l'ouverture), nez de l'avion vers -X.
Sortie : Modeles/Lobby/Parcelle_Avion.glb     Usage : python3 generate_parcelle_avion.py [--apercu]
"""
import json
import math
import os
import struct
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, Polygon, box as rect
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(HERE))
LOBBY = os.path.join(os.path.dirname(HERE), "Lobby")
POLICE = os.path.join(RACINE, "Outils", "TitanOne-Regular.ttf")
APERCU = "--apercu" in sys.argv
PBR = trimesh.visual.material.PBRMaterial
CONTOUR = (22, 27, 48)


def lin(rgb):
    c = np.asarray(rgb, float) / 255.0
    if not APERCU:
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return list(np.round(c * 255).astype(int)) + [255]


def col(nom, rgb, rugo=0.4, metal=0.0):
    return PBR(name=nom, baseColorFactor=lin(rgb), roughnessFactor=rugo, metallicFactor=metal)


def tex_logo(n=512):
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([6, 6, n - 6, n - 6], fill=CONTOUR + (255,))
    d.ellipse([30, 30, n - 30, n - 30], fill=(255, 255, 255, 255))
    d.ellipse([58, 58, n - 58, n - 58], fill=(30, 170, 90, 255))
    f = ImageFont.truetype(POLICE, 300)
    d.text((n / 2, n / 2 + 10), "$", font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=14, stroke_fill=CONTOUR)
    return img


M = {
    "blanc": col("AvBlanc", (247, 249, 252), 0.3),
    "vert": col("AvVert", (34, 178, 92), 0.32),
    "vert_fonce": col("AvVertFonce", (18, 120, 64), 0.38),
    "vitre": col("AvVitre", (30, 46, 80), 0.06),
    "porte": col("AvPorte", (214, 222, 232), 0.35),
    "chrome": col("AvChrome", (214, 220, 228), 0.18, 0.85),
    "sombre": col("AvSombre", (40, 44, 56), 0.6),
    "pneu": col("AvPneu", (32, 32, 38), 0.9),
    "jaune": col("AvJaune", (255, 204, 40), 0.5),
    "feu_rouge": col("AvFeuRouge", (255, 60, 70), 0.3),
    "feu_vert": col("AvFeuVert", (70, 255, 130), 0.3),
    "gris_sol": PBR(name="Gris", baseColorFactor=[140, 143, 148, 255], metallicFactor=0.0, roughnessFactor=0.85),
    "contour": col("AvContour", CONTOUR, 0.6),
    "logo": PBR(name="AvLogo", baseColorTexture=tex_logo(), alphaMode="MASK", alphaCutoff=0.5,
                doubleSided=True, roughnessFactor=0.35, metallicFactor=0.0),
}
if APERCU:  # le gris du sol est deja lineaire dans la plateforme : on garde le meme rendu en apercu
    M["gris_sol"] = col("Gris", (196, 198, 202), 0.85)

OUT = 0.05          # epaisseur du contour cartoon
L, R, Y0 = 13.0, 1.55, 2.25     # longueur du fuselage, rayon, hauteur de l'axe (roues au sol)
X0 = -L / 2         # nez


def coque(m, ep=OUT):
    c = m.copy()
    c.merge_vertices()
    c.vertices = c.vertices + c.vertex_normals * ep
    c.invert()
    return c


def ajouter(P, k, m, contour=False):
    if not contour and m.is_watertight and m.volume < 0:
        m.invert()
    P.setdefault(k, []).append(m)


def avec_contour(P, k, m, ep=OUT):
    ajouter(P, k, m)
    ajouter(P, "contour", coque(m, ep), True)


# ------------------------------------------------------------------ fuselage
def rayon_centre(t):
    TN, TT = 0.2, 0.6
    if t < TN:
        e = (TN - t) / TN
        return R * math.sqrt(max(1 - e * e, 0.0004)), Y0 - 0.22 * R * e * e
    if t > TT:
        s = (t - TT) / (1 - TT)
        return R * (1 - 0.70 * s ** 1.25), Y0 + 0.62 * R * s ** 1.6
    return R, Y0


def fuselage(P):
    N, Mr = 128, 260
    u = np.linspace(0, 1, Mr)
    ts = np.where(u < 0.5, 0.5 * (1 - np.cos(np.pi * u)), u)            # plus dense vers le nez
    ts = (ts - ts.min()) / (ts.max() - ts.min())
    al = np.linspace(0, 2 * np.pi, N, endpoint=False)
    V = []
    for t in ts:
        r, c = rayon_centre(t)
        x = X0 + t * L
        for a in al:
            V.append((x, c + r * math.sin(a), r * math.cos(a)))
    r0, c0 = rayon_centre(0)
    r1, c1 = rayon_centre(1)
    V.append((X0 - 0.01, c0, 0))
    V.append((X0 + L, c1, 0))
    V = np.array(V)
    nez, queue = len(V) - 2, len(V) - 1
    F, cle = [], []

    def matiere(t, a):
        s, cz = math.sin(a), math.cos(a)
        # pare-brise : 4 vitres sur le dessus avant du nez, separees par des montants blancs
        phi = math.degrees(math.atan2(cz, s))                 # 0 = tout en haut, +-90 = cotes
        if 0.05 < t < 0.098 and any(a0 < phi < a1 for a0, a1 in ((-50, -27), (-23, -2.5), (2.5, 23), (27, 50))):
            return "vitre"
        # vitres laterales du cockpit
        if 0.106 < t < 0.14 and 0.30 < s < 0.62:
            return "vitre"
        # porte avant gauche (+Z) : contour sombre + porte claire
        if 0.18 < t < 0.232 and -0.52 < s < 0.62 and cz > 0:
            if 0.187 < t < 0.225 and -0.44 < s < 0.54:
                return "porte"
            return "contour"
        # porte arriere des 2 cotes
        if 0.86 < t < 0.893 and -0.30 < s < 0.62:
            if 0.866 < t < 0.887 and -0.22 < s < 0.54:
                return "porte"
            return "contour"
        # bande verte sous les hublots (bouts droits et nets)
        if 0.245 < t < 0.88 and 0.03 < s < 0.165:
            return "vert"
        # ventre vert + liseré vert fonce
        if s < -0.30:
            return "vert"
        if s < -0.18:
            return "vert_fonce"
        return "blanc"

    for i in range(Mr - 1):
        for j in range(N):
            a, b = i * N + j, i * N + (j + 1) % N
            c_, d_ = (i + 1) * N + (j + 1) % N, (i + 1) * N + j
            F += [(a, b, c_), (a, c_, d_)]
            k = matiere((ts[i] + ts[i + 1]) / 2, al[j] + np.pi / N)
            cle += [k, k]
    for j in range(N):
        F.append((nez, (j + 1) % N, j)); cle.append("blanc")
        b0 = (Mr - 1) * N
        F.append((queue, b0 + j, b0 + (j + 1) % N)); cle.append("blanc")
    F = np.array(F)
    tout = trimesh.Trimesh(V, F, process=False)
    if tout.volume < 0:
        tout.invert()
        F = tout.faces
    vn = tout.vertex_normals
    cle = np.array(cle)
    for k in set(cle):
        sel = F[cle == k]
        idx, inv = np.unique(sel, return_inverse=True)
        m = trimesh.Trimesh(V[idx], inv.reshape(-1, 3), vertex_normals=vn[idx], process=False)
        P.setdefault(k, []).append(m)
    ajouter(P, "contour", coque(tout), True)
    # hublots ronds (un peu en relief) des 2 cotes
    for sz in (1, -1):
        for t in np.arange(0.27, 0.83, 0.048):
            if 0.84 < t:
                continue
            r, c = rayon_centre(t)
            a = math.radians(19)
            h = trimesh.creation.cylinder(radius=0.23, height=0.08, sections=28)
            h.apply_scale([1.0, 1.18, 1.0])
            h.apply_transform(rotation_matrix(-a, [1, 0, 0]))
            pos = np.array([X0 + t * L, c + r * math.sin(a), r * math.cos(a)])
            h.apply_translation(pos)
            if sz < 0:
                h.apply_transform(np.diag([1, 1, -1, 1]))
                h.invert()
            ajouter(P, "vitre", h)
            # petit reflet blanc dans chaque hublot
            g = trimesh.creation.cylinder(radius=0.06, height=0.09, sections=12)
            g.apply_transform(rotation_matrix(-a, [1, 0, 0]))
            g.apply_translation(pos + np.array([-0.06, 0.08, 0.005]))
            if sz < 0:
                g.apply_transform(np.diag([1, 1, -1, 1]))
                g.invert()
            ajouter(P, "blanc", g)


# ------------------------------------------------------------------ surfaces portantes
def plaque_profilee(contour_xz, ep_racine, ep_bout, z_bout):
    """planform (x, z) extrudee en Y, plus fine vers le bout (z = z_bout), bords arrondis"""
    poly = Polygon(contour_xz).buffer(0.12, 6).buffer(-0.06, 6)
    m = trimesh.creation.extrude_polygon(poly, 1.0)          # (x, y=z_planform, z=epaisseur)
    v = m.vertices.copy()
    frac = np.clip(np.abs(v[:, 1]) / abs(z_bout), 0, 1)
    ep = ep_racine + (ep_bout - ep_racine) * frac
    m.vertices = np.column_stack([v[:, 0], (v[:, 2] - 0.5) * ep, v[:, 1]])
    if m.volume < 0:
        m.invert()
    return m


def ailes(P):
    for sz in (1, -1):
        # aile principale
        w = plaque_profilee([(-1.6, 0.0), (1.9, 0.0), (2.9, 5.9), (1.75, 5.9)], 0.52, 0.22, 5.9)
        w.apply_transform(rotation_matrix(math.radians(6), [1, 0, 0]))       # diedre
        w.apply_translation([-0.4, Y0 - 0.55 * R, 0.3])
        if sz < 0:
            w.apply_transform(np.diag([1, 1, -1, 1])); w.invert()
        avec_contour(P, "blanc", w)
        # winglet vert
        wl = plaque_profilee([(0.0, 0.0), (1.0, 0.0), (1.25, 1.05), (0.75, 1.05)], 0.14, 0.1, 1.05)
        wl.apply_transform(rotation_matrix(-math.radians(80), [1, 0, 0]))
        tip_y = Y0 - 0.55 * R + 5.6 * math.tan(math.radians(6))
        wl.apply_translation([-0.4 + 1.75, tip_y + 0.02, 6.05])
        if sz < 0:
            wl.apply_transform(np.diag([1, 1, -1, 1])); wl.invert()
        avec_contour(P, "vert", wl, 0.035)
        feu = trimesh.creation.icosphere(2, 0.12)                  # feux de bout d'aile (rouge a gauche, vert a droite)
        feu.apply_translation([-0.4 + 2.2, tip_y + 0.05, 6.02])
        if sz < 0:
            feu.apply_transform(np.diag([1, 1, -1, 1])); feu.invert()
        ajouter(P, "feu_rouge" if sz > 0 else "feu_vert", feu)
        # stabilisateur arriere
        r, c = rayon_centre(0.9)
        s = plaque_profilee([(-0.5, 0.0), (1.2, 0.0), (1.75, 2.6), (0.85, 2.6)], 0.26, 0.12, 2.6)
        s.apply_transform(rotation_matrix(math.radians(4), [1, 0, 0]))
        s.apply_translation([X0 + 0.85 * L, c + 0.1, 0.2])
        if sz < 0:
            s.apply_transform(np.diag([1, 1, -1, 1])); s.invert()
        avec_contour(P, "blanc", s, 0.04)
    # derive verte avec le logo
    r, c = rayon_centre(0.82)
    profil = Polygon([(-0.4, 0.0), (2.6, 0.0), (3.0, 3.0), (1.7, 3.0)]).buffer(0.16, 6).buffer(-0.08, 6)
    d = trimesh.creation.extrude_polygon(profil, 0.34)       # (x, y) extrude en z
    d.apply_translation([X0 + 0.78 * L, c + r * 0.55, -0.17])
    avec_contour(P, "vert", d, 0.045)
    for sz in (1, -1):
        q = trimesh.creation.box((1.5, 1.5, 0.002))
        q.visual = trimesh.visual.TextureVisuals(uv=np.zeros((8, 2)))
        lg = trimesh.Trimesh([(-0.75, -0.75, 0), (0.75, -0.75, 0), (0.75, 0.75, 0), (-0.75, 0.75, 0)],
                             [(0, 1, 2), (0, 2, 3)] if sz > 0 else [(0, 2, 1), (0, 3, 2)], process=False)
        uv = np.array([(0, 0), (1, 0), (1, 1), (0, 1)], float) if sz > 0 else np.array([(1, 0), (0, 0), (0, 1), (1, 1)], float)
        lg.visual = trimesh.visual.TextureVisuals(uv=uv)
        lg.apply_translation([X0 + 0.78 * L + 1.55, c + r * 0.55 + 1.55, sz * 0.185])
        P.setdefault("logo", []).append(lg)


def revolve_x(profil, sec=48):
    """profil [(rayon, x)] tourne autour de l'axe X"""
    m = trimesh.creation.revolve(profil, sections=sec)       # autour de Z
    m.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))   # Z -> X
    if m.volume < 0:
        m.invert()
    return m


def reacteurs(P):
    for sz in (1, -1):
        x, y, z = -1.25, 1.02, 2.75
        nac = revolve_x([(0.0, 1.05), (0.42, 1.05), (0.56, 0.75), (0.66, 0.1), (0.68, -0.5), (0.6, -0.95), (0.0, -0.95)])
        nac.apply_translation([x, y, z * sz])
        avec_contour(P, "vert", nac, 0.04)
        levre = trimesh.creation.torus(0.6, 0.085, major_sections=48, minor_sections=14)
        levre.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
        levre.apply_translation([x - 1.0, y, z * sz])
        ajouter(P, "chrome", levre)
        fan = trimesh.creation.cylinder(radius=0.56, height=0.04, sections=40)
        fan.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
        fan.apply_translation([x - 0.97, y, z * sz])
        ajouter(P, "sombre", fan)
        cone = trimesh.creation.cone(radius=0.17, height=0.16, sections=24)
        cone.apply_transform(rotation_matrix(-np.pi / 2, [0, 1, 0]))
        cone.apply_translation([x - 0.975, y, z * sz])
        ajouter(P, "blanc", cone)
        for k in range(8):                                    # pales
            p = trimesh.creation.box((0.03, 0.4, 0.12))
            p.apply_translation([0, 0.3, 0])
            p.apply_transform(rotation_matrix(k * np.pi / 4, [1, 0, 0]))
            p.apply_transform(rotation_matrix(0.35, [0, 1, 0]) @ np.eye(4))
            p.apply_translation([x - 0.975, y, z * sz])
            ajouter(P, "chrome", p)


def train(P):
    def roue(x, z):
        w = trimesh.creation.cylinder(radius=0.36, height=0.28, sections=32)
        w.apply_translation([x, 0.36, z])
        avec_contour(P, "pneu", w, 0.03)
        j = trimesh.creation.cylinder(radius=0.16, height=0.3, sections=20)
        j.apply_translation([x, 0.36, z])
        ajouter(P, "chrome", j)

    def jambe(x, z, y1):
        j = trimesh.creation.cylinder(radius=0.085, height=y1 - 0.36, sections=16)
        j.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
        j.apply_translation([x, (y1 + 0.36) / 2, z])
        ajouter(P, "chrome", j)

    xn = X0 + 0.15 * L
    for z in (-0.17, 0.17):
        roue(xn, z)
    jambe(xn, 0, Y0 - 0.85 * R)
    for sz in (1, -1):
        for dx in (-0.4, 0.4):
            roue(0.95 + dx, sz * 1.15)
        jambe(0.95, sz * 1.0, Y0 - 0.8 * R)


# ------------------------------------------------------------------ escalier
T_PORTE = 0.206
def escalier(P):
    r, c = rayon_centre(T_PORTE)
    xp = X0 + T_PORTE * L
    seuil = c + r * -0.44
    zp = r * math.cos(math.asin(-0.44)) + 0.1
    n = 8
    mont = seuil / n
    pas = 0.34
    larg = 1.3
    for k in range(n):
        y = (n - k) * mont
        st = trimesh.creation.box((larg, 0.09, pas + 0.02))
        st.apply_translation([xp, y - 0.045, zp + 0.25 + k * pas + pas / 2])
        avec_contour(P, "porte", st, 0.02)
    plat = trimesh.creation.box((larg, 0.12, 0.5))
    plat.apply_translation([xp, seuil - 0.06, zp + 0.25 - 0.25 + 0.25])
    avec_contour(P, "porte", plat, 0.02)
    # limons verts (bandes le long de la pente) + 2 pieds sous le palier + rampes jaunes
    long_ = n * pas + 0.5
    for sx in (-1, 1):
        xs = xp + sx * (larg / 2 + 0.07)
        a = np.array([xs, seuil - 0.05, zp + 0.25])
        b = np.array([xs, 0.1, zp + long_ + 0.1])
        limon = trimesh.creation.box((0.14, 0.32, np.linalg.norm(b - a)))
        ang = math.atan2(a[1] - b[1], b[2] - a[2])
        limon.apply_transform(rotation_matrix(ang, [1, 0, 0]))
        limon.apply_translation((a + b) / 2)
        avec_contour(P, "vert", limon, 0.03)
        pied = trimesh.creation.box((0.16, seuil - 0.1, 0.16))
        pied.apply_translation([xs, (seuil - 0.1) / 2, zp + 0.3])
        avec_contour(P, "vert", pied, 0.03)
        for zz, yy in ((zp + 0.25, seuil + 1.0), (zp + long_ + 0.1, 1.0)):
            pt = trimesh.creation.cylinder(radius=0.045, height=1.0, sections=12)
            pt.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
            pt.apply_translation([xs, yy - 0.5, zz])
            ajouter(P, "jaune", pt)
        a = np.array([xs, seuil + 1.0, zp + 0.25])
        b = np.array([xs, 1.0, zp + long_ + 0.1])
        rail = trimesh.creation.cylinder(radius=0.05, segment=[a, b], sections=12)
        avec_contour(P, "jaune", rail, 0.025)
    return xp, zp + long_ + 0.1


# ------------------------------------------------------------------ sol (comme la plateforme du spawn)
RS = 10.0
def sol(P, x_roue):
    trou = 4.0
    disque = Point(0, 0).buffer(RS, 128)
    muret = disque.difference(Point(0, 0).buffer(RS - 0.2, 128))
    ouverture = rect(-RS - 1, -trou / 2, -RS + 1, trou / 2)
    muret = muret.difference(ouverture)

    def extr(poly, y0, y1):
        m = trimesh.creation.extrude_polygon(poly, y1 - y0)
        m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
        m.apply_transform(np.diag([1, 1, -1, 1]))
        m.invert()
        m.apply_translation([0, y0, 0])
        return m

    ajouter(P, "gris_sol", extr(disque, 0.0, 0.1))
    geoms = muret.geoms if hasattr(muret, "geoms") else [muret]
    for g in geoms:
        ajouter(P, "gris_sol", extr(g, 0.1, 0.6))
    # ligne jaune de guidage (de l'ouverture a la roue avant) + barre d'arret
    ligne = rect(-RS + 0.3, -0.12, x_roue, 0.12).union(rect(x_roue - 0.12, -1.2, x_roue + 0.12, 1.2))
    ajouter(P, "jaune", extr(ligne, 0.1, 0.12))


if __name__ == "__main__":
    av, es, so = {}, {}, {}
    fuselage(av)
    ailes(av)
    reacteurs(av)
    train(av)
    escalier(es)
    sol(so, X0 + 0.15 * L)
    dossier = LOBBY if not APERCU else os.environ.get("APERCU_DIR", "/tmp")
    chemin = os.path.join(dossier, "Parcelle_Avion.glb")
    sc = trimesh.Scene()
    leve = translation_matrix([0, 0.1, 0])          # l'avion et l'escalier sont poses SUR le sol (0,1 m)
    for obj, P, T in (("Parcelle_Sol", so, np.eye(4)), ("Parcelle_Avion", av, leve), ("Parcelle_Escalier", es, leve)):
        for k, ms in P.items():
            if k == "logo":
                m = trimesh.util.concatenate(ms)
                m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([x.visual.uv for x in ms]), material=M[k])
            else:
                normales = all("vertex_normals" in x._cache.cache for x in ms)
                m = trimesh.util.concatenate([trimesh.Trimesh(x.vertices, x.faces, process=False) for x in ms])
                if normales:
                    m.vertex_normals = np.vstack([x.vertex_normals for x in ms])
                m.visual = trimesh.visual.TextureVisuals(material=M[k])
            sc.add_geometry(m, node_name=f"{obj}__{k}", geom_name=f"{obj}__{k}", transform=T)
    sc.export(chemin)
    # un noeud par objet (Parcelle_Sol / Parcelle_Avion / Parcelle_Escalier)
    b = open(chemin, "rb").read()
    lj = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + lj])
    rest = b[20 + lj:]
    meshes, nodes, idx = [], [], {}
    for nd in js["nodes"]:
        if "mesh" not in nd:
            continue
        o = nd["name"].split("__")[0]
        if o not in idx:
            idx[o] = len(meshes)
            meshes.append({"name": o, "primitives": []})
            n2 = {"name": o, "mesh": idx[o]}
            for cle in ("matrix", "translation", "rotation", "scale"):
                if cle in nd:
                    n2[cle] = nd[cle]
            nodes.append(n2)
        meshes[idx[o]]["primitives"] += js["meshes"][nd["mesh"]]["primitives"]
    js["meshes"], js["nodes"] = meshes, nodes
    js["scenes"], js["scene"] = [{"nodes": list(range(len(nodes)))}], 0
    s = json.dumps(js, separators=(",", ":")).encode()
    s += b" " * ((4 - len(s) % 4) % 4)
    open(chemin, "wb").write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(s) + len(rest)) + struct.pack("<II", len(s), 0x4E4F534A) + s + rest)
    print(chemin, round(os.path.getsize(chemin) / 1e3), "Ko")
