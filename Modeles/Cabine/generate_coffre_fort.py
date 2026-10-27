"""COFFRE-FORT simple, style cartoon (comme le reste du lobby : formes rondes, gros contour sombre).
Un seul fichier, 2 objets :
- Coffre_Corps : la caisse en acier avec 4 petits pieds et les charnieres
- Coffre_Porte : la porte verte avec la molette a chiffres et la poignee a 3 branches ;
  son pivot est SUR LA CHARNIERE (a gauche vue de face) -> on peut l'ouvrir en la tournant autour de l'axe vertical.
Repere : face avant vers -Z, Y en haut, pose au sol. ~1 m de large, 1,25 m de haut.
Sortie : Modeles/Lobby/Coffre_Fort.glb     Usage : python3 generate_coffre_fort.py [--apercu]
"""
import json
import math
import os
import struct
import sys

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import box as rect
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


def tex_cadran(n=512):
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, n - 4, n - 4], fill=(232, 236, 240, 255), outline=CONTOUR, width=14)
    f = ImageFont.truetype(POLICE, 44)
    for k in range(40):                                        # graduations
        a = math.radians(k * 9 - 90)
        r0 = 200 if k % 5 else 178
        d.line([(n / 2 + math.cos(a) * r0, n / 2 + math.sin(a) * r0), (n / 2 + math.cos(a) * 232, n / 2 + math.sin(a) * 232)],
               fill=CONTOUR, width=7 if k % 5 == 0 else 4)
    for k, v in enumerate(range(0, 100, 20)):
        a = math.radians(k * 72 - 90)
        d.text((n / 2 + math.cos(a) * 140, n / 2 + math.sin(a) * 140), str(v), font=f, fill=CONTOUR, anchor="mm")
    return img


M = {
    "acier": col("CoffreAcier", (96, 106, 122), 0.35, 0.55),
    "acier_clair": col("CoffreAcierClair", (150, 160, 174), 0.3, 0.6),
    "porte": col("CoffrePorte", (34, 140, 82), 0.35, 0.2),
    "porte_fonce": col("CoffrePorteFonce", (20, 96, 56), 0.4, 0.2),
    "chrome": col("CoffreChrome", (215, 222, 230), 0.18, 0.95),
    "contour": col("CoffreContour", CONTOUR, 0.6),
    "cadran": PBR(name="CoffreCadran", baseColorTexture=tex_cadran(), alphaMode="MASK", alphaCutoff=0.5,
                  roughnessFactor=0.3, metallicFactor=0.0),
}

W, H, D = 1.00, 1.25, 0.85        # caisse
Y0 = 0.10                          # hauteur des pieds
ZF = -D / 2                        # face avant de la caisse
EP_PORTE = 0.10


def rbox(w, h, l, r, seg=5):
    """boite aux aretes arrondies (arrondi vertical) centree en 0, posee de y=0 a y=h"""
    p = rect(-w / 2 + r, -l / 2 + r, w / 2 - r, l / 2 - r).buffer(r, seg)
    m = trimesh.creation.extrude_polygon(p, h)
    m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
    m.apply_transform(np.diag([1, 1, -1, 1]))
    if m.volume < 0:
        m.invert()
    return m


def rplaque(w, h, ep, r, seg=6):
    """plaque aux coins arrondis dans le plan XY (face vers -Z), epaisseur ep vers +Z, centree en 0"""
    p = rect(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, seg)
    m = trimesh.creation.extrude_polygon(p, ep)
    return m


def cyl_z(r, z0, z1, sec=48):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sec)
    m.apply_translation([0, 0, (z0 + z1) / 2])
    return m


def coque(m, ep):
    c = m.copy()
    c.merge_vertices()
    c.vertices = c.vertices + c.vertex_normals * ep
    c.invert()
    return c


def ajouter(P, k, m, contour=False):
    if not contour and m.is_watertight and m.volume < 0:
        m.invert()
    P.setdefault(k, []).append(m)


def corps():
    P = {}
    caisse = rplaque(W, H, D, 0.10)
    caisse.apply_translation([0, Y0 + H / 2, ZF])
    ajouter(P, "acier", caisse)
    ajouter(P, "contour", coque(caisse, 0.02), True)
    # renfoncement autour de la porte (cadre plus clair)
    cadre = rplaque(W - 0.08, H - 0.08, 0.02, 0.07)
    cadre.apply_translation([0, Y0 + H / 2, ZF - 0.012])
    ajouter(P, "acier_clair", cadre)
    # pieds
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = cyl_z(0.06, 0, 1, 20)
            p.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
            p.apply_scale([1, Y0, 1])
            p.apply_translation([sx * (W / 2 - 0.13), 0, sz * (D / 2 - 0.13)])
            ajouter(P, "contour", p)
    # charnieres (cote gauche vu de face = +X)
    for y in (Y0 + 0.28, Y0 + H - 0.28):
        c = trimesh.creation.cylinder(radius=0.045, height=0.20, sections=20)
        c.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))
        c.apply_translation([W / 2 - 0.02, y, ZF - 0.05])
        ajouter(P, "chrome", c)
    return P


