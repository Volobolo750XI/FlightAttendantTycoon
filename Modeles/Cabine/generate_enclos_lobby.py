"""ENCLOS DU LOBBY, theme aeroport (comme Infinity Tower Tycoon, mais a l'aeroport).
Dedans : une grande pelouse fermee par un grillage d'aeroport (on ne peut pas sortir).
Dehors (decor) : la piste d'atterrissage, le terminal avec des avions gares, la tour de controle, des hangars.
La plateforme de spawn (Plateforme_Spawn.glb) se pose au centre (0, 0, 0).
Chaque element est un objet separe. Origine : centre de l'enclos, au sol. Y en haut, 1 unite = 1 m.
Sortie : Modeles/Lobby/Enclos_Aeroport.glb     Usage : python3 generate_enclos_lobby.py
"""
import math
import os

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import Point, Polygon
from trimesh.transformations import rotation_matrix, translation_matrix

import generate_avion_decor as AV
import generate_vehicules_aeroport as VE

HERE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(os.path.dirname(HERE), "Lobby", "Enclos_Aeroport.glb")
DEMI = 60.0          # enclos de 120 x 120 m
H_GRILLE = 3.2
rng = np.random.default_rng(11)
PBR = trimesh.visual.material.PBRMaterial


# ------------------------------------------------------------------ textures
def bruit(img, s):
    a = np.asarray(img).astype(np.int16)
    a[..., :3] += rng.normal(0, s, a.shape[:2] + (1,)).astype(np.int16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def tex_pelouse():
    n = 512
    img = Image.new("RGB", (n, n))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, n // 2, n], fill=(98, 190, 72))      # bandes de tonte
    d.rectangle([n // 2, 0, n, n], fill=(86, 176, 64))
    return bruit(img, 6).filter(ImageFilter.GaussianBlur(1.0))


def tex_uni(rgb, s=5, n=256):
    return bruit(Image.new("RGB", (n, n), rgb), s).filter(ImageFilter.GaussianBlur(0.8))


def tex_grillage():
    n = 128
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = (70, 76, 86, 255)
    for k in (-n, 0, n):
        d.line([(k, 0), (k + n, n)], fill=c, width=7)
        d.line([(k + n, 0), (k, n)], fill=c, width=7)
    return img


def tex_vitres():
    n = 256
    img = Image.new("RGB", (n, n), (235, 240, 245))
    d = ImageDraw.Draw(img)
    for i in range(2):
        for j in range(2):
            x0, y0 = i * 128 + 8, j * 128 + 8
            for y in range(y0, y0 + 112):
                t = (y - y0) / 112
                d.line([(x0, y), (x0 + 112, y)], fill=(int(90 + 70 * t), int(170 + 40 * t), int(225 + 20 * t)))
            d.line([(x0 + 20, y0 + 90), (x0 + 60, y0 + 20)], fill=(205, 235, 250), width=6)    # reflet
    return img


M = {
    "pelouse": PBR(name="Pelouse", baseColorTexture=tex_pelouse(), roughnessFactor=0.95, metallicFactor=0.0),
    "tarmac": PBR(name="Tarmac", baseColorTexture=tex_uni((120, 124, 132), 6), roughnessFactor=0.9, metallicFactor=0.0),
    "piste": PBR(name="Piste", baseColorTexture=tex_uni((62, 66, 74), 6), roughnessFactor=0.9, metallicFactor=0.0),
    "grillage": PBR(name="Grillage", baseColorTexture=tex_grillage(), alphaMode="MASK", alphaCutoff=0.5,
                    doubleSided=True, roughnessFactor=0.6, metallicFactor=0.3),
    "vitres": PBR(name="VitresTerminal", baseColorTexture=tex_vitres(), roughnessFactor=0.15, metallicFactor=0.1),
}


def col(nom, rgb, rugo=0.7, em=None):
    return PBR(name=nom, baseColorFactor=[*rgb, 255], roughnessFactor=rugo, metallicFactor=0.0,
               emissiveFactor=em)


M.update({
    "blanc": col("BlancCartoon", (244, 246, 248), 0.5),
    "beton": col("Beton", (196, 200, 206), 0.85),
    "poteau": col("PoteauGris", (150, 156, 166), 0.5),
    "vert": col("VertArgent", (40, 185, 100), 0.45),
    "vert_fonce": col("VertFonce", (22, 120, 66), 0.5),
    "sombre": col("ContourSombre", (36, 42, 58), 0.6),
    "marquage": col("MarquageBlanc", (250, 250, 250), 0.6),
    "feu_blanc": col("FeuBlanc", (255, 255, 255), 0.3, [1.0, 1.0, 1.0]),
    "feu_vert": col("FeuVert", (90, 255, 140), 0.3, [0.3, 1.0, 0.5]),
    "feu_rouge": col("FeuRouge", (255, 70, 70), 0.3, [1.0, 0.25, 0.25]),
    "hublot": col("Hublot", (40, 60, 90), 0.1),
    "orange": col("ManchetteOrange", (255, 110, 50), 0.6),
    "haie": col("Haie", (52, 150, 62), 0.9),
    "feuillage": col("Feuillage", (70, 178, 74), 0.9),
    "feuillage_fonce": col("FeuillageFonce", (46, 140, 58), 0.9),
    "tronc": col("Tronc", (120, 82, 56), 0.9),
})


# ------------------------------------------------------------------ geometrie
def uv_monde(m, tuile):
    m = m.copy()
    m.unmerge_vertices()
    v, n = m.vertices, m.face_normals
    uv = np.zeros((len(v), 2))
    for fi, f in enumerate(m.faces):
        ax = np.argmax(np.abs(n[fi]))
        p = v[f]
        uv[f] = np.c_[p[:, 2], p[:, 1]] if ax == 0 else (np.c_[p[:, 0], p[:, 2]] if ax == 1 else np.c_[p[:, 0], p[:, 1]])
    uv /= tuile
    return m, uv


class Objets:
    def __init__(self):
        self.sc = trimesh.Scene()
        self.parts = {}
        self.ordre = []

    def add(self, objet, k, m, tuile=None):
        if m.is_watertight and m.volume < 0:                 # securite : faces toujours tournees vers l'exterieur
            m.invert()
        if objet not in self.parts:
            self.parts[objet] = {}
            self.ordre.append(objet)
        self.parts[objet].setdefault((k, tuile), []).append(m)

    def exporter(self, chemin):
        for o in self.ordre:
            for (k, tuile), ms in self.parts[o].items():
                m = trimesh.util.concatenate(ms)
                mat = M[k]
                if tuile:
                    m, uv = uv_monde(m, tuile)
                    m.visual = trimesh.visual.TextureVisuals(uv=uv, material=mat)
                elif k in TEXTURES_PROPRES:
                    m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([x.visual.uv for x in ms]), material=mat)
                else:
                    m.visual = trimesh.visual.TextureVisuals(material=mat)
                self.sc.add_geometry(m, node_name=f"{o}__{k}", geom_name=f"{o}__{k}")
        self.sc.export(chemin)
        # regroupe les primitives par objet (un noeud = un objet)
        import json
        import struct
        b = open(chemin, "rb").read()
        lj = struct.unpack("<I", b[12:16])[0]
        js = json.loads(b[20:20 + lj])
        rest = b[20 + lj:]
        nouveaux_mesh, nouveaux_noeuds, index = [], [], {}
        for nd in js["nodes"]:
            if "mesh" not in nd:
                continue
            o = nd["name"].split("__")[0]
            if o not in index:
                index[o] = len(nouveaux_mesh)
                nouveaux_mesh.append({"name": o, "primitives": []})
                nouveaux_noeuds.append({"name": o, "mesh": index[o]})
            nouveaux_mesh[index[o]]["primitives"] += js["meshes"][nd["mesh"]]["primitives"]
        js["meshes"] = nouveaux_mesh
        js["nodes"] = nouveaux_noeuds
        js["scenes"] = [{"nodes": list(range(len(nouveaux_noeuds)))}]
        js["scene"] = 0
        s = json.dumps(js, separators=(",", ":")).encode()
        s += b" " * ((4 - len(s) % 4) % 4)
        out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(s) + len(rest)) + struct.pack("<II", len(s), 0x4E4F534A) + s + rest
        open(chemin, "wb").write(out)
        return self.ordre


def boite(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box((x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def cyl(r, h, x, y, z, sections=24):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    m.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([x, y + h / 2, z])
    return m


def tronc_cone(r0, r1, h, x, y, z, sections=48):
    a = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    bas = np.c_[r0 * np.cos(a), np.zeros(sections), r0 * np.sin(a)]
    haut = np.c_[r1 * np.cos(a), np.full(sections, h), r1 * np.sin(a)]
    m = trimesh.convex.convex_hull(np.vstack([bas, haut]))
    m.apply_translation([x, y, z])
    return m


def extrusion(poly, y0, y1):
    if hasattr(poly, "geoms"):
        return trimesh.util.concatenate([extrusion(p, y0, y1) for p in poly.geoms if p.area > 0.01])
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_transform(np.diag([1, 1, -1, 1]))                # (x, y) du plan -> (x, z) du monde
    m.invert()
    m.apply_translation([0, y0, 0])
    return m


def quad(p0, p1, h, y0=0.0):
    """panneau vertical de p0 a p1 (x, z), hauteur h, deux faces, UV en metres"""
    (x0, z0), (x1, z1) = p0, p1
    v = np.array([[x0, y0, z0], [x1, y0, z1], [x1, y0 + h, z1], [x0, y0 + h, z0]])
    L = math.hypot(x1 - x0, z1 - z0)
    m = trimesh.Trimesh(v, [[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]], process=False)
    return m, np.array([[0, 0], [L, 0], [L, h], [0, h]])


# ------------------------------------------------------------------ elements
M.update(AV.MATERIAUX)
M.update(VE.MATERIAUX)


def tex_peinture(txt, w=512, h=512, taille=420):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((w / 2, h / 2), txt, font=ImageFont.truetype(VE.POLICE, taille), fill=(250, 250, 250, 255),
                             anchor="mm")
    return img


def mat_texte(nom, txt, fond, encre, w=1024, h=256, taille=150, em=None):
    return PBR(name=nom, baseColorTexture=VE.tex_texte(txt, fond, encre, w, h, taille), roughnessFactor=0.5,
               metallicFactor=0.0, emissiveFactor=em)


M.update({
    "num_09": PBR(name="PisteNum09", baseColorTexture=tex_peinture("09"), alphaMode="MASK", alphaCutoff=0.5,
                  roughnessFactor=0.7, metallicFactor=0.0),
    "num_27": PBR(name="PisteNum27", baseColorTexture=tex_peinture("27"), alphaMode="MASK", alphaCutoff=0.5,
                  roughnessFactor=0.7, metallicFactor=0.0),
    "pan_restreint": mat_texte("PanneauZoneReservee", "RESTRICTED AREA", (225, 45, 45), (255, 255, 255), taille=120),
    "pan_0927": mat_texte("PanneauPiste0927", "09 - 27", (225, 45, 45), (255, 255, 255), 512, 256, 150, [0.3, 0.1, 0.1]),
    "pan_a": mat_texte("PanneauTaxiA", "A", (30, 34, 44), (255, 255, 255), 256, 256, 180, [0.15, 0.15, 0.15]),
    "pan_b": mat_texte("PanneauTaxiB", "B", (30, 34, 44), (255, 255, 255), 256, 256, 180, [0.15, 0.15, 0.15]),
    "pan_gates": mat_texte("PanneauGates", "GATES 1-3", (30, 170, 90), (255, 255, 255), 1024, 256, 140, [0.1, 0.25, 0.15]),
    "pan_pompiers": mat_texte("PanneauPompiers", "FIRE STATION", (225, 45, 45), (255, 255, 255), 1024, 256, 130),
    "pan_cargo": mat_texte("PanneauCargo", "CARGO", (30, 170, 90), (255, 255, 255), 1024, 256, 170),
    "pan_parking": mat_texte("PanneauParking", "P  PARKING", (40, 110, 220), (255, 255, 255), 1024, 256, 150, [0.1, 0.15, 0.3]),
    "pan_hotel": mat_texte("PanneauHotel", "HOTEL", (30, 170, 90), (255, 255, 255), 1024, 256, 180, [0.1, 0.3, 0.15]),
    "rouge_bat": col("BatimentRouge", (215, 55, 50), 0.6),
    "porte_garage": col("PorteGarage", (225, 230, 236), 0.5),
})
TEXTURES_PROPRES = {"av_logo", "ve_fuel", "ve_followme", "num_09", "num_27", "pan_restreint", "pan_0927", "pan_a",
                    "pan_b", "pan_gates", "pan_pompiers", "pan_cargo", "pan_parking", "pan_hotel"}


def ajouter(O, nom, P):
    for k, ms in P.items():
        for m in ms:
            O.add(nom, k, m, 1.5 if k == "ve_damier" else None)


def panneau(O, nom, k, x, y, z, w, h, cap, double=True, uv_ok=True):
    """panneau texte vertical centre en (x,y,z), face vers -Z avant rotation cap"""
    m = trimesh.Trimesh([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]],
                        [[0, 2, 1], [0, 3, 2]], process=False)
    uv = np.array([[1, 0], [0, 0], [0, 1], [1, 1]])          # lu a l'endroit depuis -Z
    T = translation_matrix([x, y, z]) @ rotation_matrix(math.radians(cap), [0, 1, 0])
    for sens in ((1, -1) if double else (1,)):
        q = m.copy()
        if sens < 0:
            q.apply_transform(rotation_matrix(np.pi, [0, 1, 0]))
            q.apply_translation([0, 0, 0.06])
        q.apply_translation([0, 0, -0.03])
        q.apply_transform(T)
        q.visual = trimesh.visual.TextureVisuals(uv=uv.copy(), material=M[k])
        O.add(nom, k, q)
M.update({
    "facade_a": PBR(name="FacadeVitreeBleue", baseColorTexture=tex_vitres(), roughnessFactor=0.2, metallicFactor=0.1),
    "facade_b": col("FacadeBlanche", (232, 236, 240), 0.6),
    "facade_c": col("FacadeVertEau", (120, 200, 170), 0.6),
    "toit": col("ToitGris", (110, 116, 126), 0.8),
    "colline": col("Colline", (92, 176, 84), 0.95),
    "colline_fonce": col("CollineFonce", (70, 150, 72), 0.95),
    "montagne": col("MontagneLointaine", (120, 160, 150), 0.95),
})
AV.RES = 0.45                                                # avions du decor en version legere
AVION = AV.parts(True)
AVION_VOL = AV.parts(False)


def avion_ligne(O, nom, x, z, cap, alt=0.0, tangage=0.0, ech=1.0, train=None):
    T = translation_matrix([x, alt, z]) @ rotation_matrix(math.radians(cap), [0, 1, 0]) @ \
        rotation_matrix(math.radians(tangage), [1, 0, 0]) @ np.diag([ech, ech, ech, 1])
    for k, ms in (AVION if (alt == 0 if train is None else train) else AVION_VOL).items():
        for m in ms:
            m = m.copy()
            m.apply_transform(T)
            O.add(nom, k, m)


def horizon(O):
    """tout autour, au loin : une ville (immeubles), des collines puis des montagnes -> on ne voit jamais le vide"""
    O.add("Sol_Lointain", "pelouse", extrusion(Polygon([(-1000, -1000), (1000, -1000), (1000, 1000), (-1000, 1000)]).difference(
        Polygon([(-260, -260), (260, -260), (260, 260), (-260, 260)])), -0.14, -0.04), 12.0)
    r = np.random.default_rng(5)
    i = 0
    for ang in np.arange(0, 360, 6.0):
        a = math.radians(ang + r.uniform(-1.2, 1.2))
        for rang, (r0, h0, h1) in enumerate(((430, 18, 45), (480, 30, 75))):
            if rang == 1 and r.random() < 0.35:
                continue
            rr = r0 + r.uniform(-10, 10)
            x, z = rr * math.cos(a), rr * math.sin(a)
            w, d, h = r.uniform(16, 26), r.uniform(16, 26), r.uniform(h0, h1)
            k = ("facade_a", "facade_b", "facade_c", "facade_a")[r.integers(4)]
            b = trimesh.creation.box((w, h, d))
            b.apply_transform(rotation_matrix(-a, [0, 1, 0]))
            b.apply_translation([x, h / 2, z])
            nom = f"Ville_{(i // 20) + 1:02d}"
            O.add(nom, k, b, 6.0 if k == "facade_a" else None)
            t = trimesh.creation.box((w + 0.8, 1.2, d + 0.8))
            t.apply_transform(rotation_matrix(-a, [0, 1, 0]))
            t.apply_translation([x, h + 0.6, z])
            O.add(nom, "toit", t)
            if k != "facade_a":                                   # bandes de fenetres sur les facades pleines
                for y in np.arange(4, h - 2, 4):
                    f = trimesh.creation.box((w + 0.2, 1.4, d + 0.2))
                    f.apply_transform(rotation_matrix(-a, [0, 1, 0]))
                    f.apply_translation([x, y, z])
                    O.add(nom, "facade_a", f, 6.0)
            i += 1
    for ang in np.arange(0, 360, 9):                               # collines vertes
        a = math.radians(ang + r.uniform(-3, 3))
        rr = 590 + r.uniform(-25, 25)
        c = trimesh.creation.icosphere(2, 1.0)
        c.apply_scale([r.uniform(70, 110), r.uniform(45, 85), r.uniform(50, 70)])
        c.apply_transform(rotation_matrix(-a, [0, 1, 0]))
        c.apply_translation([rr * math.cos(a), -10, rr * math.sin(a)])
        O.add("Collines", "colline" if int(ang / 9) % 2 else "colline_fonce", c)
    for ang in np.arange(0, 360, 14):                              # montagnes bleutees tout au fond
        a = math.radians(ang + r.uniform(-4, 4))
        rr = 820 + r.uniform(-30, 30)
        m = trimesh.creation.cone(radius=r.uniform(110, 160), height=r.uniform(130, 210), sections=7)
        m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
        m.apply_transform(rotation_matrix(r.uniform(0, 6), [0, 1, 0]))
        m.apply_translation([rr * math.cos(a), -5, rr * math.sin(a)])
        O.add("Montagnes", "montagne", m)


def sols(O):
    O.add("Sol_Pelouse", "pelouse", boite(-DEMI, -0.1, -DEMI, DEMI, 0.0, DEMI), 12.0)
    dehors = Polygon([(-260, -260), (260, -260), (260, 260), (-260, 260)]).difference(
        Polygon([(-DEMI, -DEMI), (DEMI, -DEMI), (DEMI, DEMI), (-DEMI, DEMI)]))
    from shapely.ops import unary_union
    from shapely.geometry import box as rect
    tar = unary_union([rect(-115, 66, 115, 150),            # parking avions devant le terminal
                       rect(-150, -50, -64, 50),             # devant les hangars
                       rect(-150, -78, -130, 150),           # taxiway ouest vers la piste
                       rect(64, -78, 84, 150),               # taxiway est
                       Point(95, -40).buffer(12, 48)])       # pied de la tour
    # sol simple et robuste : une grande dalle d'herbe dessous, des dalles de tarmac simples par-dessus
    for r_ in (rect(-115, 66, 115, 150), rect(-150, -50, -64, 50), rect(-150, -78, -130, 150), rect(64, -78, 84, 150),
               Point(95, -40).buffer(12, 48), rect(84, 0, 135, 50), rect(-64, -50, -61, 50)):
        O.add("Sol_Tarmac", "tarmac", extrusion(r_, -0.06, -0.01), 8.0)
    O.add("Sol_Herbe_Dehors", "pelouse", extrusion(dehors, -0.12, -0.03), 12.0)
    for x in np.arange(-110, 111, 6):                        # ligne de guidage du parking
        O.add("Sol_Tarmac", "marquage", boite(x, -0.01, 71.6, x + 3, 0.0, 72.0))
    for z in np.arange(-74, 148, 6):
        for xc in (-140, 74):
            O.add("Sol_Tarmac", "marquage", boite(xc - 0.2, -0.01, z, xc + 0.2, 0.0, z + 3))


def grillage(O):
    pas = 4.0
    coins = [(-DEMI, -DEMI), (DEMI, -DEMI), (DEMI, DEMI), (-DEMI, DEMI)]
    panneaux, uvs = [], []
    for c in range(4):
        (xa, za), (xb, zb) = coins[c], coins[(c + 1) % 4]
        L = math.hypot(xb - xa, zb - za)
        n = int(round(L / pas))
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            p0 = (xa + (xb - xa) * t0, za + (zb - za) * t0)
            p1 = (xa + (xb - xa) * t1, za + (zb - za) * t1)
            m, uv = quad(p0, p1, H_GRILLE - 0.35, 0.35)
            panneaux.append((m, uv / 0.5))
            O.add("Grillage_Poteaux", "poteau", cyl(0.07, H_GRILLE + 0.3, p0[0], 0.0, p0[1], 12))
            O.add("Grillage_Poteaux", "vert", cyl(0.1, 0.12, p0[0], H_GRILLE + 0.3, p0[1], 12))
        # rail du haut + muret beton bas
        dx, dz = (xb - xa) / L, (zb - za) / L
        rail = trimesh.creation.cylinder(radius=0.05, height=L, sections=10)
        rail.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], [dx, 0, dz]))
        rail.apply_translation([(xa + xb) / 2, H_GRILLE, (za + zb) / 2])
        O.add("Grillage_Poteaux", "poteau", rail)
        ex, ez = abs(dz) * 0.15, abs(dx) * 0.15
        O.add("Grillage_Muret", "beton", boite(min(xa, xb) - ex - 0.15, 0.0, min(za, zb) - ez - 0.15,
                                               max(xa, xb) + ex + 0.15, 0.35, max(za, zb) + ez + 0.15))
        O.add("Grillage_Muret", "vert", boite(min(xa, xb) - ex - 0.16, 0.28, min(za, zb) - ez - 0.16,
                                              max(xa, xb) + ex + 0.16, 0.35, max(za, zb) + ez + 0.16))
    m = trimesh.util.concatenate([p for p, _ in panneaux])
    m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([u for _, u in panneaux]), material=M["grillage"])
    O.sc.add_geometry(m, node_name="Grillage__grillage", geom_name="Grillage__grillage")


