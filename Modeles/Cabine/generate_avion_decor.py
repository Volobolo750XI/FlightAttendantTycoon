"""AVION DE DECOR (lobby) : avion de ligne cartoon, livree blanche et vert argent.
- fuselage loft a partir des sections mesurees sur l'A320 (memes que generate_avion_exterieur.py), un peu plus dodu
- ailes, empennages et derive en vrais profils d'aile (NACA), fleche, diedre, winglets
- reacteurs tournes (nacelle verte, levre chromee, soufflante sombre, cone)
- cockpit, hublots, portes, logo $ sur la derive, feux de navigation, trains d'atterrissage
Repere : nez vers -Z, Y en haut, roues au sol (y = 0), centre de l'avion en x = 0. ~34 m de long.
Sortie : Modeles/Lobby/Avion_Decor.glb     Usage : python3 generate_avion_decor.py
Importable : parts(train=True) -> {cle_materiau: [meshes]} et MATERIAUX.
"""
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.transformations import rotation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(HERE))
PBR = trimesh.visual.material.PBRMaterial

# sections A320 : x (nez vers -x), y bas, y haut, demi-largeur   (unites du modele)
NOSE = [(-2.12, 0.408, 0.441, 0.0), (-2.02, 0.321, 0.530, 0.120), (-1.92, 0.285, 0.593, 0.165),
        (-1.82, 0.267, 0.677, 0.205), (-1.72, 0.260, 0.710, 0.224), (-1.62, 0.255, 0.728, 0.235),
        (-1.52, 0.250, 0.742, 0.245), (-1.42, 0.246, 0.751, 0.253), (-1.32, 0.242, 0.759, 0.258),
        (-1.22, 0.240, 0.764, 0.262), (-1.12, 0.237, 0.769, 0.266)]
TAIL = [(0.70, 0.237, 0.769, 0.266), (0.78, 0.243, 0.768, 0.262), (0.98, 0.257, 0.765, 0.253),
        (1.18, 0.269, 0.763, 0.246), (1.38, 0.299, 0.760, 0.230), (1.58, 0.339, 0.754, 0.207),
        (1.78, 0.381, 0.745, 0.180), (1.98, 0.426, 0.725, 0.145), (2.18, 0.477, 0.705, 0.115),
        (2.38, 0.537, 0.690, 0.082), (2.58, 0.608, 0.670, 0.035), (2.62, 0.635, 0.645, 0.0)]
S = 7.2                    # metres par unite (fuselage ~34 m)
DODU = 1.12                # cartoon : fuselage un peu plus gros
Y_SOL = -0.237 * S + 1.75
RES = 1.0                  # finesse du fuselage (0.4 = version legere pour le lobby)  # decalage pour que le bas du fuselage soit a 1,75 m


def logo():
    n = 512
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([8, 8, n - 8, n - 8], fill=(255, 255, 255, 255))
    d.ellipse([40, 40, n - 40, n - 40], fill=(30, 170, 90, 255))
    d.ellipse([62, 62, n - 62, n - 62], fill=(255, 255, 255, 255))
    f = ImageFont.truetype(os.path.join(RACINE, "Outils", "TitanOne-Regular.ttf"), 330)
    d.text((n / 2, n / 2 + 12), "$", font=f, fill=(30, 170, 90, 255), anchor="mm")
    return img


def _col(nom, rgb, rugo=0.5, metal=0.0, em=None):
    return PBR(name=nom, baseColorFactor=[*rgb, 255], roughnessFactor=rugo, metallicFactor=metal, emissiveFactor=em)


