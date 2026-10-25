"""Plans vus de dessus (ou mettre chaque objet) + les 8 suites First deja placees.

- Modeles/Plans/plan_etage.png  : etage du haut de l'avion 4, les 11 objets numerotes, prix conseilles,
                                  et l'endroit conseille pour chaque bouton d'achat (carre vert).
- Modeles/Plans/plan_first.png  : zone First (avion 3 et pont du bas de l'avion 4), 8 suites en 1 | 2 | 1.
- Modeles/Etage/First_8_Suites_Avion3_4.glb : les 8 suites deja placees dans le repere de l'avion
  (poser a la meme position que l'avion, comme les objets de l'etage).
Le plan est dessine l'AVANT de l'avion a GAUCHE. 1 carreau = 1 m.

Usage : python3 generate_plans.py
"""
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from trimesh.ray.ray_pyembree import RayMeshIntersector

from generate_etage_salon import PAROI, UP

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
PLANS = os.path.join(MOD, "Plans")
ETAGE = os.path.join(MOD, "Etage")
POLICE = os.path.join(os.path.dirname(MOD), "Outils", "ArchivoBlack.ttf")
POLICE2 = os.path.join(os.path.dirname(MOD), "Outils", "Exo2-SemiBold.ttf")
PX = 62                     # pixels par metre
VERT, OR, FOND = (22, 120, 80), (214, 178, 110), (246, 250, 247)


def police(t, gras=True):
    return ImageFont.truetype(POLICE if gras else POLICE2, t)


# ------------------------------------------------------------------ rendu orthographique vu de dessus
def vue_dessus(scenes, z0, z1, x0, x1, y_max):
    """Image (largeur = z, hauteur = x) vue d'en haut ; rien au-dessus de y_max n'est vu (pas de plafond)."""
    ms = []
    for sc in scenes:
        for node in sc.graph.nodes_geometry:
            T, g = sc.graph[node]
            m = sc.geometry[g].copy()
            m.apply_transform(T)
            mat = getattr(m.visual, "material", None)
            tex = np.asarray(mat.baseColorTexture.convert("RGB")).astype(float) if mat is not None and \
                getattr(mat, "baseColorTexture", None) is not None else None
            ms.append((m, tex, getattr(m.visual, "uv", None)))
    tout = trimesh.util.concatenate([trimesh.Trimesh(m.vertices, m.faces, process=False) for m, _, _ in ms])
    proprio = np.concatenate([np.full(len(m.faces), i) for i, (m, _, _) in enumerate(ms)])
    debut = np.concatenate([[0], np.cumsum([len(m.faces) for m, _, _ in ms])])
    W, H = int((z1 - z0) * PX), int((x1 - x0) * PX)
    zz, xx = np.meshgrid(z0 + (np.arange(W) + 0.5) / PX, x1 - (np.arange(H) + 0.5) / PX)
    o = np.column_stack([xx.ravel(), np.full(xx.size, y_max), zz.ravel()])
    d = np.tile([0.0, -1.0, 0.0], (len(o), 1))
    tri, ray, loc = RayMeshIntersector(tout).intersects_id(o, d, multiple_hits=False, return_locations=True)
    img = np.zeros((len(o), 4))
    for k in range(len(tri)):
        t = tri[k]
        i = proprio[t]
        m, tex, uv = ms[i]
        f = m.faces[t - debut[i]]
        col = np.array([200.0, 200, 200])
        if tex is not None and uv is not None:
            bc = trimesh.triangles.points_to_barycentric(m.vertices[f][None], loc[k][None])[0]
            q = (uv[f] * bc[:, None]).sum(0)
            h, w = tex.shape[:2]
            col = tex[int((1 - q[1] % 1) * (h - 1)), int((q[0] % 1) * (w - 1))]
        n = tout.face_normals[t]
        img[ray[k], :3] = col * (0.55 + 0.45 * abs(n[1]))
        img[ray[k], 3] = 255
    return Image.fromarray(img.reshape(H, W, 4).clip(0, 255).astype(np.uint8), "RGBA")


