"""CE QUI APPARAIT AU CLAIM (lobby) : un avion de ligne BLANC normal (vu de l'exterieur) sur son socle,
relie a la plateforme du spawn par un chemin.
Un seul fichier, 4 objets separes (a cacher / montrer par Verse) :
- Claim_Chemin   : le chemin gris, du bout du petit chemin du spawn jusqu'au socle
- Claim_Socle    : un rond gris comme la plateforme du spawn (meme gris, meme muret fin), ouvert vers le chemin,
                   ligne jaune de guidage + barre d'arret
- Claim_Avion    : l'avion (celui de generate_avion_decor.py, proportions normales, tout blanc, ailes grises)
- Claim_Escalier : l'escalier d'aeroport devant la porte avant gauche (la plaque ENTER se pose a son pied)
ORIGINE = CENTRE DE LA PLATEFORME DU SPAWN : pose ce fichier exactement au meme endroit que Plateforme_Spawn,
il colle au chemin qui part vers +X. Pour les 5 autres chemins : meme position, tourne de 60, 120, 180, 240, 300.
Sortie : Modeles/Lobby/Avion_Claim.glb     Usage : python3 generate_avion_claim.py [--apercu]
"""
import json
import math
import os
import struct
import sys

import numpy as np
import trimesh
from shapely.geometry import Point, box as rect
from trimesh.transformations import rotation_matrix, translation_matrix, scale_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_avion_decor as D  # noqa: E402

LOBBY = os.path.join(os.path.dirname(HERE), "Lobby")
APERCU = "--apercu" in sys.argv
PBR = trimesh.visual.material.PBRMaterial

# --- plateforme du spawn (generate_plateforme_spawn.py) : rayon 15, petits chemins de 3 m, larges de 4 m
R_SPAWN, BOUT_CHEMIN, LARGEUR = 15.0, 18.0, 4.0
H_SOL = 0.1
# --- socle : meme rond que le spawn, plus loin sur l'axe +X (6 socles autour du spawn sans se toucher)
R_SOCLE = 15.0
X_SOCLE = 47.0
K = 0.75                     # echelle de l'avion (~25 m de long au lieu de 34)

# ---------------------------------------------------------------- avion blanc
D.DODU = 1.0                 # proportions normales (plus de fuselage "dodu")
D.MATERIAUX["av_vert"] = D._col("AvionBlanc2", (246, 248, 250), 0.35)
D.MATERIAUX["av_vert_fonce"] = D._col("AvionBlanc3", (246, 248, 250), 0.35)
_coque = D.coque


def coque_lisse():
    out, geo = _coque()
    morceaux = [m for k in ("av_blanc", "av_vert", "av_vert_fonce") for m in out.pop(k, [])]
    f = trimesh.util.concatenate(morceaux)
    f.merge_vertices()                                   # fuselage blanc en UNE piece lisse : pas de couture
    out["av_blanc"] = [f]
    return out, geo


D.coque = coque_lisse


def lin(rgb):
    c = np.asarray(rgb, float) / 255.0
    if not APERCU:
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return list(np.round(c * 255).astype(int)) + [255]


M_SOL = {
    # meme materiau que la plateforme du spawn (memes valeurs) pour que les gris soient identiques
    "gris": PBR(name="Gris", baseColorFactor=[140, 143, 148, 255] if not APERCU else [196, 198, 202, 255],
                metallicFactor=0.0, roughnessFactor=0.85),
    "jaune": PBR(name="LigneJaune", baseColorFactor=lin((250, 200, 40)), roughnessFactor=0.6, metallicFactor=0.0),
    "blanc_sol": PBR(name="LigneBlanche", baseColorFactor=lin((240, 242, 245)), roughnessFactor=0.6, metallicFactor=0.0),
}
M_ESC = {
    "esc_blanc": PBR(name="EscBlanc", baseColorFactor=lin((240, 242, 246)), roughnessFactor=0.4, metallicFactor=0.0),
    "esc_metal": PBR(name="EscMetal", baseColorFactor=lin((150, 156, 166)), roughnessFactor=0.35, metallicFactor=0.6),
    "esc_marche": PBR(name="EscMarche", baseColorFactor=lin((70, 74, 82)), roughnessFactor=0.8, metallicFactor=0.0),
    "esc_pneu": PBR(name="EscPneu", baseColorFactor=lin((30, 30, 34)), roughnessFactor=0.9, metallicFactor=0.0),
    "esc_jaune": PBR(name="EscJaune", baseColorFactor=lin((250, 196, 30)), roughnessFactor=0.5, metallicFactor=0.0),
}


