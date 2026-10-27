"""DAILY SPIN du lobby (style cartoon du HUD, gros contour sombre) :
- Roue_DailySpin.glb    : la roue (8 cases de gains), pivot AU CENTRE de la roue (c'est elle qui tourne)
- Support_DailySpin.glb : le pied, l'axe, la fleche (en haut) et le panneau "DAILY SPIN"
La case 0 est en haut (sous la fleche) ; les cases suivantes dans le sens des aiguilles d'une montre (vue de face).
L'ordre et les textes doivent correspondre a la liste Cases de Verse/daily_spin.verse.
Repere : face avant vers -Z, Y en haut. Le centre de la roue est a (0, 3, 0) sur le support.
Usage : python3 generate_daily_spin.py [--apercu]
"""
import math
import os
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, Polygon
from trimesh.transformations import rotation_matrix, translation_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(HERE))
LOBBY = os.path.join(os.path.dirname(HERE), "Lobby")
POLICE = os.path.join(RACINE, "Outils", "TitanOne-Regular.ttf")
APERCU = "--apercu" in sys.argv
PBR = trimesh.visual.material.PBRMaterial
CONTOUR = (22, 27, 48)

# (texte, couleur de la case) -- meme ordre que Gains dans daily_spin.verse
CASES = [("5 MIN", "CASH", (238, 48, 56), "horloge"), ("+10%", "MONEY", (255, 136, 24), "argent"),
         ("x2", "10 MIN", (250, 205, 30), "eclair"), ("15 MIN", "CASH", (64, 196, 64), "horloge"),
         ("REBIRTH", "+1", (24, 186, 220), "rebirth"), ("1 HOUR", "CASH", (44, 104, 240), "horloge"),
         ("x3", "5 MIN", (136, 60, 230), "eclair"), ("JACKPOT", "3 HOURS", (230, 50, 170), "couronne")]


def icone(nom, t=175):
    """icone carree (RGBA) : reprend les icones du HUD (argent, avion+argent, rebirth) ou en dessine une"""
    hud = {"argent": "FondArgent", "revenu": "FondRevenu", "rebirth": "FondRebirth"}
    if nom in hud:
        im = Image.open(os.path.join(RACINE, "Textures", "Interface", hud[nom] + ".png")).convert("RGBA")
        return im.crop((0, 0, 256, 256)).resize((t, t), Image.LANCZOS)
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if nom == "horloge":
        d.ellipse([14, 14, 242, 242], fill=(255, 255, 255), outline=CONTOUR, width=16)
        for k in range(12):
            a = math.radians(k * 30)
            r0 = 92 if k % 3 else 80
            d.line([(128 + math.cos(a) * r0, 128 + math.sin(a) * r0), (128 + math.cos(a) * 104, 128 + math.sin(a) * 104)],
                   fill=CONTOUR, width=8 if k % 3 == 0 else 5)
        d.line([(128, 128), (128, 52)], fill=(30, 150, 80), width=16)
        d.line([(128, 128), (182, 150)], fill=(30, 150, 80), width=16)
        d.ellipse([114, 114, 142, 142], fill=CONTOUR)
    elif nom == "eclair":
        pts = [(150, 10), (60, 140), (120, 140), (95, 246), (200, 100), (135, 100), (175, 10)]
        d.polygon(pts, fill=(255, 255, 255), outline=CONTOUR)
        d.line(pts + [pts[0]], fill=CONTOUR, width=12, joint="curve")
    else:                                                     # couronne du jackpot
        pts = [(28, 200), (28, 70), (80, 130), (128, 40), (176, 130), (228, 70), (228, 200)]
        d.polygon(pts, fill=(255, 205, 110), outline=CONTOUR)
        d.line(pts + [pts[0]], fill=CONTOUR, width=12, joint="curve")
        d.rectangle([28, 200, 228, 232], fill=(255, 205, 110), outline=CONTOUR, width=10)
        for x in (80, 128, 176):
            d.ellipse([x - 13, 155, x + 13, 181], fill=(240, 92, 168), outline=CONTOUR, width=5)
    return im.resize((t, t), Image.LANCZOS)
R_ROUE = 2.0
CENTRE_Y = 3.0