def piste(O):
    z0, z1, x0, x1 = -125.0, -80.0, -240.0, 240.0          # au nord, derriere le grillage
    zc = (z0 + z1) / 2
    O.add("Piste", "piste", boite(x0, -0.02, z0, x1, 0.02, z1), 10.0)
    for x in np.arange(x0 + 50, x1 - 50, 24):              # ligne centrale en tirets
        O.add("Piste", "marquage", boite(x, 0.02, zc - 0.5, x + 12, 0.04, zc + 0.5))
    for z in (z0 + 1.5, z1 - 1.5):                          # lignes de bord
        O.add("Piste", "marquage", boite(x0 + 4, 0.02, z - 0.4, x1 - 4, 0.04, z + 0.4))
    for xs, sgn in ((x0 + 6, 1), (x1 - 6, -1)):            # "piano" de seuil + zones de toucher
        for k in range(-5, 6):
            if k == 0:
                continue
            z = zc + k * 3.4
            O.add("Piste", "marquage", boite(min(xs, xs + sgn * 30), 0.02, z - 1.0, max(xs, xs + sgn * 30), 0.04, z + 1.0))
        for k in (-1, 1):
            xa = xs + sgn * 70
            O.add("Piste", "marquage", boite(min(xa, xa + sgn * 22), 0.02, zc + k * 7 - 1.6, max(xa, xa + sgn * 22), 0.04, zc + k * 7 + 1.6))
    for x in np.arange(x0 + 4, x1, 15):                     # feux de bord
        for z in (z0 + 0.4, z1 - 0.4):
            O.add("Piste_Feux", "poteau", cyl(0.12, 0.3, x, 0.0, z, 8))
            O.add("Piste_Feux", "feu_blanc", trimesh.creation.icosphere(1, 0.22).apply_translation([x, 0.42, z]))
    for xs, k in ((x0 + 2, "feu_vert"), (x1 - 2, "feu_rouge")):
        for z in np.arange(z0 + 3, z1 - 2, 3):
            O.add("Piste_Feux", k, trimesh.creation.icosphere(1, 0.25).apply_translation([xs, 0.3, z]))