class Plan:
    def __init__(self, z0, z1, demi, marge=(70, 120, 70, 330)):
        self.z0, self.z1, self.demi = z0, z1, demi
        self.ml, self.mh, self.mr, self.mb = marge
        self.W = int((z1 - z0) * PX) + self.ml + self.mr
        self.H = int(2 * demi * PX) + self.mh + self.mb
        self.im = Image.new("RGB", (self.W, self.H), FOND)
        self.d = ImageDraw.Draw(self.im)

    def p(self, x, z):
        return self.ml + (z - self.z0) * PX, self.mh + (self.demi - x) * PX

    def coller(self, img):
        self.im.paste(img, (self.ml, self.mh), img)

    def grille(self):
        for z in np.arange(np.ceil(self.z0), self.z1 + 0.01):
            a, b = self.p(self.demi, z), self.p(-self.demi, z)
            self.d.line([a, b], fill=(228, 236, 231), width=1)
        for x in np.arange(-np.floor(self.demi), self.demi + 0.01):
            self.d.line([self.p(x, self.z0), self.p(x, self.z1)], fill=(228, 236, 231), width=1)

    def rect(self, x0, x1, z0, z1, **kw):
        a, b = self.p(x1, z0), self.p(x0, z1)
        self.d.rectangle([a, b], **kw)

    def pastille(self, x, z, texte, coul=VERT, r=17):
        cx, cy = self.p(x, z)
        self.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=coul, outline="white", width=3)
        self.d.text((cx, cy + 1), texte, fill="white", font=police(16), anchor="mm")

    def bouton(self, x, z, texte):
        cx, cy = self.p(x, z)
        r = 0.3 * PX
        self.d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], 6, fill=(60, 200, 120), outline=(10, 80, 50), width=3)
        self.d.text((cx, cy), texte, fill="white", font=police(13), anchor="mm")

    def titre(self, t, st):
        self.d.text((self.ml, 22), t, fill=VERT, font=police(40 if self.W > 1500 else 30))
        self.d.text((self.ml, 76), st, fill=(70, 90, 80), font=police(20 if self.W > 1500 else 17, False))

    def fleche_avant(self):
        x, y = self.ml - 8, self.mh + self.demi * PX
        self.d.polygon([(x - 40, y), (x - 10, y - 18), (x - 10, y + 18)], fill=VERT)
        self.d.text((x - 25, y + 34), "AVANT", fill=VERT, font=police(14), anchor="mm")


def coque(plan, z0, z1, x_sol, x_max, hublots=None):
    """Contour de la cabine : plancher, largeur max (paroi au niveau des hublots), cloisons."""
    plan.rect(-x_max, x_max, z0, z1, fill=(214, 222, 218))
    plan.rect(-x_sol, x_sol, z0, z1, fill=(236, 242, 239))
    plan.grille()
    for s in (-1, 1):
        plan.d.line([plan.p(s * x_max, z0), plan.p(s * x_max, z1)], fill=(120, 135, 128), width=4)
        for z in hublots or []:
            a, b = plan.p(s * (x_max + 0.02), z - 0.13), plan.p(s * (x_max + 0.02), z + 0.13)
            plan.d.line([a, b], fill=(110, 170, 210), width=9)
    for z in (z0, z1):
        plan.d.line([plan.p(-x_max, z), plan.p(x_max, z)], fill=(90, 105, 98), width=7)