def lin(rgb):
    c = np.asarray(rgb, float) / 255.0
    if not APERCU:
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return list(np.round(c * 255).astype(int)) + [255]


def col(nom, rgb, rugo=0.45, metal=0.0, em=None):
    return PBR(name=nom, baseColorFactor=lin(rgb), roughnessFactor=rugo, metallicFactor=metal, emissiveFactor=em)


def police(t):
    return ImageFont.truetype(POLICE, t)


# ------------------------------------------------------------------ textures
def tex_roue(n=2048):
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = n / 2
    N = len(CASES)
    pas = 360 / N
    for i, (txt, sous, couleur, ico) in enumerate(CASES):
        # PIL : angles en degres, 0 = droite, sens horaire ; case i centree a "haut + i*pas" (sens horaire)
        a0 = -90 + i * pas - pas / 2
        d.pieslice([8, 8, n - 8, n - 8], a0, a0 + pas, fill=couleur + (255,), outline=(255, 255, 255, 255), width=14)
        # reflet plus clair vers l'exterieur
        clair = tuple(min(255, int(v * 1.18 + 20)) for v in couleur)
        d.pieslice([90, 90, n - 90, n - 90], a0 + 1.5, a0 + pas - 1.5, fill=clair + (255,))
        d.pieslice([170, 170, n - 170, n - 170], a0 + 1.5, a0 + pas - 1.5, fill=couleur + (255,))
    for i in range(N):                                          # rayons blancs entre les cases
        a = math.radians(-90 + i * pas - pas / 2)
        d.line([(c, c), (c + math.cos(a) * (c - 8), c + math.sin(a) * (c - 8))], fill=(255, 255, 255, 255), width=16)
    # textes radiaux : gros mot + petite ligne en dessous
    for i, (txt, sous, couleur, ico) in enumerate(CASES):
        taille = 140 if len(txt) <= 3 else (108 if len(txt) <= 5 else (90 if len(txt) <= 6 else 80))
        couche = Image.new("RGBA", (900, 320), (0, 0, 0, 0))
        dc = ImageDraw.Draw(couche)
        encre = (255, 255, 255)
        dc.text((450, 125), txt, font=police(taille), fill=encre, anchor="mm", stroke_width=14, stroke_fill=CONTOUR)
        dc.text((450, 245), sous, font=police(62), fill=(255, 255, 255), anchor="mm", stroke_width=9, stroke_fill=CONTOUR)
        ang = -90 + i * pas                                      # direction de la case (PIL, sens horaire)
        rot = -ang
        if 90 < (ang % 360) < 270:                              # moitie gauche : on retourne pour lire a l'endroit
            rot += 180
        couche = couche.rotate(rot, expand=True, resample=Image.BICUBIC)
        rx = c + math.cos(math.radians(ang)) * c * 0.47
        ry = c + math.sin(math.radians(ang)) * c * 0.47
        img.alpha_composite(couche, (int(rx - couche.width / 2), int(ry - couche.height / 2)))
        # icone pres du bord, droite (tournee comme la case)
        ic = icone(ico).rotate(-(ang + 90), expand=True, resample=Image.BICUBIC)
        ix = c + math.cos(math.radians(ang)) * c * 0.79
        iy = c + math.sin(math.radians(ang)) * c * 0.79
        img.alpha_composite(ic, (int(ix - ic.width / 2), int(iy - ic.height / 2)))
    return img


def tex_moyeu(n=512):
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([6, 6, n - 6, n - 6], fill=(255, 255, 255, 255), outline=CONTOUR, width=18)
    d.ellipse([60, 60, n - 60, n - 60], fill=(40, 185, 100, 255))
    # silhouette d'avion (vue de dessus), blanche
    s = n / 512
    avion = [(256, 96), (276, 150), (278, 230), (430, 300), (430, 330), (280, 300), (272, 380), (320, 410), (320, 430),
             (256, 415), (192, 430), (192, 410), (240, 380), (232, 300), (82, 330), (82, 300), (234, 230), (236, 150)]
    d.polygon([(x * s, y * s) for x, y in avion], fill=(255, 255, 255, 255), outline=CONTOUR)
    return img