def avion(O, nom, x, z, cap, s=3.0, alt=0.0, tangage=0.0):
    """avion cartoon (blanc + vert argent), nez vers -Z avant rotation de cap degres"""
    R = rotation_matrix(math.radians(cap), [0, 1, 0]) @ rotation_matrix(math.radians(tangage), [1, 0, 0])

    def T(m):
        m.apply_transform(R)
        m.apply_translation([x, alt, z])
        O.add(nom, k_courant[0], m)

    k_courant = ["blanc"]

    def put(k, m):
        k_courant[0] = k
        T(m)

    y = 1.15 * s
    fus = trimesh.creation.capsule(height=6.0 * s, radius=0.9 * s, count=[32, 24])
    fus.apply_translation([0, y, 0])
    put("blanc", fus)
    b = trimesh.creation.cylinder(radius=0.915 * s, height=6.0 * s, sections=48)
    b.apply_scale([1, 0.18, 1])
    b.apply_translation([0, y - 0.25 * s, 0])
    put("vert", b)

    def aile(points, ep, yy, k):
        m = trimesh.creation.extrude_polygon(Polygon(points), ep)
        m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
        m.apply_transform(np.diag([1, 1, -1, 1]))
        m.invert()
        m.apply_translation([0, yy, 0])
        put(k, m)
    aile([(0, -1.2 * s), (4.6 * s, 0.9 * s), (4.6 * s, 1.5 * s), (0, 1.0 * s), (-4.6 * s, 1.5 * s), (-4.6 * s, 0.9 * s)],
         0.22 * s, y - 0.45 * s, "blanc")
    aile([(0, 3.2 * s), (1.9 * s, 4.0 * s), (1.9 * s, 4.35 * s), (0, 4.1 * s), (-1.9 * s, 4.35 * s), (-1.9 * s, 4.0 * s)],
         0.16 * s, y + 0.2 * s, "vert")
    der = trimesh.creation.extrude_polygon(Polygon([(2.9 * s, 0), (4.3 * s, 0), (4.5 * s, 2.1 * s), (3.9 * s, 2.1 * s)]), 0.2 * s)
    der.apply_transform(rotation_matrix(-np.pi / 2, [0, 1, 0]))
    der.apply_translation([0.1 * s, y + 0.4 * s, 0])
    put("vert", der)
    for xx in (-2.3, 2.3):
        r = trimesh.creation.capsule(height=1.1 * s, radius=0.42 * s, count=[16, 12])
        r.apply_translation([xx * s, y - 0.85 * s, -0.4 * s])
        put("vert", r)
        e = trimesh.creation.cylinder(radius=0.3 * s, height=0.05 * s, sections=24)
        e.apply_translation([xx * s, y - 0.85 * s, -1.38 * s])
        put("sombre", e)
    for zz in np.arange(-2.3, 2.4, 0.5):
        for xx in (-1, 1):
            h = trimesh.creation.icosphere(2, 0.17 * s)
            h.apply_scale([0.35, 1.0, 1.0])
            h.apply_translation([xx * 0.89 * s, y + 0.2 * s, zz * s])
            put("hublot", h)
    pare = trimesh.creation.icosphere(2, 0.55 * s)
    pare.apply_scale([1.1, 0.42, 0.65])
    pare.apply_translation([0, y + 0.42 * s, -3.15 * s])
    put("hublot", pare)
    for zz, xx in (((-2.6, 0), (0.4, -1.0), (0.4, 1.0)) if alt == 0 else ()):     # train d'atterrissage
        put("sombre", cyl(0.12 * s, y - 0.35 * s, xx * s, 0.35 * s, zz * s, 10))
        roue = trimesh.creation.cylinder(radius=0.35 * s, height=0.3 * s, sections=20)
        roue.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
        roue.apply_translation([xx * s, 0.35 * s, zz * s])
        put("sombre", roue)