def extr(poly, y0, y1):
    """polygone shapely (x, y) -> prisme (x, hauteur, -y), comme la plateforme du spawn"""
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    ms = []
    for g in geoms:
        m = trimesh.creation.extrude_polygon(g, y1 - y0)
        m.apply_transform(rotation_matrix(-np.pi / 2, [1, 0, 0]))
        m.apply_translation([0, y0, 0])
        if m.volume < 0:
            m.invert()
        m.unmerge_vertices()                     # sol plat : normales plates, pas d'ombre en diagonale
        ms.append(m)
    return trimesh.util.concatenate(ms)


def sol():
    ch, so = {}, {}
    disque = Point(X_SOCLE, 0).buffer(R_SOCLE, 128)
    # chemin : bord a bord avec le bout du chemin du spawn et avec le socle (aucune surface en double :
    # deux sols a la meme hauteur l'un sur l'autre scintillent)
    ch["gris"] = [extr(rect(BOUT_CHEMIN, -LARGEUR / 2, X_SOCLE - R_SOCLE + 1.0, LARGEUR / 2).difference(disque), 0.0, H_SOL)]
    muret = disque.difference(Point(X_SOCLE, 0).buffer(R_SOCLE - 0.2, 128))
    muret = muret.difference(rect(X_SOCLE - R_SOCLE - 1, -LARGEUR / 2, X_SOCLE - R_SOCLE + 1, LARGEUR / 2))
    so["gris"] = [extr(disque, 0.0, H_SOL), extr(muret, H_SOL, H_SOL + 0.5)]
    # ligne jaune (du chemin a la roue avant) + barre d'arret, posees 2 cm au-dessus du sol (pas de scintillement)
    x_roue = X_SOCLE - 1.78 * D.S * K
    ligne = rect(X_SOCLE - R_SOCLE + 0.4, -0.12, x_roue + 0.3, 0.12).union(rect(x_roue - 0.15, -1.6, x_roue + 0.15, 1.6))
    so["jaune"] = [extr(ligne, H_SOL, H_SOL + 0.02)]
    return ch, so


def transfo_avion():
    """repere de l'avion (nez vers -Z) -> monde : nez vers -X (vers le spawn), au centre du socle, roues sur le sol"""
    return translation_matrix([X_SOCLE, H_SOL, 0]) @ scale_matrix(K) @ rotation_matrix(np.pi / 2, [0, 1, 0])