MATERIAUX = {
    "av_blanc": _col("AvionBlanc", (246, 248, 250), 0.35),
    "av_vert": _col("AvionVertArgent", (30, 170, 90), 0.35),
    "av_vert_fonce": _col("AvionVertFonce", (16, 112, 62), 0.4),
    "av_aile": _col("AvionAileGris", (214, 220, 228), 0.45),
    "av_vitre": _col("AvionVitre", (28, 40, 62), 0.08),
    "av_porte": _col("AvionPorteContour", (150, 158, 170), 0.5),
    "av_chrome": _col("AvionChrome", (200, 206, 214), 0.25, 0.7),
    "av_sombre": _col("AvionSombre", (36, 40, 50), 0.6),
    "av_pneu": _col("AvionPneu", (28, 28, 32), 0.9),
    "av_feu_rouge": _col("AvionFeuRouge", (255, 60, 60), 0.3, 0.0, [1.0, 0.2, 0.2]),
    "av_feu_vert": _col("AvionFeuVert", (60, 255, 120), 0.3, 0.0, [0.2, 1.0, 0.45]),
    "av_feu_blanc": _col("AvionFeuBlanc", (255, 255, 255), 0.3, 0.0, [1.0, 1.0, 1.0]),
    "av_logo": PBR(name="AvionLogo", baseColorTexture=logo(), alphaMode="MASK", alphaCutoff=0.5,
                   doubleSided=True, roughnessFactor=0.4, metallicFactor=0.0),
}


# ------------------------------------------------------------------ fuselage
def sections_fines():
    tab = np.array(NOSE + [(-0.6, 0.237, 0.769, 0.266), (0.2, 0.237, 0.769, 0.266)] + TAIL)
    xs = np.concatenate([np.linspace(-2.12, -1.6, int(130 * RES)), np.linspace(-1.58, 0.68, int(46 * RES) + 2), np.linspace(0.70, 2.62, int(70 * RES))])
    cols = [np.interp(xs, tab[:, 0], tab[:, k]) for k in (1, 2, 3)]
    yb, yt, hw = cols
    # nez : quart d'ellipse (radome bien rond) entre le bout et XA
    XA, YN = -1.86, 0.415
    ia = np.searchsorted(xs, XA)
    for i in range(ia):
        u = (XA - xs[i]) / (XA - xs[0])
        f = math.sqrt(max(0.0, 1 - u * u))
        hw[i] = hw[ia] * f
        yt[i] = YN + (yt[ia] - YN) * f ** 0.85
        yb[i] = YN - (YN - yb[ia]) * f
    yc = 0.503 + (yb + yt) / 2 - 0.503                       # centre
    ry = (yt - yb) / 2
    # nez arrondi : demi-largeur et rayon suivent un quart d'ellipse sur les 4 premiers cm
    return xs, yc, ry, hw


# vitres du cockpit : (x debut, x fin, angle mini, angle maxi depuis le cote, hauteur mini, maxi)
VITRES_COCKPIT = [
    (-2.040, -1.992, 42, 86, 0.05, 1),   # pare-brise (montant central = trou entre 86 et 90)
    (-1.985, -1.940, 30, 62, 0.05, 1),   # vitres d'angle
    (-1.932, -1.890, 24, 50, 0.05, 1),   # vitres laterales
]


def coque():
    xs, yc, ry, hw = sections_fines()
    N = int(128 * RES) // 4 * 4
    ang = np.linspace(0, 2 * np.pi, N, endpoint=False)       # 0 = cote +X, pi/2 = haut
    e = 2.0 / 2.15                                           # super-ellipse legere (un peu carree, cartoon)
    c, s = np.cos(ang), np.sin(ang)
    cx = np.sign(c) * np.abs(c) ** e
    sy = np.sign(s) * np.abs(s) ** e
    V, info = [], []
    for i, x in enumerate(xs):
        for j in range(N):
            V.append([cx[j] * hw[i] * DODU * S, (yc[i] + sy[j] * ry[i] * DODU) * S + Y_SOL, x * S])
            info.append((x, ang[j], sy[j]))
    V = np.array(V)
    F = []
    for i in range(len(xs) - 1):
        for j in range(N):
            a, b = i * N + j, i * N + (j + 1) % N
            F += [[a, b, a + N], [b, b + N, a + N]]            # faces tournees vers l'exterieur
    F = np.array(F)
    # couleur par face selon la position (livree)
    groupes = {}
    for fi, f in enumerate(F):
        x = np.mean([info[k][0] for k in f])
        sy_ = np.mean([info[k][2] for k in f])
        a = math.atan2(np.mean([math.sin(info[k][1]) for k in f]), np.mean([math.cos(info[k][1]) for k in f]))
        k = "av_blanc"
        # ventre vert + liseré fonce (pas sur le radome)
        seuil = -0.42 if (x > -1.30 or RES < 1) else -0.42 - 0.55 * ((-1.30 - x) / 0.52) ** 1.5
        if x > -1.82:
            if sy_ < seuil:
                k = "av_vert"
            elif sy_ < seuil + 0.12:
                k = "av_vert_fonce" if x < 2.3 else "av_vert"
        # vitres du cockpit : bandeau sur le nez
        cote_deg = abs(math.degrees(a))                      # 0 = cote droit, 90 = dessus, 180 = cote gauche
        cote_deg = min(cote_deg, 180 - cote_deg)             # 0 = de cote, 90 = dessus
        for x0, x1, l0, l1, y0, y1 in VITRES_COCKPIT:
            if x0 < x < x1 and l0 < cote_deg < l1 and y0 < sy_ < y1:
                k = "av_vitre"
        groupes.setdefault(k, []).append(fi)
    out = {}
    for k, idx in groupes.items():
        m = trimesh.Trimesh(V, F[idx], process=False)
        m.remove_unreferenced_vertices()
        out[k] = [m]
    return out, (xs, yc, ry, hw)