def terminal(O):
    z0, z1, x0, x1, H = 108.0, 138.0, -95.0, 95.0, 15.0     # au sud
    O.add("Terminal", "beton", boite(x0, 0, z0 + 2, x1, 1.0, z1))
    O.add("Terminal", "vitres", boite(x0 + 1, 1.0, z0 + 2, x1 - 1, H - 1.5, z1 - 2), 4.0)
    for x in np.arange(x0 + 1, x1, 16):                     # piliers blancs
        O.add("Terminal", "blanc", boite(x - 0.5, 1.0, z0 + 1.6, x + 0.5, H - 1.5, z0 + 2.6))
    O.add("Terminal", "vert", boite(x0, H - 1.5, z0 + 1.5, x1, H - 0.4, z1))   # bandeau vert
    # toit en vague (arc)
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        z = z0 - 4 + (z1 - z0 + 8) * t
        pts.append((z, H - 0.4 + 3.2 * math.sin(math.pi * t)))
    prof = Polygon(pts + [(p[0], p[1] + 0.8) for p in reversed(pts)][:1] +
                   [(p[0], p[1] + 0.8) for p in reversed(pts)][1:])
    toit = trimesh.creation.extrude_polygon(prof, x1 - x0 + 8)
    toit.apply_transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]))
    toit.invert()
    toit.apply_translation([x0 - 4, 0, 0])
    O.add("Terminal", "blanc", toit)
    # passerelles (jet bridges) vers les avions
    # lettres "AIRPORT" vertes sur le toit (blocs simples)
    lettres(O, "AIRPORT", 0.0, H + 3.6, z0 + 6, 5.0)