ARC_EN_CIEL = [(238, 48, 56), (255, 136, 24), (250, 205, 30), (64, 196, 64), (24, 186, 220), (44, 104, 240),
              (136, 60, 230), (230, 50, 170)]


def tex_panneau(w=2048, h=512):
    """DAILY SPIN en lettres arc-en-ciel (chaque lettre sa couleur, reflet clair en haut, gros contour sombre)"""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, w - 10, h - 10], 110, fill=CONTOUR)
    d.rounded_rectangle([34, 34, w - 34, h - 34], 90, fill=(30, 44, 92))
    f = police(285)
    mot = "DAILY SPIN"
    larg = [d.textlength(ch, font=f) + (10 if ch != " " else 0) for ch in mot]
    x = w / 2 - sum(larg) / 2
    k = 0
    for ch, lg in zip(mot, larg):
        if ch != " ":
            coul = ARC_EN_CIEL[k % len(ARC_EN_CIEL)]
            k += 1
            lettre = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            dl = ImageDraw.Draw(lettre)
            dl.text((x, h / 2 + 14), ch, font=f, fill=coul + (255,), anchor="lm", stroke_width=24, stroke_fill=CONTOUR)
            # reflet : moitie haute plus claire
            clair = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(clair).text((x, h / 2 + 14), ch, font=f, fill=tuple(min(255, int(v * 0.6 + 110)) for v in coul) + (255,),
                                       anchor="lm")
            masque = Image.new("L", (w, h), 0)
            ImageDraw.Draw(masque).rectangle([0, 0, w, h / 2 - 10], fill=255)
            lettre.alpha_composite(Image.composite(clair, Image.new("RGBA", (w, h), (0, 0, 0, 0)), masque))
            img.alpha_composite(lettre)
        x += lg
    return img


def mat_tex(nom, img, em=None):
    return PBR(name=nom, baseColorTexture=img, alphaMode="MASK", alphaCutoff=0.5, roughnessFactor=0.45, metallicFactor=0.0,
               emissiveTexture=img if em else None, emissiveFactor=em)


M = {
    "roue_face": mat_tex("DailySpinFace", tex_roue(), [0.25, 0.25, 0.25]),
    "moyeu": mat_tex("DailySpinMoyeu", tex_moyeu()),
    "panneau": mat_tex("DailySpinPanneau", tex_panneau(), [0.3, 0.3, 0.3]),
    "contour": col("DailySpinContour", CONTOUR, 0.6),
    "jante": col("DailySpinJante", (246, 248, 250), 0.35),
    "ampoule": col("DailySpinAmpoule", (255, 250, 235), 0.3, 0.0, [1.0, 0.95, 0.85]),
    "vert": col("DailySpinVert", (40, 185, 100), 0.45),
    "vert_fonce": col("DailySpinVertFonce", (18, 118, 66), 0.5),
    "rose": col("DailySpinRose", (240, 92, 168), 0.35),
    "metal": col("DailySpinMetal", (200, 206, 214), 0.3, 0.8),
}


# ------------------------------------------------------------------ outils
def disque_uv(r, z, k, n=96, sens=-1):
    """disque texture, plan XY a la profondeur z, face vers sens*Z (-1 = vers l'avant)"""
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    V = np.vstack([[0, 0, z], np.c_[r * np.cos(a), r * np.sin(a), np.full(n, z)]])
    F = [[0, 1 + (i + 1) % n, 1 + i] for i in range(n)] if sens < 0 else [[0, 1 + i, 1 + (i + 1) % n] for i in range(n)]
    m = trimesh.Trimesh(V, F, process=False)
    # vue de face (depuis -Z), la droite est -X : u = 0.5 - x/2r ; v = 0.5 + y/2r
    uv = np.c_[0.5 - V[:, 0] / (2 * r), 0.5 + V[:, 1] / (2 * r)]
    m.visual = trimesh.visual.TextureVisuals(uv=uv, material=M[k])
    return m


def cyl_z(r, z0, z1, sections=96):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections)
    m.apply_translation([0, 0, (z0 + z1) / 2])
    return m


def coque(m, ep):
    c = m.copy()
    c.merge_vertices()
    c.vertices = c.vertices + c.vertex_normals * ep
    c.invert()
    return c


