"""PANNEAU "ENTER" (au-dessus de la plaque qui fait entrer dans l'avion), style du panneau CLAIM :
grosses lettres 3D blanches avec un epais contour bleu nuit, et une fleche verte qui pointe vers la plaque.
Le panneau flotte et se tourne vers le joueur (Verse) : son pivot est au centre.
Lettres dans le plan XY (lisibles depuis +Z), Y en haut.  ~2,6 m de large.
Sortie : Modeles/Lobby/Panneau_Enter.glb     Usage : python3 generate_panneau_enter.py [--apercu]
"""
import os
import sys

import numpy as np
import trimesh
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon
from shapely.ops import unary_union

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


M = {
    "blanc": PBR(name="EnterBlanc", baseColorFactor=lin((250, 252, 255)), roughnessFactor=0.35, metallicFactor=0.0),
    "vert": PBR(name="EnterVert", baseColorFactor=lin((40, 200, 100)), roughnessFactor=0.35, metallicFactor=0.0),
    "contour": PBR(name="EnterContour", baseColorFactor=lin(CONTOUR), roughnessFactor=0.6, metallicFactor=0.0),
}


class Contours(BasePen):
    """recupere les contours d'un glyphe en polylignes (courbes echantillonnees)"""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.formes, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            a = (1 - t) ** 3
            self.cur.append(tuple(a * np.array(p0) + 3 * (1 - t) ** 2 * t * np.array(p1) + 3 * (1 - t) * t * t * np.array(p2) + t ** 3 * np.array(p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, 7)[1:]:
            self.cur.append(tuple((1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t * t * np.array(p2)))

    def _closePath(self):
        if len(self.cur) > 2:
            self.formes.append(self.cur)
        self.cur = []


def texte(mot, hauteur):
    f = TTFont(POLICE)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    upm = f["head"].unitsPerEm
    k = hauteur / (upm * 0.72)
    x, polys = 0.0, []
    for c in mot:
        g = gs[cmap[ord(c)]]
        pen = Contours(gs)
        g.draw(pen)
        forme = None
        for cont in pen.formes:
            p = Polygon([(x + px * k, py * k) for px, py in cont]).buffer(0)
            forme = p if forme is None else forme.symmetric_difference(p)
        if forme is not None:
            polys.append(forme)
        x += g.width * k * 0.98
    u = unary_union(polys)
    minx, miny, maxx, maxy = u.bounds
    from shapely.affinity import translate
    return translate(u, -(minx + maxx) / 2, -(miny + maxy) / 2), maxx - minx, maxy - miny


def extr(poly, z0, z1):
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    ms = []
    for g in geoms:
        m = trimesh.creation.extrude_polygon(g, z1 - z0)
        m.apply_translation([0, 0, z0])
        ms.append(m)
    return trimesh.util.concatenate(ms)


if __name__ == "__main__":
    lettres, L, H = texte("ENTER", 0.62)
    lettres = lettres.buffer(0.012, 4)
    # fleche verte vers le bas, sous le mot
    yf = -H / 2 - 0.2
    fleche = Polygon([(-0.13, yf), (0.13, yf), (0.13, yf - 0.22), (0.3, yf - 0.22), (0.0, yf - 0.55),
                      (-0.3, yf - 0.22), (-0.13, yf - 0.22)])
    contour = unary_union([lettres.buffer(0.07, 8), fleche.buffer(0.07, 8)])
    P = {
        "contour": extr(contour, -0.13, 0.13),
        "blanc": extr(lettres, -0.16, 0.16),
        "vert": extr(fleche, -0.16, 0.16),
    }
    # pivot au centre de l'ensemble
    tout = trimesh.util.concatenate(list(P.values()))
    c = (tout.bounds[0] + tout.bounds[1]) / 2
    sc = trimesh.Scene()
    meshes = []
    for k, m in P.items():
        m.apply_translation(-c)
        if m.volume < 0:
            m.invert()
        m.unmerge_vertices()                      # faces plates : pas d'ombrage baveux sur les aretes
        m.visual = trimesh.visual.TextureVisuals(material=M[k])
        meshes.append(m)
    sc.add_geometry(trimesh.util.concatenate(meshes) if False else meshes[0], node_name="Panneau_Enter__contour")
    for k, m in list(zip(P.keys(), meshes))[1:]:
        sc.add_geometry(m, node_name=f"Panneau_Enter__{k}")
    dossier = LOBBY if not APERCU else os.environ.get("APERCU_DIR", "/tmp")
    chemin = os.path.join(dossier, "Panneau_Enter.glb")
    sc.export(chemin)
    # un seul objet
    import json, struct
    b = open(chemin, "rb").read()
    lj = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + lj])
    rest = b[20 + lj:]
    prims = []
    for nd in js["nodes"]:
        if "mesh" in nd:
            prims += js["meshes"][nd["mesh"]]["primitives"]
    js["meshes"] = [{"name": "Panneau_Enter", "primitives": prims}]
    js["nodes"] = [{"name": "Panneau_Enter", "mesh": 0}]
    js["scenes"], js["scene"] = [{"nodes": [0]}], 0
    s = json.dumps(js, separators=(",", ":")).encode()
    s += b" " * ((4 - len(s) % 4) % 4)
    open(chemin, "wb").write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(s) + len(rest)) + struct.pack("<II", len(s), 0x4E4F534A) + s + rest)
    print(chemin, round(L, 2), "x", round(H, 2), "m", round(os.path.getsize(chemin) / 1e3), "Ko")