GLYPHES = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
}


def lettres(O, mot, xc, y0, z, h):
    px = h / 7
    larg = len(mot) * 6 * px - px
    x = xc + larg / 2                                        # vu depuis l'enclos (on regarde vers +Z), la droite est -X
    for ch in mot:
        g = GLYPHES[ch]
        for r, ligne in enumerate(g):
            for c, b in enumerate(ligne):
                if b == "1":
                    xa = x - (c + 1) * px
                    O.add("Terminal_Enseigne", "vert", boite(xa, y0 + (6 - r) * px, z, xa + px * 1.02, y0 + (7 - r) * px * 1.0, z + 0.6))
                    O.add("Terminal_Enseigne", "blanc", boite(xa - 0.08, y0 + (6 - r) * px - 0.08, z + 0.6, xa + px + 0.1, y0 + (7 - r) * px + 0.08, z + 0.9))
        x -= 6 * px
    O.add("Terminal_Enseigne", "poteau", boite(xc - larg / 2, y0 - 3.6, z + 0.2, xc + larg / 2, y0, z + 0.7))


def tour(O):
    x, z = 95.0, -40.0                                       # a l'est, pres de la piste
    O.add("Tour_Controle", "beton", cyl(6.0, 3.0, x, 0, z, 48))
    O.add("Tour_Controle", "blanc", tronc_cone(3.6, 2.8, 30.0, x, 3.0, z))
    for y in (10.0, 20.0):
        O.add("Tour_Controle", "vert", cyl(3.3 - y * 0.026, 0.8, x, y, z, 48))
    O.add("Tour_Controle", "blanc", tronc_cone(3.0, 6.0, 2.5, x, 33.0, z))
    O.add("Tour_Controle", "vitres", tronc_cone(6.0, 6.8, 4.5, x, 35.5, z), 4.0)
    O.add("Tour_Controle", "vert", tronc_cone(7.2, 3.5, 1.8, x, 40.0, z))
    O.add("Tour_Controle", "poteau", cyl(0.15, 6.0, x, 41.8, z, 8))
    O.add("Tour_Controle", "feu_rouge", trimesh.creation.icosphere(1, 0.4).apply_translation([x, 48.0, z]))
    r = trimesh.creation.icosphere(2, 1.6)                   # radar
    r.apply_scale([1, 0.5, 1])
    r.apply_translation([x + 2.5, 42.6, z])
    O.add("Tour_Controle", "blanc", r)