def porte():
    """dans le repere de la CHARNIERE : pivot en (0,0,0), la porte s'etend vers -X (vers la droite vue de face)"""
    P = {}
    wp, hp = W - 0.16, H - 0.16
    plaque = rplaque(wp, hp, EP_PORTE, 0.08)
    plaque.apply_translation([-wp / 2 - 0.04, 0, -EP_PORTE])
    ajouter(P, "porte", plaque)
    ajouter(P, "contour", coque(plaque, 0.015), True)
    # bandeau plus fonce + rivets
    bande = rplaque(wp - 0.12, hp - 0.12, 0.012, 0.06)
    bande.apply_translation([-wp / 2 - 0.04, 0, -EP_PORTE - 0.010])
    ajouter(P, "porte_fonce", bande)
    inter = rplaque(wp - 0.20, hp - 0.20, 0.013, 0.05)
    inter.apply_translation([-wp / 2 - 0.04, 0, -EP_PORTE - 0.0115])
    ajouter(P, "porte", inter)
    for sx in (-1, 1):
        for sy in (-1, 1):
            r = trimesh.creation.icosphere(2, 0.022)
            r.apply_translation([-wp / 2 - 0.04 + sx * (wp / 2 - 0.035), sy * (hp / 2 - 0.035), -EP_PORTE - 0.004])
            ajouter(P, "chrome", r)
    cx = -wp / 2 - 0.04
    # molette a chiffres (en haut)
    yc = 0.16
    base = cyl_z(0.17, -EP_PORTE - 0.06, -EP_PORTE, 48)
    base.apply_translation([cx, yc, 0])
    ajouter(P, "chrome", base)
    ajouter(P, "contour", coque(base, 0.012), True)
    a = np.linspace(0, 2 * np.pi, 64, endpoint=False)
    rr = 0.15
    zc = -EP_PORTE - 0.0605
    V = np.vstack([[cx, yc, zc], np.c_[cx + rr * np.cos(a), yc + rr * np.sin(a), np.full(64, zc)]])
    F = [[0, 1 + (i + 1) % 64, 1 + i] for i in range(64)]
    disque = trimesh.Trimesh(V, F, process=False)
    disque.visual = trimesh.visual.TextureVisuals(uv=np.c_[0.5 - (V[:, 0] - cx) / (2 * rr), 0.5 + (V[:, 1] - yc) / (2 * rr)],
                                                  material=M["cadran"])
    P.setdefault("cadran", []).append(disque)
    bouton = cyl_z(0.05, -EP_PORTE - 0.10, -EP_PORTE - 0.06, 24)
    bouton.apply_translation([cx, yc, 0])
    ajouter(P, "contour", bouton)
    # poignee a 3 branches (en bas)
    yh = -0.22
    moyeu = cyl_z(0.07, -EP_PORTE - 0.09, -EP_PORTE, 32)
    moyeu.apply_translation([cx, yh, 0])
    ajouter(P, "chrome", moyeu)
    for k in range(3):
        ang = math.radians(90 + k * 120)
        bras = trimesh.creation.cylinder(radius=0.028, height=0.20, sections=16)
        bras.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
        bras.apply_translation([0.10, 0, 0])
        bras.apply_transform(rotation_matrix(ang, [0, 0, 1]))
        bras.apply_translation([cx, yh, -EP_PORTE - 0.06])
        ajouter(P, "chrome", bras)
        bout = trimesh.creation.icosphere(2, 0.045)
        bout.apply_translation([cx + 0.20 * math.cos(ang), yh + 0.20 * math.sin(ang), -EP_PORTE - 0.06])
        ajouter(P, "contour", bout)
    return P


def exporter(objets, chemin):
    sc = trimesh.Scene()
    for obj, P, T in objets:
        for k, ms in P.items():
            m = trimesh.util.concatenate(ms)
            if k == "cadran":
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
    print(chemin, round(os.path.getsize(chemin) / 1e3), "Ko")


if __name__ == "__main__":
    charniere = translation_matrix([W / 2 - 0.04, Y0 + H / 2, ZF - 0.015])
    dossier = LOBBY if not APERCU else os.environ.get("APERCU_DIR", "/tmp")
    exporter([("Coffre_Corps", corps(), np.eye(4)), ("Coffre_Porte", porte(), charniere)],
             os.path.join(dossier, "Coffre_Fort.glb"))
