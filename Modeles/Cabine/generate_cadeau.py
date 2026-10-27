"""CADEAU du lobby (Playtime Reward), style cartoon tres colore, gros contour sombre.
Un seul fichier, 2 objets :
- Cadeau_Boite : la boite rose + le ruban cyan
- Cadeau_Couvercle : le couvercle + le gros noeud ; pivot au centre du dessous du couvercle
  -> Verse peut le faire sauter / tourner a l'ouverture.
Repere : Y en haut, pose au sol. ~1,2 m de cote, ~1,9 m de haut avec le noeud.
Sortie : Modeles/Lobby/Cadeau.glb     Usage : python3 generate_cadeau.py [--apercu]
"""
import json
import math
import os
import struct
import sys

import numpy as np
import trimesh
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



M = {
    "boite": col("CadeauRose", (236, 58, 150), 0.35),
    "boite_clair": col("CadeauRoseClair", (255, 120, 190), 0.35),
    "ruban": col("CadeauRuban", (40, 200, 235), 0.25),
    "pois": col("CadeauPois", (250, 205, 30), 0.35),
    "contour": col("CadeauContour", CONTOUR, 0.6),
}
C, HB, HC = 1.20, 1.00, 0.24      # cote de la boite, hauteur boite, hauteur couvercle
RL = 0.26                          # largeur du ruban
OUT = 0.035                        # epaisseur du contour


def boite():
    P = {}
    b = rbox(C, HB, C, 0.10)
    ajouter(P, "boite", b)
    ajouter(P, "contour", coque(b, OUT), True)
    for sens in (0, 1):                                       # ruban qui fait le tour
        r = rbox(RL if sens == 0 else C + 0.03, HB - 0.02, C + 0.03 if sens == 0 else RL, 0.03)
        ajouter(P, "ruban", r)
    # pois jaunes sur les 4 faces
    for ang in range(4):
        for x, y in ((-0.37, 0.30), (0.37, 0.62), (-0.37, 0.78), (0.37, 0.22)):
            p = cyl_z(0.075, 0, 0.02, 24)
            p.apply_translation([x, y, -C / 2 - 0.012])
            p.apply_transform(rotation_matrix(ang * np.pi / 2, [0, 1, 0]))
            ajouter(P, "pois", p)
    return P


def couvercle():
    P = {}
    c = rbox(C + 0.12, HC, C + 0.12, 0.12)
    ajouter(P, "boite_clair", c)
    ajouter(P, "contour", coque(c, OUT), True)
    for sens in (0, 1):
        r = rbox(RL if sens == 0 else C + 0.15, HC + 0.02, C + 0.15 if sens == 0 else RL, 0.03)
        r.apply_translation([0, -0.01, 0])
        ajouter(P, "ruban", r)
    # noeud : 2 boucles (tores aplatis) + un centre
    for sx in (-1, 1):
        t = trimesh.creation.torus(0.24, 0.085, major_sections=40, minor_sections=16)
        t.apply_scale([1.0, 0.55, 1.0])
        t.apply_transform(rotation_matrix(np.pi / 2, [1, 0, 0]))     # anneau debout dans le plan XY
        t.apply_transform(rotation_matrix(sx * -0.55, [0, 0, 1]))
        t.apply_translation([sx * 0.25, HC + 0.25, 0])
        ajouter(P, "ruban", t)
        ajouter(P, "contour", coque(t, OUT * 0.8), True)
        q = rbox(0.14, 0.34, 0.05, 0.02)                              # bouts qui pendent
        q.apply_transform(rotation_matrix(sx * 0.5, [0, 0, 1]))
        q.apply_translation([sx * 0.12, HC - 0.12, -0.05])
    s = trimesh.creation.icosphere(3, 0.13)
    s.apply_scale([1, 0.85, 0.85])
    s.apply_translation([0, HC + 0.13, 0])
    ajouter(P, "ruban", s)
    ajouter(P, "contour", coque(s, OUT * 0.8), True)
    return P


def exporter(objets, chemin):
    sc = trimesh.Scene()
    for obj, P, T in objets:
        for k, ms in P.items():
            m = trimesh.util.concatenate(ms)
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
    dossier = LOBBY if not APERCU else os.environ.get("APERCU_DIR", "/tmp")
    exporter([("Cadeau_Boite", boite(), np.eye(4)),
              ("Cadeau_Couvercle", couvercle(), translation_matrix([0, HB - 0.10, 0]))],
             os.path.join(dossier, "Cadeau.glb"))