def hangars(O):
    for i, zc in enumerate((-25.0, 25.0)):                  # a l'ouest
        x0, x1, r = -125.0, -90.0, 17.0
        nom = f"Hangar_{i + 1}"
        a = np.linspace(0, np.pi, 33)
        arc = [(zc + r * math.cos(t), 0.9 * r * math.sin(t)) for t in a]
        coque = Polygon([(zc - r, 0)] + [(p[0], p[1]) for p in reversed(arc)] + [(zc + r, 0)])
        m = trimesh.creation.extrude_polygon(coque, x1 - x0)
        m.apply_transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]))
        m.invert()
        m.apply_translation([x0, 0, 0])
        O.add(nom, "blanc", m)
        # grande porte verte avec bandes, face a l'enclos (+X)
        porte = Polygon([(zc - r * 0.75, 0)] + [(zc + r * 0.75 * math.cos(t), 0.9 * r * 0.75 * math.sin(t))
                                                for t in np.linspace(np.pi, 0, 25)] + [(zc + r * 0.75, 0)])
        p = trimesh.creation.extrude_polygon(porte.buffer(0), 0.3)
        p.apply_transform(np.array([[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]))
        p.invert()
        p.apply_translation([x1, 0, 0])
        O.add(nom, "vert", p)
        for k in range(1, 6):
            zz = zc - r * 0.75 + k * (1.5 * r * 0.75 / 6)
            hmax = 0.9 * r * 0.75 * math.sqrt(max(0, 1 - ((zz - zc) / (r * 0.75)) ** 2))
            O.add(nom, "vert_fonce", boite(x1 + 0.3, 0, zz - 0.15, x1 + 0.45, hmax - 0.3, zz + 0.15))
        lettres_bloc = boite(x1 + 0.05, 0.9 * r * 0.95, zc - 3, x1 + 0.4, 0.9 * r * 0.95 + 0.6, zc + 3)
        O.add(nom, "vert", lettres_bloc)


def manche_a_air(O):
    x, z = 40.0, -48.0                                       # pres d un coin de l'enclos
    O.add("Manche_A_Air", "poteau", cyl(0.12, 7.0, x, 0, z, 12))
    O.add("Manche_A_Air", "beton", cyl(0.6, 0.3, x, 0, z, 24))
    for i in range(5):
        r0, r1 = 0.65 - i * 0.08, 0.65 - (i + 1) * 0.08
        c = tronc_cone(r0, r1, 0.9, 0, 0, 0, 20)
        c.apply_transform(rotation_matrix(-np.pi / 2, [0, 0, 1]))
        c.apply_transform(rotation_matrix(math.radians(10), [0, 0, 1]))
        c.apply_translation([x + 0.2 + i * 0.9, 6.5 - i * 0.16, z])
        O.add("Manche_A_Air", "orange" if i % 2 == 0 else "blanc", c)


def lampadaires(O):
    for x in (-DEMI + 3.4, DEMI - 3.4):
        for z in np.arange(-45, 46, 30):
            O.add("Lampadaires", "poteau", cyl(0.12, 6.0, x, 0, z, 12))
            sgn = 1 if x < 0 else -1
            O.add("Lampadaires", "poteau", boite(min(x, x + sgn * 1.4), 5.85, z - 0.08, max(x, x + sgn * 1.4), 6.0, z + 0.08))
            O.add("Lampadaires", "sombre", boite(x + sgn * 1.0, 5.6, z - 0.3, x + sgn * 1.7, 5.85, z + 0.3))
            O.add("Lampadaires", "feu_blanc", boite(x + sgn * 1.05, 5.55, z - 0.25, x + sgn * 1.65, 5.6, z + 0.25))


def haies(O):
    """haie bombee tout le long du grillage, cote interieur (comme Infinity Tower)"""
    for c in range(4):
        for t in np.arange(-DEMI + 1.6, DEMI - 1.5, 1.7):
            x, z = [(t, -DEMI + 1.6), (DEMI - 1.6, t), (t, DEMI - 1.6), (-DEMI + 1.6, t)][c]
            b = trimesh.creation.icosphere(1, 1.0)
            b.apply_scale([1.15 + rng.uniform(0, 0.2), 0.85 + rng.uniform(0, 0.25), 1.15 + rng.uniform(0, 0.2)])
            b.apply_translation([x, 0.55, z])
            O.add("Haies", "haie", b)
        O.add("Haies", "beton", boite(*[(-DEMI + 0.4, 0, -DEMI + 0.4, DEMI - 0.4, 0.25, -DEMI + 2.9),
                                         (DEMI - 2.9, 0, -DEMI + 0.4, DEMI - 0.4, 0.25, DEMI - 0.4),
                                         (-DEMI + 0.4, 0, DEMI - 2.9, DEMI - 0.4, 0.25, DEMI - 0.4),
                                         (-DEMI + 0.4, 0, -DEMI + 0.4, -DEMI + 2.9, 0.25, DEMI - 0.4)][c]))


def arbre(O, nom, x, z, h=1.0):
    O.add(nom, "tronc", tronc_cone(0.35 * h, 0.22 * h, 3.2 * h, x, 0, z, 12))
    for dx, dy, dz, r, k in ((0, 4.2, 0, 2.2, "feuillage"), (1.3, 3.6, 0.6, 1.5, "feuillage_fonce"),
                             (-1.2, 3.7, -0.5, 1.6, "feuillage_fonce"), (0.3, 5.4, -0.3, 1.5, "feuillage")):
        b = trimesh.creation.icosphere(2, r * h)
        b.apply_scale([1, 0.85, 1])
        b.apply_translation([x + dx * h, dy * h, z + dz * h])
        O.add(nom, k, b)


def arbres(O):
    pos = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * (DEMI - 7), sz * (DEMI - 7)
            pos += [(cx, cz, 1.3), (cx - sx * 7, cz, 1.0), (cx, cz - sz * 7, 1.0)]
    for a in (-30, 30):
        for x, z in ((a, -DEMI + 6), (-DEMI + 6, a), (DEMI - 6, a)):          # rien au sud : on voit les avions
            pos.append((x, z, 0.9))
    for i, (x, z, h) in enumerate(pos):
        if abs(x - 50) < 4 and abs(z + 50) < 4:
            continue
        arbre(O, f"Arbre_{i + 1:02d}", x, z, h)


def tube_entre(p0, p1, w, h):
    """boite de section w x h allant de p0 a p1 (x, y, z)"""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    L = np.linalg.norm(p1 - p0)
    b = trimesh.creation.box((w, h, L))
    d = (p1 - p0) / L
    b.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d))
    b.apply_translation((p0 + p1) / 2)
    return b


def passerelles(O, gates, z_avion):
    """vraies passerelles telescopiques : rotonde contre le terminal -> tunnel -> cabine collee a la porte avant gauche"""
    for i, xa in enumerate(gates):
        nom = f"Passerelle_{i + 1}"
        yp = 2.75                                                # plancher au niveau du seuil de porte
        rot = np.array([xa + 15.0, 0, 106.0])
        porte = np.array([xa + 2.3, 0, z_avion + 10.7])
        cab = porte + np.array([2.2, 0, 0])
        O.add(nom, "beton", cyl(2.0, yp + 3.4, rot[0], 0, rot[2], 24))
        O.add(nom, "vert", cyl(2.05, 0.5, rot[0], yp + 2.4, rot[2], 24))
        a = rot + [0, yp + 1.5, 0]
        b = cab + [0.6, yp + 1.5, 0]
        mid = a + (b - a) * 0.52
        O.add(nom, "beton", tube_entre(a, mid, 3.4, 3.0))                 # partie fixe
        O.add(nom, "blanc", tube_entre(mid - (b - a) * 0.02, b, 3.1, 2.8))   # partie telescopique
        O.add(nom, "vitres", tube_entre(a + [0, 0.2, 0], b + [0, 0.2, 0], 3.5, 1.0), 4.0)
        O.add(nom, "vert", tube_entre(a + [0, 1.25, 0], b + [0, 1.25, 0], 3.52, 0.35))
        O.add(nom, "blanc", boite(cab[0] - 1.6, yp, cab[2] - 2.0, cab[0] + 1.4, yp + 3.0, cab[2] + 2.0))   # cabine
        O.add(nom, "sombre", boite(cab[0] - 2.35, yp + 0.1, cab[2] - 1.5, cab[0] - 1.6, yp + 2.8, cab[2] + 1.5))  # soufflet
        sup = a + (b - a) * 0.8
        for dz in (-1.0, 1.0):                                              # pieds + roues
            O.add(nom, "poteau", cyl(0.25, yp, sup[0], 0, sup[2] + dz, 12))
            w = trimesh.creation.cylinder(radius=0.5, height=0.4, sections=18)
            w.apply_transform(rotation_matrix(np.pi / 2, [0, 0, 1]))
            w.apply_translation([sup[0], 0.5, sup[2] + dz])
            O.add(nom, "ve_pneu", w)
        O.add(nom, "poteau", boite(sup[0] - 0.4, yp - 0.6, sup[2] - 1.3, sup[0] + 0.4, yp, sup[2] + 1.3))