def legende(plan, lignes, x0, y0, col_w=640, par_col=6):
    for i, (num, nom, prix, coul) in enumerate(lignes):
        cx = x0 + (i // par_col) * col_w
        cy = y0 + (i % par_col) * 44
        plan.d.ellipse([cx, cy, cx + 30, cy + 30], fill=coul, outline="white", width=2)
        plan.d.text((cx + 15, cy + 16), num, fill="white", font=police(14), anchor="mm")
        plan.d.text((cx + 44, cy + 15), nom, fill=(30, 40, 35), font=police(20), anchor="lm")
        if prix:
            plan.d.text((cx + col_w - 70, cy + 15), prix, fill=VERT, font=police(20), anchor="rm")


# ------------------------------------------------------------------ plan de l'etage du haut
OBJETS_ETAGE = [  # numero, nom, prix conseille, centre (x, z) pour la pastille, bouton d'achat (x, z)
    ("01", "Salon de l'escalier", "400M", (2.05, 17.9), (1.25, 14.75)),
    ("02", "Bar", "900M", (0.0, 12.15), (-1.25, 14.75)),
    ("03", "Salon", "600M", (1.6, 7.35), (0.0, 9.20)),
    ("04", "Piscine", "2B", (0.0, 2.6), (-1.10, 5.35)),
    ("05", "Transats", "1,2B", (2.12, 3.8), (1.10, 5.35)),
    ("06", "Statue Dollar", "10B", (0.0, -0.35), (0.90, -0.20)),
    ("07", "Piano", "3B", (-1.6, -2.45), (-0.45, -1.35)),
    ("08", "Casino", "4B", (1.62, -2.75), (0.45, -1.35)),
    ("09", "Cinema", "6B", (0.0, -7.6), (0.0, -4.30)),
    ("10", "Lustres", "250M", (0.0, 7.35), (0.0, 5.85)),
    ("11", "Plantes", "150M", (-2.3, 9.62), (-0.90, -0.20)),
]


def plan_etage():
    z0, z1 = -9.45, 20.84
    x_sol, x_max = PAROI[0, 0], PAROI[:, 0].max()
    plan = Plan(z0, z1, 3.4)
    plan.titre("AVION 4 - ETAGE DU HAUT : OU METTRE CHAQUE OBJET",
               "Vu de dessus, l'avant a gauche. 1 carreau = 1 m. Pastille = l'objet ; carre vert = son bouton d'achat. "
               "Tous les objets se posent a la MEME position que l'avion.")
    hublots = [-20.84 + 0.0 for _ in []]
    import generate_cabin as G
    hublots = [-(-20.84 + G.MARGIN + i * G.PITCH) for i in range(55)]
    coque(plan, z0, z1, x_sol, x_max, [z for z in hublots if z0 < z < z1])
    # tremie de l'escalier (ouverte vers l'avant)
    plan.rect(-0.65, 0.65, 15.09, 20.74, fill=(70, 80, 76))
    for i in range(21):
        z = 20.54 - i * 0.25
        plan.d.line([plan.p(-0.6, z), plan.p(0.6, z)], fill=(130, 140, 135), width=2)
    plan.d.text(plan.p(0, 19.3), "ESCALIER", fill="white", font=police(14), anchor="mm")
    plan.d.polygon([plan.p(0, 15.15), plan.p(-0.25, 15.6), plan.p(0.25, 15.6)], fill=(60, 200, 120))
    plan.d.text(plan.p(0, 16.7), "arrivee", fill="white", font=police(12), anchor="mm")
    sc = [trimesh.load(os.path.join(ETAGE, f), force="scene") for f in sorted(os.listdir(ETAGE))
          if f.startswith("Etage") and f.endswith(".glb") and "TOUT" not in f and "Lustres" not in f]
    for s in sc:
        for g in s.geometry.values():
            g.apply_translation([0, -UP, 0])
    plan.coller(vue_dessus(sc, z0, z1, -3.4, 3.4, 2.4))
    for z in (17.9, 7.35, 2.6, -2.75):                                # lustres : cercle pointille
        cx, cy = plan.p(0, z)
        r = 0.42 * PX
        for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            plan.d.arc([cx - r, cy - r, cx + r, cy + r], np.degrees(a), np.degrees(a) + 7, fill=OR, width=3)
    for num, nom, prix, c, b in OBJETS_ETAGE:
        plan.bouton(b[0], b[1], num)
    for num, nom, prix, c, b in OBJETS_ETAGE:
        plan.pastille(c[0], c[1], num, OR if num == "10" else VERT)
    plan.fleche_avant()
    legende(plan, [(n, nom, prix, OR if n == "10" else VERT) for n, nom, prix, _, _ in OBJETS_ETAGE],
            plan.ml, plan.H - plan.mb + 30)
    plan.d.text((plan.ml + 1300, plan.H - plan.mb + 40), "Ordre d'achat conseille :", fill=(30, 40, 35), font=police(20))
    ordre = "11 > 10 > 01 > 03 > 02 > 05 > 04 > 07 > 08 > 09 > 06"
    plan.d.text((plan.ml + 1300, plan.H - plan.mb + 75), ordre, fill=VERT, font=police(20))
    plan.d.text((plan.ml + 1300, plan.H - plan.mb + 120),
                "Les lustres (10) sont au plafond :\ncercles dores pointilles.", fill=(70, 90, 80), font=police(18, False))
    plan.im.save(os.path.join(PLANS, "plan_etage.png"))


# ------------------------------------------------------------------ zone First : 8 suites placees
Z_RANGEES = (-8.215, -5.845)            # centre des suites (2 rangees), glTF ; avant de la zone First : -9.45
SUITES = [(-2.75, "droite"), (-0.645, "gauche"), (0.645, "droite"), (2.75, "gauche")]


def suites_placees():
    sc = trimesh.Scene()
    n = 0
    for z in Z_RANGEES:
        for x, cote in SUITES:
            n += 1
            s = trimesh.load(os.path.join(HERE, f"suite_first_{cote}.glb"), force="scene")
            for node in s.graph.nodes_geometry:
                T, g = s.graph[node]
                m = s.geometry[g].copy()
                m.apply_transform(T)
                m.apply_translation([x, 0.0, z])
                sc.add_geometry(m, node_name=f"Suite{n}_{node}", geom_name=f"Suite{n}_{g}")
    sc.export(os.path.join(ETAGE, "First_8_Suites_Avion3_4.glb"))
    return sc


def plan_first(sc):
    z0, z1 = -9.45, -3.09
    plan = Plan(z0 - 0.3, z1 + 0.3, 4.0, marge=(110, 130, 640, 110))
    plan.titre("AVIONS 3 ET 4 (EN BAS) : ZONE FIRST",
               "8 suites en 1 | 2 | 1. L'avant a gauche, 1 carreau = 1 m. Porte de chaque suite cote allee.")
    import generate_cabin as G
    coque(plan, z0, z1, 3.55, 3.79, [-(G.CABIN[0] + G.MARGIN + i * G.PITCH) for i in range(80)
                                     if z0 < -(G.CABIN[0] + G.MARGIN + i * G.PITCH) < z1])
    for s in (-1, 1):                                                  # passages de la cloison Business / First
        plan.rect(s * 1.35 - 0.45, s * 1.35 + 0.45, z1 - 0.05, z1 + 0.05, fill=FOND)
    plan.coller(vue_dessus([sc], plan.z0, plan.z1, -4.0, 4.0, 2.0))
    n = 0
    for z in Z_RANGEES:
        for x, cote in SUITES:
            n += 1
            plan.pastille(x, z + 0.3, str(n))
            cx, cy = plan.p(x, z - 0.55)
            plan.d.text((cx, cy), cote.upper(), fill="white", font=police(11), anchor="mm",
                        stroke_width=2, stroke_fill=(20, 60, 40))
    for s in (-1, 1):
        cx, cy = plan.p(s * 1.70, -3.6)
        plan.d.text((cx, cy), "ALLEE", fill=(70, 90, 80), font=police(13), anchor="mm")
    cx, cy = plan.p(0, z1 + 0.3)
    plan.d.text((cx + 12, cy), "vers la\nBusiness", fill=(70, 90, 80), font=police(13), anchor="lm")
    plan.fleche_avant()
    x0 = plan.W - plan.mr + 110
    lignes = ["Fichier tout pret :", "First_8_Suites_Avion3_4.glb", "-> meme position que l'avion,", "   les 8 suites sont en place.",
              "", "Ou un par un :", "x = -2,75  suite DROITE", "x = -0,65  suite GAUCHE", "x = +0,65  suite DROITE",
              "x = +2,75  suite GAUCHE", "rangee 1 : z = -8,2 m", "rangee 2 : z = -5,8 m", "(par rapport a l'avion)"]
    for i, t in enumerate(lignes):
        plan.d.text((x0, plan.mh + i * 30), t, fill=VERT if i in (0, 5) else (40, 50, 45), font=police(17, i in (0, 1, 5)))
    plan.d.text((plan.ml, plan.H - plan.mb + 30), "Chaque suite s'achete une par une, apres les sieges Business.",
                fill=(30, 40, 35), font=police(18))
    plan.im.save(os.path.join(PLANS, "plan_first.png"))


if __name__ == "__main__":
    os.makedirs(PLANS, exist_ok=True)
    plan_etage()
    plan_first(suites_placees())
    print("plans ecrits dans", PLANS)