def surface_point(geo, x, sy_):
    """point (cote +X) et angle de la normale sur le fuselage a l'abscisse x (unites) et hauteur relative sy"""
    xs, yc, ry, hw = geo
    yci, ryi, hwi = (np.interp(x, xs, v) for v in (yc, ry, hw))
    s = math.asin(max(-1, min(1, sy_)))
    # inverse approx de la super-ellipse : on se contente du cercle (ecart < 2 cm)
    px = math.cos(s) * hwi * DODU * S
    py = (yci + sy_ * ryi * DODU) * S + Y_SOL
    return px, py, s


def decal_arrondi(w, h, ep=0.05, k="", r=None):
    """plaque arrondie (rectangle a coins ronds) dans le plan YZ, epaisseur en X"""
    r = min(w, h) / 2 if r is None else r
    from shapely.geometry import box
    p = box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, 8 if RES >= 1 else 3)
    m = trimesh.creation.extrude_polygon(p, ep)               # plan XY, epaisseur Z
    m.apply_translation([0, 0, -ep / 2])
    m.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))  # -> plan ZY (w le long de Z), epaisseur X
    return m


def hublots_portes(geo, P):
    def poser(m, x, sy_, cote, retrait=0.0):
        px, py, s = surface_point(geo, x, sy_)
        m = m.copy()
        m.apply_transform(rotation_matrix(s, [0, 0, 1]))       # incline suivant la courbure
        m.apply_translation([px - retrait, py, x * S])
        if cote < 0:
            m.apply_transform(np.diag([-1, 1, 1, 1]))
            m.invert()
        return m
    portes = (-1.48, -1.30, 1.42, 1.62)                       # avant (2) / arriere (2), en unites
    h = decal_arrondi(0.30, 0.42, 0.06)
    for cote in (1, -1):
        x = -1.40
        while x < 1.45:
            if all(abs(x - p) > 0.07 for p in portes):
                P.setdefault("av_vitre", []).append(poser(h, x, 0.30, cote))
            x += 0.0735
        for xp in (portes[0], portes[3]):
            cadre = decal_arrondi(0.95, 1.95, 0.05, r=0.22)
            P.setdefault("av_porte", []).append(poser(cadre, xp, 0.05, cote))
            dedans = decal_arrondi(0.82, 1.82, 0.07, r=0.18)
            P.setdefault("av_blanc", []).append(poser(dedans, xp, 0.05, cote))
            vit = decal_arrondi(0.24, 0.34, 0.09)
            P.setdefault("av_vitre", []).append(poser(vit, xp, 0.30, cote))


# ------------------------------------------------------------------ profils d'aile
def profil(n=18, t=0.13):
    x = (1 - np.cos(np.linspace(0, np.pi, n))) / 2
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    haut = np.c_[x[::-1], yt[::-1]]
    bas = np.c_[x[1:-1], -yt[1:-1]]
    return np.vstack([haut, bas])                             # boucle fermee : bord de fuite -> attaque -> fuite