def piste_details(O):
    z0, z1, x0, x1 = -125.0, -80.0, -240.0, 240.0
    zc = (z0 + z1) / 2
    for k, x, cap in (("num_09", x0 + 48, 90), ("num_27", x1 - 48, -90)):    # numeros peints
        m = trimesh.Trimesh([[-9, 0.05, -9], [9, 0.05, -9], [9, 0.05, 9], [-9, 0.05, 9]], [[0, 2, 1], [0, 3, 2]], process=False)
        m.apply_transform(rotation_matrix(math.radians(cap), [0, 1, 0]))
        m.apply_translation([x, 0, zc])
        m.visual = trimesh.visual.TextureVisuals(uv=np.array([[0, 0], [1, 0], [1, 1], [0, 1]]), material=M[k])
        O.add("Piste", k, m)
    for xs, sgn in ((x0, -1), (x1, 1)):                                     # rampe d'approche lumineuse
        for i in range(1, 9):
            x = xs + sgn * i * 12
            for dz in np.arange(-6, 6.1, 1.5):
                O.add("Piste_Approche", "feu_blanc", trimesh.creation.icosphere(1, 0.3).apply_translation([x, 1.3, zc + dz]))
            O.add("Piste_Approche", "poteau", boite(x - 0.15, 0, zc - 6.3, x + 0.15, 1.0, zc + 6.3))
            for dz in (-6, 6):
                O.add("Piste_Approche", "poteau", cyl(0.12, 1.0, x, 0, zc + dz, 8))
        for i, dz in enumerate((-30, -27, -24, -21)):                       # PAPI (2 rouges, 2 blancs)
            x = xs - sgn * 60
            O.add("Piste_PAPI", "poteau", boite(x - 0.8, 0, z1 + 6 + i * 2.6 - 0.8, x + 0.8, 0.5, z1 + 6 + i * 2.6 + 0.8))
            O.add("Piste_PAPI", "feu_rouge" if i < 2 else "feu_blanc",
                  boite(x - 0.5, 0.5, z1 + 6 + i * 2.6 - 0.5, x + 0.5, 1.2, z1 + 6 + i * 2.6 + 0.5))
    for x, k in ((-140, "pan_0927"), (74, "pan_0927")):                      # panneaux de taxiway
        for (kk, dx) in ((k, 0.0),):
            O.add("Panneaux_Taxi", "sombre", boite(x + 12.5, 0, -73.5, x + 16.5, 0.3, -72.5))
            O.add("Panneaux_Taxi", "sombre", boite(x + 12.7, 0.3, -73.15, x + 16.3, 2.1, -72.85))
            panneau(O, "Panneaux_Taxi", kk, x + 14.5, 1.2, -73.0, 3.4, 1.6, 0)
    for x, z, k, cap in ((-125, 60, "pan_a", 90), (-125, -10, "pan_a", 90), (89, 60, "pan_b", -90), (89, -10, "pan_b", -90)):
        O.add("Panneaux_Taxi", "sombre", boite(x - 0.4, 0, z - 1.2, x + 0.4, 0.3, z + 1.2))
        panneau(O, "Panneaux_Taxi", k, x, 1.1, z, 1.6, 1.6, cap)
    O.add("Panneaux_Taxi", "sombre", boite(-118, 0, 62, -114, 0.3, 63))
    panneau(O, "Panneaux_Taxi", "pan_gates", -116, 1.4, 62.5, 6.0, 1.5, 0)


def barbeles(O):
    """bras inclines vers l'exterieur + 3 fils au-dessus du grillage, et panneaux RESTRICTED AREA"""
    coins = [(-DEMI, -DEMI), (DEMI, -DEMI), (DEMI, DEMI), (-DEMI, DEMI)]
    for c in range(4):
        (xa, za), (xb, zb) = coins[c], coins[(c + 1) % 4]
        L = math.hypot(xb - xa, zb - za)
        dx, dz = (xb - xa) / L, (zb - za) / L
        nx, nz = dz, -dx                                                     # normale exterieure
        for t in np.arange(0, L + 0.1, 4.0):
            x, z = xa + dx * t, za + dz * t
            O.add("Grillage_Barbeles", "poteau", tube_entre((x, H_GRILLE + 0.3, z), (x + nx * 0.5, H_GRILLE + 0.9, z + nz * 0.5), 0.08, 0.08))
        for k in (1, 2, 3):
            f = k / 3
            o = (nx * 0.5 * f, H_GRILLE + 0.3 + 0.6 * f, nz * 0.5 * f)
            O.add("Grillage_Barbeles", "sombre", tube_entre((xa + o[0], o[1], za + o[2]), (xb + o[0], o[1], zb + o[2]), 0.04, 0.04))
        for t in np.arange(20, L - 10, 40):                                  # panneaux vers l'interieur
            x, z = xa + dx * t - nx * 0.15, za + dz * t - nz * 0.15
            cap = math.degrees(math.atan2(-nx, -nz)) + 180
            panneau(O, "Grillage_Panneaux", "pan_restreint", x, 1.9, z, 3.0, 0.75, cap, double=False)


def caserne(O):
    x0, z0 = 110.0, 10.0                                                      # a cote de la tour, porte vers l'ouest
    O.add("Caserne_Pompiers", "rouge_bat", boite(x0, 0, z0, x0 + 20, 9, z0 + 36))
    O.add("Caserne_Pompiers", "blanc", boite(x0 - 0.3, 9, z0 - 0.3, x0 + 20.3, 10, z0 + 36.3))
    for i in range(3):
        zz = z0 + 4 + i * 10.5
        O.add("Caserne_Pompiers", "porte_garage", boite(x0 - 0.1, 0, zz, x0, 6.0, zz + 7.5))
        for y in np.arange(0.8, 6, 1.0):
            O.add("Caserne_Pompiers", "poteau", boite(x0 - 0.15, y, zz, x0 - 0.1, y + 0.08, zz + 7.5))
    panneau(O, "Caserne_Pompiers", "pan_pompiers", x0 - 0.12, 7.6, z0 + 18, 14, 2.4, -90, double=False)
    for i, zz in enumerate((z0 + 7.8, z0 + 18.3)):
        ajouter(O, "Camion_Pompiers_%d" % (i + 1), VE.place(VE.camion_pompiers(), x0 - 7, zz, -90))


def zone_cargo(O):
    O.add("Cargo_Hangar", "blanc", boite(-150, 0, -48, -132, 10, -38))
    panneau(O, "Cargo_Hangar", "pan_cargo", -140.9, 7.6, -37.9, 8, 2, 180, double=False)
    n = 0
    for rx in range(5):
        for rz in range(3):
            if (rx + rz) % 4 == 3:
                continue
            ajouter(O, "Conteneurs_Cargo", VE.place(VE.conteneur(), -128 + rx * 2.0, -32 + rz * 1.7, 90))
            n += 1
    ajouter(O, "Conteneurs_Cargo", VE.place(VE.tracteur(), -116, -28, 90))