def boite(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box((x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return m


def exporter(P, chemin, nom):
    sc = trimesh.Scene()
    for k, ms in P.items():
        m = trimesh.util.concatenate(ms)
        if k in ("roue_face", "moyeu", "panneau"):
            m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([x.visual.uv for x in ms]), material=M[k])
        else:
            m.visual = trimesh.visual.TextureVisuals(material=M[k])
        sc.add_geometry(m, node_name=f"{nom}__{k}", geom_name=f"{nom}__{k}")
    sc.export(chemin)
    import json
    import struct
    b = open(chemin, "rb").read()
    lj = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + lj])
    rest = b[20 + lj:]
    prims = [p for nd in js["nodes"] if "mesh" in nd for p in js["meshes"][nd["mesh"]]["primitives"]]
    js["meshes"], js["nodes"] = [{"name": nom, "primitives": prims}], [{"name": nom, "mesh": 0}]
    js["scenes"], js["scene"] = [{"nodes": [0]}], 0
    s = json.dumps(js, separators=(",", ":")).encode()
    s += b" " * ((4 - len(s) % 4) % 4)
    open(chemin, "wb").write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(s) + len(rest)) + struct.pack("<II", len(s), 0x4E4F534A) + s + rest)
    print(chemin, round(os.path.getsize(chemin) / 1e3), "Ko", sum(len(m.faces) for ms in P.values() for m in ms), "triangles")


# ------------------------------------------------------------------ la roue (centre en 0,0,0)
def roue():
    P = {}
    R = R_ROUE
    P.setdefault("roue_face", []).append(disque_uv(R * 0.94, -0.13, "roue_face"))
    corps = cyl_z(R * 0.95, -0.12, 0.12, 128)
    P.setdefault("contour", []).append(corps)
    # jante blanche bombee + contour
    jante = trimesh.creation.torus(major_radius=R * 0.97, minor_radius=0.13, major_sections=128, minor_sections=20)
    P.setdefault("jante", []).append(jante)
    P["contour"].append(coque(jante, 0.03))
    # ampoules sur la jante (16) et picots entre les cases (8)
    for i in range(24):
        a = 2 * math.pi * i / 24
        b = trimesh.creation.icosphere(2, 0.075)
        b.apply_translation([R * 0.97 * math.cos(a), R * 0.97 * math.sin(a), -0.12])
        P.setdefault("ampoule", []).append(b)
    N = len(CASES)
    for i in range(N):
        # meme convention que la texture : case i centree a haut + i*pas, sens horaire vu de face (droite = -X)
        a = math.radians(90 + i * 360 / N + 180 / N)
        x, y = -math.cos(a) * R * 0.86, math.sin(a) * R * 0.86
        p = cyl_z(0.05, -0.30, -0.12, 16)
        p.apply_translation([x, y, 0])
        P.setdefault("metal", []).append(p)
    # moyeu bombe avec l'avion
    dome = trimesh.creation.icosphere(3, 0.42)
    dome.apply_scale([1, 1, 0.45])
    dome.apply_translation([0, 0, -0.14])
    P.setdefault("jante", []).append(dome)
    P["moyeu"] = [disque_uv(0.40, -0.335, "moyeu", 64)]
    P["contour"].append(coque(dome, 0.025))
    return P