def loft(anneaux):
    """anneaux : liste de tableaux (n,3) de meme taille -> maillage ferme"""
    n = len(anneaux[0])
    V = np.vstack(anneaux)
    F = []
    for i in range(len(anneaux) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            F += [[a, b, a + n], [b, b + n, a + n]]
    c0 = len(V)
    V = np.vstack([V, anneaux[0].mean(0), anneaux[-1].mean(0)])
    last = (len(anneaux) - 1) * n
    for j in range(n):
        F.append([c0, (j + 1) % n, j])
        F.append([c0 + 1, last + j, last + (j + 1) % n])
    m = trimesh.Trimesh(V, F, process=True)
    trimesh.repair.fix_normals(m)
    return m


def aile_horizontale(cote, racine, demi_env, c0, c1, fleche, diedre, t0=0.14, t1=0.10, z_att=0.0, y0=0.0,
                     winglet=None, n=10):
    """aile le long de X (cote = +1/-1). racine = x de depart. Profil : corde le long de +Z, epaisseur en Y."""
    P = profil()
    ann = []
    for i in range(n + 1):
        u = i / n
        span = demi_env * u
        c = c0 + (c1 - c0) * u
        t = t0 + (t1 - t0) * u
        pr = profil(t=t)
        x = cote * (racine + span)
        z = z_att + span * math.tan(math.radians(fleche))
        y = y0 + span * math.tan(math.radians(diedre))
        ann.append(np.c_[np.full(len(pr), x), y + pr[:, 1] * c, z + pr[:, 0] * c])
    if winglet:
        h, cw = winglet
        xb, yb, zb = ann[-1][:, 0].mean(), y0 + demi_env * math.tan(math.radians(diedre)), z_att + demi_env * math.tan(math.radians(fleche))
        for k, u in enumerate((0.35, 0.7, 1.0)):
            c = c1 + (cw - c1) * u
            pr = profil(t=0.09)
            ang = math.radians(90 * min(1, u * 1.2))
            off_x = cote * 0.6 * math.sin(ang) * 0.6
            yy = yb + h * u
            zz = zb + (c1 - c) * 0.9 + u * 0.9
            ann.append(np.c_[np.full(len(pr), xb + off_x + cote * 0.25 * u) + 0 * pr[:, 0], yy + pr[:, 1] * c * 0.4, zz + pr[:, 0] * c])
    m = loft(ann)
    return m


def derive(z0, y0, hauteur, c0, c1, fleche, n=8):
    ann = []
    for i in range(n + 1):
        u = i / n
        c = c0 + (c1 - c0) * u
        pr = profil(t=0.12)
        y = y0 + hauteur * u
        z = z0 + hauteur * u * math.tan(math.radians(fleche))
        ann.append(np.c_[pr[:, 1] * c, np.full(len(pr), y), z + pr[:, 0] * c])
    return loft(ann)


# ------------------------------------------------------------------ reacteur
def reacteur(P, x, y, z, L=4.6, R=1.15):
    """axe le long de Z, entree vers -Z en z"""
    prof = [(R * 0.86, 0.0), (R * 0.95, -0.06), (R, 0.15), (R * 1.02, 0.9), (R * 0.98, 2.2),
            (R * 0.86, 3.4), (R * 0.74, L)]
    ext = trimesh.creation.revolve([(r, h) for r, h in prof], sections=40 if RES >= 1 else 20)
    lev = trimesh.creation.revolve([(R * 0.80, 0.25), (R * 0.84, 0.0), (R * 0.93, -0.05), (R * 1.0, 0.12), (R * 1.0, 0.35)], sections=40 if RES >= 1 else 20)
    for m, k in ((ext, "av_vert"), (lev, "av_chrome")):
        m.apply_translation([0, 0, 0])
        m.apply_translation([x, y, z])
        P.setdefault(k, []).append(m)
    fan = trimesh.creation.cylinder(radius=R * 0.82, height=0.05, sections=40 if RES >= 1 else 20)
    fan.apply_translation([x, y, z + 0.45])
    P.setdefault("av_sombre", []).append(fan)
    for i in range(14):                                        # pales
        b = trimesh.creation.box((0.09, R * 0.72, 0.03))
        b.apply_translation([0, R * 0.42, 0])
        b.apply_transform(rotation_matrix(0.35, [0, 1, 0]) if False else np.eye(4))
        b.apply_transform(rotation_matrix(2 * np.pi * i / 14, [0, 0, 1]))
        b.apply_translation([x, y, z + 0.42])
        P.setdefault("av_chrome", []).append(b)
    cone = trimesh.creation.revolve([(0.0, -0.05), (0.18, 0.05), (0.32, 0.25), (0.34, 0.42)], sections=24)
    cone.apply_translation([x, y, z + 0.0])
    P.setdefault("av_blanc", []).append(cone)
    tuy = trimesh.creation.revolve([(R * 0.70, L), (R * 0.55, L + 0.6), (0.0, L + 1.2)], sections=32)
    tuy.apply_translation([x, y, z])
    P.setdefault("av_chrome", []).append(tuy)


# ------------------------------------------------------------------ trains
def roue(r, l, x, y, z):
    w = trimesh.creation.cylinder(radius=r, height=l, sections=28)
    w.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
    w.apply_translation([x, y, z])
    j = trimesh.creation.cylinder(radius=r * 0.55, height=l + 0.04, sections=20)
    j.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
    j.apply_translation([x, y, z])
    return w, j


def jambe(x, y0, y1, z, r=0.13):
    m = trimesh.creation.cylinder(radius=r, height=y1 - y0, sections=14)
    m.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([x, (y0 + y1) / 2, z])
    return m


# ------------------------------------------------------------------ assemblage
def parts(train=True):
    P, geo = coque()
    hublots_portes(geo, P)
    xs, yc, ry, hw = geo
    R_f = 0.266 * DODU * S                                     # rayon du fuselage
    yc_m = 0.503 * S + Y_SOL
    # ailes basses
    z_att = -3.2
    for cote in (1, -1):
        aile = aile_horizontale(cote, 0.4, 15.6, 8.2, 1.9, 27, 6, 0.15, 0.10, z_att, yc_m - R_f * 0.62,
                                winglet=None)
        P.setdefault("av_aile", []).append(aile)
        # sharklet (winglet vertical, legerement penche vers l'exterieur), vert
        xt0 = cote * (0.4 + 15.6)
        yt0 = yc_m - R_f * 0.62 + 15.6 * math.tan(math.radians(6))
        zt0 = z_att + 15.6 * math.tan(math.radians(27))
        ann = []
        for u in np.linspace(0, 1, 7):
            c = 1.9 * (1 - 0.6 * u)
            pr = profil(t=0.10)
            ann.append(np.c_[xt0 + cote * (0.08 + 0.35 * u ** 1.5) + pr[:, 1] * c, np.full(len(pr), yt0 - 0.05 + 1.9 * u),
                             zt0 + (1.9 - c) * 0.75 + 0.55 * u + pr[:, 0] * c])
        P.setdefault("av_vert", []).append(loft(ann))
        # carenage ventral (raccord aile/fuselage)
        car = trimesh.creation.icosphere(3, 1.0)
        car.apply_scale([R_f * 0.95, R_f * 0.45, 6.5])
        car.apply_translation([0, yc_m - R_f * 0.62, z_att + 3.6])
        P.setdefault("av_vert", []).append(car)
        # reacteur sous l'aile
        xe = cote * 5.9
        ze = z_att + 5.5 * math.tan(math.radians(27)) - 3.4
        ye = yc_m - R_f * 0.62 + 5.5 * math.tan(math.radians(6)) - 1.55
        reacteur(P, xe, ye, ze)
        py = derive(ze + 0.9, ye + 0.85, 1.0, 3.8, 3.4, -10)
        py.apply_translation([xe, 0, 0])
        P.setdefault("av_blanc", []).append(py)
        # feux de bout d'aile
        xt = cote * (0.4 + 15.6)
        yt = yc_m - R_f * 0.62 + 15.6 * math.tan(math.radians(6))
        zt = z_att + 15.6 * math.tan(math.radians(27))
        f = trimesh.creation.icosphere(2, 0.16)
        f.apply_translation([xt + cote * 0.05, yt, zt + 0.15])
        P.setdefault("av_feu_vert" if cote > 0 else "av_feu_rouge", []).append(f)
    # empennage horizontal
    z_h = 1.98 * S
    y_h = (0.69 + 0.04) * S + Y_SOL - 0.9
    for cote in (1, -1):
        P.setdefault("av_aile", []).append(
            aile_horizontale(cote, 0.2, 6.0, 3.9, 1.5, 32, 7, 0.11, 0.09, z_h, y_h))
    # derive verte + logo
    z_d = 1.62 * S
    y_d = 0.70 * S + Y_SOL
    der = derive(z_d, y_d, 6.6, 6.4, 2.5, 38)
    P.setdefault("av_vert", []).append(der)
    for cote in (1, -1):
        d = 2.3
        q = trimesh.Trimesh([[0, -d / 2, -d / 2], [0, -d / 2, d / 2], [0, d / 2, d / 2], [0, d / 2, -d / 2]],
                            [[0, 1, 2], [0, 2, 3]], process=False)
        uv = np.array([[1, 0], [0, 0], [0, 1], [1, 1]]) if cote > 0 else np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        yl = y_d + 3.3
        zl = z_d + 3.3 * math.tan(math.radians(38)) + (6.4 + (2.5 - 6.4) * 0.5) * 0.42
        cl = 6.4 + (2.5 - 6.4) * 0.5
        ep = 0.12 * cl * 0.5 + 0.03
        q.apply_translation([cote * ep, yl, zl])
        if cote < 0:
            q.invert()
        q.visual = trimesh.visual.TextureVisuals(uv=uv, material=MATERIAUX["av_logo"])
        P.setdefault("av_logo", []).append(q)
    # feux : anticollision, queue
    for y, z, k in ((yc_m + R_f + 0.12, 0.5, "av_feu_rouge"), (yc_m - R_f - 0.1, -2.0, "av_feu_rouge"),
                    (0.643 * S + Y_SOL, 2.62 * S + 0.1, "av_feu_blanc")):
        f = trimesh.creation.icosphere(2, 0.17)
        f.apply_translation([0, y, z])
        P.setdefault(k, []).append(f)
    if train:
        y_bas = 0.237 * S * 1.0 + Y_SOL - (DODU - 1) * 0.266 * S
        zn = -1.78 * S
        P.setdefault("av_chrome", []).append(jambe(0, 0.45, y_bas + 0.3, zn, 0.12))
        for dx in (-0.3, 0.3):
            w, j = roue(0.45, 0.32, dx, 0.45, zn)
            P.setdefault("av_pneu", []).append(w)
            P.setdefault("av_chrome", []).append(j)
        for cote in (1, -1):
            xg = cote * 3.6
            zg = z_att + 4.1
            P.setdefault("av_chrome", []).append(jambe(xg, 0.6, yc_m - R_f * 0.62, zg, 0.17))
            for dx in (-0.36, 0.36):
                w, j = roue(0.62, 0.42, xg + dx, 0.62, zg)
                P.setdefault("av_pneu", []).append(w)
                P.setdefault("av_chrome", []).append(j)
    for ms in P.values():                                      # securite : faces tournees vers l'exterieur
        for m in ms:
            if m.is_watertight and m.volume < 0:
                m.invert()
    return P


def scene(P, nom="Avion_Decor", T=np.eye(4)):
    sc = trimesh.Scene()
    for k, ms in P.items():
        m = trimesh.util.concatenate([x.copy() for x in ms])
        m.apply_transform(T)
        if k == "av_logo":
            pass
        else:
            m.visual = trimesh.visual.TextureVisuals(material=MATERIAUX[k])
        sc.add_geometry(m, node_name=f"{nom}__{k}", geom_name=f"{nom}__{k}")
    return sc


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(HERE), "Lobby", "Avion_Decor.glb")
    sc = scene(parts())
    sc.export(out)
    print(out, round(os.path.getsize(out) / 1e6, 2), "Mo", sum(len(g.faces) for g in sc.geometry.values()), "faces")