def escalier():
    """escalier d'aeroport (marches, limons metal, rampes, petit chassis blanc a roues) contre la porte avant,
    cote +Z du monde (= cote -X de l'avion)"""
    P = {}
    xs, yc, ry, hw = D.sections_fines()
    px, py, s = D.surface_point((xs, yc, ry, hw), -1.48, 0.05)
    T = transfo_avion()
    seuil = (T @ np.array([-px, py - 0.97, -1.48 * D.S, 1.0]))[:3]      # bas de la porte avant gauche
    xp, ys, zp = seuil[0], seuil[1] - H_SOL, seuil[2] + 0.15
    n = max(6, int(round(ys / 0.19)))
    mont, pas, larg = ys / n, 0.3, 1.4
    z0 = zp + 0.8                                                        # palier du haut (0,8 m)
    plat = trimesh.creation.box((larg + 0.2, 0.12, 0.8))
    plat.apply_translation([xp, H_SOL + ys - 0.06, zp + 0.4])
    P.setdefault("esc_marche", []).append(plat)
    for k in range(n - 1):
        y = H_SOL + ys - (k + 1) * mont
        st = trimesh.creation.box((larg, 0.06, pas + 0.02))
        st.apply_translation([xp, y - 0.03, z0 + k * pas + pas / 2])
        P.setdefault("esc_marche", []).append(st)
    z_bas = z0 + (n - 1) * pas
    for sx in (-1, 1):
        xl = xp + sx * (larg / 2 + 0.06)
        a = np.array([xl, H_SOL + ys - 0.1, z0])
        b = np.array([xl, H_SOL + 0.05, z_bas])
        limon = trimesh.creation.box((0.1, 0.28, np.linalg.norm(b - a)))
        limon.apply_transform(rotation_matrix(math.atan2(a[1] - b[1], b[2] - a[2]), [1, 0, 0]))
        limon.apply_translation((a + b) / 2)
        P.setdefault("esc_metal", []).append(limon)
        # rampe : poteaux + main courante (le long de la pente, et autour du palier)
        haut = 1.0
        pts = [np.array([xl, H_SOL + ys + haut, zp + 0.1]), np.array([xl, H_SOL + ys + haut, z0]),
               np.array([xl, H_SOL + haut, z_bas])]
        for p0, p1 in zip(pts[:-1], pts[1:]):
            P.setdefault("esc_metal", []).append(trimesh.creation.cylinder(radius=0.035, segment=[p0, p1], sections=12))
        for p_ in (pts[0], pts[1], pts[2]):
            pied = trimesh.creation.cylinder(radius=0.03, segment=[p_, p_ - np.array([0, haut, 0])], sections=10)
            P.setdefault("esc_metal", []).append(pied)
    # chassis blanc sous le palier, avec 4 roues et une bande jaune/noire
    hc = max(0.4, ys - 0.5)
    ch = trimesh.creation.box((larg + 0.3, hc, 1.6))
    ch.apply_translation([xp, H_SOL + 0.25 + hc / 2, zp + 0.9])
    P.setdefault("esc_blanc", []).append(ch)
    bande = trimesh.creation.box((larg + 0.32, 0.12, 1.62))
    bande.apply_translation([xp, H_SOL + 0.4, zp + 0.9])
    P.setdefault("esc_jaune", []).append(bande)
    for dx in (-1, 1):
        for dz in (0.3, 1.5):
            w = trimesh.creation.cylinder(radius=0.25, height=0.2, sections=24)
            w.apply_transform(rotation_matrix(np.pi / 2, [0, 0, 1]))
            w.apply_translation([xp + dx * (larg / 2 + 0.05), H_SOL + 0.25, zp + dz])
            P.setdefault("esc_pneu", []).append(w)
    for ms in P.values():
        for m in ms:
            if m.is_watertight and m.volume < 0:
                m.invert()
    return P, np.array([xp, H_SOL, z_bas + 1.2])


if __name__ == "__main__":
    av = D.parts()
    av.pop("av_logo", None)
    if not APERCU:
        for m_ in D.MATERIAUX.values():
            D.lineaire(m_)
    ch, so = sol()
    es, pied = escalier()
    objets = [("Claim_Chemin", ch, M_SOL, np.eye(4)), ("Claim_Socle", so, M_SOL, np.eye(4)),
              ("Claim_Avion", av, D.MATERIAUX, transfo_avion()), ("Claim_Escalier", es, M_ESC, np.eye(4))]
    sc = trimesh.Scene()
    for obj, P, MAT, T in objets:
        for k, ms in P.items():
            m = trimesh.util.concatenate([x.copy() for x in ms])
            m.apply_transform(T)
            m.visual = trimesh.visual.TextureVisuals(material=MAT[k])
            sc.add_geometry(m, node_name=f"{obj}__{k}", geom_name=f"{obj}__{k}")
    dossier = LOBBY if not APERCU else os.environ.get("APERCU_DIR", "/tmp")
    chemin = os.path.join(dossier, "Avion_Claim.glb")
    sc.export(chemin)
    # un noeud par objet
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
            nodes.append({"name": o, "mesh": idx[o]})
        meshes[idx[o]]["primitives"] += js["meshes"][nd["mesh"]]["primitives"]
    js["meshes"], js["nodes"] = meshes, nodes
    js["scenes"], js["scene"] = [{"nodes": list(range(len(nodes)))}], 0
    s = json.dumps(js, separators=(",", ":")).encode()
    s += b" " * ((4 - len(s) % 4) % 4)
    open(chemin, "wb").write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(s) + len(rest)) + struct.pack("<II", len(s), 0x4E4F534A) + s + rest)
    print(chemin, round(os.path.getsize(chemin) / 1e3), "Ko   pied de l'escalier (plaque ENTER) :",
          np.round(pied, 2), "m (repere glTF, Y en haut)")