# ------------------------------------------------------------------ le support
def support():
    P = {}
    # socle
    socle = boite(-2.4, 0, -1.0, 2.4, 0.45, 1.0)
    P.setdefault("vert", []).append(socle)
    P.setdefault("contour", []).append(coque(socle, 0.04))
    P.setdefault("vert_fonce", []).append(boite(-2.42, 0.0, -1.02, 2.42, 0.12, 1.02))
    # deux pieds en A derriere la roue, jusqu'a l'axe
    for sx in (-1, 1):
        for dz in (0.30, 0.75):
            a = np.array([sx * 1.7, 0.45, dz])
            b = np.array([sx * 0.18, CENTRE_Y, 0.30])
            L = np.linalg.norm(b - a)
            t = trimesh.creation.box((0.22, L, 0.18))
            t.apply_transform(trimesh.geometry.align_vectors([0, 1, 0], (b - a) / L))
            t.apply_translation((a + b) / 2)
            P["vert"].append(t)
            P["contour"].append(coque(t, 0.03))
    axe = cyl_z(0.16, 0.12, 0.85, 32)
    axe.apply_translation([0, CENTRE_Y, 0])
    P.setdefault("metal", []).append(axe)
    # arche + panneau DAILY SPIN au-dessus
    for sx in (-1, 1):
        mont = boite(sx * 2.45 - 0.14, 0.45, 0.38, sx * 2.45 + 0.14, 6.6, 0.62)
        P["vert"].append(mont)
        P["contour"].append(coque(mont, 0.03))
    w, h, yp = 5.6, 1.4, 6.45
    v = np.array([[-w / 2, yp - h / 2, 0.30], [w / 2, yp - h / 2, 0.30], [w / 2, yp + h / 2, 0.30], [-w / 2, yp + h / 2, 0.30]])
    q = trimesh.Trimesh(v, [[0, 2, 1], [0, 3, 2]], process=False)
    q.visual = trimesh.visual.TextureVisuals(uv=np.array([[1, 0], [0, 0], [0, 1], [1, 1]]), material=M["panneau"])
    P["panneau"] = [q]
    P["contour"].append(boite(-w / 2 + 0.1, yp - h / 2 + 0.1, 0.31, w / 2 - 0.1, yp + h / 2 - 0.1, 0.55))
    # fleche (rose) en haut, pointe vers le bas sur la jante
    tri = Polygon([(-0.32, 0.55), (0.32, 0.55), (0.0, -0.05)]).buffer(0.06, 4)
    fl = trimesh.creation.extrude_polygon(tri, 0.22)
    fl.apply_translation([0, CENTRE_Y + R_ROUE + 0.02, -0.42])
    P.setdefault("rose", []).append(fl)
    P["contour"].append(coque(fl, 0.035))
    tige = boite(-0.08, CENTRE_Y + R_ROUE + 0.5, -0.36, 0.08, yp - h / 2, -0.10)
    P["metal"].append(tige)
    return P


if __name__ == "__main__":
    dossier = LOBBY if not APERCU else os.environ.get("APERCU_DIR", "/tmp")
    exporter(roue(), os.path.join(dossier, "Roue_DailySpin.glb"), "Roue_DailySpin")
    exporter(support(), os.path.join(dossier, "Support_DailySpin.glb"), "Support_DailySpin")
    if APERCU:
        a = trimesh.load(os.path.join(dossier, "Support_DailySpin.glb"), force="scene")
        b = trimesh.load(os.path.join(dossier, "Roue_DailySpin.glb"), force="scene")
        for n in b.graph.nodes_geometry:
            T, g = b.graph[n]
            a.add_geometry(b.geometry[g].copy().apply_transform(translation_matrix([0, CENTRE_Y, 0]) @ T))
        a.export(os.path.join(dossier, "dailyspin_apercu.glb"))


def fichier_unique(chemin):
    """Daily_Spin.glb : 2 objets dans 1 fichier. Le support (origine au sol) et la roue, dont le pivot reste
    au centre de la roue (noeud deplace de 3 m vers le haut), pour qu'elle tourne sur elle-meme."""
    import json
    import struct
    sc = trimesh.Scene()
    for obj, P, T in (("Support_DailySpin", support(), np.eye(4)), ("Roue_DailySpin", roue(), translation_matrix([0, CENTRE_Y, 0]))):
        for k, ms in P.items():
            m = trimesh.util.concatenate(ms)
            if k in ("roue_face", "moyeu", "panneau"):
                m.visual = trimesh.visual.TextureVisuals(uv=np.vstack([x.visual.uv for x in ms]), material=M[k])
            else:
                m.visual = trimesh.visual.TextureVisuals(material=M[k])
            sc.add_geometry(m, node_name=f"{obj}__{k}", geom_name=f"{obj}__{k}", transform=T)
    sc.export(chemin)
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
    print(chemin, round(os.path.getsize(chemin) / 1e3), "Ko", [(n["name"], n.get("matrix", n.get("translation"))) for n in nodes])


if __name__ == "__main__" and not APERCU:
    fichier_unique(os.path.join(LOBBY, "Daily_Spin.glb"))