COULEURS_VOITURES = ["ve_valise_1", "ve_valise_2", "ve_valise_3", "ve_rouge", "ve_blanc", "ve_sombre", "ve_vert"]


def voiture(seed):
    r = np.random.default_rng(seed)
    P = {}
    k = COULEURS_VOITURES[r.integers(len(COULEURS_VOITURES))]
    VE.P_add(P, k, VE.rbox(1.8, 0.7, 4.2, 0.4, 0, 0.35, 0))
    VE.P_add(P, k, VE.rbox(1.6, 0.6, 2.2, 0.35, 0, 1.05, 0.2))
    VE.P_add(P, "ve_vitre", VE.boite(1.62, 0.38, 1.7, 0, 1.12, 0.2))
    VE.quatre_roues(P, 1.75, -1.35, 1.35, 0.35, 0.25)
    return P


def cote_ville(O):
    """derriere le terminal : route avec voitures, parking a etages, hotel de l'aeroport"""
    O.add("Route", "piste", boite(-260, -0.02, 150, 260, 0.03, 162), 10.0)
    for x in np.arange(-250, 251, 10):
        O.add("Route", "marquage", boite(x, 0.03, 155.8, x + 5, 0.05, 156.2))
    r = np.random.default_rng(9)
    for i, x in enumerate(np.arange(-230, 231, 23)):
        if r.random() < 0.6:
            z = 153 if r.random() < 0.5 else 159
            ajouter(O, "Route_Voitures", VE.place(voiture(i), x + r.uniform(-5, 5), z, 90 if z < 156 else -90))
    # parking a etages
    x0, x1, z0, z1 = -100.0, -25.0, 168.0, 205.0
    for niv in range(4):
        y = niv * 3.4
        O.add("Parking_Etages", "beton", boite(x0, y, z0, x1, y + 0.5, z1))
        O.add("Parking_Etages", "vert", boite(x0 - 0.1, y + 0.5, z0 - 0.1, x1 + 0.1, y + 1.4, z0 + 0.4))
        for x in np.arange(x0 + 1, x1, 8):
            O.add("Parking_Etages", "beton", boite(x, y + 0.5, z0 + 0.5, x + 0.6, y + 3.4, z0 + 1.1))
        for j, x in enumerate(np.arange(x0 + 3, x1 - 2, 3.2)):
            if r.random() < 0.35:
                ajouter(O, "Parking_Voitures", VE.place(voiture(100 + niv * 40 + j), x, z0 + 5, 180, y + 0.5))
    O.add("Parking_Etages", "beton", boite(x0, 13.6, z0, x1, 14.1, z1))
    panneau(O, "Parking_Etages", "pan_parking", (x0 + x1) / 2, 16.0, z0 - 0.2, 14, 3, 0, double=False)
    O.add("Parking_Etages", "poteau", boite((x0 + x1) / 2 - 3, 14.1, z0 - 0.15, (x0 + x1) / 2 + 3, 14.6, z0 + 0.3))
    # hotel
    hx0, hx1, hz0, hz1 = 30.0, 62.0, 168.0, 190.0
    O.add("Hotel", "facade_a", boite(hx0, 0, hz0, hx1, 42, hz1), 6.0)
    for y in np.arange(4, 42, 3.5):
        O.add("Hotel", "blanc", boite(hx0 - 0.2, y, hz0 - 0.2, hx1 + 0.2, y + 0.6, hz1 + 0.2))
    O.add("Hotel", "blanc", boite(hx0 - 1, 42, hz0 - 1, hx1 + 1, 43.5, hz1 + 1))
    panneau(O, "Hotel", "pan_hotel", (hx0 + hx1) / 2, 46.5, hz0 - 0.5, 20, 5, 0, double=False)
    O.add("Hotel", "vert", boite((hx0 + hx1) / 2 - 10.5, 43.5, hz0 - 0.4, (hx0 + hx1) / 2 + 10.5, 49.2, hz0 - 0.2))


def mats(O):
    for i, x in enumerate((-82, -27, 27, 82)):
        ajouter(O, f"Mat_Eclairage_{i + 1}", VE.place(VE.mat_eclairage(24), x, 72, 180))
    for i, (x, z) in enumerate(((-140, 0), (74, 30))):
        ajouter(O, f"Mat_Eclairage_{i + 5}", VE.place(VE.mat_eclairage(20), x + (8 if x < 0 else -8), z, 90 if x < 0 else -90))


if __name__ == "__main__":
    O = Objets()
    sols(O)
    grillage(O)
    piste(O)
    terminal(O)
    for i, xa in enumerate((-55, 0, 55)):
        avion_ligne(O, f"Avion_Gare_{i + 1}", xa, 86.0, 180.0)            # nez vers le terminal
        ajouter(O, f"Service_Avion_{i + 1}", VE.transformer(VE.service_avion(i),
                translation_matrix([xa, 0, 86.0]) @ rotation_matrix(np.pi, [0, 1, 0])))
    passerelles(O, (-55, 0, 55), 86.0)
    piste_details(O)
    barbeles(O)
    caserne(O)
    zone_cargo(O)
    mats(O)
    cote_ville(O)
    avion_ligne(O, "Avion_Roulage", 74.0, 0.0, 0.0)                         # avion qui roule vers la piste
    ajouter(O, "Follow_Me", VE.place(VE.follow_me(), 74.0, -24.0, 0.0))
    avion_ligne(O, "Avion_Piste", -170.0, -102.5, -90.0)                  # pret a decoller sur la piste
    avion_ligne(O, "Avion_Decollage", 60.0, -102.5, -90.0, alt=26.0, tangage=12.0)   # en train de decoller
    avion_ligne(O, "Avion_Atterrissage", -330.0, -102.5, -90.0, alt=30.0, tangage=-2.0, train=True)  # en approche
    horizon(O)
    tour(O)
    hangars(O)
    manche_a_air(O)
    lampadaires(O)
    haies(O)
    arbres(O)
    # la plateforme de spawn au centre (un objet a part)
    pf = trimesh.load(os.path.join(os.path.dirname(SORTIE), "Plateforme_Spawn.glb"), force="scene")
    for n in pf.graph.nodes_geometry:
        T, g = pf.graph[n]
        m = pf.geometry[g].copy()
        m.apply_transform(T)
        M["plateforme"] = m.visual.material
        O.add("Plateforme_Spawn", "plateforme", m)
    noms = O.exporter(SORTIE)
    import shutil
    shutil.copy(SORTIE, os.path.join(os.path.dirname(SORTIE), "Lobby_Complet.glb"))
    print(SORTIE, round(os.path.getsize(SORTIE) / 1e6, 2), "Mo", len(noms) + 1, "objets")
